import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RnicaAssessment(Base):
    __tablename__ = "rnica_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)

    # Scopes this assessment to the admission episode it belongs to. The RN
    # Initial Comprehensive Assessment (assessment_type == "RNICA") is only
    # ever performed once per admission -- this column is what lets the
    # backend enforce that (see _get_current_admission_for_patient /
    # save_rnica_assessment in app/api/visits.py) while still allowing a
    # brand-new one after a discharge + re-admission (new Admission row).
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Defense-in-depth: lets any future query filter/scope by tenant directly
    # instead of relying solely on patient_id being globally unique.
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)

    assessment_type = Column(String(32), nullable=False, default="RNICA")
    status = Column(String(32), nullable=False, default="DRAFT")
    locked = Column(Boolean, nullable=False, default=False)
    hope_workflow_status = Column(String(32), nullable=False, default="OPEN")
    hope_closed_at = Column(DateTime(timezone=True), nullable=True)
    hope_closed_by = Column(UUID(as_uuid=True), nullable=True)
    hope_ready_at = Column(DateTime(timezone=True), nullable=True)
    hope_ready_by = Column(UUID(as_uuid=True), nullable=True)
    hope_exported_to_batch_at = Column(DateTime(timezone=True), nullable=True)
    hope_exported_to_batch_by = Column(UUID(as_uuid=True), nullable=True)
    hope_export_batch_id = Column(String(128), nullable=True)
    hope_submission_number = Column(String(128), nullable=True)
    hope_already_submitted = Column(Boolean, nullable=False, default=False)
    hope_submitted_at = Column(DateTime(timezone=True), nullable=True)
    hope_submitted_by = Column(UUID(as_uuid=True), nullable=True)
    hope_inactivated = Column(Boolean, nullable=False, default=False)
    hope_inactivated_at = Column(DateTime(timezone=True), nullable=True)
    hope_inactivated_by = Column(UUID(as_uuid=True), nullable=True)
    hope_unlocked_at = Column(DateTime(timezone=True), nullable=True)
    hope_unlocked_by = Column(UUID(as_uuid=True), nullable=True)
    hope_unlock_reason = Column(Text, nullable=True)

    form_data = Column(JSONB, nullable=False, default=dict)
    notes = Column(Text, nullable=True)

    # Durable record of every structured field ever populated by the
    # AI-extraction Apply/Apply-All layer (see applyStructuredFindings.js).
    # Each entry: {section, path, value, concept_code, source_type,
    # source_excerpt, recorded_at, confidence, signal_id}. Persisted here
    # (not just held in frontend React state) so an RN can see exactly why
    # a field was populated after a page refresh, logout, or reconnect --
    # not only during the same browser session the Apply happened in.
    field_provenance = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))

    # Client-generated idempotency key for the *create* path only (see
    # save_rnica_assessment in app/api/visits.py). Offline-captured
    # assessments are queued in the browser and may be retried after a
    # dropped connection where the client cannot tell whether the original
    # request ever reached the server. Passing the same clientRequestId on
    # retry lets the server recognize "this create already happened" and
    # return the existing row instead of creating a duplicate DRAFT.
    client_request_id = Column(String(64), nullable=True, index=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="rnica_assessments")
    visit = relationship("Visit", backref="rnica_assessments")
