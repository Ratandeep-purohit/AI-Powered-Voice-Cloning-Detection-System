"""Threshold and score-distribution analysis for the Phase 05 AASIST detector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import torch
from torch import Tensor

from app.services.aasist_evaluation import AASISTEvaluator


@dataclass(frozen=True, slots=True)
class ThresholdMetrics:
    """Metrics at one SPOOF probability decision threshold."""

    threshold: float
    accuracy: float
    balanced_accuracy: float
    precision: float
    recall: float
    f1: float
    far: float
    frr: float
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScoreStatistics:
    """Compact score-distribution statistics for one class."""

    count: int
    minimum: float
    p01: float
    p05: float
    p25: float
    median: float
    p75: float
    p95: float
    p99: float
    maximum: float
    mean: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def threshold_metrics(labels: Tensor, spoof_probabilities: Tensor, threshold: float) -> ThresholdMetrics:
    """Compute binary detection metrics using score >= threshold => SPOOF."""

    labels = labels.to(torch.int64).flatten().cpu()
    scores = spoof_probabilities.to(torch.float64).flatten().cpu()
    if labels.numel() == 0 or labels.numel() != scores.numel():
        raise ValueError("Labels and spoof probabilities must be non-empty and equal in length.")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1.")
    if not torch.isfinite(scores).all():
        raise ValueError("Spoof probabilities contain NaN or infinite values.")
    if not torch.all((labels == 0) | (labels == 1)):
        raise ValueError("Labels must contain only REAL=0 and SPOOF=1.")

    predictions = (scores >= threshold).to(torch.int64)
    tn = int(((predictions == 0) & (labels == 0)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    tp = int(((predictions == 1) & (labels == 1)).sum())

    real_total = tn + fp
    spoof_total = fn + tp
    tpr = tp / spoof_total if spoof_total else 0.0
    tnr = tn / real_total if real_total else 0.0
    far = fp / real_total if real_total else 0.0
    frr = fn / spoof_total if spoof_total else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2.0 * precision * tpr / (precision + tpr) if precision + tpr else 0.0
    accuracy = (tn + tp) / labels.numel()

    return ThresholdMetrics(
        threshold=float(threshold),
        accuracy=accuracy,
        balanced_accuracy=(tpr + tnr) / 2.0,
        precision=precision,
        recall=tpr,
        f1=f1,
        far=far,
        frr=frr,
        true_negative=tn,
        false_positive=fp,
        false_negative=fn,
        true_positive=tp,
    )


def score_statistics(scores: Tensor) -> ScoreStatistics:
    """Return robust quantiles without retaining individual scores in JSON."""

    values = scores.to(torch.float64).flatten().cpu()
    if values.numel() == 0:
        raise ValueError("Scores must not be empty.")
    if not torch.isfinite(values).all():
        raise ValueError("Scores contain NaN or infinite values.")
    quantiles = torch.tensor([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99], dtype=torch.float64)
    q = torch.quantile(values, quantiles)
    return ScoreStatistics(
        count=int(values.numel()),
        minimum=float(values.min()),
        p01=float(q[0]),
        p05=float(q[1]),
        p25=float(q[2]),
        median=float(q[3]),
        p75=float(q[4]),
        p95=float(q[5]),
        p99=float(q[6]),
        maximum=float(values.max()),
        mean=float(values.mean()),
    )


def sweep_thresholds(
    labels: Tensor,
    spoof_probabilities: Tensor,
    *,
    start: float = 0.0,
    stop: float = 1.0,
    step: float = 0.01,
) -> tuple[ThresholdMetrics, ...]:
    """Evaluate a regular threshold grid, inclusive of stop when representable."""

    if step <= 0.0:
        raise ValueError("step must be positive.")
    if start < 0.0 or stop > 1.0 or start > stop:
        raise ValueError("threshold range must satisfy 0 <= start <= stop <= 1.")

    count = int(round((stop - start) / step))
    thresholds = [min(stop, start + index * step) for index in range(count + 1)]
    if thresholds[-1] < stop - 1e-12:
        thresholds.append(stop)
    return tuple(threshold_metrics(labels, spoof_probabilities, value) for value in thresholds)


def operating_point(
    labels: Tensor,
    spoof_probabilities: Tensor,
    *,
    objective: str = "f1",
) -> ThresholdMetrics:
    """Find the best grid-independent operating point on observed score values."""

    labels = labels.to(torch.int64).flatten().cpu()
    scores = spoof_probabilities.to(torch.float64).flatten().cpu()
    if labels.numel() == 0 or labels.numel() != scores.numel():
        raise ValueError("Labels and spoof probabilities must be non-empty and equal in length.")
    if objective not in {"f1", "balanced_accuracy", "eer"}:
        raise ValueError("objective must be one of: f1, balanced_accuracy, eer.")

    unique_scores = torch.unique(scores, sorted=True)
    candidates = torch.cat(
        (
            torch.tensor([0.0], dtype=torch.float64),
            unique_scores,
            torch.tensor([1.0], dtype=torch.float64),
        )
    )
    best: ThresholdMetrics | None = None
    best_key: tuple[float, float] | None = None
    for value in candidates.tolist():
        current = threshold_metrics(labels, scores, float(value))
        if objective == "f1":
            key = (current.f1, current.balanced_accuracy)
        elif objective == "balanced_accuracy":
            key = (current.balanced_accuracy, current.f1)
        else:
            key = (-abs(current.far - current.frr), current.f1)
        if best is None or key > best_key:  # type: ignore[operator]
            best = current
            best_key = key
    assert best is not None
    return best


@dataclass(frozen=True, slots=True)
class ThresholdAnalysisResult:
    """Complete score-distribution and threshold-sweep report."""

    split: str
    checkpoint: str
    device: str
    samples: int
    real_samples: int
    spoof_samples: int
    score_statistics: dict[str, ScoreStatistics]
    threshold_grid: tuple[ThresholdMetrics, ...]
    best_f1: ThresholdMetrics
    best_balanced_accuracy: ThresholdMetrics
    eer_operating_point: ThresholdMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "checkpoint": self.checkpoint,
            "device": self.device,
            "samples": self.samples,
            "real_samples": self.real_samples,
            "spoof_samples": self.spoof_samples,
            "score_statistics": {key: value.to_dict() for key, value in self.score_statistics.items()},
            "threshold_grid": [item.to_dict() for item in self.threshold_grid],
            "best_f1": self.best_f1.to_dict(),
            "best_balanced_accuracy": self.best_balanced_accuracy.to_dict(),
            "eer_operating_point": self.eer_operating_point.to_dict(),
        }


def analyze_scores(
    labels: Tensor,
    spoof_probabilities: Tensor,
    *,
    split: str,
    checkpoint: str,
    device: str,
    grid_start: float = 0.0,
    grid_stop: float = 1.0,
    grid_step: float = 0.01,
) -> ThresholdAnalysisResult:
    """Analyze already-collected scores without running model inference."""

    labels = labels.to(torch.int64).flatten().cpu()
    scores = spoof_probabilities.to(torch.float64).flatten().cpu()
    if labels.numel() == 0 or labels.numel() != scores.numel():
        raise ValueError("Labels and spoof probabilities must be non-empty and equal in length.")

    real_scores = scores[labels == 0]
    spoof_scores = scores[labels == 1]
    if real_scores.numel() == 0 or spoof_scores.numel() == 0:
        raise ValueError("Both REAL and SPOOF classes are required for threshold analysis.")

    grid = sweep_thresholds(
        labels,
        scores,
        start=grid_start,
        stop=grid_stop,
        step=grid_step,
    )
    return ThresholdAnalysisResult(
        split=split,
        checkpoint=checkpoint,
        device=device,
        samples=int(labels.numel()),
        real_samples=int(real_scores.numel()),
        spoof_samples=int(spoof_scores.numel()),
        score_statistics={"real": score_statistics(real_scores), "spoof": score_statistics(spoof_scores)},
        threshold_grid=grid,
        best_f1=operating_point(labels, scores, objective="f1"),
        best_balanced_accuracy=operating_point(labels, scores, objective="balanced_accuracy"),
        eer_operating_point=operating_point(labels, scores, objective="eer"),
    )


def collect_and_analyze(
    dataset_root: str,
    checkpoint: str,
    *,
    split: str = "dev",
    batch_size: int = 2,
    num_workers: int = 0,
    target_duration_seconds: float = 4.0,
    device: str = "auto",
    mixed_precision: bool = True,
    grid_start: float = 0.0,
    grid_stop: float = 1.0,
    grid_step: float = 0.01,
) -> ThresholdAnalysisResult:
    """Run inference once, then perform all threshold analysis in memory."""

    evaluator = AASISTEvaluator(
        dataset_root,
        checkpoint,
        batch_size=batch_size,
        num_workers=num_workers,
        target_duration_seconds=target_duration_seconds,
        device=device,
        mixed_precision=mixed_precision,
    )
    normalized_split = split.strip().lower()
    if normalized_split not in {"train", "dev", "eval"}:
        raise ValueError("split must be one of: train, dev, eval.")

    from torch.utils.data import DataLoader
    from app.services.asvspoof_torch import ASVspoofTorchDataset, asvspoof_collate_fn
    from tqdm.auto import tqdm

    dataset = ASVspoofTorchDataset(evaluator.dataset_root, normalized_split, sample_rate=16_000)
    loader = DataLoader(
        dataset,
        batch_size=evaluator.batch_size,
        shuffle=False,
        num_workers=evaluator.num_workers,
        pin_memory=evaluator.device.type == "cuda",
        collate_fn=asvspoof_collate_fn,
    )

    all_labels: list[Tensor] = []
    all_scores: list[Tensor] = []
    progress = tqdm(loader, total=len(loader), desc=f"Threshold analysis ({normalized_split})", unit="batch", dynamic_ncols=True)
    with torch.inference_mode():
        for batch in progress:
            waveforms = batch["waveforms"]
            labels = batch["labels"]
            attention_mask = batch.get("attention_mask")
            prepared = evaluator.preprocessor.prepare_batch(waveforms, attention_mask)
            waveforms = prepared["waveforms"].to(evaluator.device, non_blocking=True)
            with torch.autocast(
                device_type=evaluator.device.type,
                dtype=torch.float16,
                enabled=evaluator.device.type == "cuda" and evaluator.mixed_precision,
            ):
                logits = evaluator.model(waveforms)
            probabilities = evaluator.model.probabilities(logits)
            all_labels.append(labels.detach().cpu())
            all_scores.append(probabilities[:, evaluator.model.SPOOF_CLASS].detach().cpu())

    return analyze_scores(
        torch.cat(all_labels),
        torch.cat(all_scores),
        split=normalized_split,
        checkpoint=str(evaluator.checkpoint),
        device=str(evaluator.device),
        grid_start=grid_start,
        grid_stop=grid_stop,
        grid_step=grid_step,
    )
