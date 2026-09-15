"""Unit tests for Phase 04 audio preprocessing primitives."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.audio_processing import (
    AudioProcessingError,
    _peak_normalize_pcm16,
    _safe_input_path,
)


def test_peak_normalization_leaves_silence_unchanged() -> None:
    silence = b"\x00\x00" * 100
    assert _peak_normalize_pcm16(silence) == silence


def test_peak_normalization_scales_quiet_pcm16() -> None:
    source = (1000).to_bytes(2, "little", signed=True) * 4
    normalized = _peak_normalize_pcm16(source)
    assert int.from_bytes(normalized[:2], "little", signed=True) == 30000


def test_peak_normalization_does_not_boost_already_loud_audio() -> None:
    source = (31000).to_bytes(2, "little", signed=True) * 4
    assert _peak_normalize_pcm16(source) == source


def test_peak_normalization_rejects_empty_audio() -> None:
    with pytest.raises(AudioProcessingError, match="no samples"):
        _peak_normalize_pcm16(b"")


def test_safe_input_path_blocks_storage_escape(tmp_path: Path) -> None:
    settings = SimpleNamespace(audio_storage_path=str(tmp_path))
    with pytest.raises(AudioProcessingError, match="outside"):
        _safe_input_path(settings, "../outside.wav")


def test_safe_input_path_requires_existing_file(tmp_path: Path) -> None:
    settings = SimpleNamespace(audio_storage_path=str(tmp_path))
    with pytest.raises(AudioProcessingError, match="not available"):
        _safe_input_path(settings, "missing.wav")


def test_safe_input_path_accepts_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "input.wav"
    source.write_bytes(b"RIFF")
    settings = SimpleNamespace(audio_storage_path=str(tmp_path))
    assert _safe_input_path(settings, "input.wav") == source.resolve()
