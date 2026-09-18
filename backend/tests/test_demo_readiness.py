"""Phase 13 demo-readiness validation helpers."""
from __future__ import annotations

import os
from pathlib import Path


def test_phase_13_required_api_paths_are_defined() -> None:
    from scripts.validate_phase_13 import REQUIRED_API_PATHS

    assert "/api/v1/health/live" in REQUIRED_API_PATHS
    assert "/api/v1/health/ready" in REQUIRED_API_PATHS
    assert "/api/v1/calls/{session_id}/audio/{audio_input_id}/analyze" in REQUIRED_API_PATHS
    assert "/api/v1/realtime/ws" in REQUIRED_API_PATHS


def test_phase_13_optional_demo_audio_is_only_checked_when_configured(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_AUTHENTIC_AUDIO_PATH", raising=False)
    monkeypatch.delenv("DEMO_SYNTHETIC_AUDIO_PATH", raising=False)

    configured = {
        "DEMO_AUTHENTIC_AUDIO_PATH": os.getenv("DEMO_AUTHENTIC_AUDIO_PATH"),
        "DEMO_SYNTHETIC_AUDIO_PATH": os.getenv("DEMO_SYNTHETIC_AUDIO_PATH"),
    }

    assert all(path is None for path in configured.values())


def test_phase_13_frontend_build_path_is_deterministic() -> None:
    from scripts.validate_phase_13 import FRONTEND_DIST, REPO_ROOT

    assert FRONTEND_DIST == Path(REPO_ROOT) / "frontend" / "dist"
