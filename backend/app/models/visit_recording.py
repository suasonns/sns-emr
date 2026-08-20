from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class VisitRecording(Base):
    """
    Audio recording of a hospice visit encounter, captured so the
    "AI voice to documentation" flow can later transcribe it (Azure Speech)
    and so staff can review what was actually said/asked during the visit
    for QA/audit purposes.

    This is intentionally decoupled from a specific speech-to-text vendor:
    `transcript_text`/`transcript_status`/`transcript_provider` stay nullable
    until a real STT integration is wired up. The recording + review pipeline
    (capture, storage, playback, consent) works standalone before that.
    """

    __tablename__ = "visit_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="CASCADE"), nullable=True, index=True)

    # Optional link to the structured assessment this recording supports
    # (e.g. an RNICA or RN recert draft), so the chart can show "recording
    # for this assessment" without requiring visit_id to already exist yet.
    assessment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assessment_type = Column(String(32), nullable=True)  # e.g. "RNICA", "RN_RECERT", "MSW_ICA"

    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Explicit consent attestation — required before recording can start.
    # This is a staff attestation captured at record time, not itself PHI.
    consent_confirmed = Column(Boolean, nullable=False, default=False)
    consent_confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Storage location on disk (relative to the configured storage root —
    # never an absolute/user-controlled path; see recording_storage.py).
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=True)
    mime_type = Column(String(64), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)

    # Transcription — filled in later by whichever STT vendor is wired up
    # (Azure Speech, per current plan). Left blank/pending until then.
    transcript_status = Column(String(24), nullable=False, default="not_transcribed")  # not_transcribed | pending | complete | failed
    transcript_provider = Column(String(32), nullable=True)
    transcript_text = Column(Text, nullable=True)
    transcribed_at = Column(DateTime(timezone=True), nullable=True)

    # Staff review of the recording/transcript (separate from transcription
    # itself) — lets a supervisor/QA mark that they listened/reviewed.
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Retention: soft-delete only — recordings are never hard-deleted by the
    # app itself so an accidental delete can't destroy an audit artifact.
    # A retention/purge job (future work) can hard-delete rows past policy.
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
