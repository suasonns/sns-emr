"""
Billing readiness gate -- determines whether a patient's chart supports
generating a defensible claim for a given service period, WITHOUT exposing
any raw chart/clinical content. Callers only ever see a ready/not-ready
verdict plus a short list of billing-relevant blocker/warning labels (e.g.
"Certification of Terminal Illness not signed for this benefit period").

Real CMS documentation requirements enforced here (each backed by a real,
already-persisted table -- nothing here is fabricated or speculative):

  - Active hospice election for the service period (benefit_periods).
  - Signed election statement (patients.election_signed_at) for the
    patient's very first (INITIAL) benefit period.
  - NOE (Notice of Election) filed for the INITIAL benefit period
    (benefit_periods.noe_submitted_date / noe_exception_reason) --
    Medicare will RTP any claim submitted before an NOE is on file.
  - Certification of Terminal Illness / Recertification signed and
    FINALIZED for the benefit period being billed (certifications).
  - Face-to-face encounter attested for the 3rd and later benefit periods
    (f2f_encounters) -- required by 42 CFR 418.22(a)(4).
  - An ACTIVE Plan of Care with a PHYSICIAN_APPROVED signature on file
    (plan_of_care / poc_physician_approvals).
  - A resolvable, unambiguous payer/MSP sequence (patient_payers via
    app.billing.services.msp_validation_service) -- an EDI-blocking issue
    surfaced here *before* generation is attempted, not just at export
    time.

This module is intentionally read-only with respect to clinical/chart
content: it never blocks/writes anything itself, and the eligibility-rule
logic that computes ready/not-ready is unchanged. As of the Eligibility
Traceability Epic (Workstream 3), check_patient_billing_readiness() gains
one additional step: every evaluation is persisted as an immutable
BillingReadinessVerdict row, closing the previously confirmed Chronology
Gap ("why was this patient billable on DATE X" had no answer beyond
re-deriving today's live state). `billing_engine.generate_patient_billing`
and the batch billing API call it and decide what to do with the result
(refuse generation, surface an alert, etc.) exactly as before.

CORRECTIVE DIRECTIVE (Eligibility, Admission, Benefit-Period, and
Billing-Readiness Workflow Correction, post-Sprint-2) applied here:

  - Directive item 10 ("correct billing population queries"):
    `build_tenant_billing_readiness_report` now only evaluates patients
    with an ADMITTED admission record -- a referral/intake-hold record
    (Admission.status in DRAFT/PENDING/NON_ADMIT, or no Admission row at
    all) is never evaluated for billing readiness and never produces a
    BillingReadinessVerdict, matching the admission gate's requirement
    that intake-hold records must not contaminate billing readiness.
  - Directive item 9 ("correct the billing-readiness engine"): because
    the population is now ADMITTED-only, an admitted patient who still
    has no benefit period covering the service date is, by construction,
    an upstream admission-data exception (legacy import, migration
    defect, authorized admission exception, or a later-discovered
    discrepancy) -- never the normal path. The blocker message below was
    corrected to say so explicitly instead of a generic "Missing Benefit
    Period" label.
  - Directive item 13 ("remove duplicate readiness evaluations"):
    _persist_billing_readiness_verdict now computes a stable evidence
    hash and skips writing a new BillingReadinessVerdict row when it is
    byte-identical to the patient's most recent verdict -- a GET/page
    load/dashboard poll that recomputes the same live state no longer
    creates a new historical row every time.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict
from app.billing.services.eligibility_workflow_service import evaluate_admission_gate
from app.billing.services.msp_validation_service import resolve_payer_sequence
from app.billing.services.readiness_workflow_service import sync_blocker_records
from app.core.tenant_scope import list_billable_agency_tenants

# A recert benefit period is period_number >= this value the very first
# time an F2F encounter is required (3rd benefit period onward per
# 42 CFR 418.22(a)(4)).
F2F_REQUIRED_FROM_PERIOD_NUMBER = 3

# Named blocker categories, matched against the start of each raw blocker
# string produced by check_patient_billing_readiness(). Used to roll up
# per-patient blockers into a "Blocker Breakdown" the owner/biller can
# scan across every agency at once, without changing the underlying
# blocker text (which stays intact for the per-patient detail view).
BLOCKER_CATEGORY_PREFIXES: list[tuple[str, str]] = [
    ("Patient status is", "Patient Not Active"),
    (
        "Benefit-period information required for this admitted record",
        "Benefit Period Review Required",
    ),
    ("No benefit period covers", "Missing Benefit Period"),
    ("Hospice election statement is not signed", "Missing Election Statement"),
    ("Notice of Election (NOE) has not been filed", "Missing NOE Filing"),
    ("Certification of Terminal Illness", "Missing Certification"),
    ("Required face-to-face encounter", "Missing F2F Documentation"),
    ("Plan of Care is not active", "Missing POC Physician Signature"),
    ("Payer sequence is ambiguous", "Payer/MSP Sequencing Issue"),
    ("Patient not found", "Patient Not Found"),
]


def categorize_blocker(blocker: str) -> str:
    """
    Maps a raw blocker string to a stable, named category for the Blocker
    Breakdown view. Falls back to "Other" for any blocker text that
    doesn't match a known prefix (e.g. a future blocker added to
    check_patient_billing_readiness that this list hasn't been updated
    for yet) -- never silently drops a blocker.
    """
    for prefix, category in BLOCKER_CATEGORY_PREFIXES:
        if blocker.startswith(prefix):
            return category
    return "Other"


@dataclass(frozen=True)
class BillingReadinessResult:
    patient_id: str
    period_number: int | None
    benefit_period_id: str | None
    ready: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _fetch_billable_benefit_period(
    db: Session, tenant_id: str, patient_id: str, service_date: date
) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT id::text AS id, benefit_type, period_number,
                   election_date, start_date, end_date,
                   noe_submitted_date, noe_exception_reason
            FROM benefit_periods
            WHERE tenant_id = :tenant_id
              AND patient_id = :patient_id
              AND start_date <= :service_date
              AND (end_date IS NULL OR end_date >= :service_date)
            ORDER BY period_number DESC
            LIMIT 1
            """
        ),
        {"tenant_id": tenant_id, "patient_id": patient_id, "service_date": service_date},
    ).mappings().first()
    return dict(row) if row else None


