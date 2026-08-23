from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CHHAVisitOutcome(Base):
    __tablename__ = "chha_visit_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, unique=True, index=True)

    # Optional linkage to future/actual POC entity if you already have one
    poc_reference_id = Column(UUID(as_uuid=True), nullable=True)

    # Overall structured outcome
    tolerance_to_care = Column(String(50), nullable=False, default="WELL_TOLERATED")
    condition_during_visit = Column(String(50), nullable=False, default="STABLE")
    skin_outcome = Column(String(50), nullable=False, default="NOT_ASSESSED")

    pain_or_change_observed = Column(Boolean, nullable=False, default=False)
    rn_notification_required = Column(Boolean, nullable=False, default=False)
    rn_notified = Column(Boolean, nullable=False, default=False)
    rn_notified_at = Column(DateTime(timezone=True), nullable=True)
    rn_notified_name = Column(String(255), nullable=True)

    caregiver_instruction_provided = Column(Boolean, nullable=False, default=False)
    caregiver_understanding_confirmed = Column(Boolean, nullable=False, default=False)

    exception_narrative = Column(Text, nullable=True)

    # Visit logistics / payroll tracking (mirrors the "Visit Details" block
    # captured on RN ICA, MSW ICA, and SC ICA)
    correction = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    type_of_visit = Column(String(32), nullable=True)
    visit_kind = Column(String(32), nullable=True)
    visit_kind_specify = Column(String(255), nullable=True)
    reason_for_visit = Column(String(64), nullable=True)
    visit_date = Column(String(16), nullable=True)
    time_in = Column(String(16), nullable=True)
    time_out = Column(String(16), nullable=True)
    duration = Column(String(32), nullable=True)
    entered_by = Column(String(255), nullable=True)
    staff_assigned = Column(String(255), nullable=True)
    care_level = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    visit = relationship("Visit", backref="chha_outcome")
    task_results = relationship(
        "CHHAVisitTaskResult",
        back_populates="outcome",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("visit_id", name="uq_chha_visit_outcomes_visit_id"),
    )