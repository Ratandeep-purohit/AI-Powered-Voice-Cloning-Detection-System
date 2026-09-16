"""Training engine for the Phase 05 AASIST-family spoof detector.

The engine deliberately keeps dataset parsing, model architecture, and training
orchestration separate. It supports weighted cross-entropy for the heavily
imbalanced ASVspoof labels, mixed precision on CUDA, gradient accumulation,
checkpoint save/resume, and lightweight validation metrics.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader

from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig
from app.services.asvspoof import ASVspoofProtocolError
from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn


@dataclass(frozen=True, slots=True)
class AASISTTrainingConfig:
    """Validated knobs for detector training."""

    dataset_root: str
    epochs: int = 10
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    num_workers: int = 0
    gradient_accumulation_steps: int = 1
    target_duration_seconds: float = 4.0
    mixed_precision: bool = True
    device: str = "auto"
    checkpoint_dir: str = "artifacts/checkpoints/aasist"
    checkpoint_every_epoch: bool = True
    max_train_batches: int | None = None
    max_dev_batches: int | None = None

    def validate(self) -> None:
        if not self.dataset_root.strip():
            raise ValueError("dataset_root must not be empty.")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive.")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if self.weight_decay < 0:
            raise ValueError("weight_decay must not be negative.")
        if self.num_workers < 0:
            raise ValueError("num_workers must not be negative.")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive.")
        if self.target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be positive.")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda.")
        if self.max_train_batches is not None and self.max_train_batches <= 0:
            raise ValueError("max_train_batches must be positive when provided.")
        if self.max_dev_batches is not None and self.max_dev_batches <= 0:
            raise ValueError("max_dev_batches must be positive when provided.")


@dataclass(frozen=True, slots=True)
class EpochMetrics:
    """Metrics returned after one training or validation pass."""

    loss: float
    samples: int
    correct: int
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    eer: float | None

    @property
    def accuracy(self) -> float:
        return self.correct / self.samples if self.samples else 0.0


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Summary of the complete training run."""

    best_epoch: int
    best_f1: float
    history: tuple[dict[str, Any], ...]
    best_checkpoint: str
    latest_checkpoint: str


def resolve_device(requested: str) -> torch.device:
    """Resolve an explicit or automatic compute device."""

    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def class_weights(real_count: int, spoof_count: int, device: torch.device) -> Tensor:
    """Return inverse-frequency weights for REAL=0 and SPOOF=1."""

    if real_count <= 0 or spoof_count <= 0:
        raise ValueError("Both REAL and SPOOF counts must be positive.")
    total = real_count + spoof_count
    weights = torch.tensor(
        [total / (2.0 * real_count), total / (2.0 * spoof_count)],
        dtype=torch.float32,
        device=device,
    )
    return weights


