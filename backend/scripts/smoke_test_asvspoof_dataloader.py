"""Smoke-test the ASVspoof PyTorch DataLoader against a local dataset.

This script intentionally runs outside the automated unit-test suite because
it requires the real ASVspoof 2019 LA corpus on the local machine.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from app.services.asvspoof_integrity import ASVspoofIntegrityValidator
from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn


def _check_split(root: Path, split: str, batch_size: int, target_sample_rate: int, device: torch.device) -> None:
    dataset = ASVspoofTorchDataset(root, split, sample_rate=target_sample_rate)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=asvspoof_collate_fn,
    )

    batch = next(iter(loader))
    waveforms = batch["waveforms"]
    labels = batch["labels"]
    mask = batch["attention_mask"]

    if waveforms.ndim != 3 or waveforms.shape[1] != 1:
        raise RuntimeError(f"{split}: unexpected waveform batch shape: {tuple(waveforms.shape)}")
    if labels.ndim != 1 or labels.shape[0] != waveforms.shape[0]:
        raise RuntimeError(f"{split}: label batch shape does not match waveform batch.")
    if mask.shape != (waveforms.shape[0], waveforms.shape[-1]):
        raise RuntimeError(f"{split}: attention mask shape mismatch: {tuple(mask.shape)}")
    if not torch.isfinite(waveforms).all():
        raise RuntimeError(f"{split}: waveform batch contains non-finite values.")
    if not torch.all((labels == 0) | (labels == 1)):
        raise RuntimeError(f"{split}: labels contain values other than REAL=0/SPOOF=1.")

    gpu_waveforms = waveforms.to(device)
    gpu_labels = labels.to(device)
    gpu_mask = mask.to(device)

    if gpu_waveforms.device != device or gpu_labels.device != device or gpu_mask.device != device:
        raise RuntimeError(f"{split}: CUDA/device transfer failed.")

    real_count = int((labels == 0).sum())
    spoof_count = int((labels == 1).sum())
    valid_samples = int(mask.sum())

    print(
        f"{split}: samples={len(dataset)}, batch={waveforms.shape[0]}, "
        f"shape={tuple(waveforms.shape)}, real={real_count}, spoof={spoof_count}, "
        f"valid_samples={valid_samples}, device={device}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the real ASVspoof 2019 LA DataLoader.")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--sample-rate", type=int, default=16000)
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    if args.sample_rate <= 0:
        raise SystemExit("--sample-rate must be positive")

    root = args.dataset_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Dataset root does not exist: {root}")

    print(f"Dataset root: {root}")
    print("Running integrity validation...")
    report = ASVspoofIntegrityValidator(root).validate()
    for split_report in report.splits:
        print(
            f"{split_report.split}: total={split_report.total}, real={split_report.real}, "
            f"spoof={split_report.spoof}, missing={split_report.missing}, "
            f"duplicates={split_report.duplicate_audio_ids}, passed={split_report.passed}"
        )
    if not report.passed:
        raise SystemExit("ASVspoof integrity validation failed; DataLoader smoke test aborted.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute device: {device}")
    if device.type != "cuda":
        raise SystemExit("CUDA is not available; this smoke test requires the configured GPU environment.")

    for split in ("train", "dev", "eval"):
        _check_split(root, split, args.batch_size, args.sample_rate, device)

    print("OVERALL: ASVspoof DataLoader smoke test passed")


if __name__ == "__main__":
    main()
