"""Evaluate the trained Phase 05 AASIST-family detector on ASVspoof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.services.aasist_evaluation import AASISTEvaluator
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Evaluate the trained AASIST-family spoof detector on ASVspoof2019 LA."
    )
    parser.add_argument("--dataset-root", default=settings.asvspoof_dataset_root, required=not bool(settings.asvspoof_dataset_root))
    parser.add_argument("--checkpoint", default="artifacts/checkpoints/aasist_balanced/best.pt")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--threshold", type=float, default=settings.aasist_detection_threshold, help="Fixed spoof decision threshold; default is the DEV-derived operating point.")
    parser.add_argument("--no-amp", action="store_true", help="Disable CUDA mixed precision during evaluation.")
    parser.add_argument("--output", default="artifacts/evaluation/aasist/eval.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    checkpoint = Path(args.checkpoint).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    print(f"Dataset root: {dataset_root}")
    print(f"Checkpoint: {checkpoint}")
    print(f"Decision threshold: {args.threshold:.4f}")
    print("Validating ASVspoof dataset integrity...")
    report = ASVspoofIntegrityValidator(dataset_root).validate()
    for split in report.splits:
        print(
            f"{split.split}: total={split.total}, real={split.real}, spoof={split.spoof}, "
            f"missing={split.missing}, duplicates={split.duplicate_audio_ids}, passed={split.passed}"
        )
    if not report.passed:
        raise SystemExit("ASVspoof integrity validation failed; evaluation aborted.")

    evaluator = AASISTEvaluator(
        dataset_root,
        checkpoint,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        target_duration_seconds=args.target_duration_seconds,
        device=args.device,
        mixed_precision=not args.no_amp,
        threshold=args.threshold,
    )
    print(f"Device: {evaluator.device}")
    print(f"AMP: {evaluator.device.type == 'cuda' and not args.no_amp}")
    print("Starting full Eval split inference...")
    result = evaluator.evaluate("eval")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    metrics = result.metrics
    print("\nEvaluation complete.")
    print(f"Samples: {metrics.samples}")
    print(f"Accuracy: {metrics.accuracy:.4f}")
    print(f"Precision: {metrics.precision:.4f}")
    print(f"Recall: {metrics.recall:.4f}")
    print(f"F1: {metrics.f1:.4f}")
    print(f"ROC-AUC: {metrics.roc_auc:.4f}" if metrics.roc_auc is not None else "ROC-AUC: N/A")
    print(f"EER: {metrics.eer:.4f}" if metrics.eer is not None else "EER: N/A")
    print(
        "Confusion matrix [[TN, FP], [FN, TP]]: "
        f"[[{metrics.true_negative}, {metrics.false_positive}], "
        f"[{metrics.false_negative}, {metrics.true_positive}]]"
    )
    print(f"JSON report: {output}")


if __name__ == "__main__":
    main()
