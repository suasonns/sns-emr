from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.billing.models.billing_cycle import BillingCycle
from app.billing.models.billing_snapshot import BillingSnapshot
from app.billing.models.billing_summary import BillingSummary
from app.billing.models.claim import Claim
from app.billing.models.loc_events import ContinuousCareEvent, GIPPeriod, RespitePeriod
from app.billing.models.patient_pos import PatientPOS
from app.billing.services.claim_segment_service import build_claim_lines
from app.billing.services.cms_rate_service import CmsRateError, fiscal_year_for_date
from app.billing.services.sia_service import (
    SIA_WINDOW_DAYS,
    compute_sia_schedule,
    get_date_of_death,
)
from app.billing.services.loc_segment_service import build_loc_segments, build_loc_summary
from app.billing.services.loc_documentation_gap_service import compute_loc_documentation_gaps
from app.billing.services.pos_to_loc_service import (
    DateRangeEvent,
    build_loc_timeline,
    build_pos_timeline,
)
from app.billing.services.revenue_service import (
    DEFAULT_RATE_SCHEDULE,
    build_revenue_summary,
    build_revenue_summary_from_claim_lines,
)
from app.billing.services.unit_service import summarize_units
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.visit import Visit
from app.services.coverage_audit_logger import log_coverage_audit
from app.services.election_day_service import get_election_anchor_date, get_initial_election_noe_info
from app.services.payer_validation import PayerValidationError, validate_payer_for_claim
from app.billing.services.noe_penalty_service import (
    apply_noe_penalty_to_claim_lines,
    compute_noe_penalty,
)
from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.models.election_addendum_request import ElectionAddendumRequest
from app.billing.services.election_addendum_service import compute_addendum_compliance


class BillingEngineError(RuntimeError):
    pass


def _normalize_rate_schedule(rate_schedule: dict | None) -> dict:
    if not rate_schedule:
        return DEFAULT_RATE_SCHEDULE.copy()

    normalized = DEFAULT_RATE_SCHEDULE.copy()
    for key, value in rate_schedule.items():
        normalized[key] = Decimal(str(value))

    return normalized


