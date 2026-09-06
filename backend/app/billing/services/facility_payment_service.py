from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.billing.models.claim import Claim
from app.billing.models.facility_collection_alert import (
    FACILITY_COLLECTION_ALERT_SEVERITIES,
    FACILITY_COLLECTION_ALERT_STATUSES,
    FacilityCollectionAlert,
    FacilityCollectionAlertThreshold,
)
from app.billing.models.facility_payment_allocation import (
    FACILITY_ALLOCATION_STATUSES,
    FacilityPaymentAllocation,
)
from app.billing.models.facility_payment_audit_log import (
    FACILITY_AUDIT_ENTITY_TYPES,
    FacilityPaymentAuditLog,
)
from app.billing.models.facility_payment_expectation import (
    FACILITY_DUE_DATE_SOURCES,
    FACILITY_EXPECTATION_STATUSES,
    FACILITY_EXPECTATION_SOURCES,
    FACILITY_FUNDING_SOURCES,
    FACILITY_RECONCILIATION_STATUSES,
    RESPONSIBILITY_CATEGORIES,
    FacilityPaymentExpectation,
)
from app.billing.models.patient_pos import PatientPOS
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.services.claim_financials import patient_display_name, resolve_primary_secondary_payer_names
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_payer import PatientPayer
from app.models.tenant import Tenant

ALERT_TYPES = {
    "EXPECTATION_MISSING",
    "FUNDING_SOURCE_NOT_VERIFIED",
    "NOT_BILLED",
    "PAYMENT_NOT_RECEIVED_BY_DUE_DATE",
    "PARTIALLY_PAID",
    "OVERDUE_30",
    "OVERDUE_60",
    "OVERDUE_90",
    "UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION",
    "AMOUNT_MISMATCH",
    "SECONDARY_PAYER_PAYMENT_MISSING",
    "SHARE_OF_COST_OUTSTANDING",
    "BALANCE_EXCEEDS_THRESHOLD",
    "COLLECTION_FOLLOWUP_REQUIRED",
}

DEFAULT_ALERT_THRESHOLDS = {
    "OVERDUE_30": {"enabled": True, "threshold_days": 30, "threshold_amount": None},
    "OVERDUE_60": {"enabled": True, "threshold_days": 60, "threshold_amount": None},
    "OVERDUE_90": {"enabled": True, "threshold_days": 90, "threshold_amount": None},
    "BALANCE_EXCEEDS_THRESHOLD": {"enabled": True, "threshold_days": None, "threshold_amount": Decimal("0.01")},
}

DEFAULT_PAYMENT_TERM_DAYS = 30
PAYMENT_DERIVED_EXPECTATION_STATUSES = {"PARTIALLY_PAID", "PAID", "OVERPAID"}
ACTIVATABLE_EXPECTATION_STATUSES = {"ACTIVE"} | PAYMENT_DERIVED_EXPECTATION_STATUSES
MATCH_BASIS_EXACT_CLAIM_CONTROL_REFERENCE = "EXACT_CLAIM_CONTROL_REFERENCE"
MATCH_BASIS_EXACT_CLAIM_ASSOCIATION = "EXACT_CLAIM_ASSOCIATION"
MATCH_BASIS_PATIENT_PAYER_SERVICE_PERIOD_AMOUNT = "PATIENT_PAYER_SERVICE_PERIOD_AMOUNT"
MATCH_BASIS_REMITTANCE_LINE_REFERENCE = "REMITTANCE_LINE_REFERENCE"
MATCH_BASIS_MANUAL_RECONCILIATION = "MANUAL_RECONCILIATION"
ALLOWED_MATCH_BASIS = {
    MATCH_BASIS_EXACT_CLAIM_CONTROL_REFERENCE,
    MATCH_BASIS_EXACT_CLAIM_ASSOCIATION,
    MATCH_BASIS_PATIENT_PAYER_SERVICE_PERIOD_AMOUNT,
    MATCH_BASIS_REMITTANCE_LINE_REFERENCE,
    MATCH_BASIS_MANUAL_RECONCILIATION,
}


