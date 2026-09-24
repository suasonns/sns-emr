import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, String, Text, text
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

    # ---------------------------------------------------------
    # FY2027 HOPE submission-tracking extension (added alongside the
    # CMS FY2027 compliance work). RnicaAssessment remains the single
    # authoritative HOPE workflow/submission record -- these fields
    # extend it rather than introducing a second `hope_records`/
    # `hope_submission_obligation` table. hope_workflow_status (above)
    # remains the single submission-status owner; do not add a second
    # status column here.
    # ---------------------------------------------------------
    hope_event_type = Column(
        String(20),
        nullable=True,
        doc="ADMISSION / HUV1 / HUV2 / DISCHARGE -- kept distinguishable, never collapsed.",
    )
    hope_event_date = Column(Date, nullable=True)
    hope_submission_due_at = Column(DateTime(timezone=True), nullable=True)
    hope_overdue_at = Column(DateTime(timezone=True), nullable=True)
    hope_receipt_reference = Column(String(128), nullable=True)
    hope_validation_status = Column(String(32), nullable=True)
    hope_accepted_at = Column(DateTime(timezone=True), nullable=True)
    hope_rejected_at = Column(DateTime(timezone=True), nullable=True)
    hope_correction_required = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    hope_corrected_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
        nullable=True,
        doc="Points to the prior (superseded) assessment this one corrects, preserving submission history.",
    )
    hope_last_submission_attempt_at = Column(DateTime(timezone=True), nullable=True)

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

    __table_args__ = (
        Index("ix_rnica_assessments_tenant_status_due", "tenant_id", "hope_workflow_status", "hope_submission_due_at"),
        Index("ix_rnica_assessments_tenant_admission_event", "tenant_id", "admission_id", "hope_event_type"),
        Index("ix_rnica_assessments_tenant_overdue", "tenant_id", "hope_overdue_at"),
        CheckConstraint(
            "hope_submission_due_at IS NULL OR hope_event_date IS NOT NULL",
            name="ck_rnica_assessments_due_requires_event_date",
        ),
        CheckConstraint(
            "hope_accepted_at IS NULL OR hope_rejected_at IS NULL",
            name="ck_rnica_assessments_accept_reject_mutually_exclusive",
        ),
        CheckConstraint(
            "hope_corrected_assessment_id IS NULL OR hope_corrected_assessment_id != id",
            name="ck_rnica_assessments_no_self_correction",
        ),
        CheckConstraint(
            "hope_workflow_status != 'CORRECTION_REQUIRED' OR hope_correction_required = true",
            name="ck_rnica_assessments_correction_required_flag",
        ),
    )
