# backend/app/billing/services/eligibility_workflow_service.py
"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Phases 1-4.

Three distinct status domains meet here (Directive item 2 -- never
conflate them):

  A. PAYER ELIGIBILITY STATUS       -- EligibilityVerification.status
  B. ADMISSION BENEFIT-PERIOD REVIEW -- BenefitPeriodDetermination.status
  C. BILLING READINESS STATUS       -- readiness_workflow_service's
                                        READY/AT_RISK/NOT_READY

This module owns (A) and (B) at the service layer: recording new
evidence (source documents, verifications, determinations) and deriving
the ADMISSION_REVIEW_REQUIRED gate (Phase 4) that
billing_readiness_service consults additively (never as a hard
population filter -- see module docstring there for why).

BACKWARD-COMPATIBILITY / NON-REGRESSION RULE
---------------------------------------------
An admitted patient who has NO EligibilityVerification or
BenefitPeriodDetermination row at all is treated as CLEAR, not blocked --
per Directive item 4's closing rule, "an absent source section is not
automatically a negative finding," and per Directive item 10's framing
that BENEFIT_PERIOD_REVIEW_REQUIRED on an admitted record is the
*exceptional* path (legacy import / migration / later-discovered
conflict), never the default. This keeps every pre-existing admitted
test-fixture/patient (which predates this workflow and therefore has
none of these rows) unaffected -- the gate only ever fires once a
verification/determination row actually exists and is in an unresolved
state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.billing.models.benefit_period_determination import (
    BENEFIT_PERIOD_REVIEW_RESOLVED_STATUSES,
    BENEFIT_PERIOD_REVIEW_STATUSES,
    BenefitPeriodDetermination,
)
from app.billing.models.eligibility_source_document import (
    ELIGIBILITY_DOCUMENT_STATUSES,
    ELIGIBILITY_DOCUMENT_TYPES,
    EligibilitySourceDocument,
)
from app.billing.models.eligibility_verification import (
    PAYER_ELIGIBILITY_STATUSES,
    VERIFICATION_METHODS,
    EligibilityVerification,
)

# Payer-eligibility statuses that DO NOT satisfy the admission gate --
# i.e. still require human review before a normal admission finalizes.
PAYER_ELIGIBILITY_UNRESOLVED_STATUSES = {
    "NOT_RUN",
    "PENDING",
    "COVERAGE_CONFLICT",
    "REVIEW_REQUIRED",
    "ERROR",
}

# The exact blocker message text used for both the admission gate and,
# when it surfaces post-admission (the exceptional path), the billing
# blocker taxonomy's ELIGIBILITY_REVERIFICATION_REQUIRED code -- never a
# raw enum, always this human-readable sentence (Directive item 10/11).
ELIGIBILITY_REVIEW_BLOCKER_MESSAGE = (
    "Payer eligibility for this admitted record requires re-verification. "
    "Open the eligibility source document before claim preparation."
)

BENEFIT_PERIOD_REVIEW_BLOCKER_MESSAGE = (
    "Benefit-period information for this admitted record requires review. "
    "Open the eligibility source and admission determination before claim "
    "preparation."
)


@dataclass(frozen=True)
class AdmissionGateResult:
    """
    Phase 4 -- admission gate outcome. `gate_status` is CLEAR or
    ADMISSION_REVIEW_REQUIRED; never a hard exception, always a value
    the caller decides what to do with (block a NEW admission, or -- for
    an already-admitted record -- surface as an exceptional billing
    blocker per Directive item 10).
    """

    gate_status: str  # "CLEAR" | "ADMISSION_REVIEW_REQUIRED"
    blockers: list[str] = field(default_factory=list)
    eligibility_verification_id: Optional[str] = None
    benefit_period_determination_id: Optional[str] = None


