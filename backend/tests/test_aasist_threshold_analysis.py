from __future__ import annotations

import pytest
import torch

from app.services.aasist_threshold_analysis import (
    analyze_scores,
    operating_point,
    score_statistics,
    sweep_thresholds,
    threshold_metrics,
)


def test_threshold_metrics_uses_spoof_score_as_positive() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.10, 0.40, 0.60, 0.90])

    metrics = threshold_metrics(labels, scores, threshold=0.50)

    assert (metrics.true_negative, metrics.false_positive) == (2, 0)
    assert (metrics.false_negative, metrics.true_positive) == (0, 2)
    assert metrics.accuracy == pytest.approx(1.0)
    assert metrics.f1 == pytest.approx(1.0)
    assert metrics.far == pytest.approx(0.0)
    assert metrics.frr == pytest.approx(0.0)


def test_threshold_metrics_exposes_false_positive_tradeoff() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.10, 0.80, 0.90, 0.95])

    metrics = threshold_metrics(labels, scores, threshold=0.50)

    assert (metrics.true_negative, metrics.false_positive) == (1, 1)
    assert (metrics.false_negative, metrics.true_positive) == (0, 2)
    assert metrics.far == pytest.approx(0.5)
    assert metrics.frr == pytest.approx(0.0)


def test_sweep_thresholds_includes_requested_grid() -> None:
    labels = torch.tensor([0, 1])
    scores = torch.tensor([0.2, 0.8])

    result = sweep_thresholds(labels, scores, start=0.0, stop=1.0, step=0.25)

    assert [item.threshold for item in result] == pytest.approx([0.0, 0.25, 0.50, 0.75, 1.0])


def test_score_statistics_returns_distribution_quantiles() -> None:
    scores = torch.tensor([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

    stats = score_statistics(scores)

    assert stats.count == 11
    assert stats.minimum == pytest.approx(0.0)
    assert stats.median == pytest.approx(0.5)
    assert stats.maximum == pytest.approx(1.0)


def test_operating_point_can_find_perfect_threshold() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.05, 0.20, 0.80, 0.95])

    best = operating_point(labels, scores, objective="f1")

    assert 0.20 < best.threshold <= 0.80
    assert best.f1 == pytest.approx(1.0)
    assert best.far == pytest.approx(0.0)
    assert best.frr == pytest.approx(0.0)


def test_analyze_scores_requires_both_classes() -> None:
    with pytest.raises(ValueError, match="Both REAL and SPOOF"):
        analyze_scores(
            torch.zeros(3, dtype=torch.long),
            torch.tensor([0.1, 0.2, 0.3]),
            split="dev",
            checkpoint="checkpoint.pt",
            device="cpu",
        )


def test_threshold_metrics_rejects_invalid_inputs() -> None:
    labels = torch.tensor([0, 1])
    scores = torch.tensor([0.1, float("nan")])

    with pytest.raises(ValueError, match="NaN or infinite"):
        threshold_metrics(labels, scores, threshold=0.5)
    with pytest.raises(ValueError, match="between 0 and 1"):
        threshold_metrics(torch.tensor([0, 1]), torch.tensor([0.1, 0.9]), threshold=1.1)
