"""Analysis-session and secure audio-intake service."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audio_input import AudioInput
from app.models.call import Call
from app.models.user import User

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._ -]+")
_CHUNK_SIZE = 1024 * 1024

SUPPORTED_MEDIA = {
    "wav": {"audio/wav", "audio/x-wav", "audio/wave"},
    "mp3": {"audio/mpeg", "audio/mp3"},
    "ogg": {"audio/ogg", "application/ogg"},
    "flac": {"audio/flac", "audio/x-flac"},
    "m4a": {"audio/mp4", "audio/x-m4a", "video/mp4"},
}
DEFAULT_MEDIA_TYPE = {"wav": "audio/wav", "mp3": "audio/mpeg", "ogg": "audio/ogg", "flac": "audio/flac", "m4a": "audio/mp4"}


def _safe_original_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    cleaned = _FILENAME_SAFE.sub("_", Path(filename).name).strip()
    return cleaned[:255] or None


def _extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower().lstrip(".")


def _detect_format(header: bytes) -> str | None:
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "wav"
    if header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return "mp3"
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"fLaC"):
        return "flac"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return "m4a"
    return None


def create_session(db: Session, user: User, external_reference: str | None, caller_identifier: str | None) -> Call:
    session = Call(
        organization_id=user.organization_id,
        initiated_by_user_id=user.id,
        source_type="UPLOAD",
        status="PENDING",
        external_reference=external_reference,
        caller_identifier=caller_identifier,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_owned_session(db: Session, user: User, session_id: UUID) -> Call | None:
    return db.scalar(select(Call).where(Call.id == session_id, Call.organization_id == user.organization_id))


def store_audio_upload(db: Session, user: User, session: Call, upload: UploadFile) -> AudioInput:
    settings = get_settings()
    ext = _extension(upload.filename)
    if ext not in settings.allowed_audio_extensions or ext not in SUPPORTED_MEDIA:
        raise ValueError("Unsupported audio format")

    content_type = (upload.content_type or "").lower().split(";", 1)[0].strip()
    if content_type and content_type not in SUPPORTED_MEDIA[ext] and content_type != "application/octet-stream":
        raise ValueError("Audio media type does not match the file extension")

    root = Path(settings.audio_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    storage_key = f"{user.organization_id}/{session.id}/{uuid4().hex}.{ext}"
    destination = (root / storage_key).resolve()
    if root not in destination.parents:
        raise ValueError("Invalid storage path")
    destination.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = settings.audio_max_upload_size_mb * 1024 * 1024
    total = 0
    digest = hashlib.sha256()
    header = bytearray()

    try:
        with destination.open("wb") as target:
            while True:
                chunk = upload.file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Audio file exceeds the configured size limit")
                if len(header) < 32:
                    header.extend(chunk[: 32 - len(header)])
                digest.update(chunk)
                target.write(chunk)

        if total == 0:
            raise ValueError("Audio file is empty")

        detected = _detect_format(bytes(header))
        if detected != ext:
            raise ValueError("Audio content does not match the declared format")

        now = datetime.now(timezone.utc)
        audio = AudioInput(
            call_id=session.id,
            original_filename=_safe_original_filename(upload.filename),
            storage_key=storage_key,
            content_type=content_type or DEFAULT_MEDIA_TYPE[ext],
            detected_format=detected,
            size_bytes=total,
            sha256=digest.hexdigest(),
            intake_status="VALIDATED",
            validated_at=now,
        )
        db.add(audio)
        db.commit()
        db.refresh(audio)
        return audio
    except Exception:
        db.rollback()
        if destination.exists():
            destination.unlink()
        raise
