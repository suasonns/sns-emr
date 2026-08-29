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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class NoeEdiSubmission(Base):
    """
    Real, persisted electronic NOE (Notice of Election, TOB 81A) / NOTR
    (Notice of Termination or Revocation, TOB 81B) 837I notice generated
    for a patient (see noe_edi_builder.build_notice_837i_text). Tracks the
    generated text and its real transmission status (never assumed
    ACCEPTED just because it was generated) -- replaces the paper-PDF-only
    NOE workflow with a real electronic submission trail.
    """

    __tablename__ = "noe_edi_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="SET NULL"),
        nullable=True,
        doc="Set for NOE submissions (the INITIAL benefit period being elected); null for NOTR.",
    )

    submission_type = Column(
        String(8),
        nullable=False,
        doc="NOE or NOTR",
    )

    tob_code = Column(String(3), nullable=False, doc="81A/82A (NOE) or 81B/82B (NOTR)")

    control_number = Column(String(64), nullable=False)

    effective_date = Column(
        Date,
        nullable=False,
        doc="Election effective date (NOE) or discharge/revocation effective date (NOTR).",
    )

    edi_text = Column(Text, nullable=False)

    status = Column(
        String(32),
        nullable=False,
        default="GENERATED",
        server_default=text("'GENERATED'"),
        index=True,
        doc="GENERATED / SUBMITTED / ACCEPTED / REJECTED",
    )

    submitted_at = Column(DateTime(timezone=True), nullable=True)

    ack_status = Column(String(32), nullable=True, doc="Raw 999/277CA-style ack result, when recorded.")

    ack_raw_content = Column(Text, nullable=True)

    created_by = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tenant = relationship("Tenant")
    patient = relationship("Patient")
    benefit_period = relationship("BenefitPeriod")

    __table_args__ = (
        Index("ix_noe_edi_submissions_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_noe_edi_submissions_patient_type", "patient_id", "submission_type"),
    )
