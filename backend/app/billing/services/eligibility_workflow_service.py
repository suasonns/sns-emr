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
    ADMIT_TYPES,
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
from app.billing.models.readiness_workflow_event import ReadinessWorkflowEvent

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
    notes: str | None = None,
) -> EligibilitySourceDocument:
    """
    Phase 1 / Phase A (operational upload). Reuses the existing
    document-storage pipeline via `document_record_id` (see module
    docstring on EligibilitySourceDocument) -- this call only records the
    eligibility-specific facts layered on top of an already-uploaded
    DocumentRecord. Supersedes append-only: passing
    `supersedes_document_id` marks the prior row SUPERSEDED rather than
    deleting or overwriting it, and the new row's `version` is the prior
    row's version + 1 (1 for a brand-new, non-superseding upload).
    """
    if document_type not in ELIGIBILITY_DOCUMENT_TYPES:
        raise ValueError(f"Unknown eligibility document_type: {document_type!r}")

    prior: EligibilitySourceDocument | None = None
    if supersedes_document_id:
        prior = (
            db.query(EligibilitySourceDocument)
            .filter(
                EligibilitySourceDocument.id == supersedes_document_id,
                EligibilitySourceDocument.tenant_id == tenant_id,
            )
            .first()
        )
        if prior is None:
            raise ValueError(
                f"supersedes_document_id {supersedes_document_id!r} not found for this tenant"
            )

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
        notes=notes,
        version=(prior.version + 1) if prior is not None else 1,
    )
    db.add(doc)

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
    notes: str | None = None,
    coverage_change_flag: bool = False,
    payer_change_flag: bool = False,
    msp_change_flag: bool = False,
    ma_change_flag: bool = False,
    overlap_concern_flag: bool = False,
) -> EligibilityVerification:
    """
    Phase 2 / Phase B (reverification workflow). Records a new PAYER
    ELIGIBILITY STATUS verification. Never overwrites a prior
    verification for the same patient -- Directive item 8 requires a
    biller's later reverification to append, not replace, the intake
    verification. When `supersede_prior` is True (the default), the
    previous latest verification for this patient is marked
    superseded_at, purely for "what is current" queries; the row itself
    is retained forever.

    The five `*_change_flag` booleans are Phase C's impact-engine input:
    a reverification call records what kind of change it found relative
    to the prior verification so the caller (the API layer) can decide
    what downstream evaluation to trigger without re-diffing raw JSON
    payloads.
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
        notes=notes,
        coverage_change_flag=coverage_change_flag,
        payer_change_flag=payer_change_flag,
        msp_change_flag=msp_change_flag,
        ma_change_flag=ma_change_flag,
        overlap_concern_flag=overlap_concern_flag,
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
    admit_type: str | None = None,
    starting_cert: int | None = None,
    transfer_source: str | None = None,
    transfer_evidence_document_id: str | None = None,
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

    `admit_type`, `starting_cert`, `transfer_source`, and
    `transfer_evidence_document_id` (docs/workflows/AdmissionTypesWorkflow.md)
    are likewise always caller-supplied (staff-entered) -- this function
    never derives, defaults, or infers any of them. `admit_type` is
    validated against ADMIT_TYPES when provided; transfer_source/
    transfer_evidence_document_id are accepted for any admit_type (the
    SOC gate, not this function, is what enforces they are only
    *required* for TRANSFER_FROM_ANOTHER_HOSPICE).
    """
    if determination_status not in BENEFIT_PERIOD_REVIEW_STATUSES:
        raise ValueError(f"Unknown determination_status: {determination_status!r}")
    if admit_type is not None and admit_type not in ADMIT_TYPES:
        raise ValueError(f"Unknown admit_type: {admit_type!r}")

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
        admit_type=admit_type,
        starting_cert=starting_cert,
        transfer_source=transfer_source,
        transfer_evidence_document_id=transfer_evidence_document_id,
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


# ---------------------------------------------------------------------
# SOC hard gate (docs/workflows/BenefitPeriodWorkflow.md,
# AdmissionTypesWorkflow.md). Distinct from evaluate_admission_gate()
# above on purpose:
#
#   - evaluate_admission_gate() is CLEAR-by-default (an absent row is not
#     a negative finding) -- correct for the existing
#     already-admitted-record / legacy-import non-regression path.
#   - evaluate_soc_gate() is the opposite: it is the actual point where
#     "referral / intake / documents / insurance ID / eligibility queue
#     / transfer intake must never block, but SOC entry / admission
#     activation / certification setup / episode activation must" is
#     enforced (BenefitPeriodWorkflow.md "hard gate" section). A patient
#     with NO determination row at all is exactly the case that must be
#     blocked here, because it means staff have not yet documented
#     anything -- the opposite of the other gate's semantics.
#
# This function is read-only and side-effect free; callers decide what
# to do with a non-CLEAR result (e.g. AdmissionGuardrailService.
# set_soc_datetime raises AdmissionPrerequisiteError with the exact
# required message text).
# ---------------------------------------------------------------------

