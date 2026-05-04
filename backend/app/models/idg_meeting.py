import uuid
from sqlalchemy import Column, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func

from app.models.base import BaseModel


class IDGMeeting(BaseModel):
    __tablename__ = "idg_meetings"

    # ✅ Match DB schema
    idg_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # ✅ MUST be non-null to align with tasks & survey requirements
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=False, index=True)

    meeting_date = Column(Date, nullable=False, index=True)

    # ✅ Enforced lifecycle (ENUM already exists in DB)
    status = Column(
        ENUM("SCHEDULED", "IN_PROGRESS", "COMPLETED", name="idg_status_enum", create_type=False),
        nullable=False,
        default="SCHEDULED",
    )

    # ✅ audit / lifecycle timestamps
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    finalized_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)  # keep if present in DB

    # ✅ Required disciplines (policy-level flags)
    rn_required = Column(Boolean, nullable=False, default=True)
    physician_required = Column(Boolean, nullable=False, default=True)
    social_worker_required = Column(Boolean, nullable=False, default=True)
    chaplain_required = Column(Boolean, nullable=False, default=True)

    # ✅ Informational presence flags (NOT enforcement)
    rn_present = Column(Boolean, nullable=False, default=False)
    physician_present = Column(Boolean, nullable=False, default=False)
    social_worker_present = Column(Boolean, nullable=False, default=False)
    chaplain_present = Column(Boolean, nullable=False, default=False)

    summary = Column(Text, nullable=True)
