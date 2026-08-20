# models/idg_meeting.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Index, text
from sqlalchemy.dialects.postgresql import UUID, ENUM

from app.db.base import Base


IDGStatusEnum = ENUM(
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
    name="idg_status_enum",
    create_type=False,
)


class IDGMeeting(Base):
    """
    Authoritative IDG meeting scheduling entity.

    Domain model entity #2 of 3 ("IDG" is overloaded — do not conflate):
        1. PatientIDGReview  -> idg_review.py / IDGReview (idg_reviews table)
        2. IDGMeeting        -> this class (recurring ~14-day meeting: date/
                                 time, attendees, agenda, minutes, status)
        3. IDGMeetingPatientReview -> idg_meeting_patient_review.py
                                 (in-meeting, per-patient review workspace)

    This table represents the scheduled IDG meeting instance.
    Patient-level IDG review content belongs in idg_reviews.
    Intelligence items belong in idg_intelligence_items.
    Attendance belongs in idg_attendees.
    Signatures belong in idg_signatures / attendee signature fields.
    """

    __tablename__ = "idg_meetings"

    __table_args__ = (
        Index("ix_idg_meetings_tenant_id", "tenant_id"),
        Index("ix_idg_meetings_patient_id", "patient_id"),
        Index("ix_idg_meetings_benefit_period_id", "benefit_period_id"),
        Index("ix_idg_meetings_meeting_date", "meeting_date"),
        Index("ix_idg_meetings_status", "status"),
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
        nullable=True,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    meeting_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status = Column(
        IDGStatusEnum,
        nullable=False,
        server_default=text("'SCHEDULED'"),
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

    rescheduled_reason = Column(
        String,
        nullable=True,
    )

    rescheduled_from = Column(
        DateTime(timezone=True),
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