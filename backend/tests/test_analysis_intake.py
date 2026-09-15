"""Unit tests for Phase 03 audio intake boundaries."""

from app.services.analysis import _detect_format, _safe_original_filename


def test_detect_supported_audio_signatures() -> None:
    assert _detect_format(b"RIFF" + b"\x00\x00\x00\x00" + b"WAVEfmt ") == "wav"
    assert _detect_format(b"ID3" + b"\x00" * 20) == "mp3"
    assert _detect_format(b"OggS" + b"\x00" * 20) == "ogg"
    assert _detect_format(b"fLaC" + b"\x00" * 20) == "flac"
    assert _detect_format(b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 12) == "m4a"


def test_detect_rejects_unknown_content() -> None:
    assert _detect_format(b"not-an-audio-file") is None


def test_filename_never_controls_storage_path() -> None:
    assert _safe_original_filename("../../secret.wav") == "secret.wav"
    assert _safe_original_filename("..\\..\\secret.wav") == "secret.wav"


def test_filename_is_safely_normalized() -> None:
    assert _safe_original_filename("client recording (final).wav") == "client recording (final).wav"
