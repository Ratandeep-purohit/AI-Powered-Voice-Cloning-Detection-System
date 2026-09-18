"""Consolidated Phase 12 production-hardening validation gate."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEST_FILES = ["tests/test_hardening.py","tests/test_health.py","tests/test_realtime.py","tests/test_dashboard_api.py","tests/test_alert_policy.py","tests/test_alert_policy_extra.py","tests/test_alert_service.py","tests/test_alert_api.py","tests/test_prevention_policy.py","tests/test_prevention_service.py","tests/test_risk_scoring.py","tests/test_risk_api.py"]
def run(command: list[str], label: str) -> None:
    print(f"[RUN] {label}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode: raise SystemExit(result.returncode)
    print(f"[PASS] {label}")
def main() -> None:
    run([sys.executable,"-m","pytest",*TEST_FILES],"Phase 12 hardening + regression tests")
    run([sys.executable,"-m","compileall","-q","app","scripts"],"Python compile check")
    print("PHASE 12 VALIDATION PASSED")
    print("Full ML evaluation: not run (intentionally out of scope)")
if __name__ == "__main__": main()
