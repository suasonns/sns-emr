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

This module is intentionally read-only: it never blocks/writes anything
itself. `billing_engine.generate_patient_billing` and the batch billing
API call it and decide what to do with the result (refuse generation,
surface an alert, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.billing.services.msp_validation_service import resolve_payer_sequence
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


def _has_finalized_certification(
    db: Session, tenant_id: str, patient_id: str, benefit_period_id: str
) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM certifications
            WHERE tenant_id = :tenant_id
              AND patient_id = :patient_id
              AND benefit_period_id = :benefit_period_id
              AND status = 'FINALIZED'
              AND signed_at IS NOT NULL
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


def check_patient_billing_readiness(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    service_date: date,
) -> BillingReadinessResult:
    """
    Evaluates whether `patient_id` is ready to be billed for `service_date`
    (typically the billing cycle's start date). Returns a verdict plus
    short, billing-relevant reason labels only -- never raw chart content.
    """
    blockers: list[str] = []
    warnings: list[str] = []

    patient = _fetch_patient_core(db, tenant_id, patient_id)
    if patient is None:
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
        blockers.append(
            f"No benefit period covers the service date {service_date.isoformat()}."
        )
        return BillingReadinessResult(
            patient_id=patient_id,
            period_number=None,
            benefit_period_id=None,
            ready=False,
            blockers=blockers,
            warnings=warnings,
        )

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
    if not _has_finalized_certification(db, tenant_id, patient_id, benefit_period_id):
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

    return BillingReadinessResult(
        patient_id=patient_id,
        period_number=period_number,
        benefit_period_id=benefit_period_id,
        ready=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
    )


def build_tenant_billing_readiness_report(
    db: Session,
    *,
    tenant_id: str,
    service_date: date,
) -> dict:
    """
    Evaluates every ACTIVE patient in the tenant for `service_date` and
    returns a summary report: counts plus a per-patient ready/not-ready
    verdict and blocker labels only (no chart content, no clinical
    narrative -- safe to surface to a biller or agency owner as an
    alert/checklist).
    """
    patient_rows = db.execute(
        text(
            """
            SELECT id::text AS id, mrn
            FROM patients
            WHERE tenant_id = :tenant_id
              AND status = 'ACTIVE'
            ORDER BY mrn
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
