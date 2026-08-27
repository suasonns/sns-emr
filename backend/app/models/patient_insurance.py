from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class PatientInsurance(TenantScopedMixin, BaseModel):
    __tablename__ = "patient_insurances"

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

    payer_type = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # Examples:
    # MEDICARE, MEDICAID, HMO, PPO, VA, DENTAL, VISION, PHARMACY, OTHER

    payer_name = Column(
        String(255),
        nullable=False,
    )

    subscriber_id = Column(
        String(128),
        nullable=False,
        index=True,
    )
    # Examples:
    # Medicare = MBI
    # Medi-Cal = CIN / Medicaid member ID
    # PPO/HMO = member ID
    # VA = VA-specific member/subscriber ID

    subscriber_id_type = Column(
        String(32),
        nullable=True,
    )
    # Examples:
    # MBI, CIN, MEMBER_ID, VA_ID, RX_BINPCN, OTHER

    group_number = Column(
        String(128),
        nullable=True,
    )

    coverage_scope = Column(
        String(32),
        nullable=False,
        server_default=text("'MEDICAL_GENERAL'"),
        index=True,
    )
    # Recommended values:
    # HOSPICE, MEDICAL_GENERAL, PHARMACY, DENTAL, VISION, VA, OTHER

    priority_order = Column(
        Integer,
        nullable=False,
    )
    # 1 = primary, 2 = secondary, 3 = tertiary, etc.

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        index=True,
    )

    effective_date = Column(
        Date,
        nullable=True,
    )

    end_date = Column(
        Date,
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    eligibility_status = Column(
        String(32),
        nullable=True,
        server_default=text("'UNKNOWN'"),
        index=True,
        doc="ACTIVE / INACTIVE / UNKNOWN / ERROR -- set from the most recent PayerEligibilityCheck",
    )

    next_verification_due = Column(
        Date,
        nullable=True,
        doc="When the next eligibility check should be performed (biller-set or policy-driven cadence).",
    )

    patient = relationship(
        "Patient",
        back_populates="insurances",
    )

    eligibility_checks = relationship(
        "PayerEligibilityCheck",
        back_populates="patient_insurance",
        cascade="all, delete-orphan",
        order_by="PayerEligibilityCheck.checked_at.desc()",
    )

    __table_args__ = (
        CheckConstraint("priority_order >= 1", name="ck_patient_insurance_priority_order_gte_1"),
        Index(
            "uq_patient_insurance_patient_scope_priority_active",
            "tenant_id",
            "patient_id",
            "coverage_scope",
            "priority_order",
            unique=True,
        ),
    )