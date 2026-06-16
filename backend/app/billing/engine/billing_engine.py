from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.billing.models.billing_cycle import BillingCycle
from app.billing.models.billing_snapshot import BillingSnapshot
from app.billing.models.billing_summary import BillingSummary
from app.billing.models.loc_events import ContinuousCareEvent, GIPPeriod, RespitePeriod
from app.billing.models.patient_pos import PatientPOS
from app.billing.services.claim_segment_service import build_claim_lines
from app.billing.services.loc_segment_service import build_loc_segments, build_loc_summary
from app.billing.services.pos_to_loc_service import (
    DateRangeEvent,
    build_loc_timeline,
    build_pos_timeline,
)
from app.billing.services.revenue_service import (
    DEFAULT_RATE_SCHEDULE,
    build_revenue_summary,
)
from app.billing.services.unit_service import summarize_units
from app.models.patient import Patient
from app.services.coverage_audit_logger import log_coverage_audit
from app.services.payer_validation import PayerValidationError, validate_payer_for_claim


class BillingEngineError(RuntimeError):
    pass


def _normalize_rate_schedule(rate_schedule: dict | None) -> dict:
    if not rate_schedule:
        return DEFAULT_RATE_SCHEDULE.copy()

    normalized = DEFAULT_RATE_SCHEDULE.copy()
    for key, value in rate_schedule.items():
        normalized[key] = Decimal(str(value))

    return normalized


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
        JOIN visits v ON v.id::text = vm.visit_id
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


def _upsert_billing_summary(
    db: Session,
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
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        total_units=total_units,
        risk_score=risk_score,
        status=status,
    )
    db.add(summary)
    return summary


def _insert_billing_snapshot(
    db: Session,
    patient_id: str,
    snapshot_payload: dict,
) -> BillingSnapshot:
    snapshot = BillingSnapshot(
        id=str(uuid4()),
        patient_id=patient_id,
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
    """

    sql = text(
        """
        WITH cycle AS (
            SELECT start_date, end_date
            FROM billing_cycles
            WHERE id = :billing_cycle_id
        )
        SELECT
            -- payer identity
            pp.id::text                 AS id,
            CAST(:tenant_id AS text)    AS tenant_id,
            pp.patient_id::text         AS patient_id,
            pp.payer_type               AS payer_type,
            pp.payer_name               AS payer_name,

            -- downstream validation fields (stabilization defaults)
            pp.subscriber_id            AS subscriber_id,
            pp.subscriber_id_type       AS subscriber_id_type,


            -- normalize to legacy coverage shape
            'HOSPICE'::text             AS coverage_scope,
            1                           AS priority_order,

            -- proof fields (useful for audits and debugging)
            bp.period_number            AS period_number,
            bp.benefit_type             AS benefit_type,
            bp.election_date            AS election_date,
            bp.start_date               AS bp_start_date,
            bp.end_date                 AS bp_end_date,
            pp.effective_start_date     AS payer_start_date,
            pp.end_date                 AS payer_end_date,
            pp.is_primary               AS is_primary
        FROM cycle c
        JOIN benefit_periods bp
          ON bp.patient_id::text = :patient_id
         AND bp.tenant_id::text = :tenant_id
         AND bp.is_current IS TRUE
         AND bp.election_date IS NOT NULL
         AND bp.start_date <= c.start_date
         AND (bp.end_date IS NULL OR bp.end_date >= c.end_date)
         AND bp.benefit_type = 'HOSPICE'
        JOIN patient_payers pp
          ON pp.patient_id::text = :patient_id
         AND pp.is_primary IS TRUE
         AND pp.effective_start_date IS NOT NULL
         AND pp.effective_start_date <= c.end_date
         AND (pp.end_date IS NULL OR pp.end_date >= c.start_date)
         AND pp.payer_type IN ('HOSPICE', 'MEDICARE_HOSPICE', 'MEDICARE')
        ORDER BY pp.effective_start_date DESC
        LIMIT 1
        """
    )

    row = db.execute(
        sql,
        {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "billing_cycle_id": billing_cycle_id,
        },
    ).mappings().first()

    if not row:
        raise BillingEngineError("Missing active HOSPICE coverage for patient billing")

    return dict(row)

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
    claim_lines = build_claim_lines(
        loc_segments=loc_segments,
        rate_schedule=rate_schedule,
    )

    revenue_summary = build_revenue_summary(
        loc_summary=loc_summary,
        rate_schedule=rate_schedule,
    )

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
        "rate_schedule_used": {key: str(value) for key, value in rate_schedule.items()},
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
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            total_units=unit_summary["total_units"],
            risk_score=risk_score,
            status=status,
        )

        _insert_billing_snapshot(
            db=db,
            patient_id=patient_id,
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
        "billing_summary_id": summary.id,
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
        "payer_validation": {
            "payer_type": active_hospice_coverage.get("payer_type"),
            "payer_name": active_hospice_coverage.get("payer_name"),
            "subscriber_id_type": active_hospice_coverage.get("subscriber_id_type"),
        },
    }