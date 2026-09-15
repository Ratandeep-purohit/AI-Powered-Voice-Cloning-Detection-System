"""Deterministic audio preprocessing for Phase 04.

The service converts accepted audio to model-ready PCM WAV using ffmpeg,
then applies peak normalization and persists processing metadata. It does not
perform ML inference or risk scoring.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import uuid
import wave
from array import array
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.audio_input import AudioInput
from app.models.audio_processing import AudioProcessingJob


class AudioProcessingError(ValueError):
    """Raised when an accepted input cannot be safely processed."""


def _storage_root(settings: Settings) -> Path:
    root = Path(settings.audio_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_input_path(settings: Settings, storage_key: str) -> Path:
    root = _storage_root(settings)
    candidate = (root / storage_key).resolve()
    if candidate != root and root not in candidate.parents:
        raise AudioProcessingError("Audio storage reference is outside the configured storage root.")
    if not candidate.is_file():
        raise AudioProcessingError("Source audio file is not available for processing.")
    return candidate


def _peak_normalize_pcm16(frames: bytes) -> bytes:
    samples = array("h")
    samples.frombytes(frames)
    if os.sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise AudioProcessingError("Decoded audio contains no samples.")

    peak = max(abs(sample) for sample in samples)
    if peak == 0:
        return frames

    target_peak = 30000
    if peak >= target_peak:
        return frames

    scale = target_peak / peak
    for index, sample in enumerate(samples):
        value = int(round(sample * scale))
        samples[index] = max(-32768, min(32767, value))

    if os.sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def _decode_to_wav(source: Path, destination: Path, settings: Settings) -> None:
    command = [
        settings.audio_processing_ffmpeg_binary,
        "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source),
        "-vn", "-sn", "-dn",
        "-ac", str(settings.audio_processing_channels),
        "-ar", str(settings.audio_processing_sample_rate),
        "-sample_fmt", "s16",
        "-f", "wav", str(destination),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise AudioProcessingError("ffmpeg is not installed or AUDIO_PROCESSING_FFMPEG_BINARY is invalid.") from exc
    if result.returncode != 0:
        detail = (result.stderr or "Audio decoder failed.").strip()[-500:]
        raise AudioProcessingError(f"Audio decoding failed: {detail}")


def process_audio_input(db: Session, audio_input: AudioInput, settings: Settings) -> AudioProcessingJob:
    """Process one validated AudioInput and persist the resulting metadata."""
    if audio_input.intake_status != "VALIDATED":
        raise AudioProcessingError("Only validated audio inputs can be processed.")

    job = AudioProcessingJob(audio_input_id=audio_input.id, status="PROCESSING", started_at=datetime.now(timezone.utc))
    db.add(job)
    db.flush()

    source_path = _safe_input_path(settings, audio_input.storage_key)
    root = _storage_root(settings)
    processed_dir = root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_name = f"{uuid.uuid4()}.wav"
    processed_path = processed_dir / processed_name
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(prefix="audio-processing-", suffix=".wav", delete=False, dir=processed_dir) as temp:
            temp_path = Path(temp.name)

        _decode_to_wav(source_path, temp_path, settings)

        with wave.open(str(temp_path), "rb") as reader:
            channels = reader.getnchannels()
            sample_rate = reader.getframerate()
            sample_width = reader.getsampwidth()
            frame_count = reader.getnframes()
            frames = reader.readframes(frame_count)

        if sample_width != 2:
            raise AudioProcessingError("Decoder did not produce 16-bit PCM audio.")
        duration_ms = round(frame_count * 1000 / sample_rate) if sample_rate else 0
        if duration_ms <= 0:
            raise AudioProcessingError("Decoded audio has zero duration.")
        if duration_ms > settings.audio_processing_max_duration_seconds * 1000:
            raise AudioProcessingError("Audio duration exceeds the configured processing limit.")

        normalized = _peak_normalize_pcm16(frames)
        with wave.open(str(processed_path), "wb") as writer:
            writer.setnchannels(settings.audio_processing_channels)
            writer.setsampwidth(2)
            writer.setframerate(settings.audio_processing_sample_rate)
            writer.writeframes(normalized)

        processed_size = processed_path.stat().st_size
        digest = hashlib.sha256(processed_path.read_bytes()).hexdigest()
        job.status = "COMPLETED"
        job.source_sample_rate = sample_rate
        job.source_channels = channels
        job.source_duration_ms = duration_ms
        job.processed_sample_rate = settings.audio_processing_sample_rate
        job.processed_channels = settings.audio_processing_channels
        job.processed_duration_ms = duration_ms
        job.processed_storage_key = str(Path("processed") / processed_name).replace("\\", "/")
        job.processed_size_bytes = processed_size
        job.processed_sha256 = digest
        job.normalization_applied = normalized != frames
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:
        if processed_path.exists():
            processed_path.unlink(missing_ok=True)
        job.status = "FAILED"
        job.error_message = str(exc)[:1000]
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        if isinstance(exc, AudioProcessingError):
            raise
        raise AudioProcessingError(f"Audio processing failed: {exc}") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
