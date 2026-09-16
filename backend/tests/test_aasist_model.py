"""Tests for the Phase 05 AASIST detector integration."""

import pytest
import torch

from app.services.aasist_model import AASISTModel, AASISTModelConfig


@pytest.fixture
def model() -> AASISTModel:
    torch.manual_seed(7)
    return AASISTModel()


def test_aasist_forward_shape_and_finite_logits(model: AASISTModel) -> None:
    waveform = torch.randn((2, 1, 64_000), dtype=torch.float32)

    logits = model(waveform)

    assert logits.shape == (2, 2)
    assert logits.dtype == torch.float32
    assert torch.isfinite(logits).all()


def test_aasist_probabilities_sum_to_one(model: AASISTModel) -> None:
    waveform = torch.randn((2, 1, 64_000), dtype=torch.float32)

    logits = model(waveform)
    probabilities = model.probabilities(logits)

    assert probabilities.shape == (2, 2)
    assert torch.isfinite(probabilities).all()
    assert torch.allclose(probabilities.sum(dim=-1), torch.ones(2), atol=1e-6)
    assert torch.all((probabilities >= 0) & (probabilities <= 1))


def test_aasist_label_mapping_is_real_zero_spoof_one(model: AASISTModel) -> None:
    assert model.REAL_CLASS == 0
    assert model.SPOOF_CLASS == 1

    logits = torch.tensor([[4.0, -1.0], [-2.0, 3.0]])
    labels = model.predict_label(logits)

    assert labels.tolist() == [0, 1]


def test_aasist_backward_produces_gradients(model: AASISTModel) -> None:
    waveform = torch.randn((2, 1, 64_000), dtype=torch.float32)
    labels = torch.tensor([0, 1], dtype=torch.long)

    logits = model(waveform)
    loss = torch.nn.functional.cross_entropy(logits, labels)
    loss.backward()

    assert torch.isfinite(loss)
    gradients = [parameter.grad for parameter in model.parameters() if parameter.requires_grad]
    assert gradients
    assert all(gradient is not None for gradient in gradients)
    assert all(torch.isfinite(gradient).all() for gradient in gradients if gradient is not None)


def test_aasist_rejects_bad_input_shape(model: AASISTModel) -> None:
    with pytest.raises(ValueError, match="\[batch, 1, time\]"):
        model(torch.zeros((2, 64_000), dtype=torch.float32))


def test_aasist_rejects_non_finite_input(model: AASISTModel) -> None:
    waveform = torch.zeros((1, 1, 64_000), dtype=torch.float32)
    waveform[0, 0, 10] = float("nan")

    with pytest.raises(ValueError, match="NaN or infinite"):
        model(waveform)


def test_aasist_cuda_forward_when_available() -> None:
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available.")

    device = torch.device("cuda:0")
    model = AASISTModel().to(device)
    waveform = torch.randn((2, 1, 64_000), device=device, dtype=torch.float32)

    with torch.no_grad():
        logits = model(waveform)

    assert logits.device == device
    assert logits.shape == (2, 2)
    assert torch.isfinite(logits).all()
