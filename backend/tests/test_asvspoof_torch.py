"""Tests for the Phase 05 ASVspoof PyTorch dataset layer."""

from pathlib import Path

import pytest
import torch
import torchaudio
from torch.utils.data import DataLoader

from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn


PROTOCOLS = {
    "train": "ASVspoof2019.LA.cm.train.trn.txt",
    "dev": "ASVspoof2019.LA.cm.dev.trl.txt",
    "eval": "ASVspoof2019.LA.cm.eval.trl.txt",
}


def _write_mini_dataset(root: Path) -> None:
    protocol_dir = root / "ASVspoof2019_LA_cm_protocols"
    protocol_dir.mkdir(parents=True)

    audio_dirs = {
        "train": root / "ASVspoof2019_LA_train" / "flac",
        "dev": root / "ASVspoof2019_LA_dev" / "flac",
        "eval": root / "ASVspoof2019_LA_eval" / "flac",
    }
    for directory in audio_dirs.values():
        directory.mkdir(parents=True)

    for split, protocol_name in PROTOCOLS.items():
        rows = [
            f"LA_0001 LA_{split.upper()}_REAL - - bonafide",
            f"LA_0002 LA_{split.upper()}_SPOOF - - spoof",
        ]
        (protocol_dir / protocol_name).write_text("\n".join(rows) + "\n", encoding="utf-8")

        # Deliberately use different durations to verify variable-length
        # samples are padded only by the collate function.
        real = torch.zeros(1, 16000, dtype=torch.float32)
        spoof = torch.zeros(1, 24000, dtype=torch.float32)
        torchaudio.save(str(audio_dirs[split] / f"LA_{split.upper()}_REAL.flac"), real, 16000)
        torchaudio.save(str(audio_dirs[split] / f"LA_{split.upper()}_SPOOF.flac"), spoof, 16000)


def test_dataset_loads_waveforms_and_maps_labels(tmp_path: Path) -> None:
    _write_mini_dataset(tmp_path)
    dataset = ASVspoofTorchDataset(tmp_path, "train", sample_rate=16000)

    assert len(dataset) == 2

    real = dataset[0]
    spoof = dataset[1]

    assert real.waveform.shape == (1, 16000)
    assert real.sample_rate == 16000
    assert real.label == 0
    assert real.audio_id == "LA_TRAIN_REAL"

    assert spoof.waveform.shape == (1, 24000)
    assert spoof.label == 1
    assert spoof.audio_id == "LA_TRAIN_SPOOF"


def test_dataset_resamples_and_converts_stereo_to_mono(tmp_path: Path) -> None:
    _write_mini_dataset(tmp_path)
    audio_path = tmp_path / "ASVspoof2019_LA_train" / "flac" / "LA_TRAIN_REAL.flac"
    stereo = torch.stack([torch.ones(8000), torch.zeros(8000)])
    torchaudio.save(str(audio_path), stereo, 8000)

    dataset = ASVspoofTorchDataset(tmp_path, "train", sample_rate=16000)
    sample = dataset[0]

    assert sample.waveform.shape[0] == 1
    assert sample.sample_rate == 16000
    assert sample.waveform.shape[-1] == 16000


def test_collate_pads_variable_length_waveforms(tmp_path: Path) -> None:
    _write_mini_dataset(tmp_path)
    dataset = ASVspoofTorchDataset(tmp_path, "train", sample_rate=16000)
    loader = DataLoader(dataset, batch_size=2, shuffle=False, collate_fn=asvspoof_collate_fn)

    batch = next(iter(loader))

    assert batch["waveforms"].shape == (2, 1, 24000)
    assert batch["labels"].tolist() == [0, 1]
    assert batch["attention_mask"].shape == (2, 24000)
    assert int(batch["sample_rate"]) == 16000
    assert batch["audio_ids"] == ["LA_TRAIN_REAL", "LA_TRAIN_SPOOF"]
    assert bool(batch["attention_mask"][0, 15999]) is True
    assert bool(batch["attention_mask"][0, 16000]) is False
    assert bool(batch["attention_mask"][1, 23999]) is True


def test_dataset_rejects_invalid_sample_rate(tmp_path: Path) -> None:
    _write_mini_dataset(tmp_path)
    with pytest.raises(ValueError, match="positive"):
        ASVspoofTorchDataset(tmp_path, "train", sample_rate=0)


def test_dataset_rejects_unsupported_split(tmp_path: Path) -> None:
    _write_mini_dataset(tmp_path)
    with pytest.raises(Exception, match="Unsupported ASVspoof split"):
        ASVspoofTorchDataset(tmp_path, "test", sample_rate=16000)