def _fetch_patient_core(db: Session, tenant_id: str, patient_id: str) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT id::text AS id, status, election_signed_at
            FROM patients
            WHERE tenant_id = :tenant_id AND id = :patient_id
            """
        ),
        {"tenant_id": tenant_id, "patient_id": patient_id},
    ).mappings().first()
    return dict(row) if row else None


def _find_finalized_certification_id(
    db: Session, tenant_id: str, patient_id: str, benefit_period_id: str
) -> str | None:
    row = db.execute(
        text(
            """
            SELECT id::text AS id
            FROM certifications
            WHERE tenant_id = :tenant_id
              AND patient_id = :patient_id
              AND benefit_period_id = :benefit_period_id
              AND status = 'FINALIZED'
              AND signed_at IS NOT NULL
            ORDER BY signed_at DESC
            LIMIT 1
            """
        ),
        {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "benefit_period_id": benefit_period_id,
        },
    ).first()
    return row[0] if row else None


def _has_attested_f2f(
    db: Session, tenant_id: str, patient_id: str, benefit_period_id: str
) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM f2f_encounters
            WHERE tenant_id = :tenant_id
              AND patient_id = :patient_id
              AND benefit_period_id = :benefit_period_id
              AND attested_at IS NOT NULL
            LIMIT 1
            """
        ),
        {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "benefit_period_id": benefit_period_id,
        },
    ).first()
    return row is not None


