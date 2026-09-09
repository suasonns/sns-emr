# backend/app/billing/services/readiness_workflow_service.py
"""
Sprint 2 -- Billing Readiness Operational Workflow.

Builds the operational triage layer on top of Sprint 1's persistence
foundation (BillingReadinessVerdict, BenefitPeriodStatusEvent) without
touching any of it: this module only ever *reads*
`check_patient_billing_readiness()` output and the verdict it already
persists, then derives/records purely additive workflow state.

Responsibilities:
  - derive_readiness_status(): the READY/AT_RISK/NOT_READY derivation
    rule (Deliverable 2).
  - classify_blocker_code(): typed blocker taxonomy mapping
    (Deliverable 3).
  - sync_blocker_records(): maintains the per-blocker lifecycle overlay
    in billing_blocker_records after each verdict is persisted.
  - Assignment / follow-up create-or-update helpers (Deliverables 4/5),
    each of which writes exactly one ReadinessWorkflowEvent
    (Deliverable 9) describing the transition.
  - resolve_blocker_manually(): staff-initiated early resolution.
  - compute_operational_bucket(): the dashboard's 4-bucket rollup
    (READY / AT_RISK / NOT_READY / BLOCKED), where BLOCKED is the
    operational overlay described in docs/planning -- a NOT_READY
    patient with an open follow-up explicitly marked BLOCKED by staff,
    never inferred automatically.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from app.billing.models.billing_blocker_record import (
    BLOCKER_CODES,
    SYSTEM_AUTO_RESOLVED_BY,
    BillingBlockerRecord,
)
from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict
from app.billing.models.readiness_assignment import (
    ASSIGNMENT_STATUSES,
    ReadinessAssignment,
)
from app.billing.models.readiness_follow_up import (
    FOLLOW_UP_STATUSES,
    ReadinessFollowUp,
)
from app.billing.models.readiness_workflow_event import ReadinessWorkflowEvent

ReadinessStatus = Literal["READY", "AT_RISK", "NOT_READY"]
OperationalBucket = Literal["READY", "AT_RISK", "NOT_READY", "BLOCKED"]


# =========================================================
# DELIVERABLE 2 -- READINESS STATUS DERIVATION
# =========================================================

def derive_readiness_status(
    *, blockers: list[str], warnings: list[str]
) -> ReadinessStatus:
    """
    Pure derivation from the exact blockers/warnings a
    BillingReadinessVerdict already persisted -- no new inputs, no manual
    override. See docs/planning/eligibility_traceability_epic.md Sprint 2
    design note for the rationale.

        NOT_READY -- len(blockers) > 0 (regardless of warnings)
        AT_RISK   -- len(blockers) == 0 and len(warnings) > 0
        READY     -- neither
    """
    if blockers:
        return "NOT_READY"
    if warnings:
        return "AT_RISK"
    return "READY"


def readiness_status_for_verdict(verdict: BillingReadinessVerdict) -> ReadinessStatus:
    return derive_readiness_status(
        blockers=list(verdict.blockers or []),
        warnings=list(verdict.warnings or []),
    )


# =========================================================
# DELIVERABLE 3 -- TYPED BLOCKER TAXONOMY
# =========================================================

# Extends app.billing.services.billing_readiness_service.BLOCKER_CATEGORY_PREFIXES
# additively with the typed BlockerCode enum. Same prefix-match approach,
# same OTHER fallback so no blocker is ever dropped or crashes the
# mapper when a future blocker string doesn't match a known prefix yet.
# Extends app.billing.services.billing_readiness_service.BLOCKER_CATEGORY_PREFIXES
# additively with the typed BlockerCode enum. Same prefix-match approach,
# same OTHER fallback so no blocker is ever dropped or crashes the
# mapper when a future blocker string doesn't match a known prefix yet.
#
# Corrected taxonomy (Eligibility/Admission/Benefit-Period/Billing-
# Readiness Workflow Correction directive, item 10): billing blockers now
# primarily represent post-admission claim-preparation issues. Each entry
# also carries the "workflow owner category" (INTAKE / RN / BILLER /
# SYSTEM) responsible for resolving that category of blocker.
BLOCKER_CODE_PREFIXES: list[tuple[str, str, str]] = [
    # (prefix, blocker_code, workflow_owner_category)
    ("Patient status is", "OTHER", "BILLER"),
    (
        "Benefit-period information required for this admitted record",
        "BENEFIT_PERIOD_REVIEW_REQUIRED",
        "BILLER",
    ),
    (
        "Benefit-period information for this admitted record requires review",
        "BENEFIT_PERIOD_REVIEW_REQUIRED",
        "BILLER",
    ),
    (
        "No benefit period covers",
        "BENEFIT_PERIOD_REVIEW_REQUIRED",
        "BILLER",
    ),
    (
        "Payer eligibility for this admitted record requires re-verification",
        "ELIGIBILITY_REVERIFICATION_REQUIRED",
        "BILLER",
    ),
    ("Hospice election statement is not signed", "SERVICE_DOCUMENTATION_INCOMPLETE", "RN"),
    ("Notice of Election (NOE) has not been filed", "NOE_NOT_ACCEPTED", "BILLER"),
    ("Certification of Terminal Illness", "CERTIFICATION_NOT_COMPLETE", "RN"),
    ("Required face-to-face encounter", "FACE_TO_FACE_DOCUMENTATION_REQUIRED", "RN"),
    ("Plan of Care is not active", "REQUIRED_SIGNATURE_MISSING", "RN"),
    ("Payer sequence is ambiguous", "MSP_REVIEW_REQUIRED", "BILLER"),
    ("Patient not found", "OTHER", "BILLER"),
]

# Human-readable label for each blocker code -- the frontend/API layer
# must never display a raw enum name to users (Directive item 10, last
# line). Falls back to a titleized version of the code itself for any
# code not explicitly listed (e.g. a historical Sprint-2-era code).
BLOCKER_CODE_DISPLAY_LABELS: dict[str, str] = {
    "ELIGIBILITY_REVERIFICATION_REQUIRED": "Eligibility reverification required",
    "PAYER_ROUTING_CONFLICT": "Payer routing conflict",
    "MEDICARE_ADVANTAGE_REVIEW_REQUIRED": "Medicare Advantage review required",
    "MSP_REVIEW_REQUIRED": "MSP / payer sequencing review required",
    "ACTIVE_HOSPICE_OVERLAP": "Active hospice overlap",
    "ACTIVE_HOME_HEALTH_OVERLAP_REVIEW": "Home health overlap review required",
    "NOE_NOT_ACCEPTED": "Notice of Election not accepted",
    "CERTIFICATION_NOT_COMPLETE": "Certification not complete",
    "RECERTIFICATION_NOT_COMPLETE": "Recertification not complete",
    "FACE_TO_FACE_DOCUMENTATION_REQUIRED": "Face-to-face documentation required",
    "REQUIRED_SIGNATURE_MISSING": "Required signature missing",
    "SERVICE_DOCUMENTATION_INCOMPLETE": "Service documentation incomplete",
    "LEVEL_OF_CARE_DATA_INCOMPLETE": "Level of care data incomplete",
    "CLAIM_VALIDATION_ERROR": "Claim validation error",
    "BENEFIT_PERIOD_REVIEW_REQUIRED": "Benefit period review required",
    "OTHER": "Other",
    # Historical Sprint-2 codes, still readable if they appear on an
    # older persisted row.
    "MISSING_CERTIFICATION": "Certification missing",
    "MISSING_FACE_TO_FACE": "Face-to-face documentation missing",
    "MISSING_PHYSICIAN_SIGNATURE": "Physician signature missing",
    "MISSING_DOCUMENTATION": "Documentation missing",
    "BENEFIT_PERIOD_ISSUE": "Benefit period issue",
}


def classify_blocker_code(blocker: str) -> str:
    """
    Maps a raw blocker string to one of BLOCKER_CODES. Falls back to
    "OTHER" for any blocker text that doesn't match a known prefix,
    matching the existing categorize_blocker() fallback behavior.
    """
    for prefix, code, _owner in BLOCKER_CODE_PREFIXES:
        if blocker.startswith(prefix):
            return code
    return "OTHER"


def classify_blocker_owner_category(blocker: str) -> str:
    """
    Companion to classify_blocker_code(): which operational role is
    expected to resolve this category of blocker (Directive item 10,
    "workflow owner category"). Defaults to BILLER, matching the
    directive's framing that billing-readiness blockers primarily
    represent post-admission claim-preparation issues.
    """
    for prefix, _code, owner in BLOCKER_CODE_PREFIXES:
        if blocker.startswith(prefix):
            return owner
    return "BILLER"


def blocker_display_label(blocker_code: str) -> str:
    """Human-readable label for a blocker_code -- never show the raw enum."""
    return BLOCKER_CODE_DISPLAY_LABELS.get(
        blocker_code, blocker_code.replace("_", " ").title()
    )


# =========================================================
# DELIVERABLE 3 -- BLOCKER LIFECYCLE SYNC
# =========================================================

def sync_blocker_records(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    verdict: BillingReadinessVerdict,
) -> list[BillingBlockerRecord]:
    """
    Called once per persisted BillingReadinessVerdict. Opens a new
    BillingBlockerRecord for every blocker string in this verdict that
    doesn't already have an OPEN record for this patient, bumps
    last_seen_verdict_id/last_seen_at on ones that are still present, and
    auto-resolves any previously-OPEN record whose exact message is no
    longer present in this verdict (the underlying issue stopped
    appearing, so treat it as SYSTEM_AUTO_RESOLVED_BY without requiring
    a human to act). Matching is by exact message text -- a raw blocker
    string is a stable, deterministic label for a given issue, so no
    fuzzy matching is needed.
    """
    current_messages = list(verdict.blockers or [])

    open_records = (
        db.query(BillingBlockerRecord)
        .filter(
            BillingBlockerRecord.patient_id == patient_id,
            BillingBlockerRecord.status == "OPEN",
        )
        .all()
    )
    open_by_message = {record.message: record for record in open_records}

    touched: list[BillingBlockerRecord] = []

    for message in current_messages:
        existing = open_by_message.pop(message, None)
        if existing is not None:
            existing.last_seen_verdict_id = verdict.id
            existing.last_seen_at = verdict.evaluated_at
            touched.append(existing)
            continue

        record = BillingBlockerRecord(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            blocker_code=classify_blocker_code(message),
            workflow_owner_category=classify_blocker_owner_category(message),
            message=message,
            first_seen_verdict_id=verdict.id,
            last_seen_verdict_id=verdict.id,
            first_seen_at=verdict.evaluated_at,
            last_seen_at=verdict.evaluated_at,
            status="OPEN",
        )
        db.add(record)
        touched.append(record)

    # Anything still left in open_by_message stopped appearing in this
    # verdict -- auto-resolve it.
    for stale_record in open_by_message.values():
        previous_value = {"status": stale_record.status, "resolved_by": stale_record.resolved_by}

        stale_record.status = "RESOLVED"
        stale_record.resolved_at = verdict.evaluated_at
        stale_record.resolved_by = SYSTEM_AUTO_RESOLVED_BY
        stale_record.resolution_reason = (
            "Blocker no longer present on the most recent readiness evaluation."
        )
        touched.append(stale_record)

        db.flush()

        _record_workflow_event(
            db,
            tenant_id=stale_record.tenant_id,
            entity_type="BLOCKER",
            entity_id=stale_record.id,
            event_type="AUTO_RESOLVED",
            actor_user_id=None,
            reason=stale_record.resolution_reason,
            previous_value=previous_value,
            new_value={"status": stale_record.status, "resolved_by": stale_record.resolved_by},
            related_verdict_id=verdict.id,
        )

    db.commit()
    return touched


def resolve_blocker_manually(
    db: Session,
    *,
    blocker_id: str,
    actor_user_id: str,
    reason: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> BillingBlockerRecord:
    """
    Staff-initiated early resolution of an OPEN blocker (e.g. the biller
    confirms the underlying issue is fixed even though the next scheduled
    evaluation hasn't run yet to auto-resolve it). Audited via
    ReadinessWorkflowEvent.

    tenant_id, when given, scopes the lookup so a caller in one tenant
    can never resolve (or discover the existence of) another tenant's
    blocker record via a guessed/enumerated id.
    """
    query = db.query(BillingBlockerRecord).filter(
        BillingBlockerRecord.id == blocker_id
    )
    if tenant_id is not None:
        query = query.filter(BillingBlockerRecord.tenant_id == tenant_id)
    record = query.one()

    previous_value = {"status": record.status, "resolved_by": record.resolved_by}

    record.status = "RESOLVED"
    from datetime import datetime, timezone as _tz

    record.resolved_at = datetime.now(_tz.utc)
    record.resolved_by = str(actor_user_id)
    record.resolution_reason = reason

    db.flush()

    _record_workflow_event(
        db,
        tenant_id=record.tenant_id,
        entity_type="BLOCKER",
        entity_id=record.id,
        event_type="RESOLVED",
        actor_user_id=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value={"status": record.status, "resolved_by": record.resolved_by},
        related_verdict_id=record.last_seen_verdict_id,
    )

    db.commit()
    return record


# =========================================================
# DELIVERABLE 9 -- SHARED AUDIT HELPER
# =========================================================

def _record_workflow_event(
    db: Session,
    *,
    tenant_id: str,
    entity_type: str,
    entity_id: Any,
    event_type: str,
    actor_user_id: Optional[str],
    reason: Optional[str],
    previous_value: Optional[dict],
    new_value: dict,
    related_verdict_id: Optional[str],
) -> ReadinessWorkflowEvent:
    event = ReadinessWorkflowEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value=new_value,
        related_verdict_id=related_verdict_id,
    )
    db.add(event)
    db.flush()
    return event


# =========================================================
# DELIVERABLE 4 -- GENERIC ASSIGNMENT FRAMEWORK
# =========================================================

def upsert_assignment(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    actor_user_id: str,
    assigned_user_id: Optional[str] = None,
    assigned_role: Optional[str] = None,
    assignment_status: str = "ASSIGNED",
    assigned_date: Optional[date] = None,
    related_verdict_id: Optional[str] = None,
) -> ReadinessAssignment:
    """
    Creates the patient's assignment row if none exists yet, otherwise
    updates the existing one in place (one active assignment per patient
    at a time) -- every call writes exactly one ReadinessWorkflowEvent.
    """
    if assignment_status not in ASSIGNMENT_STATUSES:
        raise ValueError(f"assignment_status must be one of {sorted(ASSIGNMENT_STATUSES)}")

    assignment = (
        db.query(ReadinessAssignment)
        .filter(
            ReadinessAssignment.tenant_id == tenant_id,
            ReadinessAssignment.patient_id == patient_id,
        )
        .one_or_none()
    )

    previous_value = None
    event_type = "CREATED"

    if assignment is None:
        assignment = ReadinessAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
        )
        db.add(assignment)
    else:
        previous_value = {
            "assigned_user_id": str(assignment.assigned_user_id) if assignment.assigned_user_id else None,
            "assigned_role": assignment.assigned_role,
            "assignment_status": assignment.assignment_status,
        }
        event_type = "REASSIGNED" if assigned_user_id != str(assignment.assigned_user_id or "") else "STATUS_CHANGED"

    assignment.assigned_user_id = assigned_user_id
    assignment.assigned_role = assigned_role
    assignment.assigned_by = actor_user_id
    assignment.assigned_date = assigned_date or date.today()
    assignment.assignment_status = assignment_status

    db.flush()

    new_value = {
        "assigned_user_id": str(assignment.assigned_user_id) if assignment.assigned_user_id else None,
        "assigned_role": assignment.assigned_role,
        "assignment_status": assignment.assignment_status,
    }

    _record_workflow_event(
        db,
        tenant_id=tenant_id,
        entity_type="ASSIGNMENT",
        entity_id=assignment.id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        reason=None,
        previous_value=previous_value,
        new_value=new_value,
        related_verdict_id=related_verdict_id,
    )

    db.commit()
    return assignment


# =========================================================
# DELIVERABLE 5 -- FOLLOW-UP TRACKING
# =========================================================

def upsert_follow_up(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    actor_user_id: str,
    status: str = "OPEN",
    follow_up_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    follow_up_required: bool = True,
    due_date: Optional[date] = None,
    notes: Optional[str] = None,
    reason: Optional[str] = None,
    related_verdict_id: Optional[str] = None,
) -> ReadinessFollowUp:
    """
    Creates a new follow-up (follow_up_id omitted) or updates an existing
    one in place (follow_up_id given) -- every call writes exactly one
    ReadinessWorkflowEvent. Setting status to BLOCKED is the sole trigger
    for the dashboard/queue's "Blocked" bucket (see
    derive_readiness_status's docstring and compute_operational_bucket
    below) -- it is a deliberate, audited staff action, never inferred.
    """
    if status not in FOLLOW_UP_STATUSES:
        raise ValueError(f"status must be one of {sorted(FOLLOW_UP_STATUSES)}")

    previous_value = None
    event_type = "CREATED"

    if follow_up_id:
        query = db.query(ReadinessFollowUp).filter(
            ReadinessFollowUp.id == follow_up_id,
            ReadinessFollowUp.tenant_id == tenant_id,
        )
        follow_up = query.one()
        previous_value = {
            "status": follow_up.status,
            "due_date": follow_up.due_date.isoformat() if follow_up.due_date else None,
        }
        event_type = "STATUS_CHANGED"
    else:
        follow_up = ReadinessFollowUp(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            assignment_id=assignment_id,
            created_date=date.today(),
        )
        db.add(follow_up)

    follow_up.follow_up_required = follow_up_required
    follow_up.status = status
    follow_up.due_date = due_date
    follow_up.notes = notes
    if status == "RESOLVED" and follow_up.resolved_date is None:
        follow_up.resolved_date = date.today()
    if assignment_id is not None:
        follow_up.assignment_id = assignment_id

    db.flush()

    new_value = {
        "status": follow_up.status,
        "due_date": follow_up.due_date.isoformat() if follow_up.due_date else None,
    }

    _record_workflow_event(
        db,
        tenant_id=tenant_id,
        entity_type="FOLLOW_UP",
        entity_id=follow_up.id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value=new_value,
        related_verdict_id=related_verdict_id,
    )

    db.commit()
    return follow_up


# =========================================================
# DASHBOARD/QUEUE 4-BUCKET ROLLUP
# =========================================================

def compute_operational_bucket(
    *, readiness_status: ReadinessStatus, has_open_blocked_follow_up: bool
) -> OperationalBucket:
    """
    Rolls the pure, system-derived readiness_status up into the
    dashboard's 4th "Blocked" bucket: only a NOT_READY patient with an
    open follow-up explicitly set to BLOCKED counts as Blocked; every
    other NOT_READY patient still counts as Not Ready. READY/AT_RISK are
    never reclassified as Blocked.
    """
    if readiness_status == "NOT_READY" and has_open_blocked_follow_up:
        return "BLOCKED"
    return readiness_status
