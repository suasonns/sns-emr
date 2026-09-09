# backend/app/billing/services/readiness_dashboard_service.py
"""
Sprint 2 -- Billing Readiness Operational Workflow: dashboard, queue, and
history read-models (Deliverables 1, 6, 7).

Every function here is read-mostly and layers strictly on top of what
Sprint 1 + Phase 1 of Sprint 2 already persist:
  - BillingReadinessVerdict (Sprint 1) -- immutable evaluation history.
  - BenefitPeriodStatusEvent (Sprint 1) -- benefit period lifecycle audit.
  - BillingBlockerRecord / ReadinessAssignment / ReadinessFollowUp /
    ReadinessWorkflowEvent (Sprint 2 Phase 1).

build_tenant_readiness_dashboard() is the only function that also *writes*
anything, and only because it calls
build_tenant_billing_readiness_report() (Sprint 1, unchanged) to get a
fresh verdict for every ACTIVE patient -- exactly the same side effect
that endpoint already has today.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.billing.models.billing_blocker_record import BillingBlockerRecord
from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict
from app.billing.models.benefit_period_determination import BenefitPeriodDetermination
from app.billing.models.eligibility_source_document import EligibilitySourceDocument
from app.billing.models.eligibility_verification import EligibilityVerification
from app.billing.models.readiness_assignment import ReadinessAssignment
from app.billing.models.readiness_follow_up import ReadinessFollowUp
from app.billing.models.readiness_workflow_event import ReadinessWorkflowEvent
from app.billing.services.billing_readiness_service import (
    build_tenant_billing_readiness_report,
)
from app.billing.services.readiness_workflow_service import (
    compute_operational_bucket,
    derive_readiness_status,
)

TREND_WINDOW_DAYS = 14
RECENT_EVALUATIONS_LIMIT = 20
RECENTLY_CHANGED_LIMIT = 20


# =========================================================
# DASHBOARD (Deliverable 1)
# =========================================================

def _open_blocked_patient_ids(db: Session, *, tenant_id: str) -> set[str]:
    rows = (
        db.query(ReadinessFollowUp.patient_id)
        .filter(
            ReadinessFollowUp.tenant_id == tenant_id,
            ReadinessFollowUp.status == "BLOCKED",
        )
        .all()
    )
    return {str(r[0]) for r in rows}


def build_tenant_readiness_dashboard(
    db: Session, *, tenant_id: str, service_date: date
) -> dict:
    """
    Runs the same evaluation build_tenant_billing_readiness_report() runs
    (persisting a fresh verdict per ACTIVE patient, exactly as it already
    does), then layers the operational 4-bucket rollup, attention list,
    recent-change feed, recent evaluations, and a historical trend on top.
    """
    report = build_tenant_billing_readiness_report(
        db, tenant_id=tenant_id, service_date=service_date
    )

    blocked_patient_ids = _open_blocked_patient_ids(db, tenant_id=tenant_id)

    counts = {"READY": 0, "AT_RISK": 0, "NOT_READY": 0, "BLOCKED": 0}
    attention: list[dict] = []

    for patient in report["patients"]:
        readiness_status = derive_readiness_status(
            blockers=patient["blockers"], warnings=patient["warnings"]
        )
        bucket = compute_operational_bucket(
            readiness_status=readiness_status,
            has_open_blocked_follow_up=patient["patient_id"] in blocked_patient_ids,
        )
        counts[bucket] += 1

        if bucket != "READY":
            attention.append(
                {
                    "patient_id": patient["patient_id"],
                    "mrn": patient["mrn"],
                    "readiness_status": readiness_status,
                    "operational_bucket": bucket,
                    "blocker_count": len(patient["blockers"]),
                    "warning_count": len(patient["warnings"]),
                }
            )

    recently_changed = _recently_changed_status(db, tenant_id=tenant_id)
    recent_evaluations = _recent_evaluations(db, tenant_id=tenant_id)
    trend = _readiness_trend(db, tenant_id=tenant_id)

    return {
        "tenant_id": tenant_id,
        "service_date": service_date.isoformat(),
        "counts": counts,
        "patients_requiring_attention": attention,
        "recently_changed_status": recently_changed,
        "recent_evaluations": recent_evaluations,
        "readiness_trend": trend,
    }


def _mrn_lookup(db: Session, *, patient_ids: list[str]) -> dict[str, str]:
    """
    Batched patient_id -> MRN lookup shared by the recent-evaluations and
    recently-changed-status feeds so neither ever surfaces a raw UUID as
    the user-facing patient label (Directive Phase 9).
    """
    if not patient_ids:
        return {}
    rows = db.execute(
        text("SELECT id::text AS id, mrn FROM patients WHERE id = ANY(:ids)"),
        {"ids": [uuid.UUID(pid) for pid in patient_ids]},
    ).mappings().all()
    return {row["id"]: row["mrn"] for row in rows}


def _recent_evaluations(db: Session, *, tenant_id: str) -> list[dict]:
    verdicts = (
        db.query(BillingReadinessVerdict)
        .filter(BillingReadinessVerdict.tenant_id == tenant_id)
        .order_by(BillingReadinessVerdict.evaluated_at.desc())
        .limit(RECENT_EVALUATIONS_LIMIT)
        .all()
    )
    mrn_by_patient = _mrn_lookup(db, patient_ids=[str(v.patient_id) for v in verdicts])
    return [
        {
            "patient_id": str(v.patient_id),
            "mrn": mrn_by_patient.get(str(v.patient_id), ""),
            "evaluated_at": v.evaluated_at.isoformat(),
            "readiness_status": derive_readiness_status(
                blockers=list(v.blockers or []), warnings=list(v.warnings or [])
            ),
            "triggered_by": v.triggered_by,
        }
        for v in verdicts
    ]


def _recently_changed_status(db: Session, *, tenant_id: str) -> list[dict]:
    """
    Looks at up to the last 200 verdicts tenant-wide, keeps only the two
    most recent per patient, and reports every patient whose current
    readiness_status differs from their immediately prior one -- capped
    to RECENTLY_CHANGED_LIMIT, most-recent-change first.
    """
    verdicts = (
        db.query(BillingReadinessVerdict)
        .filter(BillingReadinessVerdict.tenant_id == tenant_id)
        .order_by(BillingReadinessVerdict.evaluated_at.desc())
        .limit(200)
        .all()
    )

    by_patient: dict[str, list[BillingReadinessVerdict]] = defaultdict(list)
    for v in verdicts:
        by_patient[str(v.patient_id)].append(v)

    mrn_by_patient = _mrn_lookup(db, patient_ids=list(by_patient.keys()))

    changes: list[dict] = []
    for patient_id, patient_verdicts in by_patient.items():
        if len(patient_verdicts) < 2:
            continue

        current, previous = patient_verdicts[0], patient_verdicts[1]
        current_status = derive_readiness_status(
            blockers=list(current.blockers or []), warnings=list(current.warnings or [])
        )
        previous_status = derive_readiness_status(
            blockers=list(previous.blockers or []), warnings=list(previous.warnings or [])
        )

        if current_status != previous_status:
            changes.append(
                {
                    "patient_id": patient_id,
                    "mrn": mrn_by_patient.get(patient_id, ""),
                    "previous_status": previous_status,
                    "new_status": current_status,
                    "changed_at": current.evaluated_at.isoformat(),
                }
            )

    changes.sort(key=lambda c: c["changed_at"], reverse=True)
    return changes[:RECENTLY_CHANGED_LIMIT]


def _readiness_trend(db: Session, *, tenant_id: str) -> list[dict]:
    """
    One row per calendar day for the last TREND_WINDOW_DAYS days: counts
    of each patient's LATEST verdict that day, classified by
    derive_readiness_status. A patient with no evaluation on a given day
    contributes nothing to that day's row (this is a trend of evaluation
    outcomes, not a patient census).
    """
    window_start = datetime.now(timezone.utc) - timedelta(days=TREND_WINDOW_DAYS)

    verdicts = (
        db.query(BillingReadinessVerdict)
        .filter(
            BillingReadinessVerdict.tenant_id == tenant_id,
            BillingReadinessVerdict.evaluated_at >= window_start,
        )
        .order_by(BillingReadinessVerdict.evaluated_at.asc())
        .all()
    )

    # Keep only the latest verdict per (patient, calendar day).
    latest_per_patient_day: dict[tuple[str, str], BillingReadinessVerdict] = {}
    for v in verdicts:
        day_key = v.evaluated_at.date().isoformat()
        latest_per_patient_day[(str(v.patient_id), day_key)] = v

    day_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"READY": 0, "AT_RISK": 0, "NOT_READY": 0}
    )
    for (_, day_key), v in latest_per_patient_day.items():
        status = derive_readiness_status(
            blockers=list(v.blockers or []), warnings=list(v.warnings or [])
        )
        day_counts[day_key][status] += 1

    return [
        {
            "service_date": day_key,
            "ready_count": counts["READY"],
            "at_risk_count": counts["AT_RISK"],
            "not_ready_count": counts["NOT_READY"],
        }
        for day_key, counts in sorted(day_counts.items())
    ]


# =========================================================
# OPERATIONAL QUEUE (Deliverable 7)
# =========================================================

def build_readiness_queue(
    db: Session,
    *,
    tenant_id: str,
    status_filter: Optional[str] = None,
    assignment_status_filter: Optional[str] = None,
    due_filter: Optional[str] = None,
) -> list[dict]:
    """
    Reads the latest verdict per patient (no new evaluation is run here --
    this is a pure read view over what has already been persisted, unlike
    the dashboard which re-evaluates), joined with the patient's current
    assignment/follow-up rows, and filtered per the query params.

    due_filter: "SOON" (due within 3 days, inclusive, not yet resolved) or
    "OVERDUE" (due date in the past, not yet resolved).
    """
    latest_verdict_rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (patient_id)
                id, patient_id, blockers, warnings, evaluated_at
            FROM billing_readiness_verdicts
            WHERE tenant_id = :tenant_id
            ORDER BY patient_id, evaluated_at DESC
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()

    patient_ids = [str(row["patient_id"]) for row in latest_verdict_rows]
    if not patient_ids:
        return []

    mrn_rows = db.execute(
        text("SELECT id::text AS id, mrn FROM patients WHERE id = ANY(:ids)"),
        {"ids": [uuid.UUID(pid) for pid in patient_ids]},
    ).mappings().all()
    mrn_by_patient = {row["id"]: row["mrn"] for row in mrn_rows}

    assignments = {
        str(a.patient_id): a
        for a in db.query(ReadinessAssignment)
        .filter(ReadinessAssignment.tenant_id == tenant_id)
        .all()
    }
    follow_ups = defaultdict(list)
    for f in (
        db.query(ReadinessFollowUp)
        .filter(ReadinessFollowUp.tenant_id == tenant_id)
        .all()
    ):
        follow_ups[str(f.patient_id)].append(f)

    today = date.today()
    soon_cutoff = today + timedelta(days=3)

    results: list[dict] = []
    for row in latest_verdict_rows:
        patient_id = str(row["patient_id"])
        blockers = list(row["blockers"] or [])
        warnings = list(row["warnings"] or [])
        readiness_status = derive_readiness_status(blockers=blockers, warnings=warnings)

        patient_follow_ups = follow_ups.get(patient_id, [])
        open_blocked = any(f.status == "BLOCKED" for f in patient_follow_ups)
        bucket = compute_operational_bucket(
            readiness_status=readiness_status, has_open_blocked_follow_up=open_blocked
        )

        if status_filter and bucket != status_filter:
            continue

        assignment = assignments.get(patient_id)
        assignment_status = assignment.assignment_status if assignment else "UNASSIGNED"
        if assignment_status_filter and assignment_status != assignment_status_filter:
            continue

        open_follow_ups = [f for f in patient_follow_ups if f.status in ("OPEN", "IN_PROGRESS", "BLOCKED")]
        due_dates = [f.due_date for f in open_follow_ups if f.due_date is not None]

        if due_filter == "OVERDUE" and not any(d < today for d in due_dates):
            continue
        if due_filter == "SOON" and not any(today <= d <= soon_cutoff for d in due_dates):
            continue

        results.append(
            {
                "patient_id": patient_id,
                "mrn": mrn_by_patient.get(patient_id, ""),
                "readiness_status": readiness_status,
                "operational_bucket": bucket,
                "blockers": blockers,
                "warnings": warnings,
                "assignment_status": assignment_status,
                "assigned_user_id": str(assignment.assigned_user_id) if assignment and assignment.assigned_user_id else None,
                "assigned_role": assignment.assigned_role if assignment else None,
                "open_follow_up_count": len(open_follow_ups),
                "earliest_due_date": min(due_dates).isoformat() if due_dates else None,
            }
        )

    return results


# =========================================================
# READINESS HISTORY (Deliverable 6, read-only)
# =========================================================

def build_readiness_history(db: Session, *, tenant_id: str, patient_id: str) -> dict:
    verdicts = (
        db.query(BillingReadinessVerdict)
        .filter(
            BillingReadinessVerdict.tenant_id == tenant_id,
            BillingReadinessVerdict.patient_id == patient_id,
        )
        .order_by(BillingReadinessVerdict.evaluated_at.desc())
        .all()
    )

    blocker_records = (
        db.query(BillingBlockerRecord)
        .filter(
            BillingBlockerRecord.tenant_id == tenant_id,
            BillingBlockerRecord.patient_id == patient_id,
        )
        .order_by(BillingBlockerRecord.first_seen_at.desc())
        .all()
    )

    blocker_ids = [b.id for b in blocker_records]
    assignment_ids = [
        a.id
        for a in db.query(ReadinessAssignment)
        .filter(
            ReadinessAssignment.tenant_id == tenant_id,
            ReadinessAssignment.patient_id == patient_id,
        )
        .all()
    ]
    follow_up_ids = [
        f.id
        for f in db.query(ReadinessFollowUp)
        .filter(
            ReadinessFollowUp.tenant_id == tenant_id,
            ReadinessFollowUp.patient_id == patient_id,
        )
        .all()
    ]

    entity_ids = blocker_ids + assignment_ids + follow_up_ids

    # Phases A-E: eligibility documents, verifications, and benefit-period
    # determinations also write ReadinessWorkflowEvent rows (see
    # eligibility_workflow_service.record_eligibility_workflow_event) --
    # folded additively into the same audit_trail here so the Eligibility
    # Workspace's Audit History tab and the Readiness History view share
    # one query, never a parallel audit read-path.
    eligibility_document_ids = [
        d.id
        for d in db.query(EligibilitySourceDocument)
        .filter(
            EligibilitySourceDocument.tenant_id == tenant_id,
            EligibilitySourceDocument.patient_id == patient_id,
        )
        .all()
    ]
    eligibility_verification_ids = [
        v.id
        for v in db.query(EligibilityVerification)
        .filter(
            EligibilityVerification.tenant_id == tenant_id,
            EligibilityVerification.patient_id == patient_id,
        )
        .all()
    ]
    benefit_period_determination_ids = [
        b.id
        for b in db.query(BenefitPeriodDetermination)
        .filter(
            BenefitPeriodDetermination.tenant_id == tenant_id,
            BenefitPeriodDetermination.patient_id == patient_id,
        )
        .all()
    ]
    entity_ids = (
        entity_ids
        + eligibility_document_ids
        + eligibility_verification_ids
        + benefit_period_determination_ids
        # BILLER_NOTE / BILLER_ESCALATION events have no dedicated table --
        # they use patient_id itself as entity_id.
        + [patient_id]
    )
    events = (
        db.query(ReadinessWorkflowEvent)
        .filter(ReadinessWorkflowEvent.entity_id.in_(entity_ids))
        .order_by(ReadinessWorkflowEvent.occurred_at.desc())
        .all()
        if entity_ids
        else []
    )

    return {
        "patient_id": patient_id,
        "verdicts": [
            {
                "id": str(v.id),
                "evaluated_at": v.evaluated_at.isoformat(),
                "is_ready": v.is_ready,
                "readiness_status": derive_readiness_status(
                    blockers=list(v.blockers or []), warnings=list(v.warnings or [])
                ),
                "blockers": list(v.blockers or []),
                "warnings": list(v.warnings or []),
                "triggered_by": v.triggered_by,
            }
            for v in verdicts
        ],
        "blocker_history": [
            {
                "id": str(b.id),
                "blocker_code": b.blocker_code,
                "message": b.message,
                "status": b.status,
                "first_seen_at": b.first_seen_at.isoformat(),
                "last_seen_at": b.last_seen_at.isoformat(),
                "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
                "resolved_by": b.resolved_by,
                "resolution_reason": b.resolution_reason,
            }
            for b in blocker_records
        ],
        "audit_trail": [
            {
                "id": str(e.id),
                "entity_type": e.entity_type,
                "entity_id": str(e.entity_id),
                "event_type": e.event_type,
                "actor_user_id": str(e.actor_user_id) if e.actor_user_id else None,
                "occurred_at": e.occurred_at.isoformat(),
                "reason": e.reason,
                "previous_value": e.previous_value,
                "new_value": e.new_value,
                "related_verdict_id": str(e.related_verdict_id) if e.related_verdict_id else None,
            }
            for e in events
        ],
    }
