"""PyTorch dataset primitives for ASVspoof 2019 LA.

This layer converts validated ASVspoof protocol entries into waveform tensors
without applying model-specific feature extraction. Model preprocessing remains
a separate concern so the eventual detector can define its own requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
import torchaudio
from torch import Tensor
from torch.utils.data import Dataset

from app.services.asvspoof import ASVspoofProtocolEntry, ASVspoofProtocolError
from app.services.asvspoof_dataset import ASVspoofDatasetResolver


@dataclass(frozen=True, slots=True)
class ASVspoofTorchSample:
    """One model-ready dataset sample before batching."""

    waveform: Tensor
    sample_rate: int
    label: int
    split: str
    speaker_id: str
    audio_id: str
    path: Path


class ASVspoofTorchDataset(Dataset[ASVspoofTorchSample]):
    """Load one ASVspoof split as waveform tensors.

    Labels use the project convention: REAL=0 and SPOOF=1.
    Audio is converted to mono and resampled to ``sample_rate`` when needed.
    No model-specific feature extraction is performed here.
    """

    LABEL_TO_ID = {"REAL": 0, "SPOOF": 1}

    def __init__(self, dataset_root: str | Path, split: str, sample_rate: int = 16000) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive.")

        normalized_split = split.strip().lower()
        if normalized_split not in {"train", "dev", "eval"}:
            raise ASVspoofProtocolError(
                f"Unsupported ASVspoof split '{split}'. Supported splits: train, dev, eval."
            )

        self.split = normalized_split
        self.sample_rate = sample_rate
        self.resolver = ASVspoofDatasetResolver(dataset_root)
        self.entries = self.resolver.parser.load_split(self.split)
        self.resolutions = self.resolver.resolve_split(self.split, self.entries)

    def __len__(self) -> int:
        return len(self.resolutions)

    def __getitem__(self, index: int) -> ASVspoofTorchSample:
        if index < 0 or index >= len(self.resolutions):
            raise IndexError(f"ASVspoof dataset index out of range: {index}")

        resolution = self.resolutions[index]
        waveform, source_sample_rate = torchaudio.load(str(resolution.path))

        if waveform.numel() == 0:
            raise ASVspoofProtocolError(f"ASVspoof audio file is empty: {resolution.path}")

        waveform = waveform.float()
        if waveform.ndim != 2:
            raise ASVspoofProtocolError(
                f"Unexpected waveform shape for {resolution.path}: {tuple(waveform.shape)}"
            )

        # Standardize channels at the dataset boundary. The model receives
        # [1, time] waveforms regardless of source channel count.
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        elif waveform.shape[0] == 0:
            raise ASVspoofProtocolError(f"ASVspoof audio has no channels: {resolution.path}")

        if source_sample_rate != self.sample_rate:
            waveform = torchaudio.functional.resample(
                waveform,
                orig_freq=source_sample_rate,
                new_freq=self.sample_rate,
            )

        try:
            label = self.LABEL_TO_ID[resolution.label]
        except KeyError as exc:
            raise ASVspoofProtocolError(
                f"Unsupported resolved ASVspoof label '{resolution.label}'."
            ) from exc

        return ASVspoofTorchSample(
            waveform=waveform,
            sample_rate=self.sample_rate,
            label=label,
            split=resolution.split,
            speaker_id=resolution.speaker_id,
            audio_id=resolution.audio_id,
            path=resolution.path,
        )


def asvspoof_collate_fn(samples: list[ASVspoofTorchSample]) -> dict[str, Tensor | list[str]]:
    """Pad variable-length waveforms into a batch.

    Returns ``waveforms`` shaped ``[batch, 1, max_time]`` and a boolean
    ``attention_mask`` identifying real samples. This keeps the Dataset free of
    arbitrary crop/pad policy while still making DataLoader batching possible.
    """

    if not samples:
        raise ValueError("Cannot collate an empty ASVspoof batch.")

    sample_rate = samples[0].sample_rate
    if any(sample.sample_rate != sample_rate for sample in samples):
        raise ValueError("All ASVspoof samples in a batch must use the same sample rate.")

    max_time = max(sample.waveform.shape[-1] for sample in samples)
    waveforms = torch.zeros((len(samples), 1, max_time), dtype=torch.float32)
    attention_mask = torch.zeros((len(samples), max_time), dtype=torch.bool)

    for batch_index, sample in enumerate(samples):
        length = sample.waveform.shape[-1]
        waveforms[batch_index, :, :length] = sample.waveform
        attention_mask[batch_index, :length] = True

    return {
        "waveforms": waveforms,
        "attention_mask": attention_mask,
        "labels": torch.tensor([sample.label for sample in samples], dtype=torch.long),
        "sample_rate": torch.tensor(sample_rate, dtype=torch.long),
        "audio_ids": [sample.audio_id for sample in samples],
        "speaker_ids": [sample.speaker_id for sample in samples],
        "paths": [str(sample.path) for sample in samples],
    }