def record_eligibility_source_document(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    document_record_id: str,
    document_type: str,
    uploaded_by_user_id: str,
    payer_coverage_id: str | None = None,
    verification_date: date | None = None,
    service_date_from: date | None = None,
    service_date_to: date | None = None,
    supersedes_document_id: str | None = None,
) -> EligibilitySourceDocument:
    """
    Phase 1. Reuses the existing document-storage pipeline via
    `document_record_id` (see module docstring on
    EligibilitySourceDocument) -- this call only records the
    eligibility-specific facts layered on top of an already-uploaded
    DocumentRecord. Supersedes append-only: passing
    `supersedes_document_id` marks the prior row SUPERSEDED rather than
    deleting or overwriting it.
    """
    if document_type not in ELIGIBILITY_DOCUMENT_TYPES:
        raise ValueError(f"Unknown eligibility document_type: {document_type!r}")

    doc = EligibilitySourceDocument(
        tenant_id=tenant_id,
        patient_id=patient_id,
        payer_coverage_id=payer_coverage_id,
        document_record_id=document_record_id,
        document_type=document_type,
        service_date_from=service_date_from,
        service_date_to=service_date_to,
        verification_date=verification_date,
        uploaded_by_user_id=uploaded_by_user_id,
        supersedes_document_id=supersedes_document_id,
        status="ACTIVE",
    )
    db.add(doc)

    if supersedes_document_id:
        prior = (
            db.query(EligibilitySourceDocument)
            .filter(
                EligibilitySourceDocument.id == supersedes_document_id,
                EligibilitySourceDocument.tenant_id == tenant_id,
            )
            .first()
        )
        if prior is not None:
            prior.status = "SUPERSEDED"

    db.commit()
    db.refresh(doc)
    return doc


