"""Controlled class-balanced training experiment for the AASIST-family detector.

This module keeps the existing full-training engine intact and adds a separate
experiment path for diagnosing the severe ASVspoof REAL/SPOOF imbalance.
Training batches are sampled with equal class probability and checkpoints are
selected by balanced accuracy rather than ordinary F1 on the imbalanced dev set.
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
from torch.utils.data import DataLoader, WeightedRandomSampler
from tqdm.auto import tqdm

from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig
from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn


@dataclass(frozen=True, slots=True)
class BalancedTrainingConfig:
    dataset_root: str
    epochs: int = 10
    batch_size: int = 4
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    num_workers: int = 0
    target_duration_seconds: float = 4.0
    device: str = "auto"
    mixed_precision: bool = True
    samples_per_epoch: int | None = None
    checkpoint_dir: str = "artifacts/checkpoints/aasist_balanced"
    seed: int = 42
    max_dev_batches: int | None = None

    def validate(self) -> None:
        if not self.dataset_root.strip():
            raise ValueError("dataset_root must not be empty.")
        if self.epochs <= 0 or self.batch_size <= 0:
            raise ValueError("epochs and batch_size must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if self.weight_decay < 0:
            raise ValueError("weight_decay must not be negative.")
        if self.num_workers < 0:
            raise ValueError("num_workers must not be negative.")
        if self.target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be positive.")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda.")
        if self.samples_per_epoch is not None and self.samples_per_epoch <= 0:
            raise ValueError("samples_per_epoch must be positive when provided.")
        if self.max_dev_batches is not None and self.max_dev_batches <= 0:
            raise ValueError("max_dev_batches must be positive when provided.")


def resolve_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _metrics(labels: Tensor, scores: Tensor, predictions: Tensor) -> dict[str, Any]:
    labels = labels.to(torch.int64).flatten()
    scores = scores.to(torch.float64).flatten()
    predictions = predictions.to(torch.int64).flatten()
    if labels.numel() == 0:
        raise ValueError("Metric inputs must not be empty.")

    tn = int(((predictions == 0) & (labels == 0)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    tp = int(((predictions == 1) & (labels == 1)).sum())
    real = tn + fp
    spoof = tp + fn
    tpr = tp / spoof if spoof else 0.0
    tnr = tn / real if real else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tpr
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tn + tp) / labels.numel()
    balanced_accuracy = (tpr + tnr) / 2.0

    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    auc: float | None = None
    eer: float | None = None
    if positives.numel() and negatives.numel():
        auc = float(((positives[:, None] > negatives[None, :]).double() + (positives[:, None] == negatives[None, :]).double() * 0.5).mean())
        thresholds = torch.unique(torch.cat((positives, negatives)), sorted=True)
        thresholds = torch.cat((thresholds[:1] - 1e-12, thresholds, thresholds[-1:] + 1e-12))
        best_gap = math.inf
        for threshold in thresholds:
            far = float((negatives >= threshold).double().mean())
            frr = float((positives < threshold).double().mean())
            gap = abs(far - frr)
            if gap < best_gap:
                best_gap = gap
                eer = (far + frr) / 2.0

    return {
        "samples": int(labels.numel()),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
        "eer": eer,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "predicted_real": int((predictions == 0).sum()),
        "predicted_spoof": int((predictions == 1).sum()),
    }


class BalancedAASISTTrainer:
    """Train with equal REAL/SPOOF sampling while retaining all training data."""

    def __init__(self, config: BalancedTrainingConfig) -> None:
        config.validate()
        self.config = config
        torch.manual_seed(config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.seed)
        self.device = resolve_device(config.device)
        self.model = AASISTModel(AASISTModelConfig()).to(self.device)
        self.preprocessor = AudioModelInputPreprocessor(
            ModelInputConfig(sample_rate=16_000, target_duration_seconds=config.target_duration_seconds)
        )
        self.train_dataset = ASVspoofTorchDataset(config.dataset_root, "train")
        self.dev_dataset = ASVspoofTorchDataset(config.dataset_root, "dev")
        counts = self.train_dataset.label_counts
        sample_weights = torch.tensor(
            [1.0 / counts[sample.label] for sample in self.train_dataset],
            dtype=torch.double,
        )
        self.sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=config.samples_per_epoch or len(self.train_dataset),
            replacement=True,
            generator=torch.Generator().manual_seed(config.seed),
        )
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=config.batch_size,
            sampler=self.sampler,
            num_workers=config.num_workers,
            pin_memory=self.device.type == "cuda",
            collate_fn=asvspoof_collate_fn,
        )
        self.dev_loader = DataLoader(
            self.dev_dataset,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=config.num_workers,
            pin_memory=self.device.type == "cuda",
            collate_fn=asvspoof_collate_fn,
        )
        self.loss_fn = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=max(config.epochs, 2))
        self.use_amp = self.device.type == "cuda" and config.mixed_precision
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)
        self.best_balanced_accuracy = -math.inf
        self.best_epoch = 0

    def _pass(self, loader: DataLoader, training: bool, max_batches: int | None = None) -> tuple[float, dict[str, Any]]:
        self.model.train(training)
        if training:
            self.optimizer.zero_grad(set_to_none=True)
        labels_out: list[Tensor] = []
        scores_out: list[Tensor] = []
        predictions_out: list[Tensor] = []
        total_loss = 0.0
        total_samples = 0
        total_batches = min(len(loader), max_batches) if max_batches else len(loader)
        description = "Balanced train" if training else "Dev"
        progress = tqdm(loader, total=total_batches, desc=description, unit="batch", dynamic_ncols=True)
        for batch_index, batch in enumerate(progress, start=1):
            if max_batches and batch_index > max_batches:
                break
            prepared = self.preprocessor.prepare_batch(batch["waveforms"], batch.get("attention_mask"))
            waveforms = prepared["waveforms"].to(self.device, non_blocking=True)
            labels = batch["labels"].to(self.device, non_blocking=True)
            with torch.set_grad_enabled(training):
                with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=self.use_amp):
                    logits = self.model(waveforms)
                    loss = self.loss_fn(logits, labels)
                if training:
                    self.scaler.scale(loss).backward()
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 5.0)
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                    self.optimizer.zero_grad(set_to_none=True)
            probabilities = AASISTModel.probabilities(logits)
            predictions = AASISTModel.predict_label(logits)
            n = labels.shape[0]
            total_loss += float(loss.detach().cpu()) * n
            total_samples += n
            labels_out.append(labels.detach().cpu())
            scores_out.append(probabilities[:, AASISTModel.SPOOF_CLASS].detach().cpu())
            predictions_out.append(predictions.detach().cpu())
            progress.set_postfix(loss=f"{total_loss / total_samples:.4f}", refresh=False)
        labels = torch.cat(labels_out)
        scores = torch.cat(scores_out)
        predictions = torch.cat(predictions_out)
        return total_loss / total_samples, _metrics(labels, scores, predictions)

    def _save(self, path: Path, epoch: int, train_loss: float, train_metrics: dict[str, Any], dev_loss: float, dev_metrics: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        os.close(fd)
        try:
            torch.save({
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "scheduler_state_dict": self.scheduler.state_dict(),
                "scaler_state_dict": self.scaler.state_dict(),
                "best_balanced_accuracy": self.best_balanced_accuracy,
                "best_epoch": self.best_epoch,
                "config": asdict(self.config),
                "train_loss": train_loss,
                "train_metrics": train_metrics,
                "dev_loss": dev_loss,
                "dev_metrics": dev_metrics,
            }, temporary)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    def fit(self) -> dict[str, Any]:
        checkpoint_dir = Path(self.config.checkpoint_dir)
        best_path = checkpoint_dir / "best.pt"
        latest_path = checkpoint_dir / "latest.pt"
        history: list[dict[str, Any]] = []
        for epoch in range(1, self.config.epochs + 1):
            train_loss, train_metrics = self._pass(self.train_loader, training=True)
            dev_loss, dev_metrics = self._pass(self.dev_loader, training=False, max_batches=self.config.max_dev_batches)
            self.scheduler.step()
            record = {"epoch": epoch, "train_loss": train_loss, "train": train_metrics, "dev_loss": dev_loss, "dev": dev_metrics}
            history.append(record)
            self._save(latest_path, epoch, train_loss, train_metrics, dev_loss, dev_metrics)
            if dev_metrics["balanced_accuracy"] > self.best_balanced_accuracy:
                self.best_balanced_accuracy = dev_metrics["balanced_accuracy"]
                self.best_epoch = epoch
                self._save(best_path, epoch, train_loss, train_metrics, dev_loss, dev_metrics)
            print(
                f"Epoch {epoch}/{self.config.epochs} | "
                f"Train BA {train_metrics['balanced_accuracy']:.4f} F1 {train_metrics['f1']:.4f} | "
                f"Dev BA {dev_metrics['balanced_accuracy']:.4f} F1 {dev_metrics['f1']:.4f} "
                f"AUC {dev_metrics['roc_auc']:.4f} EER {dev_metrics['eer']:.4f}"
            )
        return {
            "config": asdict(self.config),
            "device": str(self.device),
            "train_class_counts": self.train_dataset.label_counts,
            "dev_class_counts": self.dev_dataset.label_counts,
            "samples_per_epoch": self.config.samples_per_epoch or len(self.train_dataset),
            "best_epoch": self.best_epoch,
            "best_balanced_accuracy": self.best_balanced_accuracy,
            "best_checkpoint": str(best_path),
            "latest_checkpoint": str(latest_path),
            "history": history,
        }


def save_json_report(report: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
