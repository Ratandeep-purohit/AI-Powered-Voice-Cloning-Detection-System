from __future__ import annotations

import pytest
import torch

from app.services.aasist_evaluation import classification_metrics


def test_classification_metrics_perfect_predictions() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.01, 0.10, 0.90, 0.99])
    predictions = torch.tensor([0, 0, 1, 1])

    metrics = classification_metrics(labels, scores, predictions, loss=0.25)

    assert metrics.samples == 4
    assert metrics.correct == 4
    assert metrics.loss == pytest.approx(0.25)
    assert metrics.accuracy == pytest.approx(1.0)
    assert metrics.precision == pytest.approx(1.0)
    assert metrics.recall == pytest.approx(1.0)
    assert metrics.f1 == pytest.approx(1.0)
    assert metrics.roc_auc == pytest.approx(1.0)
    assert metrics.eer == pytest.approx(0.0)
    assert (metrics.true_negative, metrics.false_positive, metrics.false_negative, metrics.true_positive) == (2, 0, 0, 2)


def test_classification_metrics_confusion_matrix() -> None:
    labels = torch.tensor([0, 0, 0, 1, 1, 1])
    scores = torch.tensor([0.1, 0.8, 0.2, 0.9, 0.4, 0.7])
    predictions = torch.tensor([0, 1, 0, 1, 0, 1])

    metrics = classification_metrics(labels, scores, predictions)

    assert (metrics.true_negative, metrics.false_positive) == (2, 1)
    assert (metrics.false_negative, metrics.true_positive) == (1, 2)
    assert metrics.precision == pytest.approx(2 / 3)
    assert metrics.recall == pytest.approx(2 / 3)
    assert metrics.f1 == pytest.approx(2 / 3)
    assert metrics.roc_auc is not None
    assert metrics.eer is not None


def test_classification_metrics_single_class_returns_none_for_auc_and_eer() -> None:
    labels = torch.zeros(4, dtype=torch.long)
    scores = torch.tensor([0.1, 0.2, 0.3, 0.4])
    predictions = torch.zeros(4, dtype=torch.long)

    metrics = classification_metrics(labels, scores, predictions)

    assert metrics.accuracy == pytest.approx(1.0)
    assert metrics.precision == pytest.approx(0.0)
    assert metrics.recall == pytest.approx(0.0)
    assert metrics.f1 == pytest.approx(0.0)
    assert metrics.roc_auc is None
    assert metrics.eer is None


def test_classification_metrics_rejects_mismatched_inputs() -> None:
    with pytest.raises(ValueError, match="equal length"):
        classification_metrics(
            torch.tensor([0, 1]),
            torch.tensor([0.2]),
            torch.tensor([0, 1]),
        )


def test_classification_metrics_rejects_non_finite_scores() -> None:
    with pytest.raises(ValueError, match="NaN or infinite"):
        classification_metrics(
            torch.tensor([0, 1]),
            torch.tensor([0.2, float("nan")]),
            torch.tensor([0, 1]),
        )
