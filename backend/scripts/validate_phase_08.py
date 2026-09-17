"""Consolidated validation gate for Phase 08 risk scoring."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FOCUSED_TESTS = [
    "tests/test_risk_scoring.py",
    "tests/test_risk_api.py",
    "tests/test_prevention_policy.py",
    "tests/test_prevention_service.py",
    "tests/test_prevention_api.py",
    "tests/test_aasist_model.py",
    "tests/test_aasist_training.py",
    "tests/test_aasist_training_diagnostics.py",
    "tests/test_aasist_inference.py",
]


def run(label: str, args: list[str]) -> None:
    print(f"[CHECK] {label}")
    print("$", " ".join(args))
    result = subprocess.run(args, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print(f"[PASS] {label}")


def main() -> None:
    print("PHASE 08 — CONSOLIDATED VALIDATION GATE")
    print(f"Backend: {ROOT}")
    print("Full ML Eval: SKIPPED (Phase 08 scoring policy validation)")
    print()

    run(
        "Phase 08 risk scoring + Phase 07 regression tests",
        [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS],
    )
    print()
    run("Python compile check", [sys.executable, "-m", "compileall", "-q", "app", "scripts"])
    print()
    print("PHASE 08 VALIDATION PASSED")
    print("Risk scoring policy: 1.0")
    print("Full ML Eval: not run (intentionally out of scope)")


if __name__ == "__main__":
    main()
