"""Authenticated analysis-session and audio-intake endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.user import User
from app.schemas.analysis import AnalysisSessionCreate, AnalysisSessionResponse
from app.services.analysis import create_session, get_owned_session, store_audio_upload

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
async def create_analysis_session(
    payload: AnalysisSessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES)),
) -> Call:
    session = create_session(db, current_user, payload.external_reference, payload.caller_identifier)
    _audit(db, current_user, "SESSION_CREATED", session.id, request)
    return db.scalar(select(Call).options(selectinload(Call.audio_inputs)).where(Call.id == session.id))


@router.get("", response_model=list[AnalysisSessionResponse])
async def list_analysis_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Call]:
    return list(db.scalars(
        select(Call).options(selectinload(Call.audio_inputs))
        .where(Call.organization_id == current_user.organization_id)
        .order_by(Call.created_at.desc())
    ).all())


@router.get("/{session_id}", response_model=AnalysisSessionResponse)
async def get_analysis_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Call:
    session = db.scalar(
        select(Call).options(selectinload(Call.audio_inputs)).where(
            Call.id == session_id,
            Call.organization_id == current_user.organization_id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")
    return session


@router.post("/{session_id}/audio", response_model=AnalysisSessionResponse)
async def upload_analysis_audio(
    session_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CREATE_ANALYSIS_ROLES)),
) -> Call:
    session = get_owned_session(db, current_user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")
    if session.status in {"COMPLETED", "CANCELLED", "PROCESSING"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis session is not accepting new audio")

    try:
        audio = store_audio_upload(db, current_user, session, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    finally:
        await file.close()

    _audit(db, current_user, "AUDIO_ACCEPTED", session.id, request, {
        "audio_input_id": str(audio.id),
        "size_bytes": audio.size_bytes,
        "format": audio.detected_format,
    })
    return db.scalar(select(Call).options(selectinload(Call.audio_inputs)).where(Call.id == session.id))
