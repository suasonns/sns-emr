from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base

IDGStatusEnum = Enum(
    name="idg_status_enum",
    native_enum=True,
    create_type=False,
)


class IDGMeeting(Base):
    """
    Enterprise-grade IDG Meeting.

    Regulatory basis:
    - CMS CoPs §418.56
    """

    __tablename__ = "idg_meetings"

    id = Column(UUID(as_uuid=True), primary_key=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=True,
        index=True,
    )

    status = Column(IDGStatusEnum, nullable=False)

    meeting_date = Column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )