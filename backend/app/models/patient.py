from __future__ import annotations

from uuid import uuid4

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
from sqlalchemy.sql import func

from app.models.base import Base


class Patient(Base):
    __tablename__ = "patients"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Core identity
    # ---------------------------------------------------------
    mrn = Column(String(64), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)

    ssn_last4 = Column(String(4), nullable=True)
    primary_diagnosis = Column(String(255), nullable=False)

    # ---------------------------------------------------------
    # System lifecycle
    # ---------------------------------------------------------
    status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
        index=True,
    )

    # ---------------------------------------------------------
    # Hospice lifecycle
    # ---------------------------------------------------------
    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # SOC / admission
    # ---------------------------------------------------------
    records_release_signed_at = Column(DateTime(timezone=True), nullable=True)
    election_signed_at = Column(DateTime(timezone=True), nullable=True)
    soc_date = Column(DateTime(timezone=True), nullable=True)
    on_service_at = Column(DateTime(timezone=True), nullable=True)

    admission_status = Column(
        String(32),
        nullable=False,
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
    # Clinical acuity
    # ---------------------------------------------------------
    acuity_state = Column(
        String(32),
        nullable=False,
        server_default=text("'ROUTINE'"),
        index=True,
    )

    crisis_started_at = Column(DateTime(timezone=True), nullable=True)
    crisis_ended_at = Column(DateTime(timezone=True), nullable=True)

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Relationships ✅ (FIXED LOCATION)
    # ---------------------------------------------------------
    insurances = relationship(
        "PatientInsurance",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    medications = relationship(
        "Medication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    
    assignments = relationship(
        "PatientAssignment",
        back_populates="patient",
        cascade="all, delete-orphan",
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
    # Constraints
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