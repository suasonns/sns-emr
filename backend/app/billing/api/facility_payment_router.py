from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.billing.models.facility_collection_alert import FacilityCollectionAlert
from app.billing.models.facility_payment_allocation import FacilityPaymentAllocation
from app.billing.models.facility_payment_audit_log import FacilityPaymentAuditLog
from app.billing.models.facility_payment_expectation import FacilityPaymentExpectation
from app.billing.security import require_automated_billing
from app.billing.services.billing_provider_access_service import (
    resolve_authorized_tenant_ids_for_scope,
)
from app.billing.services import facility_payment_service as facility_service
from app.core.database import get_db
from app.core.roles import BILLING_DEPARTMENT_ROLES, FINANCIAL_ADMIN_ROLES, normalize_role
from app.core.security import get_current_user

router = APIRouter(prefix="/billing/facility-payments", tags=["Billing Reports"])


def _can_access_financial_surfaces(user) -> bool:
    role = normalize_role(getattr(user, "role", None))
    return bool(role) and (
        role in FINANCIAL_ADMIN_ROLES
        or role in BILLING_DEPARTMENT_ROLES
        or role == "PLATFORM_BILLING"
    )


def _require_financial_access(user) -> None:
    if not _can_access_financial_surfaces(user):
        raise HTTPException(status_code=403, detail="Facility payment visibility is limited to billing and finance roles.")


def _require_financial_edit_access(user) -> None:
    _require_financial_access(user)


def _resolve_read_tenant_ids(
    db: Session,
    user,
    tenant_id: UUID | None,
    tenant_ids: str | None,
    all_agencies: bool,
) -> list[UUID]:
    _require_financial_access(user)
    requested_tenant_ids = [value.strip() for value in (tenant_ids or "").split(",") if value.strip()] or None
    resolved = resolve_authorized_tenant_ids_for_scope(
        db,
        user=user,
        requested_scope="FACILITY_COLLECTIONS",
        required_permission_level="VIEW",
        requested_tenant_id=tenant_id,
        requested_tenant_ids=requested_tenant_ids,
        all_agencies=all_agencies,
    )
    for tid in resolved:
        require_automated_billing(db, str(tid))
    return resolved


def _resolve_single_tenant_id(
    db: Session,
    user,
    tenant_id: UUID | None,
    *,
    requested_scope: str = "FACILITY_COLLECTIONS",
    required_permission_level: str = "VIEW",
) -> UUID:
    _require_financial_access(user)
    scoped = resolve_authorized_tenant_ids_for_scope(
        db,
        user=user,
        requested_scope=requested_scope,
        required_permission_level=required_permission_level,
        requested_tenant_id=tenant_id,
    )[0]
    require_automated_billing(db, str(scoped))
    return scoped


def _get_expectation_for_user(
    db: Session,
    user,
    expectation_id: UUID,
    *,
    required_permission_level: str = "VIEW",
) -> FacilityPaymentExpectation:
    expectation = db.query(FacilityPaymentExpectation).filter(FacilityPaymentExpectation.id == expectation_id).one_or_none()
    if expectation is None:
        raise HTTPException(status_code=404, detail="Facility payment expectation not found.")
    try:
        authorized_tenant_id = _resolve_single_tenant_id(
            db,
            user,
            expectation.tenant_id,
            requested_scope="FACILITY_COLLECTIONS",
            required_permission_level=required_permission_level,
        )
    except HTTPException as exc:
        if exc.status_code in {403, 404, 400}:
            raise HTTPException(status_code=404, detail="Facility payment expectation not found.") from exc
        raise
    if str(authorized_tenant_id) != str(expectation.tenant_id):
        raise HTTPException(status_code=404, detail="Facility payment expectation not found.")
    return expectation


def _get_allocation_for_user(
    db: Session,
    user,
    allocation_id: UUID,
    *,
    requested_scope: str = "FACILITY_COLLECTIONS",
    required_permission_level: str = "VIEW",
) -> FacilityPaymentAllocation:
    allocation = db.query(FacilityPaymentAllocation).filter(FacilityPaymentAllocation.id == allocation_id).one_or_none()
    if allocation is None:
        raise HTTPException(status_code=404, detail="Facility payment allocation not found.")
    try:
        authorized_tenant_id = _resolve_single_tenant_id(
            db,
            user,
            allocation.tenant_id,
            requested_scope=requested_scope,
            required_permission_level=required_permission_level,
        )
    except HTTPException as exc:
        if exc.status_code in {403, 404, 400}:
            raise HTTPException(status_code=404, detail="Facility payment allocation not found.") from exc
        raise
    if str(authorized_tenant_id) != str(allocation.tenant_id):
        raise HTTPException(status_code=404, detail="Facility payment allocation not found.")
    return allocation