def _binary_metrics(labels: Tensor, probabilities: Tensor, predictions: Tensor) -> tuple[float, float, float, float | None, float | None]:
    """Compute precision, recall, F1, ROC-AUC, and EER for binary labels."""

    labels = labels.detach().cpu().long().flatten()
    probabilities = probabilities.detach().cpu().float().flatten()
    predictions = predictions.detach().cpu().long().flatten()

    tp = int(((predictions == 1) & (labels == 1)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0

    positives = int((labels == 1).sum())
    negatives = int((labels == 0).sum())
    roc_auc: float | None = None
    eer: float | None = None

    if positives and negatives:
        order = torch.argsort(probabilities, descending=True)
        sorted_labels = labels[order]
        tps = torch.cumsum((sorted_labels == 1).float(), dim=0)
        fps = torch.cumsum((sorted_labels == 0).float(), dim=0)
        tpr = tps / positives
        fpr = fps / negatives
        auc_x = torch.cat([torch.zeros(1), fpr])
        auc_y = torch.cat([torch.zeros(1), tpr])
        roc_auc = float(torch.trapezoid(auc_y, auc_x))

        fnr = 1.0 - tpr
        gap = torch.abs(fpr - fnr)
        idx = int(torch.argmin(gap))
        eer = float((fpr[idx] + fnr[idx]) / 2.0)

    return precision, recall, f1, roc_auc, eer


class AASISTTrainer:
    """Train and validate an :class:`AASISTModel`."""

    def __init__(
        self,
        config: AASISTTrainingConfig,
        model: AASISTModel | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self.device = resolve_device(config.device)
        self.model = model or AASISTModel(AASISTModelConfig())
        self.model.to(self.device)
        self.preprocessor = AudioModelInputPreprocessor(
            ModelInputConfig(
                sample_rate=16_000,
                target_duration_seconds=config.target_duration_seconds,
            )
        )

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config.epochs,
        )
        self.loss_fn = nn.CrossEntropyLoss(
            weight=torch.tensor([1.0, 1.0], dtype=torch.float32, device=self.device)
        )
        self.use_amp = config.mixed_precision and self.device.type == "cuda"
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)
        self.start_epoch = 1
        self.best_f1 = -math.inf
        self.best_epoch = 0

    def build_loaders(self) -> tuple[DataLoader, DataLoader]:
        """Build train/dev loaders from the validated ASVspoof dataset layer."""

        train = ASVspoofTorchDataset(self.config.dataset_root, "train", sample_rate=16_000)
        dev = ASVspoofTorchDataset(self.config.dataset_root, "dev", sample_rate=16_000)

        counts = train.resolver.parser.label_counts("train")
        weights = class_weights(counts["REAL"], counts["SPOOF"], self.device)
        self.loss_fn = nn.CrossEntropyLoss(weight=weights)

        common = {
            "batch_size": self.config.batch_size,
            "num_workers": self.config.num_workers,
            "pin_memory": self.device.type == "cuda",
            "collate_fn": asvspoof_collate_fn,
            "persistent_workers": self.config.num_workers > 0,
        }
        train_loader = DataLoader(train, shuffle=True, drop_last=False, **common)
        dev_loader = DataLoader(dev, shuffle=False, drop_last=False, **common)
        return train_loader, dev_loader

    def _prepare_batch(self, batch: dict[str, Any]) -> tuple[Tensor, Tensor]:
        prepared = self.preprocessor.prepare_batch(
            batch["waveforms"],
            attention_mask=batch["attention_mask"],
        )
        waveforms = prepared["waveforms"].to(self.device, non_blocking=True)
        labels = batch["labels"].to(self.device, non_blocking=True)
        return waveforms, labels

    def _run_epoch(self, loader: DataLoader, training: bool, max_batches: int | None = None) -> EpochMetrics:
        self.model.train(training)
        total_loss = 0.0
        total_samples = 0
        total_correct = 0
        all_labels: list[Tensor] = []
        all_probabilities: list[Tensor] = []
        all_predictions: list[Tensor] = []

        if training:
            self.optimizer.zero_grad(set_to_none=True)

        for batch_index, batch in enumerate(loader, start=1):
            if max_batches is not None and batch_index > max_batches:
                break
            waveforms, labels = self._prepare_batch(batch)

            with torch.set_grad_enabled(training):
                with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=self.use_amp):
                    logits = self.model(waveforms)
                    loss = self.loss_fn(logits, labels)
                    scaled_loss = loss / self.config.gradient_accumulation_steps if training else loss

                if training:
                    self.scaler.scale(scaled_loss).backward()
                    should_step = (
                        batch_index % self.config.gradient_accumulation_steps == 0
                        or batch_index == (max_batches or len(loader))
                    )
                    if should_step:
                        self.scaler.unscale_(self.optimizer)
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                        self.optimizer.zero_grad(set_to_none=True)

            probabilities = AASISTModel.probabilities(logits)
            predictions = AASISTModel.predict_label(logits)
            batch_size = labels.shape[0]
            total_loss += float(loss.detach().cpu()) * batch_size
            total_samples += batch_size
            total_correct += int((predictions == labels).sum().item())
            all_labels.append(labels.detach().cpu())
            all_probabilities.append(probabilities[:, AASISTModel.SPOOF_CLASS].detach().cpu())
            all_predictions.append(predictions.detach().cpu())

        if not total_samples:
            raise RuntimeError("No samples were processed in the epoch.")

        labels = torch.cat(all_labels)
        probabilities = torch.cat(all_probabilities)
        predictions = torch.cat(all_predictions)
        precision, recall, f1, roc_auc, eer = _binary_metrics(labels, probabilities, predictions)
        return EpochMetrics(
            loss=total_loss / total_samples,
            samples=total_samples,
            correct=total_correct,
            precision=precision,
            recall=recall,
            f1=f1,
            roc_auc=roc_auc,
            eer=eer,
        )

    def train_epoch(self, loader: DataLoader, max_batches: int | None = None) -> EpochMetrics:
        """Run one optimizer epoch."""

        return self._run_epoch(loader, training=True, max_batches=max_batches)

    @torch.no_grad()
    def validate_epoch(self, loader: DataLoader, max_batches: int | None = None) -> EpochMetrics:
        """Run one validation epoch without gradient updates."""

        return self._run_epoch(loader, training=False, max_batches=max_batches)

    def _checkpoint_payload(self, epoch: int, train_metrics: EpochMetrics, dev_metrics: EpochMetrics) -> dict[str, Any]:
        return {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "scaler_state_dict": self.scaler.state_dict(),
            "best_f1": self.best_f1,
            "best_epoch": self.best_epoch,
            "config": asdict(self.config),
            "train_metrics": asdict(train_metrics),
            "dev_metrics": asdict(dev_metrics),
            "device": str(self.device),
        }

    def save_checkpoint(self, path: str | Path, epoch: int, train_metrics: EpochMetrics, dev_metrics: EpochMetrics) -> Path:
        """Atomically save a resumable checkpoint."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        os.close(fd)
        try:
            torch.save(self._checkpoint_payload(epoch, train_metrics, dev_metrics), temporary)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        return target

    def resume(self, path: str | Path) -> None:
        """Resume model and optimizer state from a checkpoint."""

        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        required = {"epoch", "model_state_dict", "optimizer_state_dict", "scheduler_state_dict", "scaler_state_dict"}
        missing = required.difference(checkpoint)
        if missing:
            raise ValueError(f"Checkpoint is missing fields: {sorted(missing)}")
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
        self.start_epoch = int(checkpoint["epoch"]) + 1
        self.best_f1 = float(checkpoint.get("best_f1", -math.inf))
        self.best_epoch = int(checkpoint.get("best_epoch", 0))

    def fit(self) -> TrainingResult:
        """Run configured training and persist latest/best checkpoints."""

        train_loader, dev_loader = self.build_loaders()
        checkpoint_dir = Path(self.config.checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        best_path = checkpoint_dir / "best.pt"
        latest_path = checkpoint_dir / "latest.pt"
        history: list[dict[str, Any]] = []

        for epoch in range(self.start_epoch, self.config.epochs + 1):
            train_metrics = self.train_epoch(train_loader, self.config.max_train_batches)
            dev_metrics = self.validate_epoch(dev_loader, self.config.max_dev_batches)
            self.scheduler.step()

            record = {
                "epoch": epoch,
                "learning_rate": self.optimizer.param_groups[0]["lr"],
                "train": asdict(train_metrics),
                "dev": asdict(dev_metrics),
            }
            history.append(record)
            if dev_metrics.f1 > self.best_f1:
                self.best_f1 = dev_metrics.f1
                self.best_epoch = epoch
                self.save_checkpoint(best_path, epoch, train_metrics, dev_metrics)
            if self.config.checkpoint_every_epoch or epoch == self.config.epochs:
                self.save_checkpoint(latest_path, epoch, train_metrics, dev_metrics)

            history_path = checkpoint_dir / "history.json"
            history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

        return TrainingResult(
            best_epoch=self.best_epoch,
            best_f1=self.best_f1,
            history=tuple(history),
            best_checkpoint=str(best_path),
            latest_checkpoint=str(latest_path),
        )


def build_training_engine(config: AASISTTrainingConfig) -> AASISTTrainer:
    """Factory used by scripts/tests to construct a validated trainer."""

    return AASISTTrainer(config)
