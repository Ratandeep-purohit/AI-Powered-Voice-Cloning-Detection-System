from __future__ import annotations

from pathlib import Path

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.aasist_training import (
    AASISTTrainer,
    AASISTTrainingConfig,
    EpochMetrics,
    _binary_metrics,
    class_weights,
    resolve_device,
)


class TinyDataset(Dataset[dict[str, torch.Tensor]]):
    def __init__(self, size: int = 4, time: int = 64000) -> None:
        self.waveforms = torch.randn(size, 1, time) * 0.05
        self.labels = torch.tensor([0, 1] * (size // 2), dtype=torch.long)
        self.masks = torch.ones(size, time, dtype=torch.bool)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return {
            "waveforms": self.waveforms[index],
            "attention_mask": self.masks[index],
            "labels": self.labels[index],
        }


def tiny_collate(samples: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    return {
        "waveforms": torch.stack([s["waveforms"] for s in samples]),
        "attention_mask": torch.stack([s["attention_mask"] for s in samples]),
        "labels": torch.stack([s["labels"] for s in samples]),
    }


def test_class_weights_reflect_inverse_frequency() -> None:
    weights = class_weights(10, 90, torch.device("cpu"))
    assert weights.shape == (2,)
    assert weights[0] > weights[1]


def test_resolve_device_cpu() -> None:
    assert resolve_device("cpu") == torch.device("cpu")


def test_resolve_device_auto() -> None:
    device = resolve_device("auto")
    assert device.type in {"cpu", "cuda"}


def test_cuda_request_fails_when_unavailable() -> None:
    if torch.cuda.is_available():
        pytest.skip("CUDA is available")
    with pytest.raises(RuntimeError, match="CUDA was requested"):
        resolve_device("cuda")


def test_binary_metrics_perfect_predictions() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    probabilities = torch.tensor([0.01, 0.1, 0.9, 0.99])
    predictions = torch.tensor([0, 0, 1, 1])
    precision, recall, f1, auc, eer = _binary_metrics(labels, probabilities, predictions)
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)
    assert f1 == pytest.approx(1.0)
    assert auc == pytest.approx(1.0)
    assert eer == pytest.approx(0.0)


def test_binary_metrics_handles_single_class() -> None:
    labels = torch.zeros(4, dtype=torch.long)
    probabilities = torch.tensor([0.1, 0.2, 0.3, 0.4])
    predictions = torch.zeros(4, dtype=torch.long)
    precision, recall, f1, auc, eer = _binary_metrics(labels, probabilities, predictions)
    assert precision == pytest.approx(0.0)
    assert recall == pytest.approx(0.0)
    assert f1 == pytest.approx(0.0)
    assert auc is None
    assert eer is None


def test_trainer_one_epoch_with_tiny_model() -> None:
    class TinyModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pool = nn.AdaptiveAvgPool1d(8)
            self.fc = nn.Linear(8, 2)

        def forward(self, waveform: torch.Tensor) -> torch.Tensor:
            return self.fc(self.pool(waveform).flatten(1))

    config = AASISTTrainingConfig(
        dataset_root=str(Path("E:/DataSet/LA")),
        batch_size=2,
        device="cpu",
        mixed_precision=False,
        gradient_accumulation_steps=2,
    )
    trainer = AASISTTrainer(config, model=TinyModel())
    trainer.preprocessor = type("IdentityPreprocessor", (), {
        "prepare_batch": lambda self, waveforms, attention_mask=None: {
            "waveforms": waveforms,
            "attention_mask": attention_mask,
        }
    })()
    loader = DataLoader(TinyDataset(), batch_size=2, shuffle=False, collate_fn=tiny_collate)
    trainer.loss_fn = nn.CrossEntropyLoss()
    metrics = trainer.train_epoch(loader)
    assert metrics.samples == 4
    assert metrics.loss >= 0.0


def test_checkpoint_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class CheckpointDataset:
        label_counts = (2_580, 22_800)

    monkeypatch.setattr("app.services.aasist_training.ASVspoofTorchDataset", CheckpointDataset)

    config = AASISTTrainingConfig(
        dataset_root=str(tmp_path),
        device="cpu",
        mixed_precision=False,
    )
    trainer = AASISTTrainer(config, model=AASISTModel(AASISTModelConfig()))
    epoch_metrics = EpochMetrics(
        loss=1.0,
        samples=2,
        correct=1,
        precision=0.5,
        recall=0.5,
        f1=0.5,
        roc_auc=0.5,
        eer=0.5,
    )
    path = trainer.save_checkpoint(tmp_path / "checkpoint.pt", 1, epoch_metrics, epoch_metrics)
    assert path.exists()
    resumed = AASISTTrainer(config, model=AASISTModel(AASISTModelConfig()))
    resumed.resume(path)
    assert resumed.start_epoch == 2
    assert resumed.best_f1 == pytest.approx(-float("inf"))
