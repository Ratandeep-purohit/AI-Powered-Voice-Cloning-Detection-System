"""Analyze AASIST spoof scores and decision thresholds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.services.aasist_threshold_analysis import collect_and_analyze
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Analyze AASIST SPOOF scores and threshold operating points."
    )
    parser.add_argument(
        "--dataset-root",
        default=settings.asvspoof_dataset_root,
        required=not bool(settings.asvspoof_dataset_root),
    )
    parser.add_argument("--checkpoint", default="artifacts/checkpoints/aasist/best.pt")
    parser.add_argument("--split", choices=["train", "dev", "eval"], default="dev")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--target-duration-seconds", type=float, default=4.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument("--grid-start", type=float, default=0.0)
    parser.add_argument("--grid-stop", type=float, default=1.0)
    parser.add_argument("--grid-step", type=float, default=0.01)
    parser.add_argument(
        "--output",
        default="artifacts/evaluation/aasist/threshold_analysis.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    checkpoint = Path(args.checkpoint).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    print(f"Dataset root: {dataset_root}")
    print(f"Checkpoint: {checkpoint}")
    print(f"Analysis split: {args.split}")
    print("Validating ASVspoof dataset integrity...")
    report = ASVspoofIntegrityValidator(dataset_root).validate()
    for split in report.splits:
        print(
            f"{split.split}: total={split.total}, real={split.real}, spoof={split.spoof}, "
            f"missing={split.missing}, duplicates={split.duplicate_audio_ids}, passed={split.passed}"
        )
    if not report.passed:
        raise SystemExit("ASVspoof integrity validation failed; threshold analysis aborted.")

    result = collect_and_analyze(
        str(dataset_root),
        str(checkpoint),
        split=args.split,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        target_duration_seconds=args.target_duration_seconds,
        device=args.device,
        mixed_precision=not args.no_amp,
        grid_start=args.grid_start,
        grid_stop=args.grid_stop,
        grid_step=args.grid_step,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    best_f1 = result.best_f1
    best_balanced = result.best_balanced_accuracy
    eer_point = result.eer_operating_point
    real = result.score_statistics["real"]
    spoof = result.score_statistics["spoof"]

    print("\nThreshold analysis complete.")
    print(f"Samples: {result.samples} (REAL={result.real_samples}, SPOOF={result.spoof_samples})")
    print(
        "REAL score distribution: "
        f"min={real.minimum:.4f} p01={real.p01:.4f} median={real.median:.4f} "
        f"p99={real.p99:.4f} max={real.maximum:.4f}"
    )
    print(
        "SPOOF score distribution: "
        f"min={spoof.minimum:.4f} p01={spoof.p01:.4f} median={spoof.median:.4f} "
        f"p99={spoof.p99:.4f} max={spoof.maximum:.4f}"
    )
    print(
        "Best F1 operating point: "
        f"threshold={best_f1.threshold:.4f} F1={best_f1.f1:.4f} "
        f"FAR={best_f1.far:.4f} FRR={best_f1.frr:.4f} "
        f"TP={best_f1.true_positive} TN={best_f1.true_negative} "
        f"FP={best_f1.false_positive} FN={best_f1.false_negative}"
    )
    print(
        "Best balanced-accuracy point: "
        f"threshold={best_balanced.threshold:.4f} balanced_accuracy={best_balanced.balanced_accuracy:.4f} "
        f"FAR={best_balanced.far:.4f} FRR={best_balanced.frr:.4f}"
    )
    print(
        "EER operating point: "
        f"threshold={eer_point.threshold:.4f} FAR={eer_point.far:.4f} FRR={eer_point.frr:.4f}"
    )
    print(f"JSON report: {output}")


if __name__ == "__main__":
    main()
