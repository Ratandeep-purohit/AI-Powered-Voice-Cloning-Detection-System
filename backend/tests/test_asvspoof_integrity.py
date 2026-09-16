from __future__ import annotations

from pathlib import Path

from app.services.asvspoof_integrity import ASVspoofIntegrityValidator


def _make_dataset(root: Path) -> None:
    protocols = root / "ASVspoof2019_LA_asv_protocols"
    protocols.mkdir(parents=True)
    (protocols / "ASVspoof2019.LA.cm.train.trn.txt").write_text(
        "LA_0001 LA_T_1 - - bonafide\nLA_0002 LA_T_2 - - spoof\n",
        encoding="utf-8",
    )
    (protocols / "ASVspoof2019.LA.cm.dev.trl.txt").write_text(
        "LA_0003 LA_D_1 - - bonafide\n",
        encoding="utf-8",
    )
    (protocols / "ASVspoof2019.LA.cm.eval.trl.txt").write_text(
        "LA_0004 LA_E_1 - - spoof\n",
        encoding="utf-8",
    )
    for split, audio_id in (("train", "LA_T_1"), ("train", "LA_T_2"), ("dev", "LA_D_1"), ("eval", "LA_E_1")):
        directory = root / f"ASVspoof2019_LA_{split}" / "flac"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{audio_id}.flac").write_bytes(b"test")


def test_integrity_report_passes_for_complete_dataset(tmp_path: Path) -> None:
    _make_dataset(tmp_path)
    report = ASVspoofIntegrityValidator(tmp_path).validate()

    assert report.passed
    assert [(item.split, item.total, item.real, item.spoof, item.missing) for item in report.splits] == [
        ("train", 2, 1, 1, 0),
        ("dev", 1, 1, 0, 0),
        ("eval", 1, 0, 1, 0),
    ]


def test_integrity_report_detects_missing_audio(tmp_path: Path) -> None:
    _make_dataset(tmp_path)
    (tmp_path / "ASVspoof2019_LA_train" / "flac" / "LA_T_2.flac").unlink()

    report = ASVspoofIntegrityValidator(tmp_path).validate()

    train = report.splits[0]
    assert train.missing == 1
    assert not train.passed
    assert not report.passed


def test_integrity_report_detects_duplicate_audio_ids(tmp_path: Path) -> None:
    _make_dataset(tmp_path)
    protocol = tmp_path / "ASVspoof2019_LA_asv_protocols" / "ASVspoof2019.LA.cm.train.trn.txt"
    protocol.write_text(
        "LA_0001 LA_T_1 - - bonafide\nLA_0001 LA_T_1 - - bonafide\n",
        encoding="utf-8",
    )

    report = ASVspoofIntegrityValidator(tmp_path).validate()

    train = report.splits[0]
    assert train.duplicate_audio_ids == 1
    assert not train.passed