@dataclass
class ExpectationRollup:
    expected_amount: Decimal
    confirmed_amount: Decimal
    outstanding_amount: Decimal
    most_recent_payment_date: str | None
    reconciliation_status: str
    unconfirmed_allocation_count: int
    confirmed_allocation_count: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _q2(value: Decimal | str | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _jsonish(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(_q2(value))
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return json.dumps({k: _jsonish(v) for k, v in value.items()}, sort_keys=True)
    return str(value)


def _validate_choice(value: str | None, allowed: Iterable[str], field_name: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail=f"{field_name} must be one of {sorted(allowed)}.")
    return normalized


def _bump_row_version(expectation: FacilityPaymentExpectation) -> None:
    expectation.row_version = int(expectation.row_version or 0) + 1


def _assert_expected_row_version(
    expectation: FacilityPaymentExpectation,
    expected_row_version: int | None,
) -> None:
    if expected_row_version is None:
        return
    if int(expectation.row_version or 0) != int(expected_row_version):
        raise HTTPException(
            status_code=409,
            detail="This facility payment expectation was updated by someone else. Reload and retry.",
        )


def _validate_tenant_patient(db: Session, tenant_id: UUID, patient_id: UUID) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .one_or_none()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


def _select_patient_pos(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    patient_pos_id: UUID | None,
) -> PatientPOS | None:
    query = db.query(PatientPOS).filter(
        PatientPOS.tenant_id == tenant_id,
        PatientPOS.patient_id == patient_id,
    )
    if patient_pos_id is not None:
        pos = query.filter(PatientPOS.id == patient_pos_id).one_or_none()
        if pos is None:
            raise HTTPException(status_code=404, detail="PatientPOS not found.")
        return pos

    return (
        query.order_by(
            (PatientPOS.status == "ACTIVE").desc(),
            PatientPOS.effective_date.desc(),
            PatientPOS.created_at.desc(),
        )
        .first()
    )


def _latest_patient_payer_name(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
    payer_name: str | None,
) -> str | None:
    if not payer_name or not payer_name.strip():
        return None
    row = (
        db.query(PatientPayer.payer_name)
        .join(Patient, Patient.id == PatientPayer.patient_id)
        .filter(
            PatientPayer.patient_id == patient_id,
            Patient.tenant_id == tenant_id,
            func.lower(func.trim(PatientPayer.payer_name)) == payer_name.strip().lower(),
        )
        .order_by(PatientPayer.created_at.desc())
        .first()
    )
    return row[0] if row else payer_name


def _snapshot_fields(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    patient_pos_id: UUID | None,
    expected_funding_source: str,
    expected_payer_name_snapshot: str | None,
) -> tuple[PatientPOS | None, dict]:
    pos = _select_patient_pos(db, tenant_id=tenant_id, patient_id=patient_id, patient_pos_id=patient_pos_id)
    primary_payer_name, secondary_payer_name = resolve_primary_secondary_payer_names(db, patient_id)
    return pos, {
        "patient_pos_id": pos.id if pos else None,
        "facility_name_snapshot": pos.facility_name if pos else None,
        "residence_type_snapshot": pos.pos_type if pos else None,
        "room_number_snapshot": pos.room_number if pos else None,
        "residence_start_date_snapshot": pos.effective_date if pos else None,
        "residence_end_date_snapshot": pos.end_date if pos else None,
        "expected_funding_source_snapshot": expected_funding_source,
        "expected_payer_name_snapshot": expected_payer_name_snapshot,
        "primary_payer_name_snapshot": primary_payer_name,
        "secondary_payer_name_snapshot": secondary_payer_name,
    }


def resolve_due_date(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    service_period_end: date,
    explicit_due_date: date | None,
    authorization_reference: str | None,
    contract_reference: str | None,
) -> tuple[date, str, bool]:
    # Precedence slots 1-4 are intentionally stubbed today: this codebase does
    # not yet persist verified payer-rule, contract, authorization, or tenant-
    # configured payment-term sources for facility expectations. When those data
    # sources are added, wire them here without changing callers.
    _ = (db, tenant_id, patient_id, authorization_reference, contract_reference)
    if explicit_due_date is not None:
        return explicit_due_date, "AUTHORIZED_MANUAL_ENTRY", True
    return service_period_end + timedelta(days=DEFAULT_PAYMENT_TERM_DAYS), "SYSTEM_FALLBACK", False


def _flag_allocations_for_review(
    db: Session,
    *,
    expectation: FacilityPaymentExpectation,
    reason: str,
    user_id: UUID | None,
    user_role: str | None,
    confirmed_only: bool = False,
) -> list[UUID]:
    query = db.query(FacilityPaymentAllocation).filter(
        FacilityPaymentAllocation.facility_payment_expectation_id == expectation.id,
        FacilityPaymentAllocation.tenant_id == expectation.tenant_id,
        FacilityPaymentAllocation.allocation_status != "REVERSED",
    )
    if confirmed_only:
        query = query.filter(FacilityPaymentAllocation.allocation_status == "CONFIRMED")
    allocations = query.order_by(FacilityPaymentAllocation.created_at.asc()).all()
    flagged_ids: list[UUID] = []
    for allocation in allocations:
        allocation.flagged_for_review = True
        allocation.flagged_reason = reason
        flagged_ids.append(allocation.id)
        _write_audit(
            db,
            tenant_id=allocation.tenant_id,
            entity_type="ALLOCATION",
            entity_id=allocation.id,
            field_name="FLAGGED_FOR_REVIEW",
            previous_value=False,
            new_value=True,
            user_id=user_id,
            role=user_role,
            reason=reason,
        )
    return flagged_ids


def _write_audit(
    db: Session,
    *,
    tenant_id: UUID,
    entity_type: str,
    entity_id: UUID,
    field_name: str,
    previous_value=None,
    new_value=None,
    user_id: UUID | None = None,
    role: str | None = None,
    reason: str | None = None,
    supporting_reference: str | None = None,
    correlation_id: UUID | None = None,
) -> None:
    _validate_choice(entity_type, FACILITY_AUDIT_ENTITY_TYPES, "entity_type")
    db.add(
        FacilityPaymentAuditLog(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            previous_value=_jsonish(previous_value),
            new_value=_jsonish(new_value),
            user_id=user_id,
            role=role,
            reason=reason,
            supporting_reference=supporting_reference,
            correlation_id=correlation_id,
        )
    )


def _get_existing_candidate(
    db: Session,
    *,
    expectation_id: UUID,
    payment_id: UUID | None,
    remittance_advice_id: UUID | None,
    claim_id: UUID | None,
    payment_adjustment_id: UUID | None,
    match_basis: str,
) -> FacilityPaymentAllocation | None:
    query = db.query(FacilityPaymentAllocation).filter(
        FacilityPaymentAllocation.facility_payment_expectation_id == expectation_id,
        FacilityPaymentAllocation.match_basis == match_basis,
        FacilityPaymentAllocation.allocation_status != "REVERSED",
    )
    if payment_id is not None:
        query = query.filter(FacilityPaymentAllocation.payment_id == payment_id)
    elif remittance_advice_id is not None:
        query = query.filter(FacilityPaymentAllocation.remittance_advice_id == remittance_advice_id)
    elif claim_id is not None:
        query = query.filter(FacilityPaymentAllocation.claim_id == claim_id)
    elif payment_adjustment_id is not None:
        query = query.filter(FacilityPaymentAllocation.payment_adjustment_id == payment_adjustment_id)
    return query.first()


def _get_expectation(db: Session, expectation_id: UUID) -> FacilityPaymentExpectation:
    expectation = db.query(FacilityPaymentExpectation).filter(FacilityPaymentExpectation.id == expectation_id).one_or_none()
    if expectation is None:
        raise HTTPException(status_code=404, detail="Facility payment expectation not found.")
    return expectation


def _get_allocation(db: Session, allocation_id: UUID) -> FacilityPaymentAllocation:
    allocation = db.query(FacilityPaymentAllocation).filter(FacilityPaymentAllocation.id == allocation_id).one_or_none()
    if allocation is None:
        raise HTTPException(status_code=404, detail="Facility payment allocation not found.")
    return allocation


def _get_alert(db: Session, alert_id: UUID) -> FacilityCollectionAlert:
    alert = db.query(FacilityCollectionAlert).filter(FacilityCollectionAlert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Facility collection alert not found.")
    return alert


def compute_rollup(db: Session, expectation: FacilityPaymentExpectation) -> ExpectationRollup:
    expected_amount = _q2(expectation.expected_amount)
    active_allocations = (
        db.query(FacilityPaymentAllocation)
        .filter(
            FacilityPaymentAllocation.facility_payment_expectation_id == expectation.id,
            FacilityPaymentAllocation.tenant_id == expectation.tenant_id,
            FacilityPaymentAllocation.allocation_status != "REVERSED",
        )
        .all()
    )

    confirmed = [a for a in active_allocations if a.allocation_status == "CONFIRMED"]
    unconfirmed = [a for a in active_allocations if a.allocation_status != "CONFIRMED"]
    confirmed_amount = sum((_q2(a.amount_applied) for a in confirmed), Decimal("0.00"))
    outstanding_amount = _q2(expected_amount - confirmed_amount)

    most_recent_payment_date = None
    for allocation in confirmed:
        if allocation.payment_date and (
            most_recent_payment_date is None or allocation.payment_date > most_recent_payment_date
        ):
            most_recent_payment_date = allocation.payment_date

    if confirmed_amount == Decimal("0.00"):
        reconciliation_status = "UNMATCHED_PAYMENT" if unconfirmed else "EXPECTED"
    elif confirmed_amount < expected_amount:
        reconciliation_status = "PARTIALLY_PAID"
    elif confirmed_amount == expected_amount:
        reconciliation_status = "PAID"
    else:
        reconciliation_status = "OVERPAID"

    return ExpectationRollup(
        expected_amount=expected_amount,
        confirmed_amount=confirmed_amount,
        outstanding_amount=outstanding_amount,
        most_recent_payment_date=most_recent_payment_date,
        reconciliation_status=reconciliation_status,
        unconfirmed_allocation_count=len(unconfirmed),
        confirmed_allocation_count=len(confirmed),
    )


def _recompute_expectation(db: Session, expectation: FacilityPaymentExpectation) -> ExpectationRollup:
    rollup = compute_rollup(db, expectation)
    expectation.reconciliation_status = rollup.reconciliation_status
    if expectation.status in ACTIVATABLE_EXPECTATION_STATUSES:
        if rollup.confirmed_amount == Decimal("0.00"):
            expectation.status = "ACTIVE"
        elif rollup.confirmed_amount < rollup.expected_amount:
            expectation.status = "PARTIALLY_PAID"
        elif rollup.confirmed_amount == rollup.expected_amount:
            expectation.status = "PAID"
        else:
            expectation.status = "OVERPAID"
    db.flush()
    return rollup


def create_facility_payment_expectation(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    patient_pos_id: UUID | None = None,
    responsibility_category: str,
    expected_funding_source: str,
    expected_amount: Decimal,
    service_period_start: date,
    service_period_end: date,
    due_date: date | None = None,
    due_date_source: str | None = None,
    payment_term_verified: bool | None = None,
    frequency: str | None = None,
    authorization_reference: str | None = None,
    contract_reference: str | None = None,
    share_of_cost_amount: Decimal | None = None,
    status: str = "DRAFT",
    source: str = "NOT_VERIFIED",
    expected_payer_name_snapshot: str | None = None,
    notes: str | None = None,
    client_request_id: UUID | None = None,
    currency: str = "USD",
    user_id: UUID | None = None,
    user_role: str | None = None,
    auto_commit: bool = True,
) -> FacilityPaymentExpectation:
    if client_request_id is not None:
        existing = (
            db.query(FacilityPaymentExpectation)
            .filter(
                FacilityPaymentExpectation.tenant_id == tenant_id,
                FacilityPaymentExpectation.patient_id == patient_id,
                FacilityPaymentExpectation.client_request_id == client_request_id,
            )
            .one_or_none()
        )
        if existing is not None:
            return existing

    _validate_tenant_patient(db, tenant_id, patient_id)
    responsibility_category = _validate_choice(
        responsibility_category, RESPONSIBILITY_CATEGORIES, "responsibility_category"
    )
    expected_funding_source = _validate_choice(
        expected_funding_source, FACILITY_FUNDING_SOURCES, "expected_funding_source"
    )
    status = _validate_choice(status, FACILITY_EXPECTATION_STATUSES, "status")
    source = _validate_choice(source, FACILITY_EXPECTATION_SOURCES, "source")
    expected_amount = _q2(expected_amount)
    if expected_amount < Decimal("0.00"):
        raise HTTPException(status_code=400, detail="expected_amount must be >= 0.")
    if service_period_end < service_period_start:
        raise HTTPException(status_code=400, detail="service_period_end must be >= service_period_start.")
    if share_of_cost_amount is not None:
        share_of_cost_amount = _q2(share_of_cost_amount)

    expected_payer_name_snapshot = _latest_patient_payer_name(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        payer_name=expected_payer_name_snapshot,
    )
    _, snapshot = _snapshot_fields(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        patient_pos_id=patient_pos_id,
        expected_funding_source=expected_funding_source,
        expected_payer_name_snapshot=expected_payer_name_snapshot,
    )
    resolved_due_date, resolved_due_date_source, resolved_payment_term_verified = resolve_due_date(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        service_period_end=service_period_end,
        explicit_due_date=due_date,
        authorization_reference=authorization_reference,
        contract_reference=contract_reference,
    )
    if due_date_source is not None:
        resolved_due_date_source = _validate_choice(
            due_date_source, FACILITY_DUE_DATE_SOURCES, "due_date_source"
        )
    if payment_term_verified is not None:
        resolved_payment_term_verified = bool(payment_term_verified)

    expectation = FacilityPaymentExpectation(
        tenant_id=tenant_id,
        patient_id=patient_id,
        responsibility_category=responsibility_category,
        expected_funding_source=expected_funding_source,
        expected_amount=expected_amount,
        currency=(currency or "USD").strip().upper(),
        frequency=frequency,
        service_period_start=service_period_start,
        service_period_end=service_period_end,
        due_date=resolved_due_date,
        due_date_source=resolved_due_date_source,
        payment_term_verified=resolved_payment_term_verified,
        authorization_reference=authorization_reference,
        contract_reference=contract_reference,
        share_of_cost_amount=share_of_cost_amount,
        status=status,
        version_number=1,
        source=source,
        notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
        client_request_id=client_request_id,
        created_by=user_id,
        updated_by=user_id,
        **snapshot,
    )
    db.add(expectation)
    db.flush()
    _recompute_expectation(db, expectation)
    _write_audit(
        db,
        tenant_id=tenant_id,
        entity_type="EXPECTATION",
        entity_id=expectation.id,
        field_name="CREATED",
        new_value={
            "responsibility_category": expectation.responsibility_category,
            "expected_funding_source": expectation.expected_funding_source,
            "expected_amount": expectation.expected_amount,
            "status": expectation.status,
            "version_number": expectation.version_number,
            "due_date": expectation.due_date,
            "due_date_source": expectation.due_date_source,
            "payment_term_verified": expectation.payment_term_verified,
            "source": expectation.source,
        },
        user_id=user_id,
        role=user_role,
    )
    if auto_commit:
        db.commit()
        db.refresh(expectation)
        if expectation.status not in {"DRAFT", "CANCELLED", "SUPERSEDED", "CLOSED"}:
            evaluate_alerts_for_expectation(db, expectation=expectation, user_id=user_id, user_role=user_role)
            db.refresh(expectation)
    return expectation


def activate_expectation(
    db: Session,
    *,
    expectation_id: UUID,
    user_id: UUID,
    user_role: str | None = None,
    expected_row_version: int | None = None,
) -> FacilityPaymentExpectation:
    expectation = _get_expectation(db, expectation_id)
    _assert_expected_row_version(expectation, expected_row_version)
    if expectation.status in ACTIVATABLE_EXPECTATION_STATUSES:
        return expectation
    if expectation.status != "DRAFT":
        raise HTTPException(status_code=409, detail="Only DRAFT expectations can be activated.")
    missing_fields: list[str] = []
    for field_name in (
        "responsibility_category",
        "expected_funding_source",
        "expected_amount",
        "service_period_start",
        "service_period_end",
    ):
        if getattr(expectation, field_name, None) in (None, ""):
            missing_fields.append(field_name)
    if expectation.source == "NOT_VERIFIED":
        missing_fields.append("source")
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Expectation is incomplete and cannot be activated. Missing or unverified: {', '.join(missing_fields)}.",
        )

    previous_status = expectation.status
    expectation.status = "ACTIVE"
    expectation.updated_by = user_id
    expectation.cancelled_at = None
    expectation.cancelled_by = None
    expectation.cancellation_reason = None
    _bump_row_version(expectation)
    _recompute_expectation(db, expectation)
    _write_audit(
        db,
        tenant_id=expectation.tenant_id,
        entity_type="EXPECTATION",
        entity_id=expectation.id,
        field_name="EXPECTATION_ACTIVATED",
        previous_value=previous_status,
        new_value=expectation.status,
        user_id=user_id,
        role=user_role,
    )
    db.commit()
    db.refresh(expectation)
    evaluate_alerts_for_expectation(db, expectation=expectation, user_id=user_id, user_role=user_role)
    db.refresh(expectation)
    return expectation


def cancel_expectation(
    db: Session,
    *,
    expectation_id: UUID,
    cancellation_reason: str,
    user_id: UUID,
    user_role: str | None = None,
    expected_row_version: int | None = None,
    force: bool = False,
) -> FacilityPaymentExpectation:
    expectation = _get_expectation(db, expectation_id)
    _assert_expected_row_version(expectation, expected_row_version)
    if not cancellation_reason or not cancellation_reason.strip():
        raise HTTPException(status_code=400, detail="cancellation_reason is required.")
    if expectation.status == "CANCELLED":
        return expectation
    if expectation.status in {"SUPERSEDED", "CLOSED"}:
        raise HTTPException(status_code=409, detail="This expectation cannot be cancelled from its current status.")

    confirmed_allocations = (
        db.query(FacilityPaymentAllocation)
        .filter(
            FacilityPaymentAllocation.facility_payment_expectation_id == expectation.id,
            FacilityPaymentAllocation.tenant_id == expectation.tenant_id,
            FacilityPaymentAllocation.allocation_status == "CONFIRMED",
        )
        .order_by(FacilityPaymentAllocation.created_at.asc())
        .all()
    )
    if confirmed_allocations and not force:
        raise HTTPException(
            status_code=409,
            detail="Confirmed allocations exist for this expectation. Re-submit with force=true after acknowledging allocation review.",
        )

    previous_status = expectation.status
    expectation.status = "CANCELLED"
    expectation.cancellation_reason = cancellation_reason.strip()
    expectation.cancelled_at = _now()
    expectation.cancelled_by = user_id
    expectation.updated_by = user_id
    _bump_row_version(expectation)

    flagged_ids: list[UUID] = []
    if confirmed_allocations:
        flagged_ids = _flag_allocations_for_review(
            db,
            expectation=expectation,
            reason="Expectation was cancelled after payments had already been applied; review these allocations.",
            user_id=user_id,
            user_role=user_role,
            confirmed_only=True,
        )

    _write_audit(
        db,
        tenant_id=expectation.tenant_id,
        entity_type="EXPECTATION",
        entity_id=expectation.id,
        field_name="EXPECTATION_CANCELLED",
        previous_value=previous_status,
        new_value={
            "status": expectation.status,
            "flagged_allocation_ids": flagged_ids,
        },
        user_id=user_id,
        role=user_role,
        reason=expectation.cancellation_reason,
    )
    db.commit()
    db.refresh(expectation)
    return expectation


def create_corrected_expectation_version(
    db: Session,
    *,
    previous_expectation_id: UUID,
    correction_reason: str,
    user_id: UUID,
    user_role: str | None = None,
    expected_row_version: int | None = None,
    patient_pos_id: UUID | None = None,
    responsibility_category: str | None = None,
    expected_funding_source: str | None = None,
    expected_amount: Decimal | None = None,
    service_period_start: date | None = None,
    service_period_end: date | None = None,
    due_date: date | None = None,
    frequency: str | None = None,
    authorization_reference: str | None = None,
    contract_reference: str | None = None,
    share_of_cost_amount: Decimal | None = None,
    status: str | None = None,
    source: str | None = None,
    expected_payer_name_snapshot: str | None = None,
    notes: str | None = None,
    currency: str | None = None,
) -> FacilityPaymentExpectation:
    previous = _get_expectation(db, previous_expectation_id)
    if not correction_reason or not correction_reason.strip():
        raise HTTPException(status_code=400, detail="correction_reason is required.")
    _assert_expected_row_version(previous, expected_row_version)

    changed_expected_amount = (
        expected_amount is not None and _q2(expected_amount) != _q2(previous.expected_amount)
    )
    changed_service_period = any(
        [
            service_period_start is not None and service_period_start != previous.service_period_start,
            service_period_end is not None and service_period_end != previous.service_period_end,
        ]
    )

    correlation_id = uuid.uuid4()
    previous_status = previous.status
    previous.status = "SUPERSEDED"
    previous.updated_by = user_id
    _bump_row_version(previous)

    corrected = create_facility_payment_expectation(
        db,
        tenant_id=previous.tenant_id,
        patient_id=previous.patient_id,
        patient_pos_id=patient_pos_id if patient_pos_id is not None else previous.patient_pos_id,
        responsibility_category=responsibility_category or previous.responsibility_category,
        expected_funding_source=expected_funding_source or previous.expected_funding_source,
        expected_amount=expected_amount if expected_amount is not None else _q2(previous.expected_amount),
        service_period_start=service_period_start or previous.service_period_start,
        service_period_end=service_period_end or previous.service_period_end,
        due_date=due_date if due_date is not None else previous.due_date,
        frequency=frequency if frequency is not None else previous.frequency,
        authorization_reference=(
            authorization_reference if authorization_reference is not None else previous.authorization_reference
        ),
        contract_reference=(
            contract_reference if contract_reference is not None else previous.contract_reference
        ),
        share_of_cost_amount=(
            share_of_cost_amount if share_of_cost_amount is not None else previous.share_of_cost_amount
        ),
        status=status or "ACTIVE",
        source=source or previous.source,
        expected_payer_name_snapshot=(
            expected_payer_name_snapshot
            if expected_payer_name_snapshot is not None
            else previous.expected_payer_name_snapshot
        ),
        notes=notes if notes is not None else previous.notes,
        currency=currency or previous.currency,
        user_id=user_id,
        user_role=user_role,
        auto_commit=False,
    )
    corrected.version_number = int(previous.version_number or 1) + 1
    corrected.supersedes_expectation_id = previous.id
    corrected.correction_reason = correction_reason.strip()
    corrected.updated_by = user_id
    previous.superseded_by_expectation_id = corrected.id

    flagged_ids: list[UUID] = []
    if changed_expected_amount or changed_service_period:
        flagged_ids = _flag_allocations_for_review(
            db,
            expectation=previous,
            reason=(
                "Expectation correction changed the expected amount and/or service period; "
                "review prior allocations before relying on them."
            ),
            user_id=user_id,
            user_role=user_role,
        )

    _write_audit(
        db,
        tenant_id=previous.tenant_id,
        entity_type="EXPECTATION",
        entity_id=previous.id,
        field_name="status",
        previous_value=previous_status,
        new_value=previous.status,
        user_id=user_id,
        role=user_role,
        reason=correction_reason,
        correlation_id=correlation_id,
    )
    _write_audit(
        db,
        tenant_id=corrected.tenant_id,
        entity_type="EXPECTATION",
        entity_id=corrected.id,
        field_name="CORRECTED_VERSION_CREATED",
        previous_value=previous.id,
        new_value=corrected.id,
        user_id=user_id,
        role=user_role,
        reason=correction_reason,
        correlation_id=correlation_id,
    )
    if flagged_ids:
        _write_audit(
            db,
            tenant_id=previous.tenant_id,
            entity_type="EXPECTATION",
            entity_id=previous.id,
            field_name="ALLOCATIONS_FLAGGED_FOR_REVIEW",
            previous_value=None,
            new_value={"allocation_ids": flagged_ids},
            user_id=user_id,
            role=user_role,
            reason=correction_reason,
            correlation_id=correlation_id,
        )
    db.commit()
    db.refresh(previous)
    db.refresh(corrected)
    evaluate_alerts_for_expectation(db, expectation=corrected, user_id=user_id, user_role=user_role)
    return corrected


def _payments_for_rule_1(db: Session, expectation: FacilityPaymentExpectation):
    if not expectation.authorization_reference or not expectation.authorization_reference.strip():
        return []
    reference = expectation.authorization_reference.strip()
    return (
        db.query(Payment, RemittanceAdvice)
        .join(RemittanceAdvice, RemittanceAdvice.id == Payment.remittance_advice_id)
        .filter(Payment.tenant_id == expectation.tenant_id)
        .filter(Payment.claim_control_number == reference)
        .all()
    )


def _payments_for_rule_2(db: Session, expectation: FacilityPaymentExpectation):
    return (
        db.query(Payment, RemittanceAdvice, Claim)
        .join(RemittanceAdvice, RemittanceAdvice.id == Payment.remittance_advice_id)
        .join(Claim, Claim.id == Payment.claim_id)
        .filter(Payment.tenant_id == expectation.tenant_id)
        .filter(Claim.patient_id == expectation.patient_id)
        .all()
    )


def _payments_for_rule_3(db: Session, expectation: FacilityPaymentExpectation):
    payer_names = {
        n.strip().lower()
        for n in (
            expectation.expected_payer_name_snapshot,
            expectation.primary_payer_name_snapshot,
            expectation.secondary_payer_name_snapshot,
        )
        if n and n.strip()
    }
    if not payer_names:
        return []
    rows = (
        db.query(Payment, RemittanceAdvice, Claim)
        .join(RemittanceAdvice, RemittanceAdvice.id == Payment.remittance_advice_id)
        .join(Claim, Claim.id == Payment.claim_id)
        .filter(Payment.tenant_id == expectation.tenant_id)
        .filter(Claim.patient_id == expectation.patient_id)
        .filter(Claim.service_date >= expectation.service_period_start)
        .filter(Claim.service_date <= expectation.service_period_end)
        .all()
    )
    expected_amount = _q2(expectation.expected_amount)
    return [
        row
        for row in rows
        if (row[1].payer_name or "").strip().lower() in payer_names and _q2(row[0].paid_amount) == expected_amount
    ]


def _create_proposed_allocation(
    db: Session,
    *,
    expectation: FacilityPaymentExpectation,
    payment: Payment | None,
    remittance_advice: RemittanceAdvice | None,
    claim: Claim | None,
    payment_adjustment: PaymentAdjustment | None,
    amount_applied: Decimal,
    payment_date: str | None,
    payer_name: str | None,
    match_basis: str,
    allocation_status: str,
    notes: str | None = None,
) -> FacilityPaymentAllocation:
    _validate_choice(match_basis, ALLOWED_MATCH_BASIS, "match_basis")
    _validate_choice(allocation_status, FACILITY_ALLOCATION_STATUSES, "allocation_status")
    existing = _get_existing_candidate(
        db,
        expectation_id=expectation.id,
        payment_id=payment.id if payment else None,
        remittance_advice_id=remittance_advice.id if remittance_advice else None,
        claim_id=claim.id if claim else None,
        payment_adjustment_id=payment_adjustment.id if payment_adjustment else None,
        match_basis=match_basis,
    )
    if existing is not None:
        return existing

    allocation = FacilityPaymentAllocation(
        tenant_id=expectation.tenant_id,
        facility_payment_expectation_id=expectation.id,
        payment_id=payment.id if payment else None,
        remittance_advice_id=remittance_advice.id if remittance_advice else None,
        claim_id=claim.id if claim else None,
        payment_adjustment_id=payment_adjustment.id if payment_adjustment else None,
        payer_name=payer_name,
        amount_applied=_q2(amount_applied),
        payment_date=payment_date,
        allocation_status=allocation_status,
        match_basis=match_basis,
        notes=notes,
    )
    db.add(allocation)
    db.flush()
    _write_audit(
        db,
        tenant_id=expectation.tenant_id,
        entity_type="ALLOCATION",
        entity_id=allocation.id,
        field_name="CREATED",
        new_value={
            "allocation_status": allocation.allocation_status,
            "match_basis": allocation.match_basis,
            "payment_id": allocation.payment_id,
            "claim_id": allocation.claim_id,
        },
        reason=notes,
    )
    return allocation


def find_candidate_matches(
    db: Session,
    *,
    expectation: FacilityPaymentExpectation,
) -> list[FacilityPaymentAllocation]:
    existing = (
        db.query(FacilityPaymentAllocation)
        .filter(
            FacilityPaymentAllocation.facility_payment_expectation_id == expectation.id,
            FacilityPaymentAllocation.tenant_id == expectation.tenant_id,
            FacilityPaymentAllocation.allocation_status.in_(["PROPOSED", "MANUAL_REVIEW_REQUIRED"]),
        )
        .order_by(FacilityPaymentAllocation.created_at.asc())
        .all()
    )
    if existing:
        return existing

    candidates: list[FacilityPaymentAllocation] = []

    rule_1_rows = _payments_for_rule_1(db, expectation)
    if rule_1_rows:
        for payment, remittance in rule_1_rows:
            candidates.append(
                _create_proposed_allocation(
                    db,
                    expectation=expectation,
                    payment=payment,
                    remittance_advice=remittance,
                    claim=payment.claim,
                    payment_adjustment=None,
                    amount_applied=_q2(payment.paid_amount),
                    payment_date=payment.payment_date or remittance.payment_date,
                    payer_name=remittance.payer_name,
                    match_basis=MATCH_BASIS_EXACT_CLAIM_CONTROL_REFERENCE,
                    allocation_status="PROPOSED",
                )
            )
    else:
        rule_2_rows = _payments_for_rule_2(db, expectation)
        if rule_2_rows:
            for payment, remittance, claim in rule_2_rows:
                candidates.append(
                    _create_proposed_allocation(
                        db,
                        expectation=expectation,
                        payment=payment,
                        remittance_advice=remittance,
                        claim=claim,
                        payment_adjustment=None,
                        amount_applied=_q2(payment.paid_amount),
                        payment_date=payment.payment_date or remittance.payment_date,
                        payer_name=remittance.payer_name,
                        match_basis=MATCH_BASIS_EXACT_CLAIM_ASSOCIATION,
                        allocation_status="PROPOSED",
                    )
                )
        else:
            rule_3_rows = _payments_for_rule_3(db, expectation)
            if rule_3_rows:
                for payment, remittance, claim in rule_3_rows:
                    candidates.append(
                        _create_proposed_allocation(
                            db,
                            expectation=expectation,
                            payment=payment,
                            remittance_advice=remittance,
                            claim=claim,
                            payment_adjustment=None,
                            amount_applied=_q2(payment.paid_amount),
                            payment_date=payment.payment_date or remittance.payment_date,
                            payer_name=remittance.payer_name,
                            match_basis=MATCH_BASIS_PATIENT_PAYER_SERVICE_PERIOD_AMOUNT,
                            allocation_status="PROPOSED",
                        )
                    )
            else:
                candidates.append(
                    _create_proposed_allocation(
                        db,
                        expectation=expectation,
                        payment=None,
                        remittance_advice=None,
                        claim=None,
                        payment_adjustment=None,
                        amount_applied=Decimal("0.00"),
                        payment_date=None,
                        payer_name=expectation.expected_payer_name_snapshot,
                        match_basis=MATCH_BASIS_MANUAL_RECONCILIATION,
                        allocation_status="MANUAL_REVIEW_REQUIRED",
                        notes=(
                            "No exact payment candidate matched. Current schema has no dedicated remittance-line "
                            "reference field for rule-4 auto-proposal, so manual reconciliation is required."
                        ),
                    )
                )

    _recompute_expectation(db, expectation)
    db.commit()
    db.refresh(expectation)
    evaluate_alerts_for_expectation(db, expectation=expectation)
    return candidates


def confirm_allocation(
    db: Session,
    *,
    allocation_id: UUID,
    user_id: UUID,
    user_role: str | None = None,
) -> FacilityPaymentAllocation:
    allocation = _get_allocation(db, allocation_id)
    if allocation.allocation_status != "PROPOSED":
        raise HTTPException(status_code=409, detail="Only PROPOSED allocations may be confirmed.")
    if not any([allocation.payment_id, allocation.remittance_advice_id, allocation.claim_id, allocation.payment_adjustment_id]):
        raise HTTPException(status_code=400, detail="A confirmed allocation must reference a real payment source.")
    if allocation.payment_id is not None and _q2(allocation.amount_applied) > Decimal("0.00"):
        duplicate = (
            db.query(FacilityPaymentAllocation)
            .filter(
                FacilityPaymentAllocation.payment_id == allocation.payment_id,
                FacilityPaymentAllocation.id != allocation.id,
                FacilityPaymentAllocation.allocation_status == "CONFIRMED",
                FacilityPaymentAllocation.amount_applied > 0,
            )
            .first()
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=409,
                detail="This payment is already confirmed against another expectation and cannot be double-counted.",
            )
    previous_reconciliation_status = allocation.expectation.reconciliation_status
    previous_expectation_status = allocation.expectation.status
    previous_status = allocation.allocation_status
    allocation.allocation_status = "CONFIRMED"
    allocation.reconciled_by = user_id
    allocation.reconciled_at = _now()
    expectation = allocation.expectation
    expectation.updated_by = user_id
    _bump_row_version(expectation)
    rollup = _recompute_expectation(db, expectation)
    _write_audit(
        db,
        tenant_id=allocation.tenant_id,
        entity_type="ALLOCATION",
        entity_id=allocation.id,
        field_name="allocation_status",
        previous_value=previous_status,
        new_value=allocation.allocation_status,
        user_id=user_id,
        role=user_role,
    )
    _write_audit(
        db,
        tenant_id=expectation.tenant_id,
        entity_type="EXPECTATION",
        entity_id=expectation.id,
        field_name="reconciliation_status",
        previous_value=previous_reconciliation_status,
        new_value=rollup.reconciliation_status,
        user_id=user_id,
        role=user_role,
    )
    if previous_expectation_status != expectation.status:
        _write_audit(
            db,
            tenant_id=expectation.tenant_id,
            entity_type="EXPECTATION",
            entity_id=expectation.id,
            field_name="status",
            previous_value=previous_expectation_status,
            new_value=expectation.status,
            user_id=user_id,
            role=user_role,
        )
    db.commit()
    db.refresh(allocation)
    db.refresh(expectation)
    evaluate_alerts_for_expectation(db, expectation=expectation, user_id=user_id, user_role=user_role)
    return allocation


def reverse_allocation(
    db: Session,
    *,
    allocation_id: UUID,
    user_id: UUID,
    reason: str,
    user_role: str | None = None,
) -> FacilityPaymentAllocation:
    allocation = _get_allocation(db, allocation_id)
    if allocation.allocation_status != "CONFIRMED":
        raise HTTPException(status_code=409, detail="Only CONFIRMED allocations may be reversed.")
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="reason is required.")
    previous_status = allocation.allocation_status
    allocation.allocation_status = "REVERSED"
    allocation.notes = reason.strip()
    expectation = allocation.expectation
    expectation.updated_by = user_id
    previous_reconciliation_status = expectation.reconciliation_status
    previous_expectation_status = expectation.status
    _bump_row_version(expectation)
    rollup = _recompute_expectation(db, expectation)
    _write_audit(
        db,
        tenant_id=allocation.tenant_id,
        entity_type="ALLOCATION",
        entity_id=allocation.id,
        field_name="allocation_status",
        previous_value=previous_status,
        new_value=allocation.allocation_status,
        user_id=user_id,
        role=user_role,
        reason=reason,
    )
    _write_audit(
        db,
        tenant_id=expectation.tenant_id,
        entity_type="EXPECTATION",
        entity_id=expectation.id,
        field_name="reconciliation_status",
        previous_value=previous_reconciliation_status,
        new_value=rollup.reconciliation_status,
        user_id=user_id,
        role=user_role,
        reason=reason,
    )
    if previous_expectation_status != expectation.status:
        _write_audit(
            db,
            tenant_id=expectation.tenant_id,
            entity_type="EXPECTATION",
            entity_id=expectation.id,
            field_name="status",
            previous_value=previous_expectation_status,
            new_value=expectation.status,
            user_id=user_id,
            role=user_role,
            reason=reason,
        )
    db.commit()
    db.refresh(allocation)
    db.refresh(expectation)
    evaluate_alerts_for_expectation(db, expectation=expectation, user_id=user_id, user_role=user_role)
    return allocation


def compute_aging(expectation: FacilityPaymentExpectation, *, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    basis_date = expectation.due_date
    basis_source = expectation.due_date_source if expectation.due_date else None
    if basis_date is None and expectation.service_period_end is not None:
        # No payer-specific payment terms exist yet, so aging defaults to
        # service_period_end + 30 days until tenant/payer term configuration exists.
        basis_date = expectation.service_period_end + timedelta(days=DEFAULT_PAYMENT_TERM_DAYS)
        basis_source = "SYSTEM_FALLBACK"
    if basis_date is None:
        return {
            "aging_status": "NOT_VERIFIED",
            "aging_bucket": "NOT_VERIFIED",
            "days_outstanding": None,
            "aging_basis_date": None,
            "aging_basis_source": None,
        }

    days_outstanding = max((as_of - basis_date).days, 0)
    if days_outstanding <= 30:
        aging_bucket = "0-30"
    elif days_outstanding <= 60:
        aging_bucket = "31-60"
    elif days_outstanding <= 90:
        aging_bucket = "61-90"
    elif days_outstanding <= 120:
        aging_bucket = "91-120"
    else:
        aging_bucket = "120+"
    return {
        "aging_status": "VERIFIED",
        "aging_bucket": aging_bucket,
        "days_outstanding": days_outstanding,
        "aging_basis_date": basis_date.isoformat(),
        "aging_basis_source": basis_source,
    }


def _threshold_settings(db: Session, tenant_id: UUID, alert_type: str) -> dict:
    default = DEFAULT_ALERT_THRESHOLDS.get(
        alert_type,
        {"enabled": True, "threshold_days": None, "threshold_amount": None},
    )
    row = (
        db.query(FacilityCollectionAlertThreshold)
        .filter(
            FacilityCollectionAlertThreshold.tenant_id == tenant_id,
            FacilityCollectionAlertThreshold.alert_type == alert_type,
        )
        .one_or_none()
    )
    if row is None:
        return default
    return {
        "enabled": row.enabled,
        "threshold_days": row.threshold_days if row.threshold_days is not None else default["threshold_days"],
        "threshold_amount": (
            _q2(row.threshold_amount) if row.threshold_amount is not None else default["threshold_amount"]
        ),
    }


def _upsert_open_alert(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    expectation_id: UUID,
    alert_type: str,
    severity: str,
    expected_amount: Decimal | None,
    received_amount: Decimal | None,
    outstanding_amount: Decimal | None,
    due_date: date | None,
    days_outstanding: int | None,
    user_id: UUID | None = None,
    user_role: str | None = None,
) -> FacilityCollectionAlert:
    _validate_choice(alert_type, ALERT_TYPES, "alert_type")
    _validate_choice(severity, FACILITY_COLLECTION_ALERT_SEVERITIES, "severity")
    alert = (
        db.query(FacilityCollectionAlert)
        .filter(
            FacilityCollectionAlert.tenant_id == tenant_id,
            FacilityCollectionAlert.facility_payment_expectation_id == expectation_id,
            FacilityCollectionAlert.alert_type == alert_type,
            FacilityCollectionAlert.status == "OPEN",
        )
        .one_or_none()
    )
    created = alert is None
    if alert is None:
        alert = FacilityCollectionAlert(
            tenant_id=tenant_id,
            patient_id=patient_id,
            facility_payment_expectation_id=expectation_id,
            alert_type=alert_type,
            severity=severity,
            status="OPEN",
        )
        db.add(alert)
        db.flush()
    alert.severity = severity
    alert.expected_amount = _q2(expected_amount) if expected_amount is not None else None
    alert.received_amount = _q2(received_amount) if received_amount is not None else None
    alert.outstanding_amount = _q2(outstanding_amount) if outstanding_amount is not None else None
    alert.due_date = due_date
    alert.days_outstanding = days_outstanding
    _write_audit(
        db,
        tenant_id=tenant_id,
        entity_type="ALERT",
        entity_id=alert.id,
        field_name="CREATED" if created else "UPDATED",
        new_value={
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status,
            "outstanding_amount": alert.outstanding_amount,
        },
        user_id=user_id,
        role=user_role,
    )
    return alert


def evaluate_alerts_for_expectation(
    db: Session,
    *,
    expectation: FacilityPaymentExpectation,
    user_id: UUID | None = None,
    user_role: str | None = None,
) -> list[FacilityCollectionAlert]:
    if expectation.status in {"DRAFT", "CANCELLED", "SUPERSEDED", "CLOSED"}:
        return []
    rollup = _recompute_expectation(db, expectation)
    aging = compute_aging(expectation)
    alerts: list[FacilityCollectionAlert] = []
    outstanding_positive = rollup.outstanding_amount > Decimal("0.00")

    if expectation.expected_funding_source == "NOT_VERIFIED":
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="FUNDING_SOURCE_NOT_VERIFIED",
                severity="HIGH",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    if expectation.reconciliation_status == "PARTIALLY_PAID":
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="PARTIALLY_PAID",
                severity="MEDIUM",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    if expectation.reconciliation_status == "UNMATCHED_PAYMENT":
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION",
                severity="HIGH",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    if expectation.reconciliation_status == "OVERPAID":
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="AMOUNT_MISMATCH",
                severity="HIGH",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    if outstanding_positive and expectation.due_date and date.today() > expectation.due_date:
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="PAYMENT_NOT_RECEIVED_BY_DUE_DATE",
                severity="HIGH",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    if outstanding_positive and expectation.responsibility_category == "SHARE_OF_COST":
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="SHARE_OF_COST_OUTSTANDING",
                severity="MEDIUM",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    for alert_type in ("OVERDUE_30", "OVERDUE_60", "OVERDUE_90"):
        settings = _threshold_settings(db, expectation.tenant_id, alert_type)
        if (
            settings["enabled"]
            and outstanding_positive
            and aging["days_outstanding"] is not None
            and settings["threshold_days"] is not None
            and aging["days_outstanding"] >= settings["threshold_days"]
        ):
            severity = "MEDIUM" if alert_type == "OVERDUE_30" else "HIGH" if alert_type == "OVERDUE_60" else "CRITICAL"
            alerts.append(
                _upsert_open_alert(
                    db,
                    tenant_id=expectation.tenant_id,
                    patient_id=expectation.patient_id,
                    expectation_id=expectation.id,
                    alert_type=alert_type,
                    severity=severity,
                    expected_amount=rollup.expected_amount,
                    received_amount=rollup.confirmed_amount,
                    outstanding_amount=rollup.outstanding_amount,
                    due_date=expectation.due_date,
                    days_outstanding=aging["days_outstanding"],
                    user_id=user_id,
                    user_role=user_role,
                )
            )

    balance_settings = _threshold_settings(db, expectation.tenant_id, "BALANCE_EXCEEDS_THRESHOLD")
    if (
        balance_settings["enabled"]
        and outstanding_positive
        and balance_settings["threshold_amount"] is not None
        and rollup.outstanding_amount >= balance_settings["threshold_amount"]
    ):
        alerts.append(
            _upsert_open_alert(
                db,
                tenant_id=expectation.tenant_id,
                patient_id=expectation.patient_id,
                expectation_id=expectation.id,
                alert_type="BALANCE_EXCEEDS_THRESHOLD",
                severity="MEDIUM",
                expected_amount=rollup.expected_amount,
                received_amount=rollup.confirmed_amount,
                outstanding_amount=rollup.outstanding_amount,
                due_date=expectation.due_date,
                days_outstanding=aging["days_outstanding"],
                user_id=user_id,
                user_role=user_role,
            )
        )

    db.commit()
    return alerts


def resolve_alert(
    db: Session,
    *,
    alert_id: UUID,
    user_id: UUID,
    resolution_evidence: str,
    user_role: str | None = None,
) -> FacilityCollectionAlert:
    alert = _get_alert(db, alert_id)
    if not resolution_evidence or not resolution_evidence.strip():
        raise HTTPException(status_code=400, detail="resolution_evidence is required.")
    previous_status = alert.status
    alert.status = "RESOLVED"
    alert.resolution_evidence = resolution_evidence.strip()
    alert.resolved_by = user_id
    alert.resolved_at = _now()
    _write_audit(
        db,
        tenant_id=alert.tenant_id,
        entity_type="ALERT",
        entity_id=alert.id,
        field_name="status",
        previous_value=previous_status,
        new_value=alert.status,
        user_id=user_id,
        role=user_role,
        reason=resolution_evidence,
    )
    db.commit()
    db.refresh(alert)
    return alert


def list_thresholds(db: Session, *, tenant_id: UUID) -> list[dict]:
    configured = {
        row.alert_type: row
        for row in db.query(FacilityCollectionAlertThreshold).filter(
            FacilityCollectionAlertThreshold.tenant_id == tenant_id
        )
    }
    alert_types = sorted(set(DEFAULT_ALERT_THRESHOLDS) | set(configured))
    rows = []
    for alert_type in alert_types:
        settings = _threshold_settings(db, tenant_id, alert_type)
        row = configured.get(alert_type)
        rows.append(
            {
                "id": str(row.id) if row else None,
                "tenant_id": str(tenant_id),
                "alert_type": alert_type,
                "enabled": bool(settings["enabled"]),
                "threshold_amount": str(settings["threshold_amount"]) if settings["threshold_amount"] is not None else None,
                "threshold_days": settings["threshold_days"],
                "is_default": row is None,
            }
        )
    return rows


def update_threshold(
    db: Session,
    *,
    tenant_id: UUID,
    alert_type: str,
    enabled: bool,
    threshold_amount: Decimal | None,
    threshold_days: int | None,
    user_id: UUID | None = None,
    user_role: str | None = None,
) -> FacilityCollectionAlertThreshold:
    _validate_choice(alert_type, ALERT_TYPES | set(DEFAULT_ALERT_THRESHOLDS.keys()), "alert_type")
    row = (
        db.query(FacilityCollectionAlertThreshold)
        .filter(
            FacilityCollectionAlertThreshold.tenant_id == tenant_id,
            FacilityCollectionAlertThreshold.alert_type == alert_type,
        )
        .one_or_none()
    )
    if row is None:
        row = FacilityCollectionAlertThreshold(tenant_id=tenant_id, alert_type=alert_type)
        db.add(row)
        db.flush()
    previous = {
        "enabled": row.enabled,
        "threshold_amount": row.threshold_amount,
        "threshold_days": row.threshold_days,
    }
    row.enabled = bool(enabled)
    row.threshold_amount = _q2(threshold_amount) if threshold_amount is not None else None
    row.threshold_days = threshold_days
    _write_audit(
        db,
        tenant_id=tenant_id,
        entity_type="ALERT",
        entity_id=row.id,
        field_name="THRESHOLD_UPDATED",
        previous_value=previous,
        new_value={
            "enabled": row.enabled,
            "threshold_amount": row.threshold_amount,
            "threshold_days": row.threshold_days,
        },
        user_id=user_id,
        role=user_role,
    )
    db.commit()
    db.refresh(row)
    return row


def expectation_history(
    db: Session,
    *,
    expectation_id: UUID,
) -> list[FacilityPaymentExpectation]:
    current = _get_expectation(db, expectation_id)
    root = current
    backward_seen: set[UUID] = set()
    while root.supersedes_expectation_id and root.supersedes_expectation_id not in backward_seen:
        backward_seen.add(root.id)
        root = _get_expectation(db, root.supersedes_expectation_id)

    items: list[FacilityPaymentExpectation] = []
    forward_seen: set[UUID] = set()
    cursor: FacilityPaymentExpectation | None = root
    while cursor is not None and cursor.id not in forward_seen:
        forward_seen.add(cursor.id)
        items.append(cursor)
        if cursor.superseded_by_expectation_id is None:
            break
        cursor = _get_expectation(db, cursor.superseded_by_expectation_id)
    return items


def residence_snapshot_diff(
    db: Session,
    *,
    expectation_id: UUID,
) -> dict:
    expectation = _get_expectation(db, expectation_id)
    current_pos = _select_patient_pos(
        db,
        tenant_id=expectation.tenant_id,
        patient_id=expectation.patient_id,
        patient_pos_id=None,
    )
    if current_pos is None and expectation.patient_pos_id is not None:
        current_pos = _select_patient_pos(
            db,
            tenant_id=expectation.tenant_id,
            patient_id=expectation.patient_id,
            patient_pos_id=expectation.patient_pos_id,
        )
    primary_payer_name, secondary_payer_name = resolve_primary_secondary_payer_names(db, expectation.patient_id)

    def _diff(snapshot, current):
        return {
            "snapshot": snapshot.isoformat() if isinstance(snapshot, date) else snapshot,
            "current": current.isoformat() if isinstance(current, date) else current,
            "changed": snapshot != current,
        }

    fields = {
        "facility_name": _diff(expectation.facility_name_snapshot, current_pos.facility_name if current_pos else None),
        "residence_type": _diff(expectation.residence_type_snapshot, current_pos.pos_type if current_pos else None),
        "room_number": _diff(expectation.room_number_snapshot, current_pos.room_number if current_pos else None),
        "residence_start_date": _diff(
            expectation.residence_start_date_snapshot,
            current_pos.effective_date if current_pos else None,
        ),
        "residence_end_date": _diff(
            expectation.residence_end_date_snapshot,
            current_pos.end_date if current_pos else None,
        ),
        "primary_payer_name": _diff(expectation.primary_payer_name_snapshot, primary_payer_name),
        "secondary_payer_name": _diff(expectation.secondary_payer_name_snapshot, secondary_payer_name),
    }
    return {
        "expectation_id": str(expectation.id),
        "patient_id": str(expectation.patient_id),
        "patient_pos_id": str(expectation.patient_pos_id) if expectation.patient_pos_id else None,
        "has_changes": any(item["changed"] for item in fields.values()),
        "fields": fields,
    }


def expectation_patient_context(db: Session, expectation: FacilityPaymentExpectation) -> dict:
    patient_row = (
        db.query(
            Patient.id,
            Patient.mrn,
            PatientFaceSheet.first_name,
            PatientFaceSheet.middle_name,
            PatientFaceSheet.last_name,
            Tenant.legal_name,
            Tenant.display_name,
        )
        .join(Tenant, Tenant.id == Patient.tenant_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Patient.id == expectation.patient_id)
        .first()
    )
    if patient_row is None:
        return {"patient_name": None, "mrn": None, "agency_name": None}
    return {
        "patient_name": patient_display_name(
            patient_row.first_name,
            patient_row.middle_name,
            patient_row.last_name,
        ),
        "mrn": patient_row.mrn,
        "agency_name": patient_row.display_name or patient_row.legal_name,
    }
