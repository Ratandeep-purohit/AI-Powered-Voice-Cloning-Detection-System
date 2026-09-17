"""Evaluation engine for the Phase 05 AASIST-family spoof detector."""

from __future__ import annotations

import math
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
class EvaluationMetrics:
    """Classification metrics for one evaluated split."""

    samples: int
    correct: int
    loss: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    eer: float | None
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Complete model evaluation result."""

    split: str
    checkpoint: str
    device: str
    sample_rate: int
    target_duration_seconds: float
    threshold: float
    metrics: EvaluationMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "checkpoint": self.checkpoint,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "target_duration_seconds": self.target_duration_seconds,
            "threshold": self.threshold,
            "metrics": self.metrics.to_dict(),
        }


def classification_metrics(
    labels: Tensor,
    spoof_probabilities: Tensor,
    predictions: Tensor,
    loss: float = 0.0,
) -> EvaluationMetrics:
    """Compute confusion-matrix and ranking metrics."""

    labels = labels.to(torch.int64).flatten().cpu()
    scores = spoof_probabilities.to(torch.float64).flatten().cpu()
    predictions = predictions.to(torch.int64).flatten().cpu()
    if not (labels.numel() == scores.numel() == predictions.numel()) or not labels.numel():
        raise ValueError("Metric inputs must be non-empty and have equal length.")
    if not torch.isfinite(scores).all():
        raise ValueError("Spoof probabilities contain NaN or infinite values.")

    tn = int(((predictions == 0) & (labels == 0)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    tp = int(((predictions == 1) & (labels == 1)).sum())
    correct = tn + tp
    samples = int(labels.numel())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0

    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    roc_auc: float | None = None
    eer: float | None = None
    if positives.numel() and negatives.numel():
        all_scores = torch.cat((positives, negatives))
        order = torch.argsort(all_scores, stable=True)
        sorted_scores = all_scores[order]
        ranks = torch.arange(1, samples + 1, dtype=torch.float64)
        start = 0
        while start < samples:
            end = start + 1
            while end < samples and sorted_scores[end] == sorted_scores[start]:
                end += 1
            ranks[start:end] = (start + 1 + end) / 2.0
            start = end
        sorted_labels = torch.cat((torch.ones(positives.numel()), torch.zeros(negatives.numel())))[order]
        rank_sum = float(ranks[sorted_labels == 1].sum())
        n_pos = positives.numel()
        n_neg = negatives.numel()
        roc_auc = (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

        sweep_order = torch.argsort(scores, descending=True, stable=True)
        sorted_labels_desc = labels[sweep_order]
        positives_total = n_pos
        negatives_total = n_neg
        tp_running = 0
        fp_running = 0
        best_gap = math.inf
        best_eer = 1.0
        index = 0
        while index < samples:
            end = index + 1
            threshold = scores[sweep_order[index]]
            while end < samples and scores[sweep_order[end]] == threshold:
                end += 1
            group = sorted_labels_desc[index:end]
            tp_running += int((group == 1).sum())
            fp_running += int((group == 0).sum())
            far = fp_running / negatives_total
            frr = (positives_total - tp_running) / positives_total
            gap = abs(far - frr)
            if gap < best_gap:
                best_gap = gap
                best_eer = (far + frr) / 2.0
            index = end
        eer = best_eer

    return EvaluationMetrics(
        samples=samples,
        correct=correct,
        loss=float(loss),
        accuracy=correct / samples,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        eer=eer,
        true_negative=tn,
        false_positive=fp,
        false_negative=fn,
        true_positive=tp,
    )


class AASISTEvaluator:
    """Run deterministic split inference using a trained checkpoint."""

    def __init__(
        self,
        dataset_root: str | Path,
        checkpoint: str | Path,
        *,
        batch_size: int = 2,
        num_workers: int = 0,
        target_duration_seconds: float = 4.0,
        device: str = "auto",
        mixed_precision: bool = True,
        threshold: float = 0.5,
    ) -> None:
        self.dataset_root = Path(dataset_root).expanduser().resolve()
        self.checkpoint = Path(checkpoint).expanduser().resolve()
        if not self.dataset_root.is_dir():
            raise ValueError(f"Dataset root does not exist: {self.dataset_root}")
        if not self.checkpoint.is_file():
            raise ValueError(f"Checkpoint does not exist: {self.checkpoint}")
        if batch_size <= 0 or num_workers < 0 or target_duration_seconds <= 0:
            raise ValueError("Invalid evaluation configuration.")
        if device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda.")
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be between 0 and 1.")

        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        self.device = torch.device("cuda" if device == "auto" and torch.cuda.is_available() else device)
        if self.device.type == "cuda":
            self.device = torch.device("cuda:0")
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.mixed_precision = mixed_precision
        self.threshold = float(threshold)
        self.preprocessor = AudioModelInputPreprocessor(
            ModelInputConfig(sample_rate=16_000, target_duration_seconds=target_duration_seconds)
        )
        self.model = AASISTModel(AASISTModelConfig()).to(self.device)
        checkpoint_data = torch.load(self.checkpoint, map_location=self.device, weights_only=False)
        if "model_state_dict" not in checkpoint_data:
            raise ValueError("Checkpoint does not contain model_state_dict.")
        self.model.load_state_dict(checkpoint_data["model_state_dict"])
        self.model.eval()
        self.loss_fn = nn.CrossEntropyLoss()

    def evaluate(self, split: str = "eval") -> EvaluationResult:
        normalized_split = split.strip().lower()
        if normalized_split not in {"train", "dev", "eval"}:
            raise ValueError("split must be one of: train, dev, eval.")

        dataset = ASVspoofTorchDataset(self.dataset_root, normalized_split, sample_rate=16_000)
        loader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.device.type == "cuda",
            collate_fn=asvspoof_collate_fn,
        )

        all_labels: list[Tensor] = []
        all_scores: list[Tensor] = []
        all_predictions: list[Tensor] = []
        total_loss = 0.0
        total_samples = 0

        progress = tqdm(loader, total=len(loader), desc=f"Evaluate ({normalized_split})", unit="batch", dynamic_ncols=True)
        with torch.inference_mode():
            for batch in progress:
                waveforms = batch["waveforms"]
                labels = batch["labels"]
                attention_mask = batch.get("attention_mask")
                prepared = self.preprocessor.prepare_batch(waveforms, attention_mask)
                waveforms = prepared["waveforms"].to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                with torch.autocast(
                    device_type=self.device.type,
                    dtype=torch.float16,
                    enabled=self.device.type == "cuda" and self.mixed_precision,
                ):
                    logits = self.model(waveforms)
                    loss = self.loss_fn(logits, labels)

                probabilities = AASISTModel.probabilities(logits)
                spoof_scores = probabilities[:, AASISTModel.SPOOF_CLASS]
                predictions = (spoof_scores >= self.threshold).to(torch.int64)
                size = int(labels.shape[0])
                total_loss += float(loss.detach().cpu()) * size
                total_samples += size
                all_labels.append(labels.detach().cpu())
                all_scores.append(spoof_scores.detach().cpu())
                all_predictions.append(predictions.detach().cpu())
                progress.set_postfix(loss=f"{total_loss / total_samples:.4f}", refresh=False)

        metrics = classification_metrics(
            torch.cat(all_labels),
            torch.cat(all_scores),
            torch.cat(all_predictions),
            loss=total_loss / total_samples,
        )
        return EvaluationResult(
            split=normalized_split,
            checkpoint=str(self.checkpoint),
            device=str(self.device),
            sample_rate=16_000,
            target_duration_seconds=self.preprocessor.config.target_duration_seconds,
            threshold=self.threshold,
            metrics=metrics,
        )


def evaluate_checkpoint(
    dataset_root: str | Path,
    checkpoint: str | Path,
    **kwargs: Any,
) -> EvaluationResult:
    """Convenience wrapper for CLI and integration callers."""
    return AASISTEvaluator(dataset_root, checkpoint, **kwargs).evaluate("eval")
