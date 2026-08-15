from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Admission(Base):
    __tablename__ = "admissions"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

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

    # ---------------------------------------------------------
    # Admission Core
    # ---------------------------------------------------------

    admission_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status = Column(
        Text,
        nullable=False,
        server_default=text("'DRAFT'"),
        index=True,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=text("now()"),
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Clinical / Workflow
    # ---------------------------------------------------------

    attending_physician_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),   # ✅ optional but recommended
        nullable=True,
    )

    referral_source = Column(Text, nullable=True)
    reason_for_admission = Column(Text, nullable=True)

    admission_authorized_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    admission_authorized_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    soc_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    soc_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    effective_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    election_signed_at = Column(DateTime(timezone=True), nullable=True)
    certification_completed_at = Column(DateTime(timezone=True), nullable=True)
    physician_order_signed_at = Column(DateTime(timezone=True), nullable=True)
    initial_assessment_completed_at = Column(DateTime(timezone=True), nullable=True)

    discharged_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    discharge_reason = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    patient = relationship(
        "Patient",
        back_populates="admissions",
    )

    status_history = relationship(
        "AdmissionStatusHistory",
        back_populates="admission",
        cascade="all, delete-orphan",
    )