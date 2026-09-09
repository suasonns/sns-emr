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

# Sentinel actor value for auto-resolution by the sync job itself (no real
# user acted) -- distinguishes system auto-resolution from a human
# resolving a blocker early via the manual-resolve endpoint.
SYSTEM_AUTO_RESOLVED_BY = "SYSTEM_AUTO_RESOLVED"

BLOCKER_CODES = {
    "MISSING_CERTIFICATION",
    "MISSING_FACE_TO_FACE",
    "MISSING_PHYSICIAN_SIGNATURE",
    "MISSING_DOCUMENTATION",
    "BENEFIT_PERIOD_ISSUE",
    "OTHER",
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
    blocker_code = Column(String(32), nullable=False, index=True)

    # The exact free-text blocker string from
    # check_patient_billing_readiness() -- preserved verbatim for
    # backward compatibility with existing per-patient detail views.
    message = Column(Text, nullable=False)

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
