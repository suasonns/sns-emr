# models/patient.py

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.admission_status_history import AdmissionStatusHistory

class Patient(Base):
    __tablename__ = "patients"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "ACTIVE")
        kwargs.setdefault("admission_status", "PRE_REFERRAL")
        kwargs.setdefault("acuity_state", "ROUTINE")
        super().__init__(**kwargs)

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
    date_of_birth = Column(Date, nullable=False)

    ssn_last4 = Column(String(4), nullable=True)
    primary_diagnosis = Column(String(255), nullable=False)

    # ---------------------------------------------------------
    # System lifecycle
    # ---------------------------------------------------------
    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        index=True,
    )

    patient_type = Column(
        String(32),
        nullable=False,
        server_default=text("'PRODUCTION'"),
        index=True,
    )
    
    training_label = Column(Text, nullable=True)
    
    # ---------------------------------------------------------
    # Hospice lifecycle
    # ---------------------------------------------------------
    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)

    discharge_reason = Column(String(255), nullable=True)
    discharge_initiated_by = Column(String(64), nullable=True)

    discharge_projected_date = Column(DateTime(timezone=True), nullable=True)
    discharge_comments = Column(Text, nullable=True)

    discharge_plan_reviewed = Column(Boolean, nullable=True)

    discharge_notified = Column(Boolean, nullable=True)
    discharge_explained = Column(Boolean, nullable=True)
    discharge_readmission_explained = Column(Boolean, nullable=True)
    discharge_medication_instruction = Column(Boolean, nullable=True)
    discharge_contact_provided = Column(Boolean, nullable=True)
    discharge_referral_provided = Column(Boolean, nullable=True)

    # ---------------------------------------------------------
    # SOC / admission
    # ---------------------------------------------------------
    records_release_signed_at = Column(DateTime(timezone=True), nullable=True)

    election_signed_at = Column(DateTime(timezone=True), nullable=True)

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
    # Clinical acuity
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
    # IDG group assignment (entity #2/#3 scheduling cohort — see
    # IDG_DOMAIN_MODEL.md). A patient belongs to at most one active
    # IDGGroup at a time; the group's IDGGroupScheduleRule(s) determine
    # when this patient's next automatic IDGMeeting will be generated.
    # ---------------------------------------------------------
    idg_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_groups.id"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
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
    # Relationships
    # ---------------------------------------------------------
    facesheets = relationship(
        "PatientFaceSheet",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    insurances = relationship(
        "PatientInsurance",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    
    admissions = relationship(
        "Admission",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    
    medications = relationship(
        "Medication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    diagnoses = relationship(
        "PatientDiagnosis",
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

    admission_status_history = relationship(
        "AdmissionStatusHistory",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by=AdmissionStatusHistory.changed_at,
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

    allergies = relationship(
        "PatientAllergy",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    patient_orders = relationship(
        "PatientOrder",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    physician_orders = relationship(
        "PhysicianOrder",
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
