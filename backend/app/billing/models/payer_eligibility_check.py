from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class PayerEligibilityCheck(Base):
    """
    Real, persisted payer eligibility verification record for a patient's
    insurance coverage (270/271 style check, or a manually-logged
    phone/portal verification when no clearinghouse integration is
    configured yet). Extends app.models.patient_insurance.PatientInsurance
    with an audit trail of every verification attempt and its result --
    replacing any in-memory/fabricated eligibility status.

    This is intentionally NOT tied to a live 270/271 clearinghouse feed --
    that integration doesn't exist in this system yet. `check_method`
    distinguishes an automated batch check from a manually-recorded one
    so the UI never implies automation that isn't real.
    """

    __tablename__ = "payer_eligibility_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_insurance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_insurances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    checked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    check_method = Column(
        String(32),
        nullable=False,
        default="MANUAL",
        doc="MANUAL (biller-recorded phone/portal check) / BATCH_270_271 (future automated clearinghouse check)",
    )

    result_status = Column(
        String(32),
        nullable=False,
        default="UNKNOWN",
        index=True,
        doc="ACTIVE / INACTIVE / UNKNOWN / ERROR",
    )

    payer_response_code = Column(
        String(32),
        nullable=True,
        doc="Raw payer/clearinghouse response code, when available (271 EB segment or portal reference).",
    )

    plan_begin_date = Column(Date, nullable=True)

    plan_end_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    checked_by = Column(String(255), nullable=True)

    raw_response = Column(Text, nullable=True)

    tenant = relationship("Tenant")
    patient_insurance = relationship(
        "PatientInsurance", back_populates="eligibility_checks"
    )

    __table_args__ = (
        Index(
            "ix_payer_eligibility_check_insurance_checked_at",
            "patient_insurance_id",
            "checked_at",
        ),
        Index("ix_payer_eligibility_check_tenant_status", "tenant_id", "result_status"),
    )