def _get_alert_for_user(
    db: Session,
    user,
    alert_id: UUID,
    *,
    required_permission_level: str = "VIEW",
) -> FacilityCollectionAlert:
    alert = db.query(FacilityCollectionAlert).filter(FacilityCollectionAlert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Facility collection alert not found.")
    try:
        authorized_tenant_id = _resolve_single_tenant_id(
            db,
            user,
            alert.tenant_id,
            requested_scope="FINANCIAL_MONITORING",
            required_permission_level=required_permission_level,
        )
    except HTTPException as exc:
        if exc.status_code in {403, 404, 400}:
            raise HTTPException(status_code=404, detail="Facility collection alert not found.") from exc
        raise
    if str(authorized_tenant_id) != str(alert.tenant_id):
        raise HTTPException(status_code=404, detail="Facility collection alert not found.")
    return alert


def _allocation_to_dict(allocation: FacilityPaymentAllocation) -> dict:
    return {
        "id": str(allocation.id),
        "tenant_id": str(allocation.tenant_id),
        "facility_payment_expectation_id": str(allocation.facility_payment_expectation_id),
        "payment_id": str(allocation.payment_id) if allocation.payment_id else None,
        "remittance_advice_id": str(allocation.remittance_advice_id) if allocation.remittance_advice_id else None,
        "claim_id": str(allocation.claim_id) if allocation.claim_id else None,
        "payment_adjustment_id": str(allocation.payment_adjustment_id) if allocation.payment_adjustment_id else None,
        "payer_name": allocation.payer_name,
        "amount_applied": str(facility_service._q2(allocation.amount_applied)),
        "payment_date": allocation.payment_date,
        "allocation_status": allocation.allocation_status,
        "flagged_for_review": allocation.flagged_for_review,
        "flagged_reason": allocation.flagged_reason,
        "match_basis": allocation.match_basis,
        "notes": allocation.notes,
        "reconciled_by": str(allocation.reconciled_by) if allocation.reconciled_by else None,
        "reconciled_at": allocation.reconciled_at.isoformat() if allocation.reconciled_at else None,
        "created_at": allocation.created_at.isoformat() if allocation.created_at else None,
        "updated_at": allocation.updated_at.isoformat() if allocation.updated_at else None,
    }


def _expectation_to_dict(db: Session, expectation: FacilityPaymentExpectation, *, include_related: bool = False) -> dict:
    rollup = facility_service.compute_rollup(db, expectation)
    aging = facility_service.compute_aging(expectation)
    patient_context = facility_service.expectation_patient_context(db, expectation)
    payload = {
        "id": str(expectation.id),
        "tenant_id": str(expectation.tenant_id),
        "patient_id": str(expectation.patient_id),
        "patient_pos_id": str(expectation.patient_pos_id) if expectation.patient_pos_id else None,
        "patient_name": patient_context["patient_name"],
        "mrn": patient_context["mrn"],
        "agency_name": patient_context["agency_name"],
        "facility_name_snapshot": expectation.facility_name_snapshot,
        "residence_type_snapshot": expectation.residence_type_snapshot,
        "room_number_snapshot": expectation.room_number_snapshot,
        "residence_start_date_snapshot": (
            expectation.residence_start_date_snapshot.isoformat()
            if expectation.residence_start_date_snapshot
            else None
        ),
        "residence_end_date_snapshot": (
            expectation.residence_end_date_snapshot.isoformat()
            if expectation.residence_end_date_snapshot
            else None
        ),
        "expected_funding_source_snapshot": expectation.expected_funding_source_snapshot,
        "expected_payer_name_snapshot": expectation.expected_payer_name_snapshot,
        "primary_payer_name_snapshot": expectation.primary_payer_name_snapshot,
        "secondary_payer_name_snapshot": expectation.secondary_payer_name_snapshot,
        "responsibility_category": expectation.responsibility_category,
        "expected_funding_source": expectation.expected_funding_source,
        "expected_amount": str(rollup.expected_amount),
        "currency": expectation.currency,
        "frequency": expectation.frequency,
        "service_period_start": expectation.service_period_start.isoformat(),
        "service_period_end": expectation.service_period_end.isoformat(),
        "due_date": expectation.due_date.isoformat() if expectation.due_date else None,
        "due_date_source": expectation.due_date_source,
        "payment_term_verified": expectation.payment_term_verified,
        "authorization_reference": expectation.authorization_reference,
        "contract_reference": expectation.contract_reference,
        "share_of_cost_amount": (
            str(facility_service._q2(expectation.share_of_cost_amount))
            if expectation.share_of_cost_amount is not None
            else None
        ),
        "status": expectation.status,
        "version_number": expectation.version_number,
        "row_version": expectation.row_version,
        "supersedes_expectation_id": str(expectation.supersedes_expectation_id) if expectation.supersedes_expectation_id else None,
        "superseded_by_expectation_id": (
            str(expectation.superseded_by_expectation_id) if expectation.superseded_by_expectation_id else None
        ),
        "correction_reason": expectation.correction_reason,
        "cancellation_reason": expectation.cancellation_reason,
        "cancelled_at": expectation.cancelled_at.isoformat() if expectation.cancelled_at else None,
        "cancelled_by": str(expectation.cancelled_by) if expectation.cancelled_by else None,
        "notes": expectation.notes,
        "source": expectation.source,
        "client_request_id": str(expectation.client_request_id) if expectation.client_request_id else None,
        "created_by": str(expectation.created_by) if expectation.created_by else None,
        "updated_by": str(expectation.updated_by) if expectation.updated_by else None,
        "created_at": expectation.created_at.isoformat() if expectation.created_at else None,
        "updated_at": expectation.updated_at.isoformat() if expectation.updated_at else None,
        "reconciliation_status": rollup.reconciliation_status,
        "amount_received": str(rollup.confirmed_amount),
        "outstanding_amount": str(rollup.outstanding_amount),
        "most_recent_payment_date": rollup.most_recent_payment_date,
        "aging": aging,
    }
    if include_related:
        audit_rows = (
            db.query(FacilityPaymentAuditLog)
            .filter(
                FacilityPaymentAuditLog.tenant_id == expectation.tenant_id,
                FacilityPaymentAuditLog.entity_type.in_(["EXPECTATION", "ALLOCATION"]),
                FacilityPaymentAuditLog.entity_id.in_(
                    [expectation.id] + [allocation.id for allocation in expectation.allocations]
                ),
            )
            .order_by(FacilityPaymentAuditLog.created_at.desc())
            .all()
        )
        payload["allocations"] = [_allocation_to_dict(a) for a in expectation.allocations]
        payload["audit_summary"] = {
            "total_entries": len(audit_rows),
            "entries": [
                {
                    "id": str(row.id),
                    "entity_type": row.entity_type,
                    "entity_id": str(row.entity_id),
                    "field_name": row.field_name,
                    "previous_value": row.previous_value,
                    "new_value": row.new_value,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "role": row.role,
                    "reason": row.reason,
                    "supporting_reference": row.supporting_reference,
                    "correlation_id": str(row.correlation_id) if row.correlation_id else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in audit_rows[:50]
            ],
        }
    return payload


def _alert_to_dict(alert: FacilityCollectionAlert) -> dict:
    return {
        "id": str(alert.id),
        "tenant_id": str(alert.tenant_id),
        "patient_id": str(alert.patient_id) if alert.patient_id else None,
        "facility_payment_expectation_id": (
            str(alert.facility_payment_expectation_id) if alert.facility_payment_expectation_id else None
        ),
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "expected_amount": str(facility_service._q2(alert.expected_amount)) if alert.expected_amount is not None else None,
        "received_amount": str(facility_service._q2(alert.received_amount)) if alert.received_amount is not None else None,
        "outstanding_amount": (
            str(facility_service._q2(alert.outstanding_amount)) if alert.outstanding_amount is not None else None
        ),
        "due_date": alert.due_date.isoformat() if alert.due_date else None,
        "days_outstanding": alert.days_outstanding,
        "status": alert.status,
        "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
        "resolution_evidence": alert.resolution_evidence,
        "resolved_by": str(alert.resolved_by) if alert.resolved_by else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
    }


class ExpectationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    patient_pos_id: UUID | None = None
    responsibility_category: str
    expected_funding_source: str
    expected_amount: Decimal
    currency: str = "USD"
    frequency: str | None = None
    service_period_start: date
    service_period_end: date
    due_date: date | None = None
    authorization_reference: str | None = None
    contract_reference: str | None = None
    share_of_cost_amount: Decimal | None = None
    source: str = "NOT_VERIFIED"
    expected_payer_name_snapshot: str | None = None
    notes: str | None = None
    client_request_id: UUID | None = None


class ExpectationCorrectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_pos_id: UUID | None = None
    responsibility_category: str | None = None
    expected_funding_source: str | None = None
    expected_amount: Decimal | None = None
    currency: str | None = None
    frequency: str | None = None
    service_period_start: date | None = None
    service_period_end: date | None = None
    due_date: date | None = None
    authorization_reference: str | None = None
    contract_reference: str | None = None
    share_of_cost_amount: Decimal | None = None
    source: str | None = None
    expected_payer_name_snapshot: str | None = None
    notes: str | None = None
    expected_row_version: int | None = None
    correction_reason: str


class ReverseAllocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str


class ResolveAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution_evidence: str


class ThresholdUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    threshold_amount: Decimal | None = None
    threshold_days: int | None = None


class ExpectationActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_row_version: int | None = None


class ExpectationCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cancellation_reason: str
    force: bool = False
    expected_row_version: int | None = None


@router.get("/expectations")
def list_expectations(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view."),
    tenant_ids: str | None = Query(None, description="Comma-separated agency tenant IDs."),
    all_agencies: bool = Query(False),
    patient_id: UUID | None = Query(None),
    status: str | None = Query(None),
    reconciliation_status: str | None = Query(None),
    responsibility_category: str | None = Query(None),
    funding_source: str | None = Query(None),
    residence_type: str | None = Query(None),
    aging_bucket: str | None = Query(None),
    service_period_start: date | None = Query(None),
    service_period_end: date | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_ids = _resolve_read_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)
    query = db.query(FacilityPaymentExpectation).filter(
        FacilityPaymentExpectation.tenant_id.in_([str(tid) for tid in scoped_tenant_ids])
    )
    if patient_id:
        query = query.filter(FacilityPaymentExpectation.patient_id == patient_id)
    if status:
        query = query.filter(FacilityPaymentExpectation.status == status.strip().upper())
    if reconciliation_status:
        query = query.filter(
            FacilityPaymentExpectation.reconciliation_status == reconciliation_status.strip().upper()
        )
    if responsibility_category:
        query = query.filter(
            FacilityPaymentExpectation.responsibility_category == responsibility_category.strip().upper()
        )
    if funding_source:
        query = query.filter(FacilityPaymentExpectation.expected_funding_source == funding_source.strip().upper())
    if residence_type:
        query = query.filter(FacilityPaymentExpectation.residence_type_snapshot == residence_type.strip().upper())
    if service_period_start:
        query = query.filter(FacilityPaymentExpectation.service_period_end >= service_period_start)
    if service_period_end:
        query = query.filter(FacilityPaymentExpectation.service_period_start <= service_period_end)

    rows = query.order_by(
        FacilityPaymentExpectation.service_period_start.desc(),
        FacilityPaymentExpectation.created_at.desc(),
    ).all()
    serialized = [_expectation_to_dict(db, row, include_related=False) for row in rows]
    if aging_bucket:
        serialized = [row for row in serialized if row["aging"]["aging_bucket"] == aging_bucket]
    return {"count": len(serialized), "items": serialized}


@router.post("/expectations")
def create_expectation(
    payload: ExpectationCreateRequest,
    tenant_id: UUID | None = Query(None, description="Agency tenant to create for."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    scoped_tenant_id = _resolve_single_tenant_id(
        db,
        user,
        tenant_id,
        requested_scope="FACILITY_COLLECTIONS",
        required_permission_level="EDIT",
    )
    expectation = facility_service.create_facility_payment_expectation(
        db,
        tenant_id=scoped_tenant_id,
        patient_id=payload.patient_id,
        patient_pos_id=payload.patient_pos_id,
        responsibility_category=payload.responsibility_category,
        expected_funding_source=payload.expected_funding_source,
        expected_amount=payload.expected_amount,
        currency=payload.currency,
        frequency=payload.frequency,
        service_period_start=payload.service_period_start,
        service_period_end=payload.service_period_end,
        due_date=payload.due_date,
        authorization_reference=payload.authorization_reference,
        contract_reference=payload.contract_reference,
        share_of_cost_amount=payload.share_of_cost_amount,
        source=payload.source,
        expected_payer_name_snapshot=payload.expected_payer_name_snapshot,
        notes=payload.notes,
        client_request_id=payload.client_request_id,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
    )
    return _expectation_to_dict(db, expectation, include_related=True)


@router.get("/expectations/{expectation_id}")
def get_expectation(
    expectation_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expectation = _get_expectation_for_user(db, user, expectation_id)
    return _expectation_to_dict(db, expectation, include_related=True)


@router.post("/expectations/{expectation_id}/activate")
def activate_expectation(
    expectation_id: UUID,
    payload: ExpectationActivateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    _get_expectation_for_user(
        db,
        user,
        expectation_id,
        required_permission_level="EDIT",
    )
    expectation = facility_service.activate_expectation(
        db,
        expectation_id=expectation_id,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
        expected_row_version=payload.expected_row_version,
    )
    return _expectation_to_dict(db, expectation, include_related=True)


@router.post("/expectations/{expectation_id}/cancel")
def cancel_expectation(
    expectation_id: UUID,
    payload: ExpectationCancelRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    _get_expectation_for_user(
        db,
        user,
        expectation_id,
        required_permission_level="EDIT",
    )
    expectation = facility_service.cancel_expectation(
        db,
        expectation_id=expectation_id,
        cancellation_reason=payload.cancellation_reason,
        force=payload.force,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
        expected_row_version=payload.expected_row_version,
    )
    return _expectation_to_dict(db, expectation, include_related=True)


@router.get("/expectations/{expectation_id}/history")
def get_expectation_history(
    expectation_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expectation = _get_expectation_for_user(db, user, expectation_id)
    history = facility_service.expectation_history(db, expectation_id=expectation.id)
    return {
        "current_expectation_id": str(expectation.id),
        "items": [
            {
                "id": str(item.id),
                "version_number": item.version_number,
                "status": item.status,
                "correction_reason": item.correction_reason,
                "cancellation_reason": item.cancellation_reason,
                "created_by": str(item.created_by) if item.created_by else None,
                "corrected_by": str(item.updated_by) if item.updated_by else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in history
        ],
    }


@router.get("/expectations/{expectation_id}/residence-snapshot-diff")
def get_residence_snapshot_diff(
    expectation_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expectation = _get_expectation_for_user(db, user, expectation_id)
    return facility_service.residence_snapshot_diff(db, expectation_id=expectation.id)


@router.post("/expectations/{expectation_id}/correct")
def correct_expectation(
    expectation_id: UUID,
    payload: ExpectationCorrectRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    existing = _get_expectation_for_user(
        db,
        user,
        expectation_id,
        required_permission_level="EDIT",
    )
    corrected = facility_service.create_corrected_expectation_version(
        db,
        previous_expectation_id=expectation_id,
        correction_reason=payload.correction_reason,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
        expected_row_version=payload.expected_row_version,
        patient_pos_id=payload.patient_pos_id,
        responsibility_category=payload.responsibility_category,
        expected_funding_source=payload.expected_funding_source,
        expected_amount=payload.expected_amount,
        currency=payload.currency,
        frequency=payload.frequency,
        service_period_start=payload.service_period_start,
        service_period_end=payload.service_period_end,
        due_date=payload.due_date,
        authorization_reference=payload.authorization_reference,
        contract_reference=payload.contract_reference,
        share_of_cost_amount=payload.share_of_cost_amount,
        source=payload.source,
        expected_payer_name_snapshot=payload.expected_payer_name_snapshot,
        notes=payload.notes,
    )
    return _expectation_to_dict(db, corrected, include_related=True)


@router.get("/expectations/{expectation_id}/candidates")
def get_candidate_matches(
    expectation_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expectation = _get_expectation_for_user(db, user, expectation_id)
    candidates = facility_service.find_candidate_matches(db, expectation=expectation)
    return {"count": len(candidates), "items": [_allocation_to_dict(row) for row in candidates]}


@router.post("/allocations/{allocation_id}/confirm")
def confirm_allocation(
    allocation_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    allocation = _get_allocation_for_user(
        db,
        user,
        allocation_id,
        requested_scope="PAYMENT_RECONCILIATION",
        required_permission_level="EDIT",
    )
    allocation = facility_service.confirm_allocation(
        db,
        allocation_id=allocation_id,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
    )
    return _allocation_to_dict(allocation)


@router.post("/allocations/{allocation_id}/reverse")
def reverse_allocation(
    allocation_id: UUID,
    payload: ReverseAllocationRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    allocation = _get_allocation_for_user(
        db,
        user,
        allocation_id,
        requested_scope="PAYMENT_RECONCILIATION",
        required_permission_level="EDIT",
    )
    allocation = facility_service.reverse_allocation(
        db,
        allocation_id=allocation_id,
        user_id=getattr(user, "user_id", None),
        reason=payload.reason,
        user_role=getattr(user, "role", None),
    )
    return _allocation_to_dict(allocation)


@router.get("/collections-report")
def get_collections_report(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view."),
    tenant_ids: str | None = Query(None, description="Comma-separated agency tenant IDs."),
    all_agencies: bool = Query(False),
    residence_type: str | None = Query(None),
    funding_source: str | None = Query(None),
    payer_name: str | None = Query(None),
    responsibility_category: str | None = Query(None),
    reconciliation_status: str | None = Query(None),
    aging_bucket: str | None = Query(None),
    service_period_start: date | None = Query(None),
    service_period_end: date | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_ids = _resolve_read_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)
    query = db.query(FacilityPaymentExpectation).filter(
        FacilityPaymentExpectation.tenant_id.in_([str(tid) for tid in scoped_tenant_ids])
    )
    if residence_type:
        query = query.filter(FacilityPaymentExpectation.residence_type_snapshot == residence_type.strip().upper())
    if funding_source:
        query = query.filter(FacilityPaymentExpectation.expected_funding_source == funding_source.strip().upper())
    if responsibility_category:
        query = query.filter(
            FacilityPaymentExpectation.responsibility_category == responsibility_category.strip().upper()
        )
    if reconciliation_status:
        query = query.filter(
            FacilityPaymentExpectation.reconciliation_status == reconciliation_status.strip().upper()
        )
    if service_period_start:
        query = query.filter(FacilityPaymentExpectation.service_period_end >= service_period_start)
    if service_period_end:
        query = query.filter(FacilityPaymentExpectation.service_period_start <= service_period_end)

    expectations = query.order_by(
        FacilityPaymentExpectation.service_period_start.desc(),
        FacilityPaymentExpectation.created_at.desc(),
    ).all()

    rows = []
    total_expected = Decimal("0.00")
    total_received = Decimal("0.00")
    total_outstanding = Decimal("0.00")
    partially_paid_count = 0
    unmatched_count = 0
    overdue_count = 0
    reconciliation_exception_count = 0

    for expectation in expectations:
        row = _expectation_to_dict(db, expectation, include_related=False)
        if payer_name:
            payer_names = {
                value.lower()
                for value in (
                    row["expected_payer_name_snapshot"],
                    row["primary_payer_name_snapshot"],
                    row["secondary_payer_name_snapshot"],
                )
                if value
            }
            if payer_name.strip().lower() not in payer_names:
                continue
        if aging_bucket and row["aging"]["aging_bucket"] != aging_bucket:
            continue

        total_expected += Decimal(row["expected_amount"])
        total_received += Decimal(row["amount_received"])
        total_outstanding += Decimal(row["outstanding_amount"])
        if row["reconciliation_status"] == "PARTIALLY_PAID":
            partially_paid_count += 1
        if row["reconciliation_status"] == "UNMATCHED_PAYMENT":
            unmatched_count += 1
            reconciliation_exception_count += 1
        if row["aging"]["days_outstanding"] is not None and row["aging"]["days_outstanding"] > 30 and Decimal(
            row["outstanding_amount"]
        ) > Decimal("0.00"):
            overdue_count += 1
        if row["reconciliation_status"] in {"UNMATCHED_PAYMENT", "MANUAL_REVIEW_REQUIRED", "OVERPAID"}:
            reconciliation_exception_count += 1
        rows.append(
            {
                "agency_name": row["agency_name"] or "NOT_AVAILABLE",
                "patient_name": row["patient_name"],
                "mrn": row["mrn"],
                "facility_name_snapshot": row["facility_name_snapshot"],
                "residence_type_snapshot": row["residence_type_snapshot"],
                "service_period": {
                    "start": row["service_period_start"],
                    "end": row["service_period_end"],
                },
                "responsibility_category": row["responsibility_category"],
                "expected_funding_source": row["expected_funding_source"],
                "primary_payer_name": row["primary_payer_name_snapshot"],
                "secondary_payer_name": row["secondary_payer_name_snapshot"],
                "expected_amount": row["expected_amount"],
                "amount_received": row["amount_received"],
                "outstanding_amount": row["outstanding_amount"],
                "most_recent_payment_date": row["most_recent_payment_date"],
                "due_date": row["due_date"],
                "due_date_source": row["due_date_source"],
                "payment_term_verified": row["payment_term_verified"],
                "days_outstanding": row["aging"]["days_outstanding"],
                "status": row["status"],
                "reconciliation_status": row["reconciliation_status"],
                "aging_bucket": row["aging"]["aging_bucket"],
                "expectation_id": row["id"],
            }
        )

    collection_rate = "0.00"
    if total_expected > Decimal("0.00"):
        collection_rate = str(
            (total_received / total_expected).quantize(Decimal("0.01"))
        )
    return {
        "rows": rows,
        "summary": {
            "total_expected": str(total_expected.quantize(Decimal("0.01"))),
            "total_received": str(total_received.quantize(Decimal("0.01"))),
            "total_outstanding": str(total_outstanding.quantize(Decimal("0.01"))),
            "partially_paid_count": partially_paid_count,
            "unmatched_payments_count": unmatched_count,
            "overdue_obligations_count": overdue_count,
            "reconciliation_exceptions_count": reconciliation_exception_count,
            "collection_rate": collection_rate,
        },
    }


@router.get("/alerts")
def list_alerts(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view."),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = _resolve_single_tenant_id(
        db,
        user,
        tenant_id,
        requested_scope="FINANCIAL_MONITORING",
        required_permission_level="VIEW",
    )
    query = db.query(FacilityCollectionAlert).filter(FacilityCollectionAlert.tenant_id == scoped_tenant_id)
    if status:
        query = query.filter(FacilityCollectionAlert.status == status.strip().upper())
    rows = query.order_by(FacilityCollectionAlert.created_at.desc()).all()
    return {"count": len(rows), "items": [_alert_to_dict(row) for row in rows]}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: UUID,
    payload: ResolveAlertRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_access(user)
    _get_alert_for_user(
        db,
        user,
        alert_id,
        required_permission_level="EDIT",
    )
    alert = facility_service.resolve_alert(
        db,
        alert_id=alert_id,
        user_id=getattr(user, "user_id", None),
        resolution_evidence=payload.resolution_evidence,
        user_role=getattr(user, "role", None),
    )
    return _alert_to_dict(alert)


@router.get("/alert-thresholds")
def get_alert_thresholds(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = _resolve_single_tenant_id(
        db,
        user,
        tenant_id,
        requested_scope="FINANCIAL_MONITORING",
        required_permission_level="VIEW",
    )
    return {"items": facility_service.list_thresholds(db, tenant_id=scoped_tenant_id)}


@router.put("/alert-thresholds/{alert_type}")
def put_alert_threshold(
    alert_type: str,
    payload: ThresholdUpdateRequest,
    tenant_id: UUID | None = Query(None, description="Agency tenant to update."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_financial_edit_access(user)
    scoped_tenant_id = _resolve_single_tenant_id(
        db,
        user,
        tenant_id,
        requested_scope="FINANCIAL_MONITORING",
        required_permission_level="EDIT",
    )
    row = facility_service.update_threshold(
        db,
        tenant_id=scoped_tenant_id,
        alert_type=alert_type.strip().upper(),
        enabled=payload.enabled,
        threshold_amount=payload.threshold_amount,
        threshold_days=payload.threshold_days,
        user_id=getattr(user, "user_id", None),
        user_role=getattr(user, "role", None),
    )
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "alert_type": row.alert_type,
        "enabled": row.enabled,
        "threshold_amount": str(facility_service._q2(row.threshold_amount)) if row.threshold_amount is not None else None,
        "threshold_days": row.threshold_days,
    }