def _load_tenant_cbsa(db: Session, tenant_id: str) -> str | None:
    return db.execute(
        select(Tenant.cbsa_code).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()


def _load_billing_cycle(db: Session, billing_cycle_id: str) -> BillingCycle:
    cycle = db.execute(
        select(BillingCycle).where(BillingCycle.id == billing_cycle_id)
    ).scalar_one_or_none()

    if cycle is None:
        raise BillingEngineError(f"BillingCycle not found: {billing_cycle_id}")

    return cycle


def _load_patient(db: Session, patient_id: str) -> Patient:
    patient = db.execute(
        select(Patient).where(Patient.id == patient_id)
    ).scalar_one_or_none()

    if patient is None:
        raise BillingEngineError(f"Patient not found: {patient_id}")

    return patient


def _load_pos_records(
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
):
    stmt = (
        select(PatientPOS)
        .where(PatientPOS.patient_id == patient_id)
        .where(PatientPOS.effective_date <= end_date)
        .where((PatientPOS.end_date.is_(None)) | (PatientPOS.end_date >= start_date))
        .order_by(PatientPOS.effective_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def _load_range_events(
    model,
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
) -> list[DateRangeEvent]:
    stmt = (
        select(model)
        .where(model.patient_id == patient_id)
        .where(model.start_date <= end_date)
        .where(model.end_date >= start_date)
        .order_by(model.start_date.asc())
    )
    rows = db.execute(stmt).scalars().all()

    return [
        DateRangeEvent(
            start_date=row.start_date,
            end_date=row.end_date,
            reason=getattr(row, "reason", None),
        )
        for row in rows
    ]


def _load_sia_visits(
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Real finalized-visit rows for the SIA last-7-days-of-life window, in the
    shape sia_service.compute_sia_schedule() expects (visit_date,
    visit_discipline, start_time, end_time, status).
    """
    stmt = (
        select(Visit)
        .where(Visit.patient_id == patient_id)
        .where(Visit.visit_datetime.isnot(None))
        .where(Visit.visit_datetime >= start_date)
        .where(Visit.visit_datetime < end_date + timedelta(days=1))
    )
    rows = db.execute(stmt).scalars().all()

    return [
        {
            "visit_date": row.visit_datetime.date() if row.visit_datetime else None,
            "visit_discipline": row.visit_discipline,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "status": row.status,
        }
        for row in rows
    ]


def _load_total_minutes_for_cycle(
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
) -> int:
    sql = text(
        """
        SELECT COALESCE(SUM(vm.minutes), 0) AS total_minutes
        FROM visit_minutes vm
        JOIN visits v ON v.id = vm.visit_id
        WHERE v.patient_id::text = :patient_id
          AND v.visit_datetime::date BETWEEN :start_date AND :end_date
        """
    )

    result = db.execute(
        sql,
        {
            "patient_id": patient_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    ).scalar_one()

    return int(result or 0)


def _load_visit_minutes_by_date(
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
) -> dict[date, int]:
    """
    Real documented direct-care minutes per calendar date, from actual
    visit_minutes rows -- used to check the CHC 8-hour/day minimum
    against what is really on file (never a computed/assumed figure).
    """
    sql = text(
        """
        SELECT v.visit_datetime::date AS visit_date, COALESCE(SUM(vm.minutes), 0) AS total_minutes
        FROM visit_minutes vm
        JOIN visits v ON v.id = vm.visit_id
        WHERE v.patient_id::text = :patient_id
          AND v.visit_datetime::date BETWEEN :start_date AND :end_date
        GROUP BY v.visit_datetime::date
        """
    )

    rows = db.execute(
        sql,
        {
            "patient_id": patient_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    ).all()

    return {row.visit_date: int(row.total_minutes or 0) for row in rows}


CHC_NURSING_DISCIPLINES = ("RN", "LVN", "LPN")
CHC_AIDE_DISCIPLINES = ("AIDE", "CHHA")


def _load_chc_discipline_minutes_by_date(
    db: Session,
    patient_id: str,
    start_date: date,
    end_date: date,
) -> tuple[dict[date, int], dict[date, list[int]]]:
    """
    Real documented direct-care minutes per calendar date, split out so the
    CHC "predominantly nursing" (>=50%) rule and the agency's 4-hour/shift
    aide cap can both be checked against actual visit_minutes rows -- never
    a computed/assumed figure.

    Returns:
        (nursing_minutes_by_date, aide_shift_minutes_by_date) where the
        first is the RN/LVN/LPN total per day and the second is the list of
        individual CHHA/AIDE visit ("shift") durations per day.
    """
    sql = text(
        """
        SELECT
            v.visit_datetime::date AS visit_date,
            v.visit_discipline AS discipline,
            v.id AS visit_id,
            COALESCE(SUM(vm.minutes), 0) AS visit_minutes
        FROM visit_minutes vm
        JOIN visits v ON v.id = vm.visit_id
        WHERE v.patient_id::text = :patient_id
          AND v.visit_datetime::date BETWEEN :start_date AND :end_date
        GROUP BY v.visit_datetime::date, v.visit_discipline, v.id
        """
    )

    rows = db.execute(
        sql,
        {
            "patient_id": patient_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    ).all()

    nursing_minutes_by_date: dict[date, int] = {}
    aide_shift_minutes_by_date: dict[date, list[int]] = {}
    for row in rows:
        discipline = (row.discipline or "").upper()
        minutes = int(row.visit_minutes or 0)
        if discipline in CHC_NURSING_DISCIPLINES:
            nursing_minutes_by_date[row.visit_date] = nursing_minutes_by_date.get(row.visit_date, 0) + minutes
        elif discipline in CHC_AIDE_DISCIPLINES:
            aide_shift_minutes_by_date.setdefault(row.visit_date, []).append(minutes)

    return nursing_minutes_by_date, aide_shift_minutes_by_date


def _upsert_billing_summary(
    db: Session,
    tenant_id: str,
    patient_id: str,
    billing_cycle_id: str,
    total_units: int,
    risk_score: int,
    status: str,
) -> BillingSummary:
    existing = db.execute(
        select(BillingSummary)
        .where(BillingSummary.patient_id == patient_id)
        .where(BillingSummary.billing_cycle_id == billing_cycle_id)
    ).scalar_one_or_none()

    if existing:
        existing.total_units = total_units
        existing.risk_score = risk_score
        existing.status = status
        return existing

    summary = BillingSummary(
        id=str(uuid4()),
        tenant_id=tenant_id,
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        total_units=total_units,
        risk_score=risk_score,
        status=status,
    )
    db.add(summary)
    return summary


def _upsert_claim(
    db: Session,
    tenant_id: str,
    patient_id: str,
    billing_cycle_id: str,
    payer_name: str | None,
    service_date,
    total_charge,
    total_units: int,
    risk_score: int,
) -> Claim:
    """
    Creates/refreshes the real claim record backing the Biller's Dashboard
    claim-lifecycle counts and the Claims Management page. A claim already
    past READY (SENT/ACCEPTED/DENIED/PAID) keeps its lifecycle status --
    re-running billing generation only refreshes the billable amounts, it
    never regresses a claim that has already been submitted.
    """
    existing = db.execute(
        select(Claim)
        .where(Claim.patient_id == patient_id)
        .where(Claim.billing_cycle_id == billing_cycle_id)
    ).scalar_one_or_none()

    if existing:
        existing.payer_name = payer_name
        existing.service_date = service_date
        existing.total_charge = total_charge
        existing.total_units = total_units
        existing.risk_score = risk_score
        return existing

    claim = Claim(
        id=str(uuid4()),
        tenant_id=tenant_id,
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        payer_name=payer_name,
        service_date=service_date,
        total_charge=total_charge,
        total_units=total_units,
        risk_score=risk_score,
        status="READY",
    )
    db.add(claim)
    return claim


def _insert_billing_snapshot(
    db: Session,
    tenant_id: str,
    patient_id: str,
    billing_cycle_id: str,
    snapshot_payload: dict,
    snapshot_type: str = "BILLING",
) -> BillingSnapshot:
    snapshot = BillingSnapshot(
        id=str(uuid4()),
        tenant_id=tenant_id,
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        snapshot_type=snapshot_type,
        data=snapshot_payload,
    )
    db.add(snapshot)
    return snapshot


def _derive_status(risk_score: int) -> str:
    if risk_score >= 80:
        return "HIGH_RISK"
    if risk_score > 0:
        return "WARNING"
    return "READY"


def _load_active_hospice_coverage(
    db: Session,
    tenant_id: str,
    patient_id: str,
    billing_cycle_id: str,
) -> dict[str, Any]:
    """
    ✅ ENTERPRISE-SAFE ACTIVE HOSPICE COVERAGE RESOLVER (STABILIZATION)

    Canonical sources (current SNS EMR):
    - benefit_periods: proves hospice election + active benefit period window
    - patient_payers: proves active hospice payer coverage overlapping the cycle

    This REPLACES the legacy patient_insurances lookup (schema drift).

    IMPORTANT: coverage is valid whenever the patient has CONTINUOUS,
    gapless hospice benefit-period coverage across the entire billing
    cycle -- even when that coverage spans more than one benefit period
    (e.g. a 60-day recertification boundary falls mid-month). Requiring a
    single benefit_periods row to span the whole cycle was wrong: a real,
    CMS-paid claim for this exact scenario (one calendar-month claim whose
    DOS crossed a recert boundary) proves CMS pays monthly claims as long
    as election/certification is unbroken across the billed range,
    regardless of whether a recert happened mid-month.
    """

    cycle_row = db.execute(
        text("SELECT start_date, end_date FROM billing_cycles WHERE id = :id"),
        {"id": billing_cycle_id},
    ).mappings().first()

    if not cycle_row:
        raise BillingEngineError("Missing active HOSPICE coverage for patient billing")

    cycle_start = cycle_row["start_date"]
    cycle_end = cycle_row["end_date"]

    bp_rows = db.execute(
        text(
            """
            SELECT period_number, benefit_type, election_date, start_date, end_date, is_current
            FROM benefit_periods
            WHERE patient_id::text = :patient_id
              AND tenant_id::text = :tenant_id
              AND election_date IS NOT NULL
              AND start_date <= :cycle_end
              AND (end_date IS NULL OR end_date >= :cycle_start)
            ORDER BY start_date ASC
            """
        ),
        {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "cycle_start": cycle_start,
            "cycle_end": cycle_end,
        },
    ).mappings().all()

    if not bp_rows:
        raise BillingEngineError("Missing active HOSPICE coverage for patient billing")

    # Verify continuous, gapless benefit-period coverage across the whole
    # cycle. Adjacent periods may touch (period N end_date == period N+1
    # start_date, or be exactly one day apart) but must never leave a gap.
    covered_through = None
    for row in bp_rows:
        if covered_through is None:
            if row["start_date"] > cycle_start:
                raise BillingEngineError(
                    "Missing active HOSPICE coverage for patient billing"
                )
        else:
            gap_days = (row["start_date"] - covered_through).days
            if gap_days > 1:
                raise BillingEngineError(
                    "Missing active HOSPICE coverage for patient billing"
                )
        row_end = row["end_date"] if row["end_date"] is not None else date.max
        if covered_through is None or row_end > covered_through:
            covered_through = row_end

    if covered_through < cycle_end:
        raise BillingEngineError("Missing active HOSPICE coverage for patient billing")

    latest_bp = bp_rows[-1]

    payer_row = db.execute(
        text(
            """
            SELECT
                pp.id::text             AS id,
                pp.patient_id::text     AS patient_id,
                pp.payer_type           AS payer_type,
                pp.payer_name           AS payer_name,
                pp.subscriber_id        AS subscriber_id,
                pp.subscriber_id_type   AS subscriber_id_type,
                pp.effective_start_date AS payer_start_date,
                pp.end_date             AS payer_end_date,
                pp.is_primary           AS is_primary
            FROM patient_payers pp
            WHERE pp.patient_id::text = :patient_id
              AND pp.is_primary IS TRUE
              AND pp.effective_start_date IS NOT NULL
              AND pp.effective_start_date <= :cycle_end
              AND (pp.end_date IS NULL OR pp.end_date >= :cycle_start)
              AND pp.payer_type IN ('HOSPICE', 'MEDICARE_HOSPICE', 'MEDICARE')
            ORDER BY pp.effective_start_date DESC
            LIMIT 1
            """
        ),
        {
            "patient_id": patient_id,
            "cycle_start": cycle_start,
            "cycle_end": cycle_end,
        },
    ).mappings().first()

    if not payer_row:
        raise BillingEngineError("Missing active HOSPICE coverage for patient billing")

    return {
        "id": payer_row["id"],
        "tenant_id": tenant_id,
        "patient_id": payer_row["patient_id"],
        "payer_type": payer_row["payer_type"],
        "payer_name": payer_row["payer_name"],
        "subscriber_id": payer_row["subscriber_id"],
        "subscriber_id_type": payer_row["subscriber_id_type"],
        "coverage_scope": "HOSPICE",
        "priority_order": 1,
        "period_number": latest_bp["period_number"],
        "benefit_type": latest_bp["benefit_type"],
        "election_date": latest_bp["election_date"],
        "bp_start_date": latest_bp["start_date"],
        "bp_end_date": latest_bp["end_date"],
        "payer_start_date": payer_row["payer_start_date"],
        "payer_end_date": payer_row["payer_end_date"],
        "is_primary": payer_row["is_primary"],
        "benefit_periods_in_cycle": [
            {
                "period_number": r["period_number"],
                "benefit_type": r["benefit_type"],
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]) if r["end_date"] else None,
            }
            for r in bp_rows
        ],
    }

def generate_patient_billing(
    db: Session,
    patient_id: str,
    billing_cycle_id: str,
    rate_schedule: dict | None = None,
) -> dict:
    """
    ✅ ENTERPRISE BILLING ENGINE

    Includes:
    - billing cycle validation
    - patient validation
    - active hospice coverage validation
    - payer identifier validation
    - summary + snapshot persistence
    - audit logging
    """

    patient = _load_patient(db, patient_id)
    cycle = _load_billing_cycle(db, billing_cycle_id)
    rate_schedule = _normalize_rate_schedule(rate_schedule)

    # ---------------------------------------------------------
    # BILLING READINESS GATE -- refuse to generate a claim for a chart
    # that is not yet documentation-complete (missing signed CTI, F2F,
    # Plan of Care, NOE, or an unresolved payer/MSP sequence). This is a
    # hard gate, not a warning: a claim generated from an incomplete
    # chart is a real compliance and revenue-recoupment risk.
    # ---------------------------------------------------------
    readiness = check_patient_billing_readiness(
        db,
        tenant_id=str(patient.tenant_id),
        patient_id=patient_id,
        service_date=cycle.start_date,
    )
    if not readiness.ready:
        raise BillingEngineError(
            "Patient is not ready to be billed: " + "; ".join(readiness.blockers)
        )

    # ---------------------------------------------------------
    # COVERAGE / PAYER VALIDATION
    # ---------------------------------------------------------
    active_hospice_coverage = _load_active_hospice_coverage(
        db=db,
        tenant_id=str(patient.tenant_id),
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
    )

    try:
        validate_payer_for_claim(active_hospice_coverage)
    except PayerValidationError as e:
        try:
            log_coverage_audit(
                db=db,
                tenant_id=str(patient.tenant_id),
                action="PAYER_VALIDATION_FAILED",
                entity_type="patient_payer",
                entity_id=active_hospice_coverage.get("id"),
                user_id=None,
                role="SYSTEM",
                request_id=None,
                ip_address=None,
                metadata={
                    "patient_id": patient_id,
                    "billing_cycle_id": billing_cycle_id,
                    "payer_type": active_hospice_coverage.get("payer_type"),
                    "subscriber_id_type": active_hospice_coverage.get("subscriber_id_type"),
                    "error": str(e),
                },
            )
        except Exception:
            pass

        raise BillingEngineError(str(e)) from e

    # ---------------------------------------------------------
    # LOAD TIMELINES / EVENTS
    # ---------------------------------------------------------
    pos_records = _load_pos_records(
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )

    gip_events = _load_range_events(
        GIPPeriod,
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
    respite_events = _load_range_events(
        RespitePeriod,
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
    continuous_events = _load_range_events(
        ContinuousCareEvent,
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )

    pos_timeline = build_pos_timeline(
        pos_records=pos_records,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )

    loc_timeline = build_loc_timeline(
        pos_timeline=pos_timeline,
        gip_events=gip_events,
        respite_events=respite_events,
        continuous_events=continuous_events,
    )

    loc_segments = build_loc_segments(loc_timeline)
    loc_summary = build_loc_summary(loc_timeline)

    total_minutes = _load_total_minutes_for_cycle(
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
    unit_summary = summarize_units(total_minutes)

    chc_minutes_by_date = _load_visit_minutes_by_date(
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
    chc_nursing_minutes_by_date, chc_aide_shift_minutes_by_date = _load_chc_discipline_minutes_by_date(
        db=db,
        patient_id=patient_id,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
    loc_doc_gap_result = compute_loc_documentation_gaps(
        gip_events=gip_events,
        respite_events=respite_events,
        continuous_events=continuous_events,
        chc_minutes_by_date=chc_minutes_by_date,
        chc_nursing_minutes_by_date=chc_nursing_minutes_by_date,
        chc_aide_shift_minutes_by_date=chc_aide_shift_minutes_by_date,
    )

    # ---------------------------------------------------------
    # RISK / STATUS
    # ---------------------------------------------------------
    risk_score = 0
    if any(row["pos"] is None for row in pos_timeline):
        risk_score += 60
    if any(row["loc"] is None for row in loc_timeline):
        risk_score += 35

    status = _derive_status(risk_score)

    # ---------------------------------------------------------
    # CLAIM LINES / REVENUE
    # ---------------------------------------------------------
    tenant_cbsa_code = _load_tenant_cbsa(db, str(patient.tenant_id))
    election_anchor_date = get_election_anchor_date(
        db,
        tenant_id=str(patient.tenant_id),
        patient_id=patient_id,
    )

    claim_lines = build_claim_lines(
        loc_segments=loc_segments,
        rate_schedule=rate_schedule,
        cbsa_code=tenant_cbsa_code,
        election_anchor_date=election_anchor_date,
    )

    # Late-NOE penalty (42 CFR 418.24(b)): if the real NOE filing date is
    # more than 5 calendar days after the real election date, the days
    # from election through the day before filing are non-covered. This
    # can zero out real revenue the same way a CMS rate gap can -- apply
    # it here so the snapshot/claim export reflects the true billable
    # amount, not the pre-penalty estimate.
    noe_penalty_reason = None
    noe_info = get_initial_election_noe_info(
        db,
        tenant_id=str(patient.tenant_id),
        patient_id=patient_id,
    )
    if noe_info and noe_info.get("election_date"):
        noe_penalty = compute_noe_penalty(
            election_date=noe_info["election_date"],
            noe_submitted_date=noe_info.get("noe_submitted_date"),
            exception_reason=noe_info.get("noe_exception_reason"),
        )
        if noe_penalty.is_late and not noe_penalty.is_exempt:
            claim_lines = apply_noe_penalty_to_claim_lines(claim_lines, noe_penalty)
            noe_penalty_reason = noe_penalty.reason

    # Election Statement Addendum timeliness (42 CFR 418.24(b)): a late or
    # still-outstanding addendum past its 5-day/72-hour furnishing deadline
    # is a real Condition of Participation exposure -- surface it as a risk
    # the same way a late NOE is, using only real, already-logged request/
    # delivery dates (never fabricated or assumed).
    addendum_gap_reasons: list[str] = []
    if noe_info and noe_info.get("election_date"):
        addendum_requests = (
            db.query(ElectionAddendumRequest)
            .filter(ElectionAddendumRequest.patient_id == patient_id)
            .all()
        )
        if addendum_requests:
            discharge_or_death = get_date_of_death(patient)
            for addendum_request in addendum_requests:
                addendum_result = compute_addendum_compliance(
                    election_date=noe_info["election_date"],
                    requested_date=addendum_request.requested_date,
                    delivered_date=addendum_request.delivered_date,
                    discharge_or_death_date=discharge_or_death,
                    not_required_reason=addendum_request.not_required_reason,
                )
                if addendum_result.is_late:
                    addendum_gap_reasons.append(addendum_result.reason)

    # Service Intensity Add-on (SIA): for a patient who died during this
    # billing cycle, CMS pays an additional per-visit add-on for real
    # RN/MSW direct-care minutes on RHC days in the last 7 days of life
    # (42 CFR 418.302). Requires real CMS wage-adjusted rates (cbsa_code)
    # since the SIA hourly rate is derived from the CHC per-diem rate.
    sia_schedule = None
    sia_rate_gap_reason = None
    date_of_death = get_date_of_death(patient)
    if date_of_death and cycle.start_date <= date_of_death <= cycle.end_date and tenant_cbsa_code:
        sia_window_start = date_of_death - timedelta(days=SIA_WINDOW_DAYS - 1)

        sia_pos_records = _load_pos_records(
            db=db, patient_id=patient_id, start_date=sia_window_start, end_date=date_of_death
        )
        sia_gip_events = _load_range_events(
            GIPPeriod, db, patient_id, sia_window_start, date_of_death
        )
        sia_respite_events = _load_range_events(
            RespitePeriod, db, patient_id, sia_window_start, date_of_death
        )
        sia_continuous_events = _load_range_events(
            ContinuousCareEvent, db, patient_id, sia_window_start, date_of_death
        )
        sia_pos_timeline = build_pos_timeline(
            pos_records=sia_pos_records, start_date=sia_window_start, end_date=date_of_death
        )
        sia_loc_timeline = build_loc_timeline(
            pos_timeline=sia_pos_timeline,
            gip_events=sia_gip_events,
            respite_events=sia_respite_events,
            continuous_events=sia_continuous_events,
        )
        loc_by_date = {row["date"]: row["loc"] for row in sia_loc_timeline}

        sia_visits = _load_sia_visits(
            db, patient_id, sia_window_start, date_of_death
        )

        try:
            sia_schedule = compute_sia_schedule(
                date_of_death=date_of_death,
                loc_by_date=loc_by_date,
                visits=sia_visits,
                cbsa_code=tenant_cbsa_code,
            )
        except CmsRateError as exc:
            sia_rate_gap_reason = str(exc)

        if sia_schedule:
            for day in sia_schedule["days"]:
                if Decimal(day["amount"]) <= 0:
                    continue
                claim_lines.append(
                    {
                        "from_date": str(day["date"]),
                        "to_date": str(day["date"]),
                        "days": 1,
                        "loc": "ROUTINE",
                        "pos": None,
                        "facility_name": None,
                        # SIA is billed via HCPCS G0299 (RN)/G0300 (LPN) on
                        # revenue code 0551; this combines RN+MSW minutes
                        # into a single line since sia_service does not
                        # currently split the amount by discipline.
                        "revenue_code": "0551",
                        "hcpcs_code": "G0299",
                        "rate": day["amount"],
                        "estimated_amount": day["amount"],
                        "fiscal_year": fiscal_year_for_date(day["date"]),
                        "rhc_day_tier": "SIA",
                        "rate_gap_reason": None,
                        "is_sia": True,
                    }
                )

    # If any real, CMS-rate-priced claim line was produced (i.e. the tenant
    # has a CBSA on file), the revenue summary is derived directly from
    # those (already tier/FY-split) claim lines so the dollar total always
    # matches what the 837I would actually bill. Otherwise, fall back to
    # the legacy flat rate_schedule summary (unchanged behavior for tenants
    # without a CBSA configured yet).
    if tenant_cbsa_code:
        revenue_summary = build_revenue_summary_from_claim_lines(claim_lines)
    else:
        revenue_summary = build_revenue_summary(
            loc_summary=loc_summary,
            rate_schedule=rate_schedule,
        )

    # A rate gap (e.g. this tenant is CMS-rate-enabled but a fiscal year or
    # CBSA wage index isn't populated yet for some part of this cycle)
    # means the dollar total above is a real under-count, not just a risk
    # heuristic -- surface it the same way other high-severity billing
    # risks are surfaced, so it isn't silently missed.
    if revenue_summary.get("has_rate_gaps"):
        risk_score += 75
        status = _derive_status(risk_score)

    # A late-NOE penalty is a real, CMS-enforced revenue reduction (not a
    # data gap) -- still surface it at the same severity so a biller sees
    # why the total dropped instead of assuming a system error.
    if noe_penalty_reason:
        risk_score += 75
        status = _derive_status(risk_score)

    # A missing wage index/FY for the SIA lookback window means the SIA
    # add-on (real, additional revenue for last-7-days-of-life RN/MSW care)
    # couldn't be priced -- surface it, don't silently omit it.
    if sia_rate_gap_reason:
        risk_score += 75
        status = _derive_status(risk_score)

    # GIP/Respite/CHC documentation gaps are a real audit-supportability
    # exposure (missing physician/caregiver justification, or a CHC day
    # under the CMS 8-hour direct-care minimum) -- surface it at the same
    # severity as the other billing-integrity risks above.
    if loc_doc_gap_result.has_gaps:
        risk_score += 75
        status = _derive_status(risk_score)

    # A late/outstanding Election Statement Addendum is a real Condition of
    # Participation exposure (not just a data gap) -- surface it at the
    # same severity as the other billing-integrity risks above.
    if addendum_gap_reasons:
        risk_score += 75
        status = _derive_status(risk_score)

    snapshot_payload = {
        "patient_id": patient_id,
        "billing_cycle_id": billing_cycle_id,
        "billing_period": {
            "start_date": str(cycle.start_date),
            "end_date": str(cycle.end_date),
            "month": cycle.month,
            "year": cycle.year,
        },
        "payer_validation": {
            "payer_type": active_hospice_coverage.get("payer_type"),
            "payer_name": active_hospice_coverage.get("payer_name"),
            "subscriber_id_type": active_hospice_coverage.get("subscriber_id_type"),
        },
        "benefit_periods_in_cycle": active_hospice_coverage.get("benefit_periods_in_cycle", []),
        "noe_penalty_reason": noe_penalty_reason,
        "sia_rate_gap_reason": sia_rate_gap_reason,
        "loc_documentation_gap_reasons": loc_doc_gap_result.reasons,
        "election_addendum_gap_reasons": addendum_gap_reasons,
        "sia_schedule": (
            {
                "date_of_death": str(sia_schedule["date_of_death"]),
                "window_start": str(sia_schedule["window_start"]),
                "days": [
                    {**day, "date": str(day["date"])} for day in sia_schedule["days"]
                ],
                "total_amount": sia_schedule["total_amount"],
            }
            if sia_schedule
            else None
        ),
        "rate_schedule_used": {key: str(value) for key, value in rate_schedule.items()},
        "cms_rate_metadata": {
            "cbsa_code": tenant_cbsa_code,
            "election_anchor_date": str(election_anchor_date) if election_anchor_date else None,
            "real_cms_rates_applied": bool(tenant_cbsa_code),
        },
        "pos_timeline": [
            {
                "date": str(row["date"]),
                "pos": row["pos"],
                "facility_name": row.get("facility_name"),
            }
            for row in pos_timeline
        ],
        "loc_timeline": [
            {
                "date": str(row["date"]),
                "pos": row["pos"],
                "loc": row["loc"],
                "facility_name": row.get("facility_name"),
            }
            for row in loc_timeline
        ],
        "loc_segments": [
            {
                "start_date": str(seg["start_date"]),
                "end_date": str(seg["end_date"]),
                "pos": seg["pos"],
                "loc": seg["loc"],
                "facility_name": seg.get("facility_name"),
            }
            for seg in loc_segments
        ],
        "loc_summary": loc_summary,
        "units": unit_summary,
        "claim_lines": claim_lines,
        "revenue_summary": revenue_summary,
        "risk_score": risk_score,
        "status": status,
    }

    # ---------------------------------------------------------
    # WRITE SUMMARY / SNAPSHOT
    # ---------------------------------------------------------
    try:
        summary = _upsert_billing_summary(
            db=db,
            tenant_id=str(patient.tenant_id),
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            total_units=unit_summary["total_units"],
            risk_score=risk_score,
            status=status,
        )

        _upsert_claim(
            db=db,
            tenant_id=str(patient.tenant_id),
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            payer_name=active_hospice_coverage.get("payer_name"),
            service_date=cycle.start_date,
            total_charge=revenue_summary.get("total_estimated_amount") or 0,
            total_units=unit_summary["total_units"],
            risk_score=risk_score,
        )

        _insert_billing_snapshot(
            db=db,
            tenant_id=str(patient.tenant_id),
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            snapshot_payload=snapshot_payload,
        )

        db.commit()

    except Exception as e:
        db.rollback()

        try:
            log_coverage_audit(
                db=db,
                tenant_id=str(patient.tenant_id),
                action="BILLING_GENERATION_FAILED",
                entity_type="billing_cycle",
                entity_id=billing_cycle_id,
                user_id=None,
                role="SYSTEM",
                request_id=None,
                ip_address=None,
                metadata={
                    "patient_id": patient_id,
                    "error": str(e),
                },
            )
        except Exception:
            pass

        raise BillingEngineError(f"Billing generation failed: {e}") from e

    # ---------------------------------------------------------
    # SUCCESS AUDIT
    # ---------------------------------------------------------
    try:
        log_coverage_audit(
            db=db,
            tenant_id=str(patient.tenant_id),
            action="BILLING_GENERATED",
            entity_type="billing_summary",
            entity_id=str(summary.id),
            user_id=None,
            role="SYSTEM",
            request_id=None,
            ip_address=None,
            metadata={
                "patient_id": patient_id,
                "billing_cycle_id": billing_cycle_id,
                "status": status,
                "risk_score": risk_score,
                "total_units": unit_summary["total_units"],
                "payer_type": active_hospice_coverage.get("payer_type"),
                "subscriber_id_type": active_hospice_coverage.get("subscriber_id_type"),
            },
        )
    except Exception:
        # Never fail billing because audit logging fails after commit
        pass

    return {
        "billing_summary_id": str(summary.id),
        "patient_id": patient_id,
        "billing_cycle_id": billing_cycle_id,
        "status": status,
        "risk_score": risk_score,
        "units": unit_summary["total_units"],
        "total_minutes": unit_summary["total_minutes"],
        "loc_summary": loc_summary,
        "loc_segments": snapshot_payload["loc_segments"],
        "claim_lines": claim_lines,
        "revenue_summary": revenue_summary,
        "cms_rate_metadata": snapshot_payload["cms_rate_metadata"],
        "payer_validation": {
            "payer_type": active_hospice_coverage.get("payer_type"),
            "payer_name": active_hospice_coverage.get("payer_name"),
            "subscriber_id_type": active_hospice_coverage.get("subscriber_id_type"),
        },
    }