# backend/app/models/benefit_period.py

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, text
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