def record_eligibility_verification(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    source_document_id: str,
    verified_by_user_id: str,
    status: str,
    payer_coverage_id: str | None = None,
    verification_date: date | None = None,
    verification_method: str = "MANUAL_ENTRY",
    response_reference: str | None = None,
    effective_date: date | None = None,
    termination_date: date | None = None,
    entitlement_data: dict | None = None,
    payment_routing_data: dict | None = None,
    hospice_utilization_data: dict | None = None,
    supersede_prior: bool = True,
) -> EligibilityVerification:
    """
    Phase 2. Records a new PAYER ELIGIBILITY STATUS verification. Never
    overwrites a prior verification for the same patient -- Directive
    item 8 requires a biller's later reverification to append, not
    replace, the intake verification. When `supersede_prior` is True
    (the default), the previous latest verification for this patient is
    marked superseded_at, purely for "what is current" queries; the row
    itself is retained forever.
    """
    if status not in PAYER_ELIGIBILITY_STATUSES:
        raise ValueError(f"Unknown payer eligibility status: {status!r}")
    if verification_method not in VERIFICATION_METHODS:
        raise ValueError(f"Unknown verification_method: {verification_method!r}")

    if supersede_prior:
        prior = get_latest_eligibility_verification(db, tenant_id=tenant_id, patient_id=patient_id)
        if prior is not None and prior.superseded_at is None:
            prior.superseded_at = datetime.now(timezone.utc)

    verification = EligibilityVerification(
        tenant_id=tenant_id,
        patient_id=patient_id,
        payer_coverage_id=payer_coverage_id,
        source_document_id=source_document_id,
        verification_date=verification_date,
        verified_by_user_id=verified_by_user_id,
        verification_method=verification_method,
        response_reference=response_reference,
        status=status,
        effective_date=effective_date,
        termination_date=termination_date,
        entitlement_data=entitlement_data or {},
        payment_routing_data=payment_routing_data or {},
        hospice_utilization_data=hospice_utilization_data or {},
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def record_benefit_period_determination(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    determination_status: str,
    admission_id: str | None = None,
    eligibility_verification_id: str | None = None,
    source_document_id: str | None = None,
    prior_hospice_episode_count: int | None = None,
    benefit_periods_used: int | None = None,
    anticipated_benefit_period_number: int | None = None,
    anticipated_period_start_date: date | None = None,
    anticipated_period_end_date: date | None = None,
    face_to_face_applicability: bool | None = None,
    determined_by_user_id: str | None = None,
    review_notes: str | None = None,
    conflict_reason: str | None = None,
    supersedes_determination_id: str | None = None,
) -> BenefitPeriodDetermination:
    """
    Phase 3. Records the RN/authorized-reviewer conclusion about which
    hospice benefit period an admission falls into. Never manufactures a
    confident period number from incomplete evidence -- if the caller
    doesn't have one, leave `anticipated_benefit_period_number` None and
    pass determination_status="INFORMATION_INCOMPLETE" or
    "CONFLICT_REQUIRES_REVIEW" instead. Corrections are append-only: a
    new determination row references the one it supersedes rather than
    mutating it.
    """
    if determination_status not in BENEFIT_PERIOD_REVIEW_STATUSES:
        raise ValueError(f"Unknown determination_status: {determination_status!r}")

    determination = BenefitPeriodDetermination(
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        eligibility_verification_id=eligibility_verification_id,
        source_document_id=source_document_id,
        prior_hospice_episode_count=prior_hospice_episode_count,
        benefit_periods_used=benefit_periods_used,
        anticipated_benefit_period_number=anticipated_benefit_period_number,
        anticipated_period_start_date=anticipated_period_start_date,
        anticipated_period_end_date=anticipated_period_end_date,
        face_to_face_applicability=face_to_face_applicability,
        determination_status=determination_status,
        determined_by_user_id=determined_by_user_id,
        determined_at=datetime.now(timezone.utc) if determined_by_user_id else None,
        review_notes=review_notes,
        conflict_reason=conflict_reason,
    )
    db.add(determination)

    if supersedes_determination_id:
        prior = (
            db.query(BenefitPeriodDetermination)
            .filter(
                BenefitPeriodDetermination.id == supersedes_determination_id,
                BenefitPeriodDetermination.tenant_id == tenant_id,
            )
            .first()
        )
        if prior is not None:
            db.flush()
            prior.superseded_at = datetime.now(timezone.utc)
            prior.superseded_by_id = determination.id

    db.commit()
    db.refresh(determination)
    return determination


def get_latest_eligibility_verification(
    db: Session, *, tenant_id: str, patient_id: str
) -> EligibilityVerification | None:
    return (
        db.query(EligibilityVerification)
        .filter(
            EligibilityVerification.tenant_id == tenant_id,
            EligibilityVerification.patient_id == patient_id,
        )
        .order_by(EligibilityVerification.created_at.desc())
        .first()
    )


def get_latest_benefit_period_determination(
    db: Session, *, tenant_id: str, patient_id: str
) -> BenefitPeriodDetermination | None:
    return (
        db.query(BenefitPeriodDetermination)
        .filter(
            BenefitPeriodDetermination.tenant_id == tenant_id,
            BenefitPeriodDetermination.patient_id == patient_id,
        )
        .order_by(BenefitPeriodDetermination.created_at.desc())
        .first()
    )


def evaluate_admission_gate(
    db: Session, *, tenant_id: str, patient_id: str
) -> AdmissionGateResult:
    """
    Phase 4. CLEAR unless a verification/determination row *exists* and
    is in an unresolved state (see module docstring for the
    non-regression rationale). Callers decide what CLEAR vs.
    ADMISSION_REVIEW_REQUIRED means for them:
      - a NEW-admission workflow can block finalization outright;
      - billing_readiness_service surfaces ADMISSION_REVIEW_REQUIRED on
        an already-admitted record as an exceptional billing blocker
        (Directive item 10), never as a silent exclusion.
    """
    blockers: list[str] = []

    verification = get_latest_eligibility_verification(
        db, tenant_id=tenant_id, patient_id=patient_id
    )
    if verification is not None and verification.status in PAYER_ELIGIBILITY_UNRESOLVED_STATUSES:
        blockers.append(ELIGIBILITY_REVIEW_BLOCKER_MESSAGE)

    determination = get_latest_benefit_period_determination(
        db, tenant_id=tenant_id, patient_id=patient_id
    )
    if (
        determination is not None
        and determination.determination_status not in BENEFIT_PERIOD_REVIEW_RESOLVED_STATUSES
    ):
        blockers.append(BENEFIT_PERIOD_REVIEW_BLOCKER_MESSAGE)

    return AdmissionGateResult(
        gate_status="ADMISSION_REVIEW_REQUIRED" if blockers else "CLEAR",
        blockers=blockers,
        eligibility_verification_id=str(verification.id) if verification else None,
        benefit_period_determination_id=str(determination.id) if determination else None,
    )
