# models/idg_review.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import Base


class IDGReview(Base):
    """
    Patient-level IDG review record — Domain model entity #1 of 3
    ("IDG" is overloaded — do not conflate these):
        1. PatientIDGReview -> this class (patient-chart clinical
           documentation: Admission/Initial/Routine/Recert/Significant-
           Change IDG review notes — nursing, physician, MSW, chaplain
           discussion, POC review). Belongs to ONE patient. NOT a meeting.
        2. IDGMeeting -> idg_meeting.py (the recurring ~14-day scheduled
           team meeting itself: date/time, attendees, agenda, minutes).
        3. IDGMeetingPatientReview -> idg_meeting_patient_review.py (the
           temporary in-meeting review workspace: POC/med-list/med-rec/
           orders review + physician Reviewed/Deferred + batch-sign
           eligibility for ONE patient within ONE IDGMeeting).

    This table is the patient review container for IDG.
    It should connect the patient, benefit period, IDG meeting,
    summary, POC action decision, plan-of-care version, and
    finalization state.

    This table should not duplicate POC problems, goals,
    interventions, signatures, MD approvals, or intelligence items.
    Those have separate existing SSOT tables.
    """

    __tablename__ = "idg_reviews"

    __table_args__ = (
        Index("ix_idg_reviews_tenant_id", "tenant_id"),
        Index("ix_idg_reviews_patient_id", "patient_id"),
        Index("ix_idg_reviews_idg_meeting_id", "idg_meeting_id"),
        Index("ix_idg_reviews_benefit_period_id", "benefit_period_id"),
        Index("ix_idg_reviews_review_date", "review_date"),
        Index("ix_idg_reviews_plan_of_care_version_id", "plan_of_care_version_id"),
        Index("ix_idg_reviews_is_finalized", "is_finalized"),
        Index("ix_idg_reviews_tenant_follow_up_status", "tenant_id", "follow_up_status"),
        CheckConstraint(
            "follow_up_status != 'COMPLETED' OR follow_up_completed_at IS NOT NULL",
            name="ck_idg_reviews_follow_up_completion_requires_timestamp",
        ),
        CheckConstraint(
            "follow_up_status != 'COMPLETED' OR closure_summary IS NOT NULL",
            name="ck_idg_reviews_completion_requires_closure_summary",
        ),
        CheckConstraint(
            "reopened_at IS NULL OR reopen_reason IS NOT NULL",
            name="ck_idg_reviews_reopen_requires_reason",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    review_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    poc_action = Column(
        Text,
        nullable=True,
    )

    plan_of_care_version_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    is_finalized = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        index=True,
    )

    finalized_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    finalized_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # ---------------------------------------------------------
    # IDG follow-up extension (added alongside the CMS/California
    # compliance work, issue #143). Reuses this existing patient-IDG
    # review record as the follow-up authority rather than creating a
    # second, parallel idg_follow_ups table.
    # ---------------------------------------------------------
    follow_up_required = Column(Boolean, nullable=False, server_default=text("false"))
    follow_up_status = Column(
        String(20),
        nullable=True,
        doc="ASSIGNED / IN_PROGRESS / COMPLETED",
    )
    follow_up_assigned_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_assigned_to_user_id = Column(UUID(as_uuid=True), nullable=True)
    follow_up_completed_at = Column(DateTime(timezone=True), nullable=True)
    source_patient_response_event_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_clinical_outcome_record_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ---------------------------------------------------------
    # Follow-up detail fields (added for the Clinical Outcome + IDG
    # implementation phase). desired_patient_outcome/follow_up_action/
    # follow_up_due_date are required before a follow-up can be
    # considered actionable; closure_summary is required before
    # follow_up_status can become COMPLETED; continuing_plan is
    # required when the linked outcome/remaining need is persistent or
    # worsening. Reassignment history is preserved via RecordVersion
    # snapshots (see app.models.record_version), not a duplicate column.
    # ---------------------------------------------------------
    desired_patient_outcome = Column(Text, nullable=True)
    follow_up_action = Column(Text, nullable=True)
    follow_up_due_date = Column(DateTime(timezone=True), nullable=True)
    closure_summary = Column(Text, nullable=True)
    continuing_plan = Column(Text, nullable=True)
    reopened_at = Column(DateTime(timezone=True), nullable=True)
    reopened_by = Column(UUID(as_uuid=True), nullable=True)
    reopen_reason = Column(Text, nullable=True)


class IDGReviewAuditEvent(Base):
    """Domain audit trail for IDG patient-outcome follow-up lifecycle events."""

    __tablename__ = "idg_review_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    idg_review_id = Column(UUID(as_uuid=True), ForeignKey("idg_reviews.id", ondelete="CASCADE"), nullable=False, index=True)
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
            "ix_idg_review_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        CheckConstraint(
            "event_type IN ("
            "'IDG_FOLLOW_UP_CREATED','IDG_RECOMMENDATION_RECORDED','FOLLOW_UP_ASSIGNED',"
            "'FOLLOW_UP_REASSIGNED','FOLLOW_UP_PROGRESS_RECORDED','PATIENT_RESPONSE_LINKED',"
            "'FOLLOW_UP_COMPLETED','FOLLOW_UP_REOPENED'"
            ")",
            name="ck_idg_review_audit_events_type",
        ),
    )