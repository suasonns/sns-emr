# backend/app/billing/models/billing_blocker_record.py
"""
Typed blocker lifecycle records (Sprint 2 -- Billing Readiness Operational
Workflow, Deliverable 3: Typed Blocker Framework).

`check_patient_billing_readiness()` (Sprint 1) already produces a
free-text `blockers: list[str]` per evaluation, persisted verbatim on
`BillingReadinessVerdict`. This table adds a typed, *per-blocker*
lifecycle on top of that -- one row per distinct blocker a patient has
had, tracking when it first/last appeared and when (and by whom) it was
resolved -- without changing or replacing the free-text message, which
stays intact here for backward compatibility and for the per-patient
detail view.

Rows are created/updated by
`app.billing.services.readiness_workflow_service.sync_blocker_records`,
called once per verdict right after
`billing_readiness_service._persist_billing_readiness_verdict` runs. A
blocker present in the new verdict but not already OPEN for the patient
starts a new row; a currently-OPEN row not present in the new verdict is
auto-resolved (`resolved_by = SYSTEM_AUTO_RESOLVED_BY`). Staff can also
resolve a blocker early via the manual resolve endpoint, which records a
real actor and reason instead.

This is intentionally NOT a replacement for
`BillingReadinessVerdict.blockers` -- that JSONB column remains the
immutable record of what a given evaluation actually said. This table is
a derived, mutable-status overlay for operational triage only.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel

# EligibilitySourceDocument must be imported wherever this module is
# imported so the eligibility_source_documents table is registered in
# Base.metadata before this module's source_document_id FK is resolved
# (SQLAlchemy resolves string-based ForeignKey targets lazily, by table
# name, against whatever has been imported so far).
from app.billing.models.eligibility_source_document import (  # noqa: F401
    EligibilitySourceDocument,
)

# Sentinel actor value for auto-resolution by the sync job itself (no real
# user acted) -- distinguishes system auto-resolution from a human
# resolving a blocker early via the manual-resolve endpoint.
SYSTEM_AUTO_RESOLVED_BY = "SYSTEM_AUTO_RESOLVED"

# Corrected taxonomy (Eligibility/Admission/Benefit-Period/Billing-Readiness
# Workflow Correction directive, item 10): billing-readiness blockers now
# primarily represent post-admission claim-preparation issues, replacing
# the original Sprint 2 6-code list. The original codes are retained in
# this set for backward compatibility with any already-persisted rows
# (this table is append-only/never rewritten) -- classify_blocker_code()
# in readiness_workflow_service.py only ever assigns a code from the
# corrected list going forward.
BLOCKER_CODES = {
    # --- corrected taxonomy (directive item 10) ---
    "ELIGIBILITY_REVERIFICATION_REQUIRED",
    "PAYER_ROUTING_CONFLICT",
    "MEDICARE_ADVANTAGE_REVIEW_REQUIRED",
    "MSP_REVIEW_REQUIRED",
    "ACTIVE_HOSPICE_OVERLAP",
    "ACTIVE_HOME_HEALTH_OVERLAP_REVIEW",
    "NOE_NOT_ACCEPTED",
    "CERTIFICATION_NOT_COMPLETE",
    "RECERTIFICATION_NOT_COMPLETE",
    "FACE_TO_FACE_DOCUMENTATION_REQUIRED",
    "REQUIRED_SIGNATURE_MISSING",
    "SERVICE_DOCUMENTATION_INCOMPLETE",
    "LEVEL_OF_CARE_DATA_INCOMPLETE",
    "CLAIM_VALIDATION_ERROR",
    "BENEFIT_PERIOD_REVIEW_REQUIRED",
    "MISSING_AUTHORIZATION_EVIDENCE",
    "OTHER",
    # --- original Sprint 2 codes, retained for historical rows only ---
    "MISSING_CERTIFICATION",
    "MISSING_FACE_TO_FACE",
    "MISSING_PHYSICIAN_SIGNATURE",
    "MISSING_DOCUMENTATION",
    "BENEFIT_PERIOD_ISSUE",
}

BLOCKER_RECORD_STATUSES = {"OPEN", "RESOLVED"}


class BillingBlockerRecord(BaseModel):
    __tablename__ = "billing_blocker_records"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    # One of BLOCKER_CODES -- see
    # app.billing.services.readiness_workflow_service.classify_blocker_code
    # for the mapping from the existing free-text blocker prefixes.
    blocker_code = Column(String(48), nullable=False, index=True)

    # The exact free-text blocker string from
    # check_patient_billing_readiness() -- preserved verbatim for
    # backward compatibility with existing per-patient detail views.
    message = Column(Text, nullable=False)

    # Which operational role is expected to resolve this category of
    # blocker (Directive item 10: "workflow owner category"). One of
    # INTAKE / RN / BILLER / SYSTEM. Never displayed as a raw enum to
    # users -- the frontend maps this to a human label, same as
    # blocker_code (Directive item 10, last line: "Do not display
    # internal enum names to users").
    workflow_owner_category = Column(String(16), nullable=False, server_default="BILLER")

    # The eligibility source document this blocker traces back to, when
    # applicable (e.g. BENEFIT_PERIOD_REVIEW_REQUIRED, ELIGIBILITY_
    # REVERIFICATION_REQUIRED) -- nullable because most claim-preparation
    # blockers (missing signature, missing F2F) have no eligibility
    # document as their evidence source.
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("eligibility_source_documents.id"), nullable=True
    )

    first_seen_verdict_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_readiness_verdicts.id"), nullable=False
    )
    last_seen_verdict_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_readiness_verdicts.id"), nullable=False
    )

    first_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # OPEN | RESOLVED
    status = Column(String(16), nullable=False, server_default="OPEN", index=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    # A real user id for a manual resolve, or SYSTEM_AUTO_RESOLVED_BY when
    # the blocker simply stopped appearing on a later verdict.
    resolved_by = Column(String(64), nullable=True)
    resolution_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_bbr_patient_status", "patient_id", "status"),
        Index("ix_bbr_tenant_status", "tenant_id", "status"),
    )
