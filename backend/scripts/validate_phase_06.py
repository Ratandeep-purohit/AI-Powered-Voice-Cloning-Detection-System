"""One-command validation gate for Phase 06 AASIST inference integration.

This intentionally keeps expensive full Eval inference opt-in. Development and
phase-completion checks should validate code, configuration, dataset integrity,
checkpoint compatibility, and a real inference smoke path without repeatedly
processing all 71k Eval samples.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.services.aasist_inference import build_aasist_inference_service
from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Run the consolidated Phase 06 validation gate."
    )
    parser.add_argument(
        "--dataset-root",
        default=settings.asvspoof_dataset_root,
        required=not bool(settings.asvspoof_dataset_root),
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
    )
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument(
        "--full-eval",
        action="store_true",
        help="Also run the full 71k-sample Eval inference. This is intentionally opt-in and can take ~25+ minutes.",
    )
    parser.add_argument(
        "--pytest-all",
        action="store_true",
        help="Run the complete backend test suite instead of the Phase 06-focused suite.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/evaluation/phase_06_validation.json",
    )
    return parser.parse_args()


def run_command(command: list[str], label: str) -> dict[str, object]:
    print(f"\n[CHECK] {label}")
    print("$ " + " ".join(command))
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=BACKEND_ROOT, check=False)
    elapsed = round(time.perf_counter() - started, 2)
    result = {"label": label, "passed": completed.returncode == 0, "returncode": completed.returncode, "seconds": elapsed}
    print(f"[{'PASS' if result['passed'] else 'FAIL'}] {label} ({elapsed}s)")
    if not result["passed"]:
        raise SystemExit(completed.returncode or 1)
    return result


def validate_dataset(dataset_root: Path) -> dict[str, object]:
    print("\n[CHECK] ASVspoof dataset integrity")
    validator = ASVspoofIntegrityValidator(dataset_root)
    report = validator.validate()
    splits = []
    for split in report.splits:
        item = {
            "split": split.split,
            "total": split.total,
            "real": split.real,
            "spoof": split.spoof,
            "missing": split.missing,
            "duplicates": split.duplicate_audio_ids,
            "passed": split.passed,
        }
        splits.append(item)
        print(
            f"  {split.split}: total={split.total}, real={split.real}, spoof={split.spoof}, "
            f"missing={split.missing}, duplicates={split.duplicate_audio_ids}, passed={split.passed}"
        )
    if not report.passed:
        raise SystemExit("ASVspoof dataset integrity validation failed.")
    return {"label": "ASVspoof dataset integrity", "passed": True, "splits": splits}


def write_smoke_wav(path: Path, seconds: float = 4.0) -> None:
    sample_rate = 16_000
    frame_count = int(sample_rate * seconds)
    frames = bytearray()
    for index in range(frame_count):
        # Deterministic low-amplitude waveform; this is only a model-loading/inference smoke input.
        sample = int(800 * ((index % 80) - 40) / 40)
        frames.extend(struct.pack("<h", sample))
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(bytes(frames))


def run_inference_smoke() -> dict[str, object]:
    print("\n[CHECK] Real checkpoint inference smoke test")
    settings = get_settings()
    with tempfile.TemporaryDirectory(prefix="phase06-aasist-") as temp_dir:
        temp_root = Path(temp_dir)
        settings.audio_storage_path = str(temp_root)
        relative_key = "processed/phase06-smoke.wav"
        audio_path = temp_root / relative_key
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        write_smoke_wav(audio_path)

        service = build_aasist_inference_service(settings, device="auto", mixed_precision=True)
        result = service.predict_processed_audio(relative_key)

        checks = {
            "checkpoint_loaded": True,
            "device": str(service.device),
            "model_name": result.model_name,
            "model_version": result.model_version,
            "threshold": result.threshold,
            "predicted_label": result.predicted_label,
            "probabilities_sum_to_one": abs(
                result.spoof_probability + result.authentic_probability - 1.0
            ) < 1e-4,
            "confidence_in_range": 0.0 <= result.confidence <= 1.0,
            "processing_time_ms_nonnegative": result.processing_time_ms >= 0,
        }
        for key, value in checks.items():
            print(f"  {key}: {value}")
        if not all(bool(value) for value in checks.values() if isinstance(value, bool)):
            raise SystemExit("AASIST inference smoke test failed.")
        return {"label": "Real checkpoint inference smoke test", "passed": True, **checks}


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    output = (BACKEND_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()

    print("=" * 72)
    print("PHASE 06 — CONSOLIDATED VALIDATION GATE")
    print("=" * 72)
    print(f"Backend: {BACKEND_ROOT}")
    print(f"Dataset: {dataset_root}")
    print(f"Full Eval: {'ENABLED' if args.full_eval else 'SKIPPED (use --full-eval)'}")

    checks: list[dict[str, object]] = []
    checks.append(validate_dataset(dataset_root))

    focused_tests = [
        "tests/test_aasist_model.py",
        "tests/test_aasist_training.py",
        "tests/test_aasist_training_diagnostics.py",
        "tests/test_aasist_inference.py",
    ]
    if args.pytest_all:
        checks.append(run_command([sys.executable, "-m", "pytest", "-q"], "Complete backend test suite"))
    else:
        checks.append(run_command([sys.executable, "-m", "pytest", "-q", *focused_tests], "Phase 05/06 ML and inference tests"))

    checks.append(run_command([sys.executable, "-m", "compileall", "-q", "app", "scripts"], "Python compile check"))
    checks.append(run_inference_smoke())

    if args.full_eval:
        settings = get_settings()
        checkpoint = Path(settings.aasist_checkpoint_path).expanduser().resolve()
        eval_output = BACKEND_ROOT / "artifacts/evaluation/aasist/eval.json"
        checks.append(
            run_command(
                [
                    sys.executable,
                    "scripts/evaluate_aasist.py",
                    "--dataset-root",
                    str(dataset_root),
                    "--checkpoint",
                    str(checkpoint),
                    "--batch-size",
                    "2",
                    "--device",
                    args.device,
                    "--threshold",
                    str(settings.aasist_detection_threshold),
                    *( ["--no-amp"] if args.no_amp else [] ),
                    "--output",
                    str(eval_output),
                ],
                "Full held-out Eval inference",
            )
        )

    report = {
        "phase": "06",
        "passed": True,
        "decision_threshold": get_settings().aasist_detection_threshold,
        "full_eval_requested": args.full_eval,
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("PHASE 06 VALIDATION PASSED")
    print("=" * 72)
    print(f"Decision threshold: {report['decision_threshold']:.4f}")
    print(f"Validation report: {output}")
    print("Full Eval: completed" if args.full_eval else "Full Eval: not run (intentionally opt-in)")


if __name__ == "__main__":
    main()
