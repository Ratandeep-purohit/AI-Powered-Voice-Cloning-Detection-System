"""CLI entry point for Phase 05 AASIST training.

Examples:
    python scripts/train_aasist.py --epochs 1 --max-train-batches 2 --max-dev-batches 1
    python scripts/train_aasist.py --epochs 20 --batch-size 2 --gradient-accumulation-steps 4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow direct execution from backend/scripts without requiring package installation.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.services.aasist_training import AASISTTrainer, AASISTTrainingConfig


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Train the Phase 05 AASIST-family spoof detector.")
    parser.add_argument("--dataset-root", default=settings.asvspoof_dataset_root)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--checkpoint-dir", default="artifacts/checkpoints/aasist")
    parser.add_argument("--no-amp", action="store_true", help="Disable CUDA mixed precision.")
    parser.add_argument("--no-epoch-checkpoints", action="store_true")
    parser.add_argument("--max-train-batches", type=int, default=None)
    parser.add_argument("--max-dev-batches", type=int, default=None)
    parser.add_argument("--resume", default=None, help="Checkpoint path to resume from.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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
    print(f"Dataset: {config.dataset_root}")
    print(f"Batch size: {config.batch_size}")
    print(f"Gradient accumulation: {config.gradient_accumulation_steps}")
    result = trainer.fit()
    print(json.dumps({
        "best_epoch": result.best_epoch,
        "best_f1": result.best_f1,
        "best_checkpoint": result.best_checkpoint,
        "latest_checkpoint": result.latest_checkpoint,
        "history": list(result.history),
    }, indent=2))


if __name__ == "__main__":
    main()
