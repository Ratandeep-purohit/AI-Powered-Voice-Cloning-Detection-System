"""Run a controlled balanced AASIST training diagnosis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.aasist_training_diagnostics import BalancedSmokeConfig, run_balanced_smoke, save_json_report
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose AASIST training with a deterministic balanced REAL/SPOOF smoke experiment."
    )
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--samples-per-class", type=int, default=250)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="artifacts/evaluation/aasist/training_diagnosis.json")
    return parser.parse_args()


def validate_dataset(root: str) -> None:
    print("Validating ASVspoof dataset integrity...")
    validator = ASVspoofIntegrityValidator(root)
    results = [validator.validate_split(split) for split in ("train", "dev", "eval")]
    for result in results:
        print(
            f"{result.split}: total={result.total} real={result.real} spoof={result.spoof} "
            f"missing={result.missing} duplicates={result.duplicate_audio_ids} passed={result.passed}"
        )
    if not all(result.passed for result in results):
        raise RuntimeError("ASVspoof dataset integrity validation failed; diagnosis aborted.")


def main() -> None:
    args = parse_args()
    validate_dataset(args.dataset_root)
    config = BalancedSmokeConfig(
        dataset_root=args.dataset_root,
        samples_per_class=args.samples_per_class,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        target_duration_seconds=args.target_duration_seconds,
        device=args.device,
        mixed_precision=not args.no_amp,
        seed=args.seed,
    )
    report = run_balanced_smoke(config)
    output = save_json_report(report, args.output)

    before = report["before"]
    after = report["after"]
    print("\nBalanced smoke diagnosis complete.")
    print(f"Device: {report['device']}")
    print(f"Balanced train samples: {report['balanced_train_samples']}")
    print(f"Balanced dev samples: {report['balanced_dev_samples']}")
    print(f"Class weights [REAL, SPOOF]: {report['class_weights']}")
    print(
        f"Before: F1={before['f1']:.4f} AUC={before['roc_auc']} EER={before['eer']} "
        f"predicted REAL={before['predicted_real']} SPOOF={before['predicted_spoof']}"
    )
    print(
        f"After:  F1={after['f1']:.4f} AUC={after['roc_auc']} EER={after['eer']} "
        f"predicted REAL={after['predicted_real']} SPOOF={after['predicted_spoof']}"
    )
    print(f"JSON report: {output}")


if __name__ == "__main__":
    main()
