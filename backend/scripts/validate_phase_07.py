"""Consolidated validation gate for Phase 07 Prevention & Response Engine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = BACKEND_ROOT / "artifacts" / "evaluation" / "phase_07_validation.json"

FOCUSED_TESTS = [
    "tests/test_prevention_policy.py",
    "tests/test_prevention_service.py",
    "tests/test_prevention_api.py",
    "tests/test_aasist_model.py",
    "tests/test_aasist_training.py",
    "tests/test_aasist_training_diagnostics.py",
    "tests/test_aasist_inference.py",
]


def run(label: str, command: list[str]) -> dict:
    print(f"\n[CHECK] {label}")
    print("$ " + " ".join(command))
    started = perf_counter()
    result = subprocess.run(command, cwd=BACKEND_ROOT, text=True)
    elapsed = perf_counter() - started
    passed = result.returncode == 0
    print(f"[{'PASS' if passed else 'FAIL'}] {label} ({elapsed:.2f}s)")
    return {"label": label, "passed": passed, "elapsed_seconds": round(elapsed, 3), "returncode": result.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 07 consolidated validation gate")
    parser.add_argument("--pytest-all", action="store_true", help="Also run the complete backend test suite")
    args = parser.parse_args()

    print("=" * 72)
    print("PHASE 07 — CONSOLIDATED VALIDATION GATE")
    print("=" * 72)
    print(f"Backend: {BACKEND_ROOT}")
    print("Full ML Eval: SKIPPED (Phase 07 is policy-only)")

    checks: list[dict] = []
    checks.append(run("Phase 07 policy/service/API tests", [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS]))
    checks.append(run("Python compile check", [sys.executable, "-m", "compileall", "-q", "app", "scripts"]))

    if args.pytest_all:
        checks.append(run("Complete backend regression suite", [sys.executable, "-m", "pytest", "-q"]))

    report = {
        "phase": "07",
        "name": "Prevention & Response Engine",
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "full_ml_eval_run": False,
        "policy_version": "1.0",
        "risk_to_response": {
            "SAFE": "ALLOW",
            "LOW": "ALLOW",
            "MEDIUM": "MONITOR",
            "HIGH": "REQUIRE_REVIEW",
            "CRITICAL": "BLOCK",
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    if report["passed"]:
        print("PHASE 07 VALIDATION PASSED")
    else:
        print("PHASE 07 VALIDATION FAILED")
    print("=" * 72)
    print("Policy version: 1.0")
    print(f"Validation report: {REPORT_PATH}")
    print("Full ML Eval: not run (intentionally out of scope)")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
