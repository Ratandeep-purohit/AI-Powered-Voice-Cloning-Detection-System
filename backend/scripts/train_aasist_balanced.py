"""Run a class-balanced AASIST training experiment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.aasist_balanced_training import BalancedAASISTTrainer, BalancedTrainingConfig, save_json_report
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the AASIST-family detector with balanced REAL/SPOOF sampling.")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--samples-per-epoch", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument("--max-dev-batches", type=int, default=None)
    parser.add_argument("--checkpoint-dir", default="artifacts/checkpoints/aasist_balanced")
    parser.add_argument("--output", default="artifacts/evaluation/aasist/balanced_training.json")
    return parser.parse_args()


def validate_dataset(root: str) -> None:
    print("Validating ASVspoof dataset integrity...")
    results = [ASVspoofIntegrityValidator(root).validate_split(split) for split in ("train", "dev", "eval")]
    for result in results:
        print(f"{result.split}: total={result.total} real={result.real} spoof={result.spoof} missing={result.missing} duplicates={result.duplicate_audio_ids} passed={result.passed}")
    if not all(result.passed for result in results):
        raise RuntimeError("ASVspoof dataset integrity validation failed; training aborted.")


def main() -> None:
    args = parse_args()
    validate_dataset(args.dataset_root)
    config = BalancedTrainingConfig(
        dataset_root=args.dataset_root,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        num_workers=args.num_workers,
        target_duration_seconds=args.target_duration_seconds,
        device=args.device,
        mixed_precision=not args.no_amp,
        samples_per_epoch=args.samples_per_epoch,
        checkpoint_dir=args.checkpoint_dir,
        seed=args.seed,
        max_dev_batches=args.max_dev_batches,
    )
    trainer = BalancedAASISTTrainer(config)
    print(f"Device: {trainer.device}")
    print(f"Balanced samples/epoch: {config.samples_per_epoch or len(trainer.train_dataset)}")
    print(f"Batch size: {config.batch_size}")
    print(f"Epochs: {config.epochs}")
    print("Starting class-balanced training...")
    result = trainer.fit()
    output = save_json_report(result, args.output)
    print("\nBalanced training complete.")
    print(f"Best epoch: {result['best_epoch']}")
    print(f"Best dev balanced accuracy: {result['best_balanced_accuracy']:.4f}")
    print(f"Best checkpoint: {result['best_checkpoint']}")
    print(f"JSON report: {output}")


if __name__ == "__main__":
    main()
