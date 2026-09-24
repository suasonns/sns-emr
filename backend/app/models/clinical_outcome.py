from __future__ import annotations

"""
Clinical outcome tracking for the California two-hour response requirement
(issue #143). Records whether the patient was appropriately cared for
(primary criterion), independent of which discipline performed the work.
See docs decision: discipline identifies who performed work, but does not
determine ownership of patient outcomes -- IDG remains responsible for
patient outcomes (see idg_follow_up_id below, which links to the existing
`idg_reviews` table rather than a new parallel IDG structure).
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ClinicalOutcomeRecord(Base):
    __tablename__ = "clinical_outcome_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    benefit_period_id = Column(
        UUID(as_uuid=True), ForeignKey("benefit_periods.id", ondelete="SET NULL"), nullable=True, index=True
    )

    patient_response_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_response_events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    source_visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)

    # Controlled workflow-status lifecycle (distinct from
    # patient_response_status, which is the clinical response quality).
    OUTCOME_STATUSES = (
        "IDENTIFIED",
        "ASSESSED",
        "INTERVENTION_IN_PROGRESS",
        "AWAITING_RESPONSE",
        "IDG_FOLLOW_UP_REQUIRED",
        "IDG_FOLLOW_UP_ASSIGNED",
        "IDG_FOLLOW_UP_COMPLETED",
        "IMPROVED",
        "RESOLVED",
        "PERSISTENT",
        "WORSENED",
        "TRANSFERRED_FOR_HIGHER_LEVEL_OF_CARE",
        "CLOSED_WITH_ONGOING_PLAN",
    )
    outcome_status = Column(String(40), nullable=False, server_default="IDENTIFIED")

    # Primary evaluation criterion.
    patient_appropriately_cared_for = Column(Boolean, nullable=True)
    patient_response_status = Column(
        String(30),
        nullable=True,
        doc="IMPROVED / STABLE / PERSISTENT / WORSENED",
    )
    remaining_need_identified = Column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="Required true when patient_response_status is PERSISTENT or WORSENED.",
    )

    # Secondary evaluation criteria.
    idg_communicated = Column(Boolean, nullable=False, server_default="false")
    idg_communicated_at = Column(DateTime(timezone=True), nullable=True)
    intervention_timely = Column(Boolean, nullable=True)
    documentation_complete = Column(Boolean, nullable=False, server_default="false")

    # IDG remains responsible for patient outcomes; multiple disciplines
    # may contribute evidence, but no single discipline is stored as the
    # "owner" of the outcome. Links to the existing idg_reviews table.
    idg_review_id = Column(UUID(as_uuid=True), ForeignKey("idg_reviews.id", ondelete="SET NULL"), nullable=True, index=True)

    response_recorded_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reopened_at = Column(DateTime(timezone=True), nullable=True)
    reopened_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reopen_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_account_discipline = Column(
        String(50),
        nullable=True,
        doc="Snapshot of the recording staff member's discipline -- identifies who performed the work, not who owns the outcome.",
    )
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    patient = relationship("Patient")

    __table_args__ = (
        Index("ix_clinical_outcome_records_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_clinical_outcome_records_outcome_status", "outcome_status"),
        CheckConstraint(
            "closed_at IS NULL OR response_recorded_at IS NOT NULL",
            name="ck_clinical_outcome_records_closure_requires_response",
        ),
        CheckConstraint(
            "outcome_status NOT IN ('PERSISTENT','WORSENED','CLOSED_WITH_ONGOING_PLAN') OR remaining_need_identified = true",
            name="ck_clinical_outcome_records_persistent_requires_remaining_need",
        ),
        CheckConstraint(
            "outcome_status IN ("
            + ",".join(f"'{s}'" for s in OUTCOME_STATUSES)
            + ")",
            name="ck_clinical_outcome_records_outcome_status",
        ),
        CheckConstraint(
            "reopened_at IS NULL OR reopen_reason IS NOT NULL",
            name="ck_clinical_outcome_records_reopen_requires_reason",
        ),
    )


class ClinicalOutcomeAuditEvent(Base):
    """Domain audit trail for clinical-outcome lifecycle events."""

    __tablename__ = "clinical_outcome_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    clinical_outcome_record_id = Column(
        UUID(as_uuid=True), ForeignKey("clinical_outcome_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_account_discipline = Column(String(50), nullable=True)
    prior_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index(
            "ix_clinical_outcome_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        CheckConstraint(
            "event_type IN ("
            "'OUTCOME_CREATED','INTERVENTION_RECORDED','PATIENT_RESPONSE_RECORDED',"
            "'OUTCOME_STATUS_CHANGED','REMAINING_NEED_RECORDED','IDG_FOLLOW_UP_REQUIRED',"
            "'OUTCOME_CORRECTED','OUTCOME_FINALIZED','OUTCOME_REOPENED'"
            ")",
            name="ck_clinical_outcome_audit_events_type",
        ),
    )
