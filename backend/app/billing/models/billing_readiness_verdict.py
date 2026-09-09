# backend/app/billing/models/billing_readiness_verdict.py
"""
Immutable, append-only history of every billing-readiness evaluation.

Closes the confirmed Chronology Gap documented across this engagement's
review phases (see docs/planning/reimbursement_defensibility_review.md and
docs/planning/eligibility_traceability_epic.md, Workstream 3):
`check_patient_billing_readiness()` was previously a pure live computation
with zero persistence -- "why was this patient billable on a past date"
had no answer beyond re-deriving today's state. Every evaluation is now
persisted here, so a past verdict can be looked up directly instead of
recomputed or assumed.

This is purely additive: the underlying eligibility-rule logic in
check_patient_billing_readiness() is unchanged; this table stores the
verdict that function was already computing.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import Base


class BillingReadinessVerdict(Base):
    __tablename__ = "billing_readiness_verdicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    evaluated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    is_ready = Column(Boolean, nullable=False)

    # The exact blocker/warning lists check_patient_billing_readiness()
    # already computes -- persisted verbatim, no new logic.
    blockers = Column(JSONB, nullable=False)
    warnings = Column(JSONB, nullable=False)

    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    # The certification the verdict cited when checking
    # _find_finalized_certification_id, if one exists -- a forward-
    # traceability link (Workstream 6 groundwork; populated by Workstream 3
    # itself since the lookup already happens as part of the existing
    # blocker check).
    certification_id = Column(UUID(as_uuid=True), ForeignKey("certifications.id"), nullable=True, index=True)

    # SCHEDULED_CHECK | MANUAL_CHECK | CLAIM_SUBMISSION_ATTEMPT
    triggered_by = Column(String(32), nullable=False, server_default="MANUAL_CHECK")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
