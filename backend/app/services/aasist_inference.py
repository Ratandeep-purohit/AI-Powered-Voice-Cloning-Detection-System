"""Runtime AASIST-family inference for processed application audio."""

from __future__ import annotations

import time
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path

import torch

from app.config import Settings
from app.services.aasist_model import AASISTModel, AASISTModelConfig
from app.services.audio_model_input import AudioModelInputPreprocessor, ModelInputConfig


class AASISTInferenceError(ValueError):
    """Raised when detector inference cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class AASISTInferenceResult:
    """Model output for one processed application audio file."""

    model_name: str
    model_version: str
    spoof_probability: float
    authentic_probability: float
    predicted_label: str
    confidence: float
    processing_time_ms: int
    threshold: float


def _load_processed_waveform(path: Path) -> torch.Tensor:
    if not path.is_file():
        raise AASISTInferenceError("Processed audio file is not available.")
    try:
        with wave.open(str(path), "rb") as reader:
            channels = reader.getnchannels()
            sample_rate = reader.getframerate()
            sample_width = reader.getsampwidth()
            frame_count = reader.getnframes()
            frames = reader.readframes(frame_count)
    except (OSError, wave.Error) as exc:
        raise AASISTInferenceError("Processed audio is not a valid WAV file.") from exc

    if channels != 1 or sample_rate != 16_000 or sample_width != 2 or frame_count <= 0:
        raise AASISTInferenceError("Processed audio must be 16 kHz, mono, 16-bit PCM WAV.")

    waveform = torch.frombuffer(bytearray(frames), dtype=torch.int16).clone().to(torch.float32) / 32768.0
    return waveform.unsqueeze(0)


def _safe_processed_path(settings: Settings, storage_key: str) -> Path:
    root = Path(settings.audio_storage_path).resolve()
    candidate = (root / storage_key).resolve()
    if candidate != root and root not in candidate.parents:
        raise AASISTInferenceError("Processed audio reference is outside the configured storage root.")
    return candidate


class AASISTInferenceService:
    """Load one detector checkpoint and perform cached synchronous inference."""

    def __init__(self, settings: Settings, *, device: str = "auto", mixed_precision: bool = True) -> None:
        checkpoint = Path(settings.aasist_checkpoint_path).expanduser().resolve()
        if not checkpoint.is_file():
            raise AASISTInferenceError(f"AASIST checkpoint does not exist: {checkpoint}")
        if device not in {"auto", "cpu", "cuda"}:
            raise AASISTInferenceError("AASIST inference device must be auto, cpu, or cuda.")
        if device == "cuda" and not torch.cuda.is_available():
            raise AASISTInferenceError("CUDA was requested but is not available.")

        selected = "cuda" if device == "auto" and torch.cuda.is_available() else device
        self.device = torch.device("cuda:0" if selected == "cuda" else selected)
        self.mixed_precision = mixed_precision and self.device.type == "cuda"
        self.threshold = float(settings.aasist_detection_threshold)
        if not 0.0 < self.threshold < 1.0:
            raise AASISTInferenceError("AASIST_DETECTION_THRESHOLD must be between 0 and 1.")

        self.checkpoint = checkpoint
        self.model_name = settings.aasist_model_name
        self.model_version = settings.aasist_model_version
        self.preprocessor = AudioModelInputPreprocessor(
            ModelInputConfig(sample_rate=16_000, target_duration_seconds=settings.aasist_target_duration_seconds)
        )
        self.model = AASISTModel(AASISTModelConfig()).to(self.device)
        checkpoint_data = torch.load(checkpoint, map_location=self.device, weights_only=False)
        state_dict = checkpoint_data.get("model_state_dict") if isinstance(checkpoint_data, dict) else None
        if state_dict is None:
            raise AASISTInferenceError("AASIST checkpoint does not contain model_state_dict.")
        try:
            self.model.load_state_dict(state_dict)
        except (RuntimeError, ValueError) as exc:
            raise AASISTInferenceError("AASIST checkpoint does not match the project model architecture.") from exc
        self.model.eval()

    def predict_processed_audio(self, processed_storage_key: str) -> AASISTInferenceResult:
        path = _safe_processed_path(self._settings, processed_storage_key)
        waveform = _load_processed_waveform(path)
        prepared = self.preprocessor.prepare(waveform)[0].unsqueeze(0).to(self.device)

        started = time.perf_counter()
        with torch.inference_mode():
            with torch.autocast(
                device_type=self.device.type,
                dtype=torch.float16,
                enabled=self.mixed_precision,
            ):
                logits = self.model(prepared)
            probabilities = AASISTModel.probabilities(logits)[0]

        spoof_probability = float(probabilities[AASISTModel.SPOOF_CLASS].detach().cpu())
        authentic_probability = float(probabilities[AASISTModel.REAL_CLASS].detach().cpu())
        predicted_label = "SPOOF" if spoof_probability >= self.threshold else "REAL"
        confidence = max(spoof_probability, authentic_probability)
        elapsed_ms = max(0, round((time.perf_counter() - started) * 1000))

        return AASISTInferenceResult(
            model_name=self.model_name,
            model_version=self.model_version,
            spoof_probability=spoof_probability,
            authentic_probability=authentic_probability,
            predicted_label=predicted_label,
            confidence=confidence,
            processing_time_ms=elapsed_ms,
            threshold=self.threshold,
        )

    def bind_settings(self, settings: Settings) -> "AASISTInferenceService":
        self._settings = settings
        return self


def build_aasist_inference_service(settings: Settings, *, device: str = "auto", mixed_precision: bool = True) -> AASISTInferenceService:
    """Build a detector service with the application settings bound."""
    return AASISTInferenceService(settings, device=device, mixed_precision=mixed_precision).bind_settings(settings)