SOC_GATE_BLOCKER_MESSAGE = "Benefit Period Documentation Required Before SOC Activation"


@dataclass(frozen=True)
class SocGateResult:
    ready: bool
    blockers: list[str] = field(default_factory=list)
    benefit_period_determination_id: Optional[str] = None


def evaluate_soc_gate(
    db: Session, *, tenant_id: str, patient_id: str
) -> SocGateResult:
    """
    The actual SOC/admission-activation hard gate. Requires a resolved
    BenefitPeriodDetermination row to exist with Starting Cert and
    Benefit Period documented, and -- only when
    admit_type == "TRANSFER_FROM_ANOTHER_HOSPICE" -- Transfer Source and
    Transfer Evidence documented too (AdmissionTypesWorkflow.md SOC gate
    summary table). Never computes any of these values itself.
    """
    determination = get_latest_benefit_period_determination(
        db, tenant_id=tenant_id, patient_id=patient_id
    )

    if determination is None:
        return SocGateResult(ready=False, blockers=[SOC_GATE_BLOCKER_MESSAGE])

    blockers: list[str] = []

    if determination.determination_status not in BENEFIT_PERIOD_REVIEW_RESOLVED_STATUSES:
        blockers.append(SOC_GATE_BLOCKER_MESSAGE)

    if determination.starting_cert is None:
        blockers.append(SOC_GATE_BLOCKER_MESSAGE)

    if determination.admit_type == "TRANSFER_FROM_ANOTHER_HOSPICE":
        if not determination.transfer_source:
            blockers.append(SOC_GATE_BLOCKER_MESSAGE)
        if not determination.transfer_evidence_document_id:
            blockers.append(SOC_GATE_BLOCKER_MESSAGE)

    # De-duplicate while preserving order -- several checks above can add
    # the same shared message text.
    deduped_blockers = list(dict.fromkeys(blockers))

    return SocGateResult(
        ready=not deduped_blockers,
        blockers=deduped_blockers,
        benefit_period_determination_id=str(determination.id),
    )


# =========================================================
# SHARED AUDIT TRAIL -- reuses ReadinessWorkflowEvent (Sprint 2
# Deliverable 9 / Directive item 18), never a parallel/competing
# mechanism. entity_type values below are new additions to the same
# table readiness_workflow_service.py already writes ASSIGNMENT/
# FOLLOW_UP/BLOCKER events to.
# =========================================================

# ELIGIBILITY_DOCUMENT | ELIGIBILITY_VERIFICATION |
# BENEFIT_PERIOD_DETERMINATION | BILLER_NOTE | BILLER_ESCALATION
ELIGIBILITY_WORKFLOW_ENTITY_TYPES = {
    "ELIGIBILITY_DOCUMENT",
    "ELIGIBILITY_VERIFICATION",
    "BENEFIT_PERIOD_DETERMINATION",
    "BILLER_NOTE",
    "BILLER_ESCALATION",
}


def record_eligibility_workflow_event(
    db: Session,
    *,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    actor_user_id: str,
    reason: Optional[str] = None,
    previous_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> ReadinessWorkflowEvent:
    """
    Every eligibility/benefit-period/biller-action state change writes
    exactly one of these -- timestamp, actor, previous value, new value,
    and reason are all captured by the shared ReadinessWorkflowEvent
    schema (Deliverable 9), same as blocker/assignment/follow-up events.
    """
    if entity_type not in ELIGIBILITY_WORKFLOW_ENTITY_TYPES:
        raise ValueError(f"Unknown eligibility workflow entity_type: {entity_type!r}")

    event = ReadinessWorkflowEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value=new_value or {},
    )
    db.add(event)
    db.flush()
    return event


# =========================================================
# PHASE D -- RN REVIEW ACTIONS
# =========================================================

# Every action creates a NEW BenefitPeriodDetermination row that
# supersedes the current one (append-only, matching
# record_benefit_period_determination's existing invariant) -- an RN
# action never mutates a prior determination in place.
RN_REVIEW_ACTIONS = {
    "APPROVE_DETERMINATION",
    "REJECT_DETERMINATION",
    "REQUEST_CLARIFICATION",
    "UPDATE_BENEFIT_PERIOD",
    "MARK_F2F_REQUIRED",
    "MARK_F2F_NOT_REQUIRED",
    "PLACE_ADMISSION_HOLD",
    "RELEASE_ADMISSION_HOLD",
}

