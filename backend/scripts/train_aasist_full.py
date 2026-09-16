"""Full ASVspoof2019 LA training entry point for the Phase 05 detector.

This script intentionally uses the existing AASIST training engine instead of
creating a second training implementation. It performs a dataset integrity
check, prints the real train/dev class counts, and starts an unrestricted
training run unless explicit debug limits are supplied.

Recommended RTX 3050 profile:
    python scripts/train_aasist_full.py --dataset-root "E:\\DataSet\\LA"

The ASVspoof dataset itself must remain outside Git; only code and metadata
belong in the repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.aasist_training import AASISTTrainer, AASISTTrainingConfig
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator
from app.services.asvspoof_torch import ASVspoofTorchDataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run full ASVspoof2019 LA training for the AASIST-family detector."
    )
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--checkpoint-dir", default="artifacts/checkpoints/aasist")
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument("--no-epoch-checkpoints", action="store_true")
    parser.add_argument("--resume", default=None)
    parser.add_argument("--max-train-batches", type=int, default=None)
    parser.add_argument("--max-dev-batches", type=int, default=None)
    return parser.parse_args()


def validate_dataset(root: str) -> None:
    print("Validating ASVspoof dataset integrity...")
    report = ASVspoofIntegrityValidator(root).validate_all()
    for split in ("train", "dev", "eval"):
        result = report[split]
        print(
            f"{split}: total={result.total_entries} "
            f"real={result.real_entries} spoof={result.spoof_entries} "
            f"missing={result.missing_audio} duplicates={result.duplicate_audio_ids} "
            f"passed={result.passed}"
        )
    if not report.passed:
        raise RuntimeError("ASVspoof dataset integrity validation failed; training aborted.")


def print_class_counts(root: str) -> None:
    train = ASVspoofTorchDataset(root, "train")
    dev = ASVspoofTorchDataset(root, "dev")
    print(f"Train class counts [REAL, SPOOF]: {train.label_counts}")
    print(f"Dev class counts   [REAL, SPOOF]: {dev.label_counts}")


def main() -> None:
    args = parse_args()
    validate_dataset(args.dataset_root)
    print_class_counts(args.dataset_root)

    config = AASISTTrainingConfig(
        dataset_root=args.dataset_root,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        num_workers=args.num_workers,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        target_duration_seconds=args.target_duration_seconds,
        mixed_precision=not args.no_amp,
        device=args.device,
        checkpoint_dir=args.checkpoint_dir,
        checkpoint_every_epoch=not args.no_epoch_checkpoints,
        max_train_batches=args.max_train_batches,
        max_dev_batches=args.max_dev_batches,
    )

    trainer = AASISTTrainer(config)
    if args.resume:
        trainer.resume(args.resume)

    print(f"Device: {trainer.device}")
    print(f"AMP: {trainer.use_amp}")
    print(f"Epochs: {config.epochs}")
    print(f"Batch size: {config.batch_size}")
    print(f"Gradient accumulation: {config.gradient_accumulation_steps}")
    print(f"Target duration: {config.target_duration_seconds:.2f}s")
    print("Starting full training...")

    result = trainer.fit()
    print("\nTraining complete.")
    print(f"Best epoch: {result.best_epoch}")
    print(f"Best dev F1: {result.best_f1:.4f}")
    print(f"Best checkpoint: {result.best_checkpoint}")
    print(f"Latest checkpoint: {result.latest_checkpoint}")


if __name__ == "__main__":
    main()
