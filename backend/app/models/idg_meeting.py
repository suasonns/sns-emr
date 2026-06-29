from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


IDGStatusEnum = Enum(
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
    name="idg_status_enum",
)


class IDGMeeting(Base):
    """
    IDG Meeting (Authoritative scheduling entity)

    One record = one patient’s IDG session

    This drives:
    - IDG tasks
    - IDG reviews
    - compliance audit
    """

    __tablename__ = "idg_meetings"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "patient_id",
            "meeting_date",
            name="uq_idg_meeting_patient_date",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
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
        default="SCHEDULED",
    )

    finalized_by = Column(UUID(as_uuid=True))
    finalized_at = Column(DateTime(timezone=True))

    # audit fields
    created_by = Column(UUID(as_uuid=True))
    rescheduled_reason = Column(String)
    rescheduled_from = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )