"""End-to-end orchestration across the completed voice security phases."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audio_input import AudioInput
from app.models.audio_processing import AudioProcessingJob
from app.models.call import Call
from app.models.user import User
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.alert import AlertResponse
from app.schemas.analysis_pipeline import AnalysisPipelineResponse, PipelineProcessingResponse
from app.schemas.prevention import PreventionDecisionResponse
from app.schemas.risk import RiskScoreResponse
from app.schemas.voice_analysis import VoiceAnalysisResponse
from app.services.aasist_inference import build_aasist_inference_service
from app.services.audio_processing import process_audio_input
from app.services.prevention_service import generate_prevention_decision
from app.services.risk_scoring import generate_risk_score
from app.services.alert_service import generate_alert


class AnalysisPipelineError(ValueError):
    """Raised when the end-to-end pipeline cannot safely complete."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    response: AnalysisPipelineResponse


PipelineEventCallback = Callable[[str, dict], None]


def _emit(callback: PipelineEventCallback | None, event_type: str, payload: dict) -> None:
    if callback is not None:
        callback(event_type, payload)


def _owned_audio(db: Session, user: User, session_id: UUID, audio_input_id: UUID) -> AudioInput | None:
    return db.scalar(
        select(AudioInput)
        .join(Call, Call.id == AudioInput.call_id)
        .where(
            AudioInput.id == audio_input_id,
            AudioInput.call_id == session_id,
            Call.organization_id == user.organization_id,
        )
    )


def run_analysis_pipeline(
    db: Session,
    user: User,
    session_id: UUID,
    audio_input_id: UUID,
    event_callback: PipelineEventCallback | None = None,
) -> AnalysisPipelineResponse:
    """Run processing -> detection -> risk -> prevention -> alert for one audio input."""
    audio = _owned_audio(db, user, session_id, audio_input_id)
    if audio is None:
        raise AnalysisPipelineError("Audio input not found")
    if audio.intake_status != "VALIDATED":
        raise AnalysisPipelineError("Audio input is not validated")

    session = db.scalar(
        select(Call).where(Call.id == session_id, Call.organization_id == user.organization_id)
    )
    if session is None:
        raise AnalysisPipelineError("Analysis session not found")

    session.status = "PROCESSING"
    db.commit()
    _emit(event_callback, "analysis.started", {"audio_input_id": str(audio_input_id)})

    settings = get_settings()
    try:
        job = process_audio_input(db, audio, settings)
        if job.status != "COMPLETED" or not job.processed_storage_key:
            raise AnalysisPipelineError("Audio processing did not complete successfully")
        _emit(event_callback, "analysis.processing_completed", {
            "audio_input_id": str(audio_input_id),
            "processing_job_id": str(job.id),
            "duration_ms": job.processed_duration_ms,
        })

        result = build_aasist_inference_service(settings).predict_processed_audio(job.processed_storage_key)
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
        _emit(event_callback, "analysis.detection_completed", {
            "analysis_id": str(analysis.id),
            "decision": result.predicted_label,
            "spoof_probability": result.spoof_probability,
            "authentic_probability": result.authentic_probability,
            "confidence": result.confidence,
            "processing_time_ms": result.processing_time_ms,
        })

        risk = generate_risk_score(
            db, user, session_id, analysis.id,
            ip_address=None,
        )
        _emit(event_callback, "analysis.risk_scored", {
            "analysis_id": str(analysis.id),
            "risk_score_id": str(risk.id),
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
        })

        prevention = generate_prevention_decision(
            db, user, session_id, risk.id,
            ip_address=None,
        )
        _emit(event_callback, "analysis.prevention_decided", {
            "prevention_decision_id": str(prevention.id),
            "response_action": prevention.response_action,
            "risk_level": risk.risk_level,
        })

        alert = generate_alert(db, risk.id, user.organization_id, user.id)
        if alert is not None:
            _emit(event_callback, "alert.created", {
                "alert_id": str(alert.id),
                "severity": alert.severity,
                "status": alert.status,
                "title": alert.title,
                "risk_score_id": str(risk.id),
            })

        session.status = "COMPLETED"
        session.started_at = session.started_at or analysis.analyzed_at
        session.ended_at = analysis.analyzed_at
        session.duration_ms = job.processed_duration_ms
        db.commit()
        db.refresh(session)
        _emit(event_callback, "analysis.completed", {
            "analysis_id": str(analysis.id),
            "risk_score_id": str(risk.id),
            "prevention_decision_id": str(prevention.id),
            "alert_id": str(alert.id) if alert else None,
            "decision": result.predicted_label,
            "risk_level": risk.risk_level,
            "response_action": prevention.response_action,
        })

    except Exception as exc:
        session = db.scalar(select(Call).where(Call.id == session_id, Call.organization_id == user.organization_id))
        if session is not None:
            session.status = "FAILED"
            db.commit()
        _emit(event_callback, "analysis.failed", {"reason": str(exc) or "Voice analysis pipeline failed"})
        if isinstance(exc, AnalysisPipelineError):
            raise
        raise AnalysisPipelineError(str(exc) or "Voice analysis pipeline failed") from exc

    return AnalysisPipelineResponse(
        session_id=session_id,
        audio_input_id=audio_input_id,
        processing=PipelineProcessingResponse.model_validate(job),
        detection=VoiceAnalysisResponse.model_validate(analysis),
        decision=result.predicted_label,
        detector_threshold=result.threshold,
        risk=RiskScoreResponse.model_validate(risk),
        prevention=PreventionDecisionResponse.model_validate(prevention),
        alert=AlertResponse.model_validate(alert) if alert else None,
        completed_at=datetime.now(timezone.utc),
    )
