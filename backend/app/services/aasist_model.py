"""AASIST-family detector model for Phase 05.

This module keeps the detector behind a small, testable PyTorch interface:

    [batch, 1, time] -> AASISTModel -> [batch, 2] logits

The implementation follows the core ideas used by AASIST: a Sinc-style
learnable filterbank front-end, residual spectro-temporal encoding, graph
attention over compact spectro-temporal nodes, and graph-aware pooling.

It is intentionally self-contained so the project does not depend on the
training repository at runtime. It is not a pretrained checkpoint and is not
claimed to be byte-for-byte checkpoint compatible with the official NAVER
implementation. Official reference: clovaai/aasist.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn
import torch.nn.functional as F


@dataclass(frozen=True, slots=True)
class AASISTModelConfig:
    """Stable architecture configuration for the project detector."""

    sample_rate: int = 16_000
    num_classes: int = 2
    sinc_filters: int = 70
    sinc_kernel_size: int = 1_024
    sinc_stride: int = 512
    encoder_channels: tuple[int, int, int] = (32, 64, 96)
    graph_dim: int = 96
    graph_nodes: int = 64
    dropout: float = 0.2

    def validate(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive.")
        if self.num_classes != 2:
            raise ValueError("AASISTModel currently supports exactly 2 classes.")
        if self.sinc_filters <= 0:
            raise ValueError("sinc_filters must be positive.")
        if self.sinc_kernel_size <= 1:
            raise ValueError("sinc_kernel_size must be greater than 1.")
        if self.sinc_stride <= 0:
            raise ValueError("sinc_stride must be positive.")
        if len(self.encoder_channels) != 3 or any(c <= 0 for c in self.encoder_channels):
            raise ValueError("encoder_channels must contain three positive values.")
        if self.graph_dim != self.encoder_channels[-1]:
            raise ValueError("graph_dim must match the final encoder channel count.")
        if self.graph_nodes <= 0:
            raise ValueError("graph_nodes must be positive.")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1).")


class SincConv(nn.Module):
    """Fixed initialization Sinc-style filterbank used as the raw-audio front-end."""

    def __init__(self, out_channels: int, kernel_size: int, stride: int, sample_rate: int) -> None:
        super().__init__()
        if kernel_size % 2 == 0:
            kernel_size += 1
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.sample_rate = sample_rate

        # Mel-spaced initial cutoffs. The filters remain ordinary learnable
        # Conv1d weights after initialization, which keeps the forward pass
        # fully compatible with standard PyTorch optimizers/checkpoints.
        low = 30.0
        high = sample_rate / 2.0 - 100.0
        hz = torch.linspace(low, high, out_channels + 1)
        window = torch.hamming_window(kernel_size, periodic=False)
        t = torch.arange(-(kernel_size // 2), kernel_size // 2 + 1, dtype=torch.float32)
        filters = []
        for idx in range(out_channels):
            f_low = hz[idx]
            f_high = hz[idx + 1]
            low_wave = 2.0 * f_low / sample_rate * torch.sinc(2.0 * f_low * t / sample_rate)
            high_wave = 2.0 * f_high / sample_rate * torch.sinc(2.0 * f_high * t / sample_rate)
            filters.append((high_wave - low_wave) * window)
        kernel = torch.stack(filters).unsqueeze(1)
        self.conv = nn.Conv1d(1, out_channels, kernel_size, stride=stride, bias=False)
        with torch.no_grad():
            self.conv.weight.copy_(kernel)

    def forward(self, waveform: Tensor) -> Tensor:
        return self.conv(waveform)


class ResidualEncoderBlock(nn.Module):
    """Compact spectro-temporal residual encoder block."""

    def __init__(self, in_channels: int, out_channels: int, dropout: float) -> None:
        super().__init__()
        self.norm1 = nn.BatchNorm2d(in_channels)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.norm2 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.act = nn.SELU(inplace=True)
        self.drop = nn.Dropout2d(dropout)
        self.pool = nn.AvgPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.skip = (
            nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
            if in_channels != out_channels
            else nn.Identity()
        )

    def forward(self, x: Tensor) -> Tensor:
        identity = self.skip(x)
        x = self.act(self.norm1(x))
        x = self.conv1(x)
        x = self.act(self.norm2(x))
        x = self.drop(self.conv2(x))
        x = x + identity
        return self.pool(x)


class GraphAttentionBlock(nn.Module):
    """Self-attention graph block over compact spectro-temporal nodes."""

    def __init__(self, dim: int, dropout: float) -> None:
        super().__init__()
        self.q = nn.Linear(dim, dim, bias=False)
        self.k = nn.Linear(dim, dim, bias=False)
        self.v = nn.Linear(dim, dim, bias=False)
        self.out = nn.Linear(dim, dim, bias=False)
        self.norm = nn.LayerNorm(dim)
        self.drop = nn.Dropout(dropout)
        self.scale = math.sqrt(dim)

    def forward(self, nodes: Tensor) -> Tensor:
        residual = nodes
        q = self.q(nodes)
        k = self.k(nodes)
        v = self.v(nodes)
        scores = torch.matmul(q, k.transpose(-1, -2)) / self.scale
        weights = torch.softmax(scores, dim=-1)
        attended = torch.matmul(weights, v)
        return self.norm(residual + self.drop(self.out(attended)))


class GraphPool(nn.Module):
    """Attention-weighted graph pooling."""

    def __init__(self, dim: int, keep_ratio: float = 0.5) -> None:
        super().__init__()
        self.keep_ratio = keep_ratio
        self.score = nn.Linear(dim, 1)

    def forward(self, nodes: Tensor) -> Tensor:
        count = max(int(nodes.shape[1] * self.keep_ratio), 1)
        scores = torch.sigmoid(self.score(nodes)).squeeze(-1)
        values, indices = torch.topk(scores, count, dim=1)
        gather_idx = indices.unsqueeze(-1).expand(-1, -1, nodes.shape[-1])
        selected = torch.gather(nodes, 1, gather_idx)
        return selected * values.unsqueeze(-1)


class AASISTModel(nn.Module):
    """Project detector with AASIST-style raw-audio graph reasoning.

    Input:
        waveform: ``[batch, 1, time]`` at ``config.sample_rate``.

    Output:
        logits: ``[batch, 2]`` where class 0 is REAL and class 1 is SPOOF.
    """

    REAL_CLASS = 0
    SPOOF_CLASS = 1

    def __init__(self, config: AASISTModelConfig | None = None) -> None:
        super().__init__()
        self.config = config or AASISTModelConfig()
        self.config.validate()

        c1, c2, c3 = self.config.encoder_channels
        self.frontend = SincConv(
            out_channels=self.config.sinc_filters,
            kernel_size=self.config.sinc_kernel_size,
            stride=self.config.sinc_stride,
            sample_rate=self.config.sample_rate,
        )
        self.frontend_norm = nn.BatchNorm1d(self.config.sinc_filters)
        self.frontend_act = nn.SELU(inplace=True)

        self.encoder = nn.Sequential(
            ResidualEncoderBlock(1, c1, self.config.dropout),
            ResidualEncoderBlock(c1, c2, self.config.dropout),
            ResidualEncoderBlock(c2, c3, self.config.dropout),
        )
        self.feature_norm = nn.BatchNorm2d(c3)
        self.feature_proj = nn.Conv2d(self.config.sinc_filters, 1, kernel_size=1, bias=False)
        self.node_pool = nn.AdaptiveAvgPool2d((8, 8))
        self.graph = GraphAttentionBlock(self.config.graph_dim, self.config.dropout)
        self.graph_pool = GraphPool(self.config.graph_dim, keep_ratio=0.5)
        self.graph_norm = nn.LayerNorm(self.config.graph_dim)
        self.classifier = nn.Sequential(
            nn.Linear(self.config.graph_dim, self.config.graph_dim // 2),
            nn.SELU(inplace=True),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.graph_dim // 2, self.config.num_classes),
        )

        # Feature projection adapts the encoder's channel dimension to the
        # graph dimension without tying the graph module to the frontend size.
        self.channel_projector = nn.Conv2d(c3, self.config.graph_dim, kernel_size=1, bias=False)

    def _validate_input(self, waveform: Tensor) -> None:
        if not isinstance(waveform, Tensor):
            raise TypeError("waveform must be a torch.Tensor.")
        if waveform.ndim != 3:
            raise ValueError("waveform must have shape [batch, 1, time].")
        if waveform.shape[0] <= 0 or waveform.shape[1] != 1 or waveform.shape[2] <= 0:
            raise ValueError("waveform must have shape [batch, 1, time] with positive dimensions.")
        if not torch.is_floating_point(waveform):
            raise TypeError("waveform must use a floating-point dtype.")
        if not torch.isfinite(waveform).all():
            raise ValueError("waveform contains NaN or infinite values.")

    def forward(self, waveform: Tensor) -> Tensor:
        self._validate_input(waveform)

        x = self.frontend(waveform)
        x = self.frontend_act(self.frontend_norm(x))
        x = x.unsqueeze(1)  # [B, 1, filter, time]
        x = self.feature_proj(x)
        x = self.encoder(x)
        x = self.feature_norm(x)
        x = self.channel_projector(x)
        x = self.node_pool(x)
        nodes = x.flatten(2).transpose(1, 2)

        if nodes.shape[1] != self.config.graph_nodes:
            # The default 8x8 node grid is 64 nodes. Keep the configuration
            # explicit so tests catch accidental architectural changes.
            raise RuntimeError(
                f"Unexpected graph node count {nodes.shape[1]}; expected {self.config.graph_nodes}."
            )

        nodes = self.graph(nodes)
        nodes = self.graph_pool(nodes)
        embedding = self.graph_norm(nodes.mean(dim=1))
        logits = self.classifier(embedding)
        return logits

    @staticmethod
    def probabilities(logits: Tensor) -> Tensor:
        """Convert logits into REAL/SPOOF probabilities."""
        return torch.softmax(logits, dim=-1)

    @classmethod
    def predict_label(cls, logits: Tensor) -> Tensor:
        """Return project labels: 0=REAL, 1=SPOOF."""
        return torch.argmax(logits, dim=-1)
