# models/idg_review.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID

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