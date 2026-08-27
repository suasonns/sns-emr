# backend/app/models/benefit_period.py

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


BenefitTypeEnum = ENUM(
    "INITIAL",
    "RECERT",
    name="benefit_type_enum",
    create_type=False,
)


class BenefitPeriod(BaseModel):
    __tablename__ = "benefit_periods"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    benefit_type = Column(
        BenefitTypeEnum,
        nullable=False,
        index=True,
    )

    period_number = Column(
        Integer,
        nullable=False,
        index=True,
    )

    election_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    start_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    end_date = Column(
        Date,
        nullable=True,
        index=True,
    )

    is_current = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # Real-world NOE filing date for this period's election (only meaningful
    # for benefit_type=INITIAL / period_number=1). Used to compute CMS's
    # late-NOE non-covered-day penalty -- see
    # app/billing/services/noe_penalty_service.py.
    noe_submitted_date = Column(Date, nullable=True)

    # Free-text note when a CMS-recognized exception waives the late-NOE
    # penalty (e.g. "MAC system outage per CMS transmittal X"). Presence of
    # a non-null value suppresses the penalty even if filed late.
    noe_exception_reason = Column(String, nullable=True)

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    patient = relationship(
        "Patient",
        back_populates="benefit_periods",
        foreign_keys=[patient_id],
    )

    tasks = relationship(
        "Task",
        back_populates="benefit_period",
    )