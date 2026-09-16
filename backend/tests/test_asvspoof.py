"""Phase 05 ASVspoof protocol parser tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.asvspoof import ASVspoofProtocolError, ASVspoofProtocolParser


def _write_protocol(root: Path, filename: str, content: str) -> Path:
    protocol_dir = root / "ASVspoof2019_LA_asv_protocols"
    protocol_dir.mkdir(parents=True)
    path = protocol_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_protocol_maps_labels(tmp_path: Path) -> None:
    path = _write_protocol(
        tmp_path,
        "ASVspoof2019.LA.cm.train.trn.txt",
        """
LA_0079 LA_T_000001 - - bonafide
LA_0080 LA_T_000002 - A01 spoof
""".strip(),
    )

    parser = ASVspoofProtocolParser(tmp_path)
    entries = parser.parse_file(path)

    assert entries[0].speaker_id == "LA_0079"
    assert entries[0].audio_id == "LA_T_000001"
    assert entries[0].label == "REAL"
    assert entries[1].label == "SPOOF"
    assert parser.count_labels(entries) == {"REAL": 1, "SPOOF": 1}


def test_load_split_resolves_official_filename(tmp_path: Path) -> None:
    _write_protocol(
        tmp_path,
        "ASVspoof2019.LA.cm.dev.trl.txt",
        "LA_0001 LA_D_000001 - - bonafide\n",
    )

    parser = ASVspoofProtocolParser(tmp_path)

    assert parser.protocol_path("dev").name == "ASVspoof2019.LA.cm.dev.trl.txt"
    assert parser.load_split("dev")[0].audio_id == "LA_D_000001"


def test_supported_splits_are_train_dev_eval(tmp_path: Path) -> None:
    parser = ASVspoofProtocolParser(tmp_path)

    assert parser.protocol_path("train").name == "ASVspoof2019.LA.cm.train.trn.txt"
    assert parser.protocol_path("dev").name == "ASVspoof2019.LA.cm.dev.trl.txt"
    assert parser.protocol_path("eval").name == "ASVspoof2019.LA.cm.eval.trl.txt"


def test_invalid_split_is_rejected(tmp_path: Path) -> None:
    parser = ASVspoofProtocolParser(tmp_path)

    with pytest.raises(ASVspoofProtocolError, match="Unsupported ASVspoof split"):
        parser.protocol_path("test")


def test_missing_protocol_file_is_rejected(tmp_path: Path) -> None:
    parser = ASVspoofProtocolParser(tmp_path)

    with pytest.raises(ASVspoofProtocolError, match="does not exist"):
        parser.load_split("train")


def test_invalid_field_count_is_rejected(tmp_path: Path) -> None:
    path = _write_protocol(
        tmp_path,
        "ASVspoof2019.LA.cm.train.trn.txt",
        "LA_0079 LA_T_000001 - bonafide\n",
    )
    parser = ASVspoofProtocolParser(tmp_path)

    with pytest.raises(ASVspoofProtocolError, match="expected 5 fields"):
        parser.parse_file(path)


def test_unknown_label_is_rejected(tmp_path: Path) -> None:
    path = _write_protocol(
        tmp_path,
        "ASVspoof2019.LA.cm.train.trn.txt",
        "LA_0079 LA_T_000001 - - unknown\n",
    )
    parser = ASVspoofProtocolParser(tmp_path)

    with pytest.raises(ASVspoofProtocolError, match="Unsupported ASVspoof label"):
        parser.parse_file(path)


def test_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    path = _write_protocol(
        tmp_path,
        "ASVspoof2019.LA.cm.train.trn.txt",
        "# comment\n\nLA_0079 LA_T_000001 - - bonafide\n",
    )
    parser = ASVspoofProtocolParser(tmp_path)

    assert len(parser.parse_file(path)) == 1


def test_empty_dataset_root_is_rejected() -> None:
    with pytest.raises(ASVspoofProtocolError, match="dataset root must not be empty"):
        ASVspoofProtocolParser("   ")