# The resulting determination_status for actions that change it. Actions
# not listed here (the two F2F actions) keep the current determination's
# status and only change face_to_face_applicability.
_RN_ACTION_STATUS = {
    "APPROVE_DETERMINATION": "BENEFIT_PERIOD_CONFIRMED",
    "REJECT_DETERMINATION": "CONFLICT_REQUIRES_REVIEW",
    "REQUEST_CLARIFICATION": "INFORMATION_INCOMPLETE",
    "UPDATE_BENEFIT_PERIOD": "BENEFIT_PERIOD_CONFIRMED",
    "PLACE_ADMISSION_HOLD": "CONFLICT_REQUIRES_REVIEW",
    "RELEASE_ADMISSION_HOLD": "BENEFIT_PERIOD_CONFIRMED",
}


def apply_rn_review_action(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    action: str,
    actor_user_id: str,
    reason: str,
    anticipated_benefit_period_number: int | None = None,
    anticipated_period_start_date: date | None = None,
    anticipated_period_end_date: date | None = None,
) -> BenefitPeriodDetermination:
    """
    Phase D. Every allowed RN action (approve/reject/request
    clarification/update benefit period/mark F2F required-or-not/place
    or release an admission hold) is implemented as a new, superseding
    BenefitPeriodDetermination row -- "place admission hold" and "reject
    determination" both resolve to CONFLICT_REQUIRES_REVIEW (an
    unresolved status the admission gate already treats as blocking,
    Phase 4), and "release admission hold"/"approve determination" both
    resolve to BENEFIT_PERIOD_CONFIRMED (gate-clearing) -- there is
    deliberately no separate "hold" state machine bolted on top of the
    existing determination_status domain (Directive item 2: never
    invent a competing status domain).

    `reason` is required for every action (Directive: "Every action
    requires: user, timestamp, reason, audit event.").
    """
    if action not in RN_REVIEW_ACTIONS:
        raise ValueError(f"Unknown RN review action: {action!r}")
    if not reason or not reason.strip():
        raise ValueError("reason is required for every RN review action")

    prior = get_latest_benefit_period_determination(
        db, tenant_id=tenant_id, patient_id=patient_id
    )

    new_status = _RN_ACTION_STATUS.get(
        action, prior.determination_status if prior else "REVIEW_IN_PROGRESS"
    )

    face_to_face_applicability = prior.face_to_face_applicability if prior else None
    if action == "MARK_F2F_REQUIRED":
        face_to_face_applicability = True
    elif action == "MARK_F2F_NOT_REQUIRED":
        face_to_face_applicability = False

    resolved_period_number = (
        anticipated_benefit_period_number
        if anticipated_benefit_period_number is not None
        else (prior.anticipated_benefit_period_number if prior else None)
    )
    resolved_period_start = (
        anticipated_period_start_date
        if anticipated_period_start_date is not None
        else (prior.anticipated_period_start_date if prior else None)
    )
    resolved_period_end = (
        anticipated_period_end_date
        if anticipated_period_end_date is not None
        else (prior.anticipated_period_end_date if prior else None)
    )

    previous_value = (
        {
            "determination_status": prior.determination_status,
            "face_to_face_applicability": prior.face_to_face_applicability,
            "anticipated_benefit_period_number": prior.anticipated_benefit_period_number,
        }
        if prior is not None
        else None
    )

    determination = record_benefit_period_determination(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        determination_status=new_status,
        admission_id=prior.admission_id if prior else None,
        eligibility_verification_id=prior.eligibility_verification_id if prior else None,
        source_document_id=prior.source_document_id if prior else None,
        prior_hospice_episode_count=prior.prior_hospice_episode_count if prior else None,
        benefit_periods_used=prior.benefit_periods_used if prior else None,
        anticipated_benefit_period_number=resolved_period_number,
        anticipated_period_start_date=resolved_period_start,
        anticipated_period_end_date=resolved_period_end,
        face_to_face_applicability=face_to_face_applicability,
        determined_by_user_id=actor_user_id,
        review_notes=reason,
        conflict_reason=reason if new_status == "CONFLICT_REQUIRES_REVIEW" else None,
        supersedes_determination_id=str(prior.id) if prior else None,
    )

    record_eligibility_workflow_event(
        db,
        tenant_id=tenant_id,
        entity_type="BENEFIT_PERIOD_DETERMINATION",
        entity_id=str(determination.id),
        event_type=action,
        actor_user_id=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value={
            "determination_status": determination.determination_status,
            "face_to_face_applicability": determination.face_to_face_applicability,
            "anticipated_benefit_period_number": determination.anticipated_benefit_period_number,
        },
    )
    db.commit()

    return determination
