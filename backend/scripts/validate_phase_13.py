"""Phase 13 demo-readiness validation gate."""
from __future__ import annotations

import os
import shutil
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

# Make `backend` importable when this script is launched from backend/scripts.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_API_PATHS = {
    "/api/v1/health",
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/calls",
    "/api/v1/calls/{session_id}/audio/{audio_input_id}/analyze",
    "/api/v1/realtime/ws",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_file(path: Path, label: str) -> None:
    if not path.is_file():
        fail(f"{label} missing: {path}")
    print(f"[PASS] {label}: {path}")


def check_command(binary: str, label: str) -> None:
    resolved = shutil.which(binary) or (binary if Path(binary).is_file() else None)
    if not resolved:
        fail(f"{label} not available: {binary}")
    try:
        result = subprocess.run([resolved, "-version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        fail(f"{label} could not be executed: {exc}")
    if result.returncode != 0:
        fail(f"{label} returned exit code {result.returncode}")
    print(f"[PASS] {label}: {resolved}")


def check_routes() -> None:
    os.environ.setdefault("APP_ENV", "testing")
    try:
        from app.main import app
    except Exception as exc:
        fail(f"FastAPI application could not be imported: {exc}")

    routes = {route.path for route in app.routes if getattr(route, "path", None)}
    missing = sorted(REQUIRED_API_PATHS - routes)
    if missing:
        fail(f"Required demo API routes are missing: {', '.join(missing)}")
    print(f"[PASS] Required demo API routes present: {len(REQUIRED_API_PATHS)}")


def check_frontend_readiness() -> None:
    package_json = REPO_ROOT / "frontend" / "package.json"
    check_file(package_json, "Frontend package manifest")
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Frontend package manifest could not be parsed: {exc}")

    scripts = package.get("scripts", {})
    missing_scripts = [name for name in ("build", "test", "lint") if not scripts.get(name)]
    if missing_scripts:
        fail(f"Frontend validation scripts missing: {', '.join(missing_scripts)}")
    print("[PASS] Frontend build/test/lint scripts are defined")

    check_file(FRONTEND_DIST / "index.html", "Frontend production build")


def check_optional_demo_audio() -> None:
    configured = {
        "DEMO_AUTHENTIC_AUDIO_PATH": os.getenv("DEMO_AUTHENTIC_AUDIO_PATH"),
        "DEMO_SYNTHETIC_AUDIO_PATH": os.getenv("DEMO_SYNTHETIC_AUDIO_PATH"),
    }
    missing = [label for label, path in configured.items() if path and not Path(path).is_file()]
    if missing:
        fail(f"Configured demo audio files are missing: {', '.join(missing)}")

    configured_count = sum(bool(path) for path in configured.values())
    if configured_count == 2:
        print("[PASS] Authentic + synthetic demo audio paths configured and present")
    else:
        print("[WARN] Demo audio paths are not both configured; prepare authorized samples before presentation")


def main() -> None:
    print("Phase 13 — Demo Readiness Gate")
    print(f"Repository: {REPO_ROOT}")

    check_file(ROOT / "app" / "main.py", "Backend application")
    check_file(ROOT / "app" / "services" / "analysis_pipeline.py", "End-to-end analysis pipeline")
    check_file(ROOT / "scripts" / "validate_phase_12.py", "Phase 12 validation gate")
    check_file(ROOT / "artifacts" / "checkpoints" / "aasist_balanced" / "best.pt", "AASIST production checkpoint")
    check_command("ffmpeg", "FFmpeg")
    check_routes()
    check_optional_demo_audio()

    check_frontend_readiness()

    print("PHASE 13 READINESS GATE PASSED")
    print("Presentation samples remain an operator responsibility and must be authorized demo audio.")


if __name__ == "__main__":
    main()
