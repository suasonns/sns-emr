# backend/app/billing/models/eligibility_verification.py
"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Directive item 4/5: structured hospice-relevant eligibility
findings, linked to the source document that is their evidence.

PAYER ELIGIBILITY STATUS (Directive item 2.A) lives on `status` here --
this is intentionally a *different* status domain from admission
benefit-period review status (BenefitPeriodDetermination.status) and
billing readiness status (derive_readiness_status in
readiness_workflow_service.py). Do not conflate them.

FIELD-LEVEL TRI-STATE DESIGN
-----------------------------
Directive item 4 lists ~25 distinct structured facts (Medicare
entitlement dates, Medicare Advantage enrollment, MSP, crossover, QMB,
hospice election history, benefit-period history, home-health overlap,
etc.) and item 4's closing paragraph requires that "returned value / not
returned / does not apply / unknown / unable to determine" remain
DISTINCT states -- an absent section must never silently become a
negative finding (e.g. "report didn't mention hospice" must not become
"patient has no prior hospice").

Rather than ~25 nullable columns (which cannot represent this tri-state
distinction -- NULL would ambiguously mean both "not returned" and
"does not apply"), each fact is stored as a small JSON object:

    {"state": "RETURNED" | "NOT_RETURNED" | "DOES_NOT_APPLY" | "UNKNOWN",
     "value": <any JSON-serializable value, only meaningful when
               state == "RETURNED">}

and the facts are grouped into three JSONB columns matching the
directive's three fact groups (entitlement / payment routing / hospice
utilization) rather than ~25 separate columns, keeping the migration and
ORM surface tractable while still satisfying every field the directive
lists. See FIELD SCHEMAS below for the exact key list each group uses --
this schema is enforced at the Pydantic layer (billing_schema.py), not by
a DB CHECK constraint, so a not-yet-modeled key never causes a write
failure.

FIELD SCHEMAS
-------------
entitlement_data keys: part_a_entitlement_status, part_a_effective_date,
    part_a_termination_date, part_b_status, inactive_coverage_indicator,
    inactive_coverage_dates, inactive_coverage_reason

payment_routing_data keys: primary_payer, medicare_advantage_enrollment,
    medicare_advantage_effective_date, medicare_advantage_termination_date,
    medicare_advantage_administering_organization,
    medicare_advantage_plan_reference, medicare_advantage_contract_reference,
    msp_applicability, msp_payer_information, crossover_coverage,
    qmb_status

hospice_utilization_data keys: prior_hospice_election_history,
    hospice_noe_information, hospice_benefit_period_history,
    prior_hospice_episode_dates, hospice_provider_identifier,
    open_hospice_episode_indicator, possible_hospice_overlap,
    home_health_episode_information, possible_home_health_overlap

Every value under these keys is the tri-state envelope above -- never a
bare value -- so "does not apply" and "not returned" can never collapse
into each other or into a false negative.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import false as sa_false
from sqlalchemy.sql import func

from app.models.base import BaseModel

# Directive item 2.A -- PAYER ELIGIBILITY STATUS domain. Distinct from
# BenefitPeriodDetermination's status domain and readiness_workflow_service's
# READY/AT_RISK/NOT_READY domain -- do not merge these enums.
PAYER_ELIGIBILITY_STATUSES = {
    "NOT_RUN",
    "PENDING",
    "VERIFIED_ACTIVE",
    "VERIFIED_INACTIVE",
    "COVERAGE_CONFLICT",
    "REVIEW_REQUIRED",
    "ERROR",
}

VERIFICATION_METHODS = {"MANUAL_UPLOAD", "MANUAL_ENTRY", "PORTAL_CHECK", "PARSED_AUTOMATED"}

FIELD_STATES = {"RETURNED", "NOT_RETURNED", "DOES_NOT_APPLY", "UNKNOWN"}


class EligibilityVerification(BaseModel):
    __tablename__ = "eligibility_verifications"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    payer_coverage_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_insurances.id"), nullable=True, index=True
    )

    # The document a human (or, later, an automated parser) read to
    # produce this verification -- every structured finding must be
    # traceable to its evidence source (Directive item 4).
    source_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_source_documents.id"),
        nullable=False,
        index=True,
    )

    verification_date = Column(Date, nullable=True)
    verified_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    verification_method = Column(String(32), nullable=False, server_default="MANUAL_ENTRY")

    # Free-text reference to the payer/clearinghouse response identifier,
    # when one exists (a 271 trace number, a portal confirmation code).
    response_reference = Column(String(128), nullable=True)

    status = Column(String(24), nullable=False, server_default="NOT_RUN", index=True)

    effective_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)

    # See FIELD SCHEMAS in the module docstring for the exact key lists.
    entitlement_data = Column(JSONB, nullable=False, server_default="{}")
    payment_routing_data = Column(JSONB, nullable=False, server_default="{}")
    hospice_utilization_data = Column(JSONB, nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Set when a LATER verification for the same patient+coverage
    # supersedes this one -- append-only, this row is never deleted or
    # overwritten (Directive item 8: "allow the biller to append a later
    # reverification without overwriting the original intake verification").
    superseded_at = Column(DateTime(timezone=True), nullable=True)

    # Phase B (reverification workflow) / Phase C (eligibility change
    # impact engine): a reverification records *what kind* of change it
    # found relative to the prior verification, so the impact engine can
    # decide what downstream evaluation to trigger without re-diffing raw
    # JSON payloads. All default False -- a first-time (non-reverification)
    # verification simply never sets any of these.
    notes = Column(Text, nullable=True)
    coverage_change_flag = Column(Boolean, nullable=False, server_default=sa_false())
    payer_change_flag = Column(Boolean, nullable=False, server_default=sa_false())
    msp_change_flag = Column(Boolean, nullable=False, server_default=sa_false())
    ma_change_flag = Column(Boolean, nullable=False, server_default=sa_false())
    overlap_concern_flag = Column(Boolean, nullable=False, server_default=sa_false())

    __table_args__ = (
        Index("ix_ev_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_ev_patient_status", "patient_id", "status"),
    )
