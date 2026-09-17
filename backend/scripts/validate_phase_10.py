"""Consolidated Phase 10 dashboard API validation gate."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, args: list[str]) -> None:
    print(f"[RUN] {label}")
    result = subprocess.run(args, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print(f"[PASS] {label}")


def main() -> None:
    run("Phase 10 dashboard + Phase 07/08/09 regression tests", [
        sys.executable, "-m", "pytest",
        "tests/test_dashboard_api.py",
        "tests/test_alert_policy.py",
        "tests/test_alert_policy_extra.py",
        "tests/test_alert_service.py",
        "tests/test_alert_api.py",
        "tests/test_prevention_policy.py",
        "tests/test_prevention_service.py",
        "tests/test_risk_scoring.py",
        "tests/test_risk_api.py",
        "-q",
    ])
    run("Python compile check", [sys.executable, "-m", "compileall", "-q", "app", "scripts"])
    print("PHASE 10 VALIDATION PASSED")
    print("Full ML evaluation: not run (intentionally out of scope)")


if __name__ == "__main__":
    main()
