"""SNS Body Systems — persistence models for the Respiratory proof-of-pattern
milestone.

Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
section 4.2 (primary entities) and section 12 (persistence/concurrency).
Transcribes `BodySystemsAssessment` and `SystemAssessment` from that section
into SQLAlchemy models. Per-system clinical field values are stored in
`SystemAssessment.data` (JSONB), following the same "whole-form JSONB blob"
convention already used by `RnicaAssessment.form_data` — this is a reuse of
an existing persistence convention, not a new one invented for this
milestone. A relational `ClinicalFinding`/`Evidence` schema (section 4.2)
is intentionally deferred until a second system's proof-of-pattern
justifies the added complexity; see the module docstring in
`respiratoryFieldInventory.ts` (frontend) for the matching "don't invent
ahead of an approved field inventory" rationale.

`ReviewException` is relational (not JSONB) because open exceptions must be
queried/filtered by type, status, and blocking level independently of which
system or assessment they belong to (worklists, review-progress counts).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

# Canonical body system codes -- must match
# sns-emr-frontend/src/domain/body-systems/types.ts BODY_SYSTEMS exactly.
# Transcribed, not re-derived, so the two can never silently drift.
BODY_SYSTEM_CODES = (
    "neurological",
    "respiratory",
    "cardiovascular",
    "nutrition",
    "gastrointestinal",
    "genitourinary",
    "musculoskeletal",
    "integumentary",
    "infection_immunological",
    "endocrine",
)

VISIT_MODES = ("admission_comprehensive", "routine_rn", "recertification")
ASSESSMENT_STATUSES = ("draft", "ready_for_review", "recorded", "signed")
ASSESSMENT_SITUATIONS = ("no_current_concern", "stable_existing", "new_or_worsening", "unable_to_assess")
REVIEW_STATES = ("not_reviewed", "in_progress", "reviewed", "reviewed_with_exception")
EXCEPTION_TYPES = (
    "unreviewed_system",
    "required_field_missing",
    "partial_scope",
    "unable_to_assess",
    "source_missing",
    "date_time_missing",
    "conflicting_evidence",
    "nurse_judgment_required",
    "low_confidence_ai",
    "follow_up_missing",
)
EXCEPTION_BLOCKING_LEVELS = ("informational", "draft_allowed", "record_blocking", "signature_blocking")
EXCEPTION_STATUSES = ("open", "resolved", "waived")


class BodySystemsAssessment(Base):
    __tablename__ = "body_systems_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)
    visit_mode = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="draft", server_default=text("'draft'"))
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    recorded_at = Column(DateTime(timezone=True), nullable=True)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Optimistic-concurrency version counter (section 12). Incremented by
    # application logic on every write; a stale-version write must be
    # rejected rather than silently overwritten.
    version = Column(Integer, nullable=False, default=1, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="body_systems_assessments")
    visit = relationship("Visit", backref="body_systems_assessments")
    system_assessments = relationship(
        "SystemAssessment", back_populates="body_systems_assessment", cascade="all, delete-orphan"
    )
    review_exceptions = relationship(
        "ReviewException", back_populates="body_systems_assessment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(f"visit_mode IN {VISIT_MODES!r}", name="ck_body_systems_assessments_visit_mode"),
        CheckConstraint(f"status IN {ASSESSMENT_STATUSES!r}", name="ck_body_systems_assessments_status"),
    )


class SystemAssessment(Base):
    __tablename__ = "system_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    body_systems_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("body_systems_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    system = Column(String(32), nullable=False)
    situation = Column(String(32), nullable=True)
    review_state = Column(String(32), nullable=False, default="not_reviewed", server_default=text("'not_reviewed'"))
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Limitation sub-fields (AssessmentLimitation, section 4.2) -- scope is
    # stored as a JSONB string array since Postgres has no native text[]
    # requirement here and every other clinical-data field on this table
    # already uses JSONB for the same reason (schema flexibility without a
    # migration per new verified field).
    limitation_scope = Column(JSONB, nullable=True)
    limitation_reason = Column(Text, nullable=True)
    limitation_assessed_portion = Column(Text, nullable=True)
    limitation_follow_up_required = Column(Text, nullable=True)
    # Verified clinical field values for this system (e.g. the Respiratory
    # field inventory in respiratoryFieldInventory.ts), keyed by fieldId.
    # See module docstring: reuses RnicaAssessment.form_data's JSONB-blob
    # convention rather than a per-field relational schema.
    data = Column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    summary = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    body_systems_assessment = relationship("BodySystemsAssessment", back_populates="system_assessments")

    __table_args__ = (
        UniqueConstraint("body_systems_assessment_id", "system", name="uq_system_assessments_assessment_system"),
        CheckConstraint(f"system IN {BODY_SYSTEM_CODES!r}", name="ck_system_assessments_system"),
        CheckConstraint(
            f"situation IS NULL OR situation IN {ASSESSMENT_SITUATIONS!r}", name="ck_system_assessments_situation"
        ),
        CheckConstraint(f"review_state IN {REVIEW_STATES!r}", name="ck_system_assessments_review_state"),
    )


class ReviewException(Base):
    __tablename__ = "review_exceptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    body_systems_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("body_systems_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    system = Column(String(32), nullable=False)
    type = Column(String(32), nullable=False)
    field_path = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    blocking_level = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="open", server_default=text("'open'"))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    body_systems_assessment = relationship("BodySystemsAssessment", back_populates="review_exceptions")

    __table_args__ = (
        CheckConstraint(f"system IN {BODY_SYSTEM_CODES!r}", name="ck_review_exceptions_system"),
        CheckConstraint(f"type IN {EXCEPTION_TYPES!r}", name="ck_review_exceptions_type"),
        CheckConstraint(
            f"blocking_level IN {EXCEPTION_BLOCKING_LEVELS!r}", name="ck_review_exceptions_blocking_level"
        ),
        CheckConstraint(f"status IN {EXCEPTION_STATUSES!r}", name="ck_review_exceptions_status"),
        CheckConstraint(
            "status = 'open' OR resolved_at IS NOT NULL", name="ck_review_exceptions_resolved_has_timestamp"
        ),
    )