def _has_physician_approved_plan_of_care(
    db: Session, tenant_id: str, patient_id: str
) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM plan_of_care poc
            JOIN poc_physician_approvals appr
              ON appr.poc_version_id = poc.current_version_id
            WHERE poc.tenant_id = :tenant_id
              AND poc.patient_id = :patient_id
              AND poc.status = 'ACTIVE'
              AND appr.approval_status = 'PHYSICIAN_APPROVED'
            LIMIT 1
            """
        ),
        {"tenant_id": tenant_id, "patient_id": patient_id},
    ).first()
    return row is not None


def _fetch_active_payers(db: Session, patient_id: str) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT id, patient_id, payer_name, payer_type, subscriber_id,
                   subscriber_id_type, is_primary, effective_start_date,
                   end_date, msp_type_code, priority_order
            FROM patient_payers
            WHERE patient_id = :patient_id
            """
        ),
        {"patient_id": patient_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def _compute_evidence_hash(
    *, result: "BillingReadinessResult", certification_id: str | None
) -> str:
    """
    Stable signature of the exact evidence a verdict is a function of
    (Directive item 13). Two evaluations of the same patient with
    identical evidence produce the identical hash regardless of *when*
    they ran -- the basis for skipping a duplicate write.
    """
    payload = {
        "ready": result.ready,
        "blockers": list(result.blockers),
        "warnings": list(result.warnings),
        "benefit_period_id": result.benefit_period_id,
        "certification_id": certification_id,
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fetch_latest_verdict_evidence_hash(
    db: Session, *, tenant_id: str, patient_id: str
) -> str | None:
    row = db.execute(
        text(
            """
            SELECT evidence_hash
            FROM billing_readiness_verdicts
            WHERE tenant_id = :tenant_id AND patient_id = :patient_id
            ORDER BY evaluated_at DESC
            LIMIT 1
            """
        ),
        {"tenant_id": tenant_id, "patient_id": patient_id},
    ).first()
    return row[0] if row else None


def _persist_billing_readiness_verdict(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    result: BillingReadinessResult,
    certification_id: str | None,
    triggered_by: str,
) -> None:
    """
    Writes one immutable BillingReadinessVerdict row (Eligibility
    Traceability Epic, Workstream 3). Never updated -- a new evaluation
    always produces a new row, so "why was this patient billable on
    DATE X" can be answered by querying the most recent verdict as of
    that date instead of recomputing live state.

    Directive item 13 correction: if this evaluation's evidence is
    byte-identical to the patient's most recently persisted verdict (same
    ready/blockers/warnings/benefit_period/certification), no new row is
    written and no blocker-record sync runs -- a GET request, dashboard
    poll, page render, or route navigation that recomputes unchanged live
    state must never create a new historical row. Only evidence that
    actually changed creates a new verdict.
    """
    evidence_hash = _compute_evidence_hash(result=result, certification_id=certification_id)
    latest_hash = _fetch_latest_verdict_evidence_hash(
        db, tenant_id=tenant_id, patient_id=patient_id
    )
    if latest_hash is not None and latest_hash == evidence_hash:
        return

    verdict = BillingReadinessVerdict(
        tenant_id=tenant_id,
        patient_id=patient_id,
        is_ready=result.ready,
        blockers=result.blockers,
        warnings=result.warnings,
        benefit_period_id=result.benefit_period_id,
        certification_id=certification_id,
        triggered_by=triggered_by,
        evidence_hash=evidence_hash,
    )
    db.add(verdict)
    db.commit()

    # Sprint 2 (Billing Readiness Operational Workflow, Deliverable 3):
    # maintain the typed, per-blocker lifecycle overlay right after the
    # immutable verdict itself is committed. Additive only -- never
    # changes the verdict row above, never affects the ready/not-ready
    # result already returned to the caller.
    db.refresh(verdict)
    sync_blocker_records(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        verdict=verdict,
    )


def check_patient_billing_readiness(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    service_date: date,
    triggered_by: str = "MANUAL_CHECK",
) -> BillingReadinessResult:
    """
    Evaluates whether `patient_id` is ready to be billed for `service_date`
    (typically the billing cycle's start date). Returns a verdict plus
    short, billing-relevant reason labels only -- never raw chart content.

    Every evaluation that resolves to a real patient is persisted as an
    immutable BillingReadinessVerdict row (Workstream 3) before returning,
    with `triggered_by` recording why the check ran (a scheduled job, a
    manual biller check, or a claim-submission attempt) -- this is
    strictly additive: the eligibility-rule logic below is unchanged from
    before this persistence step was added.
    """
    blockers: list[str] = []
    warnings: list[str] = []

    patient = _fetch_patient_core(db, tenant_id, patient_id)
    if patient is None:
        # No patient row to attach a verdict to (patient_id doesn't
        # resolve for this tenant) -- nothing to persist.
        return BillingReadinessResult(
            patient_id=patient_id,
            period_number=None,
            benefit_period_id=None,
            ready=False,
            blockers=["Patient not found for this tenant."],
        )

    if patient["status"] != "ACTIVE":
        blockers.append(f"Patient status is '{patient['status']}', not ACTIVE.")

    benefit_period = _fetch_billable_benefit_period(db, tenant_id, patient_id, service_date)
    if benefit_period is None:
        # Directive item 9 correction: by construction, only ADMITTED
        # patients reach this evaluation via
        # build_tenant_billing_readiness_report's corrected population
        # query (see module docstring) -- an admitted patient with no
        # benefit period covering the service date is always an upstream
        # admission-data exception (legacy import, migration defect,
        # authorized admission exception, or later-discovered
        # discrepancy), never the normal path. Message text is the exact
        # wording required by the directive so it is never displayed as
        # a generic/context-free "Missing Benefit Period" label.
        blockers.append(
            "Benefit-period information required for this admitted record "
            "is unresolved. Review the eligibility source document and "
            "admission determination before claim preparation."
        )
        result = BillingReadinessResult(
            patient_id=patient_id,
            period_number=None,
            benefit_period_id=None,
            ready=False,
            blockers=blockers,
            warnings=warnings,
        )
        _persist_billing_readiness_verdict(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            result=result,
            certification_id=None,
            triggered_by=triggered_by,
        )
        return result

    benefit_period_id = benefit_period["id"]
    period_number = benefit_period["period_number"]


    # --- Election statement + NOE (INITIAL benefit period only) ---
    if period_number == 1:
        if not patient.get("election_signed_at"):
            blockers.append("Hospice election statement is not signed.")

        if not benefit_period.get("noe_submitted_date") and not benefit_period.get(
            "noe_exception_reason"
        ):
            blockers.append(
                "Notice of Election (NOE) has not been filed and no CMS "
                "exception is documented -- Medicare will return the claim."
            )
        elif benefit_period.get("noe_submitted_date"):
            filed_within = (
                benefit_period["noe_submitted_date"] - benefit_period["election_date"]
            ).days
            if filed_within > 5 and not benefit_period.get("noe_exception_reason"):
                warnings.append(
                    "NOE was filed late -- a non-covered day penalty applies "
                    "to the days prior to filing."
                )

    # --- Certification / Recertification ---
    certification_id = _find_finalized_certification_id(db, tenant_id, patient_id, benefit_period_id)
    if certification_id is None:
        blockers.append(
            "Certification of Terminal Illness (CTI/Recert) is not signed "
            "and finalized for this benefit period."
        )

    # --- Face-to-Face encounter (3rd+ benefit period) ---
    if period_number >= F2F_REQUIRED_FROM_PERIOD_NUMBER:
        if not _has_attested_f2f(db, tenant_id, patient_id, benefit_period_id):
            blockers.append(
                "Required face-to-face encounter is not attested for this "
                "benefit period."
            )

    # --- Plan of Care ---
    if not _has_physician_approved_plan_of_care(db, tenant_id, patient_id):
        blockers.append("Plan of Care is not active with a physician signature on file.")

    # --- Payer / MSP sequencing ---
    payers = _fetch_active_payers(db, patient_id)
    sequence = resolve_payer_sequence(payers, service_date=service_date)
    if sequence.has_conflict:
        blockers.append(f"Payer sequence is ambiguous: {sequence.conflict_reason}")

    # --- Admission gate (Directive item 10, exceptional post-admission
    # path only) --- Only fires when an EligibilityVerification or
    # BenefitPeriodDetermination row actually exists for this patient and
    # is in an unresolved state -- see eligibility_workflow_service module
    # docstring for why an admitted patient with NEITHER row is never
    # penalized (legacy/pre-workflow data, not a negative finding).
    gate = evaluate_admission_gate(db, tenant_id=tenant_id, patient_id=patient_id)
    for gate_blocker in gate.blockers:
        if gate_blocker not in blockers:
            blockers.append(gate_blocker)

    result = BillingReadinessResult(
        patient_id=patient_id,
        period_number=period_number,
        benefit_period_id=benefit_period_id,
        ready=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
    )
    _persist_billing_readiness_verdict(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        result=result,
        certification_id=certification_id,
        triggered_by=triggered_by,
    )
    return result


def build_tenant_billing_readiness_report(
    db: Session,
    *,
    tenant_id: str,
    service_date: date,
) -> dict:
    """
    Evaluates every ADMITTED patient in the tenant for `service_date` and
    returns a summary report: counts plus a per-patient ready/not-ready
    verdict and blocker labels only (no chart content, no clinical
    narrative -- safe to surface to a biller or agency owner as an
    alert/checklist).

    Directive item 10 population correction: population is patients with
    at least one ADMITTED admission record, not merely `patients.status =
    'ACTIVE'`. A referral-only or intake-hold record (no ADMITTED
    admission row yet) is excluded regardless of its `patients.status`
    value -- it must never appear in billing readiness, be counted, or
    receive a BillingReadinessVerdict (see the admission gate in
    eligibility_workflow_service.evaluate_admission_gate, which is the
    intended place such a record gets stopped before reaching this
    query at all).
    """
    patient_rows = db.execute(
        text(
            """
            SELECT DISTINCT p.id::text AS id, p.mrn
            FROM patients p
            JOIN admissions a
              ON a.tenant_id = p.tenant_id AND a.patient_id = p.id
            WHERE p.tenant_id = :tenant_id
              AND p.status = 'ACTIVE'
              AND a.status = 'ADMITTED'
            ORDER BY p.mrn
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()

    results: list[dict] = []
    ready_count = 0
    for row in patient_rows:
        verdict = check_patient_billing_readiness(
            db,
            tenant_id=tenant_id,
            patient_id=row["id"],
            service_date=service_date,
        )
        if verdict.ready:
            ready_count += 1

        results.append(
            {
                "patient_id": verdict.patient_id,
                "mrn": row["mrn"],
                "period_number": verdict.period_number,
                "ready": verdict.ready,
                "blockers": verdict.blockers,
                "warnings": verdict.warnings,
            }
        )

    return {
        "tenant_id": tenant_id,
        "service_date": service_date.isoformat(),
        "total_patients": len(results),
        "ready_count": ready_count,
        "not_ready_count": len(results) - ready_count,
        "patients": results,
    }


def build_cross_agency_billing_readiness_report(
    db: Session,
    *,
    service_date: date,
) -> dict:
    """
    Aggregates check_patient_billing_readiness() across every billable
    agency tenant (see app.core.tenant_scope.list_billable_agency_tenants),
    for the owner's platform-wide Billing Readiness view and the Tenant
    Analytics financials/billing mirror.

    Adds a "Blocker Breakdown" -- the same raw per-patient blocker
    strings from build_tenant_billing_readiness_report(), rolled up into
    named categories (see categorize_blocker) and counted across all
    agencies, so a platform owner or biller can see e.g. "14 patients
    across 3 agencies are missing F2F Documentation" without reading
    every patient row.

    Agencies with billing_enabled=False are still real tenants but have
    no billing data of their own to check; they're included in the
    per-agency breakdown with zero counts rather than silently omitted,
    so the report accounts for every agency in the system.
    """
    agencies = [
        a for a in list_billable_agency_tenants(db) if a.get("status") != "ARCHIVED"
    ]

    blocker_breakdown: dict[str, int] = {}
    agency_reports: list[dict] = []
    total_patients = 0
    total_ready = 0

    for agency in agencies:
        tenant_id = agency["tenant_id"]

        if not agency.get("billing_enabled"):
            agency_reports.append(
                {
                    "tenant_id": tenant_id,
                    "tenant_name": agency["display_name"],
                    "billing_enabled": False,
                    "total_patients": 0,
                    "ready_count": 0,
                    "not_ready_count": 0,
                }
            )
            continue

        report = build_tenant_billing_readiness_report(
            db, tenant_id=tenant_id, service_date=service_date
        )

        for patient in report["patients"]:
            for blocker in patient["blockers"]:
                category = categorize_blocker(blocker)
                blocker_breakdown[category] = blocker_breakdown.get(category, 0) + 1

        total_patients += report["total_patients"]
        total_ready += report["ready_count"]

        agency_reports.append(
            {
                "tenant_id": tenant_id,
                "tenant_name": agency["display_name"],
                "billing_enabled": True,
                "total_patients": report["total_patients"],
                "ready_count": report["ready_count"],
                "not_ready_count": report["not_ready_count"],
                "patients": report["patients"],
            }
        )

    return {
        "service_date": service_date.isoformat(),
        "total_agencies": len(agencies),
        "total_patients": total_patients,
        "ready_count": total_ready,
        "not_ready_count": total_patients - total_ready,
        "blocker_breakdown": [
            {"category": category, "count": count}
            for category, count in sorted(
                blocker_breakdown.items(), key=lambda kv: kv[1], reverse=True
            )
        ],
        "agencies": agency_reports,
    }
