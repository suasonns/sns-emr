# backend/app/billing/models/benefit_period_determination.py
"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Directive item 6: benefit-period determination.

The raw eligibility source document/verification is evidence, not a
conclusion. This table is the actual, authorized conclusion an RN (or
authorized admitting staff) reaches about which hospice benefit period an
admission falls into -- explicitly separate from
EligibilityVerification's PAYER ELIGIBILITY STATUS domain and from
readiness_workflow_service's BILLING READINESS STATUS domain (Directive
item 2: three distinct status domains, never mixed).

`determination_status` (Directive item 2.B, "ADMISSION BENEFIT-PERIOD
REVIEW STATUS") deliberately never lets the system manufacture a
confident period number when the evidence is incomplete --
`anticipated_benefit_period_number` stays NULL and `determination_status`
is INFORMATION_INCOMPLETE or CONFLICT_REQUIRES_REVIEW instead. The
admission gate (Directive item 7,
app.billing.services.eligibility_workflow_service.evaluate_admission_gate)
reads this row, not the raw eligibility document, to decide whether a
normal admission can finalize.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel

# Directive item 2.B -- ADMISSION BENEFIT-PERIOD REVIEW STATUS domain.
BENEFIT_PERIOD_REVIEW_STATUSES = {
    "NOT_REVIEWED",
    "FILE_UPLOADED",
    "REVIEW_IN_PROGRESS",
    "BENEFIT_PERIOD_CONFIRMED",
    "BENEFIT_PERIOD_NOT_APPLICABLE",
    "INFORMATION_INCOMPLETE",
    "CONFLICT_REQUIRES_REVIEW",
}

# A determination only "gates open" (satisfies the admission gate,
# Directive item 7) when in one of these terminal, resolved states.
BENEFIT_PERIOD_REVIEW_RESOLVED_STATUSES = {
    "BENEFIT_PERIOD_CONFIRMED",
    "BENEFIT_PERIOD_NOT_APPLICABLE",
}

# docs/workflows/AdmissionTypesWorkflow.md -- Admit Type driver. Mutually
# exclusive workflow paths, always staff-selected, never inferred.
ADMIT_TYPES = {
    "NEW_ADMISSION",
    "READMISSION",
    "TRANSFER_FROM_ANOTHER_HOSPICE",
}


class BenefitPeriodDetermination(BaseModel):
    __tablename__ = "benefit_period_determinations"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )

    # Nullable: a determination can exist for a referral/intake-hold
    # record before any Admission row has been created yet.
    admission_id = Column(
        UUID(as_uuid=True), ForeignKey("admissions.id"), nullable=True, index=True
    )

    eligibility_verification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_verifications.id"),
        nullable=True,
        index=True,
    )
    source_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_source_documents.id"),
        nullable=True,
        index=True,
    )

    # NULL is the explicit "unknown" state -- never default to 0 (which
    # would be indistinguishable from "confirmed zero prior episodes").
    prior_hospice_episode_count = Column(Integer, nullable=True)
    benefit_periods_used = Column(Integer, nullable=True)

    anticipated_benefit_period_number = Column(Integer, nullable=True)
    anticipated_period_start_date = Column(Date, nullable=True)
    anticipated_period_end_date = Column(Date, nullable=True)

    # NULL = not yet determined; True/False once an RN has actually
    # reviewed whether the period-3+ F2F rule applies to this admission.
    face_to_face_applicability = Column(Boolean, nullable=True)

    determination_status = Column(
        String(32), nullable=False, server_default="NOT_REVIEWED", index=True
    )

    determined_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    determined_at = Column(DateTime(timezone=True), nullable=True)

    review_notes = Column(Text, nullable=True)
    conflict_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Set when a correction supersedes this determination (append-only --
    # corrections create a new row rather than mutating history away).
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by_id = Column(
        UUID(as_uuid=True), ForeignKey("benefit_period_determinations.id"), nullable=True
    )

    # ---------------------------------------------------------------
    # Admit Type driver (docs/workflows/AdmissionTypesWorkflow.md).
    # Mutually exclusive workflow path, always staff-selected -- never
    # inferred. Drives which fields below are required by the SOC gate.
    # ---------------------------------------------------------------
    admit_type = Column(String(32), nullable=True, index=True)

    # Staff-entered, every admit type. Never defaulted (not even to 1
    # for a "no prior hospice" new admission).
    starting_cert = Column(Integer, nullable=True)

    # Transfer-only fields (Admit Type = TRANSFER_FROM_ANOTHER_HOSPICE).
    # Remain NULL and UI-hidden for NEW_ADMISSION / READMISSION.
    transfer_source = Column(String(255), nullable=True)
    transfer_evidence_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_source_documents.id"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_bpd_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_bpd_admission", "admission_id"),
        Index("ix_bpd_patient_status", "patient_id", "determination_status"),
    )
