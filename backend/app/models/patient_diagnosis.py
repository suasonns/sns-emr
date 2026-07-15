from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.enums import (
    DiagnosisSource,
    DiagnosisStatus,
    DiagnosisType,
)


class PatientDiagnosis(Base):
    __tablename__ = "patient_diagnoses"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---------------------------------------------------------
    # Diagnosis metadata
    # ---------------------------------------------------------

    diagnosis_type = Column(
        SQLEnum(
            DiagnosisType,
            name="patient_diagnosis_type_enum",
            values_callable=lambda enum_class: [
                enum_item.value for enum_item in enum_class
            ],
        ),
        nullable=False,
    )

    status = Column(
        SQLEnum(
            DiagnosisStatus,
            name="patient_diagnosis_status_enum",
            values_callable=lambda enum_class: [
                enum_item.value for enum_item in enum_class
            ],
        ),
        nullable=False,
        server_default=text("'PROPOSED'"),
    )

    source = Column(
        SQLEnum(
            DiagnosisSource,
            name="patient_diagnosis_source_enum",
            values_callable=lambda enum_class: [
                enum_item.value for enum_item in enum_class
            ],
        ),
        nullable=False,
    )

    # ---------------------------------------------------------
    # ICD
    # ---------------------------------------------------------

    icd10_code = Column(
        String(32),
        nullable=False,
    )

    diagnosis_description = Column(
        String(255),
        nullable=False,
    )

    display_name = Column(
        String(512),
        nullable=False,
    )

    # ---------------------------------------------------------
    # Hospice Classification
    # ---------------------------------------------------------

    is_terminal = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    is_related_to_terminal = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # ---------------------------------------------------------
    # Effective Dates
    # ---------------------------------------------------------

    effective_date = Column(
        Date,
        nullable=True,
    )

    resolved_date = Column(
        Date,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Benefit Period Governance
    # ---------------------------------------------------------

    effective_benefit_period_number = Column(
        Integer,
        nullable=True,
    )

    resolved_benefit_period_number = Column(
        Integer,
        nullable=True,
    )

    # ---------------------------------------------------------
    # IDG Diagnosis Change Governance
    # ---------------------------------------------------------

    idg_discussion_required = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    idg_discussed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    idg_discussed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    idg_summary = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Supporting Evidence
    # ---------------------------------------------------------

    hospital_records_reviewed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    diagnostic_results_reviewed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    specialist_documentation_reviewed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    specialist_name = Column(
        String(255),
        nullable=True,
    )

    specialist_documentation_date = Column(
        Date,
        nullable=True,
    )

    prior_specialist_certification_present = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    supporting_evidence_summary = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Physician-Signed Governing Document
    # ---------------------------------------------------------

    physician_signed_document_type = Column(
        String(64),
        nullable=True,
    )

    physician_signed_document_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    physician_signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    physician_signature_notes = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Diagnosis Change Documentation
    # ---------------------------------------------------------

    change_reason = Column(
        Text,
        nullable=True,
    )

    rejected_reason = Column(
        Text,
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
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

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    patient = relationship(
        "Patient",
        back_populates="diagnoses",
    )

    # ---------------------------------------------------------
    # Constraints / Indexes
    # ---------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "length(trim(icd10_code)) > 0",
            name="ck_patient_diagnoses_icd10_code_not_blank",
        ),
        CheckConstraint(
            "length(trim(diagnosis_description)) > 0",
            name="ck_patient_diagnoses_description_not_blank",
        ),
        CheckConstraint(
            "length(trim(display_name)) > 0",
            name="ck_patient_diagnoses_display_name_not_blank",
        ),
        CheckConstraint(
            (
                "resolved_date IS NULL "
                "OR effective_date IS NULL "
                "OR resolved_date >= effective_date"
            ),
            name="ck_patient_diagnoses_resolved_after_effective",
        ),
        CheckConstraint(
            (
                "(status != 'REJECTED') "
                "OR (rejected_reason IS NOT NULL "
                "AND length(trim(rejected_reason)) > 0)"
            ),
            name="ck_patient_diagnoses_rejected_requires_reason",
        ),
        CheckConstraint(
            (
                "resolved_benefit_period_number IS NULL "
                "OR effective_benefit_period_number IS NULL "
                "OR resolved_benefit_period_number "
                ">= effective_benefit_period_number"
            ),
            name="ck_patient_diagnoses_resolved_benefit_after_effective",
        ),
        Index(
            "ix_patient_diagnoses_tenant_id",
            "tenant_id",
        ),
        Index(
            "ix_patient_diagnoses_patient_id",
            "patient_id",
        ),
        Index(
            "ix_patient_diagnoses_icd10_code",
            "icd10_code",
        ),
        Index(
            "ix_patient_diagnoses_created_by",
            "created_by",
        ),
        Index(
            "ix_patient_diagnoses_idg_meeting_id",
            "idg_meeting_id",
        ),
        Index(
            "ix_patient_diagnoses_patient_type_status",
            "patient_id",
            "diagnosis_type",
            "status",
        ),
        Index(
            "ix_patient_diagnoses_tenant_patient_active",
            "tenant_id",
            "patient_id",
            "active",
        ),
        Index(
            "ix_patient_diagnoses_effective_benefit_period",
            "patient_id",
            "effective_benefit_period_number",
        ),
        Index(
            "ix_patient_diagnoses_idg_review",
            "patient_id",
            "idg_discussion_required",
            "idg_discussed",
        ),
        Index(
            "uq_patient_diagnoses_one_active_primary",
            "tenant_id",
            "patient_id",
            unique=True,
            postgresql_where=text(
                "diagnosis_type = 'PRIMARY' "
                "AND status = 'ACTIVE' "
                "AND active = true "
                "AND resolved_date IS NULL"
            ),
        ),
    )