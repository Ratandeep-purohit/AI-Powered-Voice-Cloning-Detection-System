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
from tqdm.auto import tqdm

from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig
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


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Final result returned by the training engine."""

    best_epoch: int
    best_f1: float
    history: tuple[dict[str, Any], ...]
    best_checkpoint: str
    latest_checkpoint: str


def resolve_device(requested: str) -> torch.device:
    """Resolve the requested compute device with CUDA validation."""

    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def class_weights(real_count: int, spoof_count: int, device: torch.device) -> Tensor:
    """Return inverse-frequency weights for [REAL, SPOOF]."""

    if real_count <= 0 or spoof_count <= 0:
        raise ValueError("Both classes must have positive counts.")
    total = real_count + spoof_count
    return torch.tensor(
        [total / (2.0 * real_count), total / (2.0 * spoof_count)],
        dtype=torch.float32,
        device=device,
    )


def _binary_metrics(
    labels: Tensor,
    spoof_probabilities: Tensor,
    predictions: Tensor,
) -> tuple[float, float, float, float | None, float | None]:
    """Compute classification metrics without requiring sklearn."""

    labels = labels.to(torch.int64).flatten()
    spoof_probabilities = spoof_probabilities.to(torch.float64).flatten()
    predictions = predictions.to(torch.int64).flatten()
    if labels.numel() == 0:
        raise ValueError("Metric inputs must not be empty.")

    tp = int(((predictions == 1) & (labels == 1)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    positives = spoof_probabilities[labels == 1]
    negatives = spoof_probabilities[labels == 0]
    roc_auc: float | None = None
    eer: float | None = None
    if positives.numel() and negatives.numel():
        comparisons = (positives[:, None] > negatives[None, :]).double()
        ties = (positives[:, None] == negatives[None, :]).double() * 0.5
        roc_auc = float((comparisons + ties).mean())

        thresholds = torch.unique(torch.cat((positives, negatives)), sorted=True)
        thresholds = torch.cat((thresholds[:1] - 1e-12, thresholds, thresholds[-1:] + 1e-12))
        best_gap = float("inf")
        best_eer = 1.0
        for threshold in thresholds:
            false_accept = float((negatives >= threshold).double().mean())
            false_reject = float((positives < threshold).double().mean())
            gap = abs(false_accept - false_reject)
            if gap < best_gap:
                best_gap = gap
                best_eer = (false_accept + false_reject) / 2.0
        eer = best_eer
    return precision, recall, f1, roc_auc, eer


class AASISTTrainer:
    """Train and validate the project AASIST-family spoof detector."""

    def __init__(
        self,
        config: AASISTTrainingConfig,
        model: nn.Module | None = None,
        preprocessor: AudioModelInputPreprocessor | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self.device = resolve_device(config.device)
        self.model = (model or AASISTModel(AASISTModelConfig())).to(self.device)
        self.preprocessor = preprocessor or AudioModelInputPreprocessor(
            ModelInputConfig(
                sample_rate=16_000,
                target_duration_seconds=config.target_duration_seconds,
            )
        )
        # Keep the descriptive alias for callers that already use it.
        self.input_preprocessor = self.preprocessor

        train_dataset = ASVspoofTorchDataset(config.dataset_root, "train")
        counts = train_dataset.label_counts
        weights = class_weights(counts[0], counts[1], self.device)
        self.loss_fn = nn.CrossEntropyLoss(weight=weights)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=max(config.epochs, 2),
        )
        self.use_amp = self.device.type == "cuda" and config.mixed_precision
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)
        self.start_epoch = 1
        self.best_f1 = -math.inf
        self.best_epoch = 0
        self._optimizer_updates = 0

    def build_loaders(self) -> tuple[DataLoader, DataLoader]:
        train_dataset = ASVspoofTorchDataset(self.config.dataset_root, "train")
        dev_dataset = ASVspoofTorchDataset(self.config.dataset_root, "dev")
        common = {
            "batch_size": self.config.batch_size,
            "num_workers": self.config.num_workers,
            "pin_memory": self.device.type == "cuda",
            "collate_fn": asvspoof_collate_fn,
        }
        return (
            DataLoader(train_dataset, shuffle=True, **common),
            DataLoader(dev_dataset, shuffle=False, **common),
        )

    def _run_epoch(
        self,
        loader: DataLoader,
        training: bool,
        max_batches: int | None = None,
    ) -> EpochMetrics:
        self.model.train(training)
        if training:
            self.optimizer.zero_grad(set_to_none=True)

        total_loss = 0.0
        total_samples = 0
        total_correct = 0
        all_labels: list[Tensor] = []
        all_probabilities: list[Tensor] = []
        all_predictions: list[Tensor] = []
        total_batches = min(len(loader), max_batches) if max_batches is not None else len(loader)
        description = "Train" if training else "Dev"
        progress = tqdm(
            loader,
            total=total_batches,
            desc=description,
            unit="batch",
            dynamic_ncols=True,
            leave=True,
        )

        for batch_index, batch in enumerate(progress, start=1):
            if max_batches is not None and batch_index > max_batches:
                break

            waveforms = batch["waveforms"]
            labels = batch["labels"]
            attention_mask = batch.get("attention_mask")
            if not isinstance(waveforms, Tensor) or not isinstance(labels, Tensor):
                raise TypeError(
                    "ASVspoof collate output must contain Tensor waveforms and labels."
                )
            if attention_mask is not None and not isinstance(attention_mask, Tensor):
                raise TypeError("attention_mask must be a torch.Tensor when provided.")

            prepared = self.preprocessor.prepare_batch(waveforms, attention_mask)
            waveforms = prepared["waveforms"].to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            with torch.set_grad_enabled(training):
                with torch.autocast(
                    device_type=self.device.type,
                    dtype=torch.float16,
                    enabled=self.use_amp,
                ):
                    logits = self.model(waveforms)
                    loss = self.loss_fn(logits, labels)
                    scaled_loss = (
                        loss / self.config.gradient_accumulation_steps
                        if training
                        else loss
                    )

                if training:
                    self.scaler.scale(scaled_loss).backward()
                    should_step = (
                        batch_index % self.config.gradient_accumulation_steps == 0
                        or batch_index == total_batches
                    )
                    if should_step:
                        self.scaler.unscale_(self.optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(),
                            max_norm=5.0,
                        )
                        scale_before = self.scaler.get_scale()
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                        scale_after = self.scaler.get_scale()
                        if scale_after >= scale_before:
                            self._optimizer_updates += 1
                        self.optimizer.zero_grad(set_to_none=True)

            probabilities = AASISTModel.probabilities(logits)
            predictions = AASISTModel.predict_label(logits)
            batch_size = labels.shape[0]
            total_loss += float(loss.detach().cpu()) * batch_size
            total_samples += batch_size
            total_correct += int((predictions == labels).sum().item())
            all_labels.append(labels.detach().cpu())
            all_probabilities.append(
                probabilities[:, AASISTModel.SPOOF_CLASS].detach().cpu()
            )
            all_predictions.append(predictions.detach().cpu())
            progress.set_postfix(
                loss=f"{total_loss / total_samples:.4f}",
                refresh=False,
            )

        if not total_samples:
            raise RuntimeError("No samples were processed in the epoch.")

        labels = torch.cat(all_labels)
        probabilities = torch.cat(all_probabilities)
        predictions = torch.cat(all_predictions)
        precision, recall, f1, roc_auc, eer = _binary_metrics(
            labels,
            probabilities,
            predictions,
        )
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

    def train_epoch(
        self,
        loader: DataLoader,
        max_batches: int | None = None,
    ) -> EpochMetrics:
        """Run one optimizer epoch."""
        return self._run_epoch(loader, training=True, max_batches=max_batches)

    @torch.no_grad()
    def validate_epoch(
        self,
        loader: DataLoader,
        max_batches: int | None = None,
    ) -> EpochMetrics:
        """Run one validation epoch without gradient updates."""
        return self._run_epoch(loader, training=False, max_batches=max_batches)

    def _checkpoint_payload(
        self,
        epoch: int,
        train_metrics: EpochMetrics,
        dev_metrics: EpochMetrics,
    ) -> dict[str, Any]:
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

    def save_checkpoint(
        self,
        path: str | Path,
        epoch: int,
        train_metrics: EpochMetrics,
        dev_metrics: EpochMetrics,
    ) -> Path:
        """Atomically save a resumable checkpoint."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
        )
        os.close(fd)
        try:
            torch.save(
                self._checkpoint_payload(epoch, train_metrics, dev_metrics),
                temporary,
            )
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        return target

    def resume(self, path: str | Path) -> None:
        """Resume model and optimizer state from a checkpoint."""
        checkpoint = torch.load(
            path,
            map_location=self.device,
            weights_only=False,
        )
        required = {
            "epoch",
            "model_state_dict",
            "optimizer_state_dict",
            "scheduler_state_dict",
            "scaler_state_dict",
        }
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
            print(f"\nEpoch {epoch}/{self.config.epochs}")
            optimizer_updates_before = self._optimizer_updates
            train_metrics = self.train_epoch(
                train_loader,
                self.config.max_train_batches,
            )
            dev_metrics = self.validate_epoch(
                dev_loader,
                self.config.max_dev_batches,
            )
            if self._optimizer_updates > optimizer_updates_before:
                self.scheduler.step()

            record = {
                "epoch": epoch,
                "learning_rate": self.optimizer.param_groups[0]["lr"],
                "train": asdict(train_metrics),
                "dev": asdict(dev_metrics),
            }
            history.append(record)
            print(
                f"Epoch {epoch}/{self.config.epochs} complete | "
                f"Train loss {train_metrics.loss:.4f} F1 {train_metrics.f1:.4f} | "
                f"Dev loss {dev_metrics.loss:.4f} F1 {dev_metrics.f1:.4f}"
            )

            if dev_metrics.f1 > self.best_f1:
                self.best_f1 = dev_metrics.f1
                self.best_epoch = epoch
                self.save_checkpoint(
                    best_path,
                    epoch,
                    train_metrics,
                    dev_metrics,
                )
                print(f"New best model: Dev F1 {self.best_f1:.4f}")

            if self.config.checkpoint_every_epoch or epoch == self.config.epochs:
                self.save_checkpoint(
                    latest_path,
                    epoch,
                    train_metrics,
                    dev_metrics,
                )

            history_path = checkpoint_dir / "history.json"
            history_path.write_text(
                json.dumps(history, indent=2),
                encoding="utf-8",
            )

        if self.best_epoch == 0:
            raise RuntimeError("Training completed without producing a best checkpoint.")
        return TrainingResult(
            best_epoch=self.best_epoch,
            best_f1=self.best_f1,
            history=tuple(history),
            best_checkpoint=str(best_path),
            latest_checkpoint=str(latest_path),
        )


def build_training_engine(config: AASISTTrainingConfig) -> AASISTTrainer:
    """Factory for the Phase 05 training engine."""
    return AASISTTrainer(config)