"""Tests for ASVspoof 2019 LA audio-path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.asvspoof import ASVspoofProtocolEntry, ASVspoofProtocolError
from app.services.asvspoof_dataset import ASVspoofDatasetResolver


def test_audio_path_resolves_expected_train_file(tmp_path: Path) -> None:
    resolver = ASVspoofDatasetResolver(tmp_path)

    path = resolver.audio_path("train", "LA_T_1138215")

    assert path == (tmp_path / "ASVspoof2019_LA_train" / "flac" / "LA_T_1138215.flac").resolve()


def test_audio_path_resolves_all_supported_splits(tmp_path: Path) -> None:
    resolver = ASVspoofDatasetResolver(tmp_path)

    assert resolver.audio_path("train", "LA_T_1").parts[-3:] == (
        "ASVspoof2019_LA_train", "flac", "LA_T_1.flac"
    )
    assert resolver.audio_path("dev", "LA_D_1").parts[-3:] == (
        "ASVspoof2019_LA_dev", "flac", "LA_D_1.flac"
    )
    assert resolver.audio_path("eval", "LA_E_1").parts[-3:] == (
        "ASVspoof2019_LA_eval", "flac", "LA_E_1.flac"
    )


def test_audio_path_accepts_flac_suffix(tmp_path: Path) -> None:
    resolver = ASVspoofDatasetResolver(tmp_path)

    assert resolver.audio_path("train", "LA_T_1.flac").name == "LA_T_1.flac"


def test_audio_path_rejects_path_traversal(tmp_path: Path) -> None:
    resolver = ASVspoofDatasetResolver(tmp_path)

    with pytest.raises(ASVspoofProtocolError, match="Invalid ASVspoof audio ID"):
        resolver.audio_path("train", "../LA_T_1")


def test_resolve_entry_requires_existing_file(tmp_path: Path) -> None:
    resolver = ASVspoofDatasetResolver(tmp_path)
    entry = ASVspoofProtocolEntry("LA_0079", "LA_T_1", "REAL")

    with pytest.raises(ASVspoofProtocolError, match="does not exist"):
        resolver.resolve_entry("train", entry)


def test_resolve_entry_returns_metadata_and_path(tmp_path: Path) -> None:
    audio_dir = tmp_path / "ASVspoof2019_LA_train" / "flac"
    audio_dir.mkdir(parents=True)
    audio_path = audio_dir / "LA_T_1.flac"
    audio_path.write_bytes(b"test")

    resolver = ASVspoofDatasetResolver(tmp_path)
    entry = ASVspoofProtocolEntry("LA_0079", "LA_T_1", "REAL")
    resolved = resolver.resolve_entry("train", entry)

    assert resolved.split == "train"
    assert resolved.speaker_id == "LA_0079"
    assert resolved.audio_id == "LA_T_1"
    assert resolved.label == "REAL"
    assert resolved.path == audio_path.resolve()
