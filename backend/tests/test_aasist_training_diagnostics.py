from __future__ import annotations

import torch

from app.services.aasist_training_diagnostics import _auc_and_eer, _snapshot


def test_auc_and_eer_are_perfect_for_separated_scores() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.1, 0.2, 0.8, 0.9])

    auc, eer = _auc_and_eer(labels, scores)

    assert auc == 1.0
    assert eer == 0.0


def test_snapshot_reports_balanced_predictions() -> None:
    labels = torch.tensor([0, 0, 1, 1])
    scores = torch.tensor([0.1, 0.2, 0.8, 0.9])
    predictions = torch.tensor([0, 0, 1, 1])

    result = _snapshot("test", labels, scores, predictions, 0.25, 1.5)

    assert result.samples == 4
    assert result.real == 2
    assert result.spoof == 2
    assert result.accuracy == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0
    assert result.predicted_real == 2
    assert result.predicted_spoof == 2
    assert result.gradient_norm == 1.5
    assert result.spoof_probability.real is not None
    assert result.spoof_probability.spoof is not None
