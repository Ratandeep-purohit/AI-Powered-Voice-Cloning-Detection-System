"""Training diagnostics for the Phase 05 AASIST-family detector.

The diagnostic runner is intentionally small and deterministic. It measures the
model before training, verifies class-weight behavior, runs a short balanced
REAL/SPOOF smoke experiment, and reports whether the model starts separating the
classes instead of merely predicting the majority class.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader, Subset

from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.aasist_training import AASISTTrainer, AASISTTrainingConfig, class_weights
from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig
from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn


@dataclass(frozen=True, slots=True)
class ScoreStats:
    count: int
    mean: float
    minimum: float
    maximum: float
    std: float


@dataclass(frozen=True, slots=True)
class ClassScoreStats:
    real: ScoreStats | None
    spoof: ScoreStats | None


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    stage: str
    samples: int
    real: int
    spoof: int
    loss: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    eer: float | None
    predicted_real: int
    predicted_spoof: int
    spoof_probability: ClassScoreStats
    gradient_norm: float | None = None


@dataclass(frozen=True, slots=True)
class BalancedSmokeConfig:
    dataset_root: str
    samples_per_class: int = 250
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    gradient_accumulation_steps: int = 1
    target_duration_seconds: float = 4.0
    device: str = "auto"
    mixed_precision: bool = True
    seed: int = 42
    max_dev_batches: int | None = None

    def validate(self) -> None:
        if not self.dataset_root.strip():
            raise ValueError("dataset_root must not be empty.")
        if self.samples_per_class <= 0:
            raise ValueError("samples_per_class must be positive.")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive.")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if self.weight_decay < 0:
            raise ValueError("weight_decay must not be negative.")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive.")
        if self.target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be positive.")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda.")
        if self.max_dev_batches is not None and self.max_dev_batches <= 0:
            raise ValueError("max_dev_batches must be positive when provided.")


def _stats(values: Tensor) -> ScoreStats | None:
    values = values.detach().to(torch.float64).flatten()
    if values.numel() == 0:
        return None
    return ScoreStats(
        count=int(values.numel()),
        mean=float(values.mean()),
        minimum=float(values.min()),
        maximum=float(values.max()),
        std=float(values.std(unbiased=False)),
    )


def _auc_and_eer(labels: Tensor, scores: Tensor) -> tuple[float | None, float | None]:
    labels = labels.to(torch.int64).flatten()
    scores = scores.to(torch.float64).flatten()
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    if not positives.numel() or not negatives.numel():
        return None, None
    auc = float(((positives[:, None] > negatives[None, :]).double() +
                 (positives[:, None] == negatives[None, :]).double() * 0.5).mean())
    thresholds = torch.unique(torch.cat((positives, negatives)), sorted=True)
    thresholds = torch.cat((thresholds[:1] - 1e-12, thresholds, thresholds[-1:] + 1e-12))
    best_gap = math.inf
    best_eer = 1.0
    for threshold in thresholds:
        far = float((negatives >= threshold).double().mean())
        frr = float((positives < threshold).double().mean())
        gap = abs(far - frr)
        if gap < best_gap:
            best_gap = gap
            best_eer = (far + frr) / 2.0
    return auc, best_eer


def _snapshot(
    stage: str,
    labels: Tensor,
    scores: Tensor,
    predictions: Tensor,
    loss: float,
    gradient_norm: float | None = None,
) -> DiagnosticSnapshot:
    labels = labels.to(torch.int64).flatten()
    scores = scores.to(torch.float64).flatten()
    predictions = predictions.to(torch.int64).flatten()
    tp = int(((predictions == 1) & (labels == 1)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    correct = int((predictions == labels).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    auc, eer = _auc_and_eer(labels, scores)
    return DiagnosticSnapshot(
        stage=stage,
        samples=int(labels.numel()),
        real=int((labels == 0).sum()),
        spoof=int((labels == 1).sum()),
        loss=loss,
        accuracy=correct / labels.numel(),
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=auc,
        eer=eer,
        predicted_real=int((predictions == 0).sum()),
        predicted_spoof=int((predictions == 1).sum()),
        spoof_probability=ClassScoreStats(_stats(scores[labels == 0]), _stats(scores[labels == 1])),
        gradient_norm=gradient_norm,
    )


def balanced_indices(dataset: ASVspoofTorchDataset, samples_per_class: int, seed: int) -> list[int]:
    """Return deterministic, balanced indices from an ASVspoof split."""
    rng = random.Random(seed)
    real = [i for i, entry in enumerate(dataset.entries) if entry.label == "REAL"]
    spoof = [i for i, entry in enumerate(dataset.entries) if entry.label == "SPOOF"]
    if len(real) < samples_per_class or len(spoof) < samples_per_class:
        raise ValueError("Dataset does not contain enough samples for the requested balanced subset.")
    rng.shuffle(real)
    rng.shuffle(spoof)
    selected = real[:samples_per_class] + spoof[:samples_per_class]
    rng.shuffle(selected)
    return selected


class AASISTTrainingDiagnostics:
    """Run pre-training diagnostics and a small balanced smoke experiment."""

    def __init__(self, config: BalancedSmokeConfig) -> None:
        config.validate()
        self.config = config
        self.device = self._resolve_device(config.device)
        torch.manual_seed(config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.seed)
        self.preprocessor = AudioModelInputPreprocessor(
            ModelInputConfig(sample_rate=16_000, target_duration_seconds=config.target_duration_seconds)
        )

    @staticmethod
    def _resolve_device(requested: str) -> torch.device:
        if requested == "cpu":
            return torch.device("cpu")
        if requested == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA was requested but is not available.")
            return torch.device("cuda")
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _loader(self, dataset: ASVspoofTorchDataset, indices: list[int], shuffle: bool) -> DataLoader:
        return DataLoader(
            Subset(dataset, indices),
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=0,
            pin_memory=self.device.type == "cuda",
            collate_fn=asvspoof_collate_fn,
        )

    def _collect(self, model: nn.Module, loader: DataLoader, loss_fn: nn.Module) -> DiagnosticSnapshot:
        model.eval()
        labels_out: list[Tensor] = []
        scores_out: list[Tensor] = []
        predictions_out: list[Tensor] = []
        total_loss = 0.0
        total_samples = 0
        with torch.inference_mode():
            for batch in loader:
                waveforms = batch["waveforms"]
                labels = batch["labels"]
                prepared = self.preprocessor.prepare_batch(waveforms, batch.get("attention_mask"))
                waveforms = prepared["waveforms"].to(self.device)
                labels_device = labels.to(self.device)
                logits = model(waveforms)
                loss = loss_fn(logits, labels_device)
                probabilities = AASISTModel.probabilities(logits)
                predictions = AASISTModel.predict_label(logits)
                n = labels.shape[0]
                total_loss += float(loss.detach().cpu()) * n
                total_samples += n
                labels_out.append(labels.cpu())
                scores_out.append(probabilities[:, AASISTModel.SPOOF_CLASS].cpu())
                predictions_out.append(predictions.cpu())
        return _snapshot(
            "before_training",
            torch.cat(labels_out),
            torch.cat(scores_out),
            torch.cat(predictions_out),
            total_loss / total_samples,
        )

    def run(self) -> dict[str, Any]:
        train = ASVspoofTorchDataset(self.config.dataset_root, "train")
        dev = ASVspoofTorchDataset(self.config.dataset_root, "dev")
        train_indices = balanced_indices(train, self.config.samples_per_class, self.config.seed)
        dev_indices = balanced_indices(dev, min(self.config.samples_per_class, min(dev.label_counts.values())), self.config.seed)
        train_loader = self._loader(train, train_indices, shuffle=True)
        dev_loader = self._loader(dev, dev_indices, shuffle=False)

        model = AASISTModel(AASISTModelConfig()).to(self.device)
        weights = class_weights(self.config.samples_per_class, self.config.samples_per_class, self.device)
        loss_fn = nn.CrossEntropyLoss(weight=weights)
        before = self._collect(model, dev_loader, loss_fn)

        optimizer = torch.optim.AdamW(model.parameters(), lr=self.config.learning_rate, weight_decay=self.config.weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(self.config.epochs, 2))
        use_amp = self.device.type == "cuda" and self.config.mixed_precision
        scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
        history: list[dict[str, Any]] = []
        last_gradient_norm: float | None = None

        for epoch in range(1, self.config.epochs + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            total_loss = 0.0
            total_samples = 0
            labels_out: list[Tensor] = []
            scores_out: list[Tensor] = []
            predictions_out: list[Tensor] = []
            for batch_index, batch in enumerate(train_loader, start=1):
                prepared = self.preprocessor.prepare_batch(batch["waveforms"], batch.get("attention_mask"))
                waveforms = prepared["waveforms"].to(self.device, non_blocking=True)
                labels = batch["labels"].to(self.device, non_blocking=True)
                with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=use_amp):
                    logits = model(waveforms)
                    loss = loss_fn(logits, labels)
                    scaled_loss = loss / self.config.gradient_accumulation_steps
                scaler.scale(scaled_loss).backward()
                should_step = batch_index % self.config.gradient_accumulation_steps == 0 or batch_index == len(train_loader)
                if should_step:
                    scaler.unscale_(optimizer)
                    last_gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0).detach().cpu())
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad(set_to_none=True)
                n = labels.shape[0]
                total_loss += float(loss.detach().cpu()) * n
                total_samples += n
                probabilities = AASISTModel.probabilities(logits)
                labels_out.append(labels.detach().cpu())
                scores_out.append(probabilities[:, AASISTModel.SPOOF_CLASS].detach().cpu())
                predictions_out.append(AASISTModel.predict_label(logits).detach().cpu())
            train_snapshot = _snapshot(
                f"smoke_train_epoch_{epoch}", torch.cat(labels_out), torch.cat(scores_out), torch.cat(predictions_out), total_loss / total_samples, last_gradient_norm
            )
            dev_snapshot = self._collect(model, dev_loader, loss_fn)
            history.append({"epoch": epoch, "train": asdict(train_snapshot), "dev": asdict(dev_snapshot)})
            scheduler.step()

        return {
            "config": asdict(self.config),
            "device": str(self.device),
            "class_weights": [float(value) for value in weights.detach().cpu()],
            "train_source_counts": train.label_counts,
            "dev_source_counts": dev.label_counts,
            "balanced_train_samples": len(train_indices),
            "balanced_dev_samples": len(dev_indices),
            "before": asdict(before),
            "history": history,
            "after": history[-1]["dev"] if history else asdict(before),
        }


def run_balanced_smoke(config: BalancedSmokeConfig) -> dict[str, Any]:
    return AASISTTrainingDiagnostics(config).run()


def save_json_report(report: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
