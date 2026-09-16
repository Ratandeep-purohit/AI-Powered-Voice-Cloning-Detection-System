"""Model-input preprocessing primitives for the voice spoof detector.

This layer sits after the ASVspoof PyTorch Dataset/DataLoader. It performs
model-agnostic tensor hygiene and deterministic length handling while keeping
architecture-specific feature extraction out of the dataset layer.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True, slots=True)
class ModelInputConfig:
    """Configuration for deterministic detector input preparation."""

    sample_rate: int = 16000
    target_duration_seconds: float = 4.0
    normalize: bool = True
    normalization_epsilon: float = 1e-8

    @property
    def target_num_samples(self) -> int:
        return round(self.sample_rate * self.target_duration_seconds)

    def validate(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive.")
        if self.target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be positive.")
        if self.target_num_samples <= 0:
            raise ValueError("target_num_samples must be positive.")
        if self.normalization_epsilon <= 0:
            raise ValueError("normalization_epsilon must be positive.")


class AudioModelInputPreprocessor:
    """Prepare mono waveform tensors for a detector model.

    Expected input shape is ``[channels, time]`` or ``[batch, channels, time]``.
    The current pipeline uses one mono channel. Inputs are made finite,
    optionally peak-normalized, and deterministically cropped/padded to the
    configured duration. No spectrogram, LFCC, or architecture-specific
    feature extraction is performed here.
    """

    def __init__(self, config: ModelInputConfig | None = None) -> None:
        self.config = config or ModelInputConfig()
        self.config.validate()

    def _validate_waveform(self, waveform: Tensor) -> None:
        if not isinstance(waveform, Tensor):
            raise TypeError("waveform must be a torch.Tensor.")
        if waveform.ndim not in {2, 3}:
            raise ValueError(
                "waveform must have shape [channels, time] or [batch, channels, time]."
            )
        if waveform.shape[-1] <= 0:
            raise ValueError("waveform must contain at least one sample.")
        if waveform.shape[-2] != 1:
            raise ValueError("waveform must be mono with exactly one channel.")
        if not torch.is_floating_point(waveform):
            waveform = waveform.float()
        if not torch.isfinite(waveform).all():
            raise ValueError("waveform contains NaN or infinite values.")

    def _normalize(self, waveform: Tensor) -> Tensor:
        if not self.config.normalize:
            return waveform

        peak = waveform.abs().amax(dim=-1, keepdim=True)
        scale = peak.clamp_min(self.config.normalization_epsilon)
        return waveform / scale

    def _fit_length(self, waveform: Tensor) -> tuple[Tensor, Tensor]:
        target = self.config.target_num_samples
        current = waveform.shape[-1]

        if current >= target:
            prepared = waveform[..., :target]
            mask = torch.ones(
                prepared.shape[:-2] + (target,), dtype=torch.bool, device=waveform.device
            )
            return prepared, mask

        pad = target - current
        prepared = torch.nn.functional.pad(waveform, (0, pad))
        mask = torch.zeros(
            prepared.shape[:-2] + (target,), dtype=torch.bool, device=waveform.device
        )
        mask[..., :current] = True
        return prepared, mask

    def prepare(self, waveform: Tensor) -> tuple[Tensor, Tensor]:
        """Return fixed-length waveform and its valid-sample mask."""

        self._validate_waveform(waveform)
        waveform = waveform.float()
        waveform = self._normalize(waveform)
        return self._fit_length(waveform)

    def prepare_batch(self, waveforms: Tensor, attention_mask: Tensor | None = None) -> dict[str, Tensor]:
        """Prepare a batched ``[batch, 1, time]`` tensor.

        An existing DataLoader attention mask is accepted and intersected with
        the generated fixed-length mask so padded source samples stay invalid.
        """

        if not isinstance(waveforms, Tensor) or waveforms.ndim != 3:
            raise ValueError("waveforms must have shape [batch, channels, time].")
        if waveforms.shape[1] != 1:
            raise ValueError("waveforms must be mono with exactly one channel.")
        if waveforms.shape[0] <= 0:
            raise ValueError("waveforms batch must not be empty.")

        prepared, generated_mask = self.prepare(waveforms)

        if attention_mask is not None:
            if attention_mask.ndim != 2:
                raise ValueError("attention_mask must have shape [batch, time].")
            if attention_mask.shape[0] != waveforms.shape[0]:
                raise ValueError("attention_mask batch size must match waveforms.")
            if attention_mask.shape[1] != waveforms.shape[-1]:
                raise ValueError("attention_mask time dimension must match waveforms.")
            source_mask = attention_mask.to(device=prepared.device, dtype=torch.bool)
            if source_mask.shape[-1] >= self.config.target_num_samples:
                source_mask = source_mask[..., : self.config.target_num_samples]
            else:
                source_mask = torch.nn.functional.pad(
                    source_mask,
                    (0, self.config.target_num_samples - source_mask.shape[-1]),
                )
            generated_mask = generated_mask & source_mask

        return {
            "waveforms": prepared,
            "attention_mask": generated_mask,
        }
