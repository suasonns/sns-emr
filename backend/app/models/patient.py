from __future__ import annotations

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class Patient(TenantScopedMixin, BaseModel):
    __tablename__ = "patients"

    # ---------------------------------------------------------
    # TENANT ISOLATION
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # CORE IDENTITY
    # ---------------------------------------------------------
    mrn = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    primary_diagnosis = Column(String, nullable=False)

    # ---------------------------------------------------------
    # SYSTEM LIFECYCLE
    # ---------------------------------------------------------
    status = Column(
        String,
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    # ---------------------------------------------------------
    # HOSPICE LIFECYCLE (LEGACY)
    # ---------------------------------------------------------
    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String, nullable=True)

    # ---------------------------------------------------------
    # SOC / ADMISSION (COMPLIANCE CRITICAL)
    # ---------------------------------------------------------
    records_release_signed_at = Column(DateTime(timezone=True), nullable=True)
    election_signed_at = Column(DateTime(timezone=True), nullable=True)

    soc_date = Column(DateTime(timezone=True), nullable=True)

    admission_status = Column(
        String(32),
        nullable=False,
        server_default=text("'PRE_REFERRAL'"),
    )

    admission_authorized_at = Column(DateTime(timezone=True), nullable=True)

    admission_authorized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    not_admitted_at = Column(DateTime(timezone=True), nullable=True)
    not_admitted_reason = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # CLINICAL ACUITY
    # ---------------------------------------------------------
    acuity_state = Column(
        String,
        nullable=False,
        server_default=text("'ROUTINE'"),
    )

    crisis_started_at = Column(DateTime(timezone=True), nullable=True)
    crisis_ended_at = Column(DateTime(timezone=True), nullable=True)

    # ---------------------------------------------------------
    # AUDIT PROVENANCE
    # ---------------------------------------------------------
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS (CRITICAL FOR ORM + COMPLIANCE TRACE)
    # ---------------------------------------------------------

    tasks = relationship(
        "Task",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    benefit_periods = relationship(
        "BenefitPeriod",
        back_populates="patient",
        cascade="all, delete-orphan",
    )