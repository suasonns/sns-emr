from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class ServiceCoverageDecision(TenantScopedMixin, BaseModel):
    __tablename__ = "service_coverage_decisions"

    # ---------------------------------------------------------
    # TENANT / PATIENT SCOPE (COMPLIANCE CRITICAL)
    # ---------------------------------------------------------
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
    # SERVICE CONTEXT
    # ---------------------------------------------------------
    service_type = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # MEDICATION, VISIT, DME, SUPPLY, OTHER

    service_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    # Optional reference to medication/order/etc.

    # ---------------------------------------------------------
    # COVERAGE DECISION
    # ---------------------------------------------------------
    coverage_intent = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # COMFORT, MAINTENANCE, CURATIVE, EXTERNAL

    financial_responsibility = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # HOSPICE, INSURANCE, PATIENT_FAMILY

    decision_source = Column(
        String(32),
        nullable=False,
        server_default=text("'CLINICIAN'"),
        index=True,
    )
    # CLINICIAN, BILLER, SYSTEM, OVERRIDE

    decision_reason = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # EVIDENCE LINKAGE (AUDIT SAFE)
    # ---------------------------------------------------------
    evidence_reference_type = Column(
        String(32),
        nullable=True,
    )
    # VISIT, NOTE, ORDER, ASSESSMENT, OTHER

    evidence_reference_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # PAYER SELECTION (CANONICAL)
    # ---------------------------------------------------------
    selected_payer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_payers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Nullable when responsibility = PATIENT_FAMILY or EXTERNAL

    # ---------------------------------------------------------
    # AUDIT
    # ---------------------------------------------------------
    decided_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )

    decided_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    patient = relationship(
        "Patient",
        back_populates="coverage_decisions",
    )

    selected_payer = relationship(
        "PatientPayer",
    )

    # ---------------------------------------------------------
    # ENTERPRISE CONSTRAINTS
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_service_coverage_patient_service",
            "tenant_id",
            "patient_id",
            "service_type",
            "service_id",
        ),
    )