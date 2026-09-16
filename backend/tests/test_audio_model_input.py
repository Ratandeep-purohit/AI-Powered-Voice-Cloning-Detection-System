"""Tests for detector model-input preprocessing."""

import pytest
import torch

from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig


def test_prepare_crops_long_waveform_and_normalizes() -> None:
    preprocessor = AudioModelInputPreprocessor(
        ModelInputConfig(sample_rate=16000, target_duration_seconds=1.0)
    )
    waveform = torch.full((1, 24000), 0.25, dtype=torch.float32)

    prepared, mask = preprocessor.prepare(waveform)

    assert prepared.shape == (1, 16000)
    assert mask.shape == (16000,)
    assert bool(mask.all()) is True
    assert torch.allclose(prepared, torch.ones_like(prepared))


def test_prepare_pads_short_waveform_and_marks_padding_invalid() -> None:
    preprocessor = AudioModelInputPreprocessor(
        ModelInputConfig(sample_rate=16000, target_duration_seconds=1.0)
    )
    waveform = torch.full((1, 8000), 0.5, dtype=torch.float32)

    prepared, mask = preprocessor.prepare(waveform)

    assert prepared.shape == (1, 16000)
    assert mask.shape == (16000,)
    assert int(mask.sum()) == 8000
    assert bool(mask[:8000].all()) is True
    assert bool(mask[8000:].any()) is False
    assert torch.allclose(prepared[:, :8000], torch.ones((1, 8000)))
    assert torch.count_nonzero(prepared[:, 8000:]) == 0


def test_prepare_batch_preserves_batch_shape_and_intersects_source_mask() -> None:
    preprocessor = AudioModelInputPreprocessor(
        ModelInputConfig(sample_rate=16000, target_duration_seconds=1.0)
    )
    waveforms = torch.zeros((2, 1, 12000), dtype=torch.float32)
    waveforms[0, 0, :6000] = 0.5
    waveforms[1, 0, :12000] = 0.25
    source_mask = torch.zeros((2, 12000), dtype=torch.bool)
    source_mask[0, :6000] = True
    source_mask[1, :10000] = True

    result = preprocessor.prepare_batch(waveforms, source_mask)

    assert result["waveforms"].shape == (2, 1, 16000)
    assert result["attention_mask"].shape == (2, 16000)
    assert int(result["attention_mask"][0].sum()) == 6000
    assert int(result["attention_mask"][1].sum()) == 10000
    assert torch.isfinite(result["waveforms"]).all()


def test_prepare_rejects_non_mono_waveform() -> None:
    preprocessor = AudioModelInputPreprocessor()
    waveform = torch.zeros((2, 16000), dtype=torch.float32)

    with pytest.raises(ValueError, match="mono"):
        preprocessor.prepare(waveform)


def test_prepare_rejects_non_finite_waveform() -> None:
    preprocessor = AudioModelInputPreprocessor()
    waveform = torch.zeros((1, 16000), dtype=torch.float32)
    waveform[0, 100] = float("nan")

    with pytest.raises(ValueError, match="NaN or infinite"):
        preprocessor.prepare(waveform)


def test_prepare_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="target_duration_seconds"):
        AudioModelInputPreprocessor(
            ModelInputConfig(target_duration_seconds=0)
        )


def test_prepare_can_run_on_cuda_when_available() -> None:
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available.")

    device = torch.device("cuda:0")
    preprocessor = AudioModelInputPreprocessor(
        ModelInputConfig(sample_rate=16000, target_duration_seconds=1.0)
    )
    waveform = torch.rand((2, 1, 8000), device=device)

    result = preprocessor.prepare_batch(waveform)

    assert result["waveforms"].device == device
    assert result["attention_mask"].device == device
    assert result["waveforms"].shape == (2, 1, 16000)
