"""Authenticated analysis-session, audio-processing and detector endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.audio_input import AudioInput
from app.models.audio_processing import AudioProcessingJob
from app.models.call import Call
from app.models.user import User
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.analysis import AnalysisSessionCreate, AnalysisSessionResponse
from app.schemas.audio_processing import AudioProcessingResponse
from app.schemas.voice_analysis import DetectionResponse, VoiceAnalysisResponse
from app.services.aasist_inference import AASISTInferenceError, build_aasist_inference_service
from app.services.analysis import create_session, get_owned_session, store_audio_upload
from app.services.audio_processing import AudioProcessingError, process_audio_input

router = APIRouter(prefix="/calls", tags=["analysis"])
CREATE_ANALYSIS_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


def _audit(db: Session, user: User, action: str, entity_id: UUID, request: Request, metadata: dict | None = None) -> None:
    db.add(AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="ANALYSIS",
        action=action,
        entity_type="CALL",
        entity_id=entity_id,
        event_metadata=metadata,
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()


@router.post("", response_model=AnalysisSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis_session(payload: AnalysisSessionCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES))) -> Call:
    session = create_session(db, current_user, payload.external_reference, payload.caller_identifier)
    _audit(db, current_user, "SESSION_CREATED", session.id, request)
    return db.scalar(select(Call).options(selectinload(Call.audio_inputs)).where(Call.id == session.id))


@router.get("", response_model=list[AnalysisSessionResponse])
async def list_analysis_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Call]:
    return list(db.scalars(
        select(Call).options(selectinload(Call.audio_inputs))
        .where(Call.organization_id == current_user.organization_id)
        .order_by(Call.created_at.desc())
    ).all())


@router.get("/{session_id}", response_model=AnalysisSessionResponse)
async def get_analysis_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Call:
    session = db.scalar(select(Call).options(selectinload(Call.audio_inputs)).where(Call.id == session_id, Call.organization_id == current_user.organization_id))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")
    return session


@router.post("/{session_id}/audio", response_model=AnalysisSessionResponse)
async def upload_analysis_audio(session_id: UUID, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES))) -> Call:
    session = get_owned_session(db, current_user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")
    if session.status in {"COMPLETED", "CANCELLED", "PROCESSING"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis session is not accepting new audio")

    try:
        audio = store_audio_upload(db, current_user, session, file)
    except ValueError as exc:
        _audit(db, current_user, "AUDIO_REJECTED", session.id, request, {"reason": str(exc)})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    finally:
        await file.close()

    _audit(db, current_user, "AUDIO_ACCEPTED", session.id, request, {
        "audio_input_id": str(audio.id),
        "size_bytes": audio.size_bytes,
        "format": audio.detected_format,
    })
    return db.scalar(select(Call).options(selectinload(Call.audio_inputs)).where(Call.id == session.id))


@router.post("/{session_id}/audio/{audio_input_id}/process", response_model=AudioProcessingResponse)
async def process_analysis_audio(
    session_id: UUID,
    audio_input_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES)),
) -> AudioProcessingResponse:
    """Decode, standardize, normalize and persist one validated audio input."""
    audio = db.scalar(
        select(AudioInput)
        .join(Call, Call.id == AudioInput.call_id)
        .where(
            AudioInput.id == audio_input_id,
            AudioInput.call_id == session_id,
            Call.organization_id == current_user.organization_id,
        )
    )
    if audio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio input not found")
    if audio.intake_status != "VALIDATED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audio input is not validated")

    settings = get_settings()
    try:
        job = process_audio_input(db, audio, settings)
    except AudioProcessingError as exc:
        _audit(db, current_user, "AUDIO_PROCESSING_FAILED", session_id, request, {
            "audio_input_id": str(audio.id),
            "reason": str(exc),
        })
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from None

    _audit(db, current_user, "AUDIO_PROCESSING_COMPLETED", session_id, request, {
        "audio_input_id": str(audio.id),
        "processing_job_id": str(job.id),
        "processed_storage_key": job.processed_storage_key,
    })
    return job


@router.post("/{session_id}/audio/{audio_input_id}/detect", response_model=DetectionResponse)
async def detect_analysis_audio(
    session_id: UUID,
    audio_input_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES)),
) -> DetectionResponse:
    """Run the trained AASIST-family detector on processed application audio."""
    audio = db.scalar(
        select(AudioInput)
        .join(Call, Call.id == AudioInput.call_id)
        .where(
            AudioInput.id == audio_input_id,
            AudioInput.call_id == session_id,
            Call.organization_id == current_user.organization_id,
        )
    )
    if audio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio input not found")

    job = db.scalar(
        select(AudioProcessingJob)
        .where(AudioProcessingJob.audio_input_id == audio.id, AudioProcessingJob.status == "COMPLETED")
        .order_by(AudioProcessingJob.completed_at.desc())
    )
    if job is None or not job.processed_storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audio must be successfully processed before detection")

    settings = get_settings()
    try:
        result = build_aasist_inference_service(settings).predict_processed_audio(job.processed_storage_key)
    except AASISTInferenceError as exc:
        _audit(db, current_user, "DETECTION_FAILED", session_id, request, {
            "audio_input_id": str(audio.id),
            "reason": str(exc),
        })
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from None

    analysis = VoiceAnalysis(
        call_id=session_id,
        model_name=result.model_name,
        model_version=result.model_version,
        detection_status="COMPLETED",
        synthetic_score=result.spoof_probability,
        synthetic_probability=result.spoof_probability,
        authentic_probability=result.authentic_probability,
        confidence=result.confidence,
        processing_time_ms=result.processing_time_ms,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    _audit(db, current_user, "DETECTION_COMPLETED", session_id, request, {
        "audio_input_id": str(audio.id),
        "analysis_id": str(analysis.id),
        "model": result.model_name,
        "model_version": result.model_version,
        "decision": result.predicted_label,
        "threshold": result.threshold,
        "spoof_probability": result.spoof_probability,
        "processing_time_ms": result.processing_time_ms,
    })

    return DetectionResponse(
        analysis=VoiceAnalysisResponse.model_validate(analysis),
        decision=result.predicted_label,
        threshold=result.threshold,
    )
