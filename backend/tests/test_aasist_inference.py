"""Unit tests for the Phase 06 AASIST inference boundary."""

import struct
import wave

import pytest

from app.config import Settings
from app.services.aasist_inference import (
    AASISTInferenceError,
    _load_processed_waveform,
    _safe_processed_path,
)


def _write_wav(path, *, sample_rate=16_000, channels=1, sample_width=2, frames=b"\x00\x00" * 32_000):
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(sample_width)
        writer.setframerate(sample_rate)
        writer.writeframes(frames)


def test_safe_processed_path_rejects_path_escape(tmp_path):
    settings = Settings(
        database_url="postgresql://test:test@localhost/test",
        jwt_secret="test-secret",
        audio_storage_path=str(tmp_path / "audio"),
    )
    with pytest.raises(AASISTInferenceError, match="outside the configured storage root"):
        _safe_processed_path(settings, "../outside.wav")


def test_load_processed_waveform_accepts_16khz_mono_pcm(tmp_path):
    path = tmp_path / "processed.wav"
    frames = struct.pack("<hhhh", 0, 16384, -16384, 32767)
    _write_wav(path, frames=frames)

    waveform = _load_processed_waveform(path)

    assert tuple(waveform.shape) == (1, 4)
    assert waveform.dtype.is_floating_point
    assert waveform[0, 1].item() == pytest.approx(0.5)
    assert waveform[0, 2].item() == pytest.approx(-0.5)


def test_load_processed_waveform_rejects_non_mono(tmp_path):
    path = tmp_path / "stereo.wav"
    _write_wav(path, channels=2, frames=b"\x00\x00" * 64_000)

    with pytest.raises(AASISTInferenceError, match="16 kHz, mono, 16-bit PCM WAV"):
        _load_processed_waveform(path)


def test_load_processed_waveform_rejects_wrong_sample_rate(tmp_path):
    path = tmp_path / "wrong-rate.wav"
    _write_wav(path, sample_rate=8_000)

    with pytest.raises(AASISTInferenceError, match="16 kHz, mono, 16-bit PCM WAV"):
        _load_processed_waveform(path)


def test_inference_settings_reject_invalid_threshold():
    with pytest.raises(ValueError, match="AASIST_DETECTION_THRESHOLD"):
        Settings(
            database_url="postgresql://test:test@localhost/test",
            jwt_secret="test-secret",
            aasist_detection_threshold=1.0,
        )
