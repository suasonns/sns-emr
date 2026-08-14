from __future__ import annotations

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class Patient(TenantScopedMixin, BaseModel):
    __tablename__ = "patients"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "ACTIVE")
        kwargs.setdefault("admission_status", "PRE_REFERRAL")
        kwargs.setdefault("acuity_state", "ROUTINE")
        super().__init__(**kwargs)

    # ---------------------------------------------------------
    # TENANT ISOLATION (COMPLIANCE CRITICAL)
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # CORE IDENTITY (ENTERPRISE LOCKED)
    # ---------------------------------------------------------
    mrn = Column(String(64), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)

    ssn_last4 = Column(String(4), nullable=True)
    primary_diagnosis = Column(String(255), nullable=False)

    # ---------------------------------------------------------
    # SYSTEM LIFECYCLE
    # ---------------------------------------------------------
    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        index=True,
    )

    # ---------------------------------------------------------
    # HOSPICE LIFECYCLE
    # ---------------------------------------------------------
    hospice_election_date = Column(Date, nullable=True)

    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # SOC / ADMISSION (COMPLIANCE CRITICAL)
    # ---------------------------------------------------------
    records_release_signed_at = Column(DateTime(timezone=True), nullable=True)
    election_signed_at = Column(DateTime(timezone=True), nullable=True)

    soc_date = Column(DateTime(timezone=True), nullable=True)

    # ✅ System-level SOC trigger
    on_service_at = Column(DateTime(timezone=True), nullable=True)

    admission_status = Column(
        String(32),
        nullable=False,
        default="PRE_REFERRAL",
        server_default=text("'PRE_REFERRAL'"),
        index=True,
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
        String(32),
        nullable=False,
        default="ROUTINE",
        server_default=text("'ROUTINE'"),
        index=True,
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
    # RELATIONSHIPS (ENTERPRISE-SAFE)
    # ---------------------------------------------------------
    
    assignments = relationship(
        "PatientAssignment",
        back_populates="patient"
    )


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

    # ✅ FIXED: Legacy-safe relationship using explicit cast
    payers = relationship(
        "PatientPayer",
        primaryjoin="Patient.id == cast(foreign(PatientPayer.patient_id), UUID(as_uuid=True))",
        back_populates="patient",
        viewonly=True,
        lazy="selectin",
    )

    coverage_decisions = relationship(
        "ServiceCoverageDecision",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    external_substances = relationship(
        "ExternalSubstance",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    # ---------------------------------------------------------
    # ENTERPRISE CONSTRAINTS
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "uq_patients_tenant_mrn",
            "tenant_id",
            "mrn",
            unique=True,
        ),
        Index(
            "ix_patients_status_tenant",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_patients_admission_status",
            "admission_status",
        ),
    )
