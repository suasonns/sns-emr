"""
Credit Balance Report API -- claim-level overpayment detection, patient/
account summary, and a controlled case-lifecycle workflow, layered over
existing claims/payment/adjustment/denial records (see
app.billing.services.credit_balance_service for the calculation and
app.billing.services.credit_balance_case_service for the case workflow).

Agency filtering reuses app.billing.scope.resolve_multi_agency_tenant_ids
(the same Single/Multi/All-Assigned-Agencies pattern as the Aging Report)
so this endpoint never introduces an unscoped cross-agency query.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.billing.models.credit_balance_case import CreditBalanceCase
from app.billing.scope import resolve_multi_agency_tenant_ids
from app.billing.security import require_automated_billing, tenant_has_automated_billing
from app.billing.services import credit_balance_case_service as case_service
from app.billing.services.claim_financials import (
    load_claim_financials,
    resolve_payer_type_for_claim,
    resolve_primary_secondary_payer_names,
)
from app.billing.services.credit_balance_service import (
    build_credit_balance_report,
    classify_medicare_reportability,
)
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/billing/credit-balance", tags=["Billing Reports"])


def _resolve_report_scope(db: Session, user, tenant_id, tenant_ids, all_agencies) -> list[UUID]:
    resolved_tenant_ids = resolve_multi_agency_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)
    if len(resolved_tenant_ids) == 1:
        require_automated_billing(db, str(resolved_tenant_ids[0]))
        return resolved_tenant_ids
    return [tid for tid in resolved_tenant_ids if tenant_has_automated_billing(db, str(tid))]


@router.get("/reason-codes")
def get_reason_codes(user=Depends(get_current_user)):
    """
    The enumerated root-cause reason codes a biller may attach to a case
    (e.g. after reviewing a "Potential Duplicate Payment" flag). The
    system never infers one of these automatically -- see
    app.billing.services.credit_balance_case_service.
    DUPLICATE_PAYMENT_REASON_CODES.
    """
    return {"reason_codes": sorted(case_service.DUPLICATE_PAYMENT_REASON_CODES)}


@router.get("/report")
def get_credit_balance_report(
    tenant_id: UUID | None = Query(None, description="Single agency tenant to view."),
    tenant_ids: str | None = Query(None, description="Comma-separated agency tenant IDs (billing-department accounts only)."),
    all_agencies: bool = Query(False, description="Aggregate across every agency the current billing-department user is assigned to."),
    as_of: date | None = Query(None, description="Report as-of date; defaults to today."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Claim-level credit-balance detection + patient/account summary.
    Claim Net Balance = Total Charges - Posted Payments - Adjustments -
    Write-offs; a potential credit balance exists when this is negative.
    """
    resolved = _resolve_report_scope(db, user, tenant_id, tenant_ids, all_agencies)
    return build_credit_balance_report(db, resolved, as_of=as_of)


def _case_to_dict(db: Session, case: CreditBalanceCase) -> dict:
    primary_payer_name, secondary_payer_name = resolve_primary_secondary_payer_names(db, case.patient_id)
    return {
        "case_id": str(case.id),
        "tenant_id": str(case.tenant_id),
        "claim_id": str(case.claim_id),
        "patient_id": str(case.patient_id),
        "status": case.status,
        "medicare_classification": case.medicare_classification,
        "reason_code": case.reason_code,
        # Billing context only -- see claim_financials.
        # resolve_primary_secondary_payer_names. Reuses existing
        # PatientPayer priority_order/is_primary; not a new subsystem.
        "primary_payer_name": primary_payer_name,
        "secondary_payer_name": secondary_payer_name,
        "credit_amount_at_detection": {"amount": str(case.credit_amount_at_detection), "currency": "USD"},
        "amount_repaid": {"amount": str(case.amount_repaid), "currency": "USD"},
        "amount_recouped": {"amount": str(case.amount_recouped), "currency": "USD"},
        "amount_reallocated": {"amount": str(case.amount_reallocated), "currency": "USD"},
        "repayment_method": case.repayment_method,
        "assigned_to": case.assigned_to,
        "notes": case.notes,
        "detected_at": case.detected_at.isoformat() if case.detected_at else None,
        "review_started_at": case.review_started_at.isoformat() if case.review_started_at else None,
        "identified_at": case.identified_at.isoformat() if case.identified_at else None,
        "confirmed_at": case.confirmed_at.isoformat() if case.confirmed_at else None,
        "repayment_due_at": case.repayment_due_at.isoformat() if case.repayment_due_at else None,
        "repaid_at": case.repaid_at.isoformat() if case.repaid_at else None,
        "recouped_at": case.recouped_at.isoformat() if case.recouped_at else None,
        "reallocated_at": case.reallocated_at.isoformat() if case.reallocated_at else None,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "events": [
            {
                "action": e.action,
                "previous_status": e.previous_status,
                "new_status": e.new_status,
                "reason": e.reason,
                "performed_by": e.performed_by,
                "source_transaction_reference": e.source_transaction_reference,
                "amount_before": str(e.amount_before) if e.amount_before is not None else None,
                "amount_after": str(e.amount_after) if e.amount_after is not None else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in case.events
        ],
    }


def _get_authorized_case(db: Session, user, case_id: UUID) -> CreditBalanceCase:
    case = db.query(CreditBalanceCase).filter(CreditBalanceCase.id == case_id).one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail="Credit-balance case not found.")
    # Enforce the same tenant/billing-scope authorization as every other
    # billing endpoint -- a case can only be viewed/acted on if the caller
    # is authorized to view that case's tenant.
    resolve_multi_agency_tenant_ids(db, user, case.tenant_id, None, False)
    return case


class OpenCaseRequest(BaseModel):
    claim_id: UUID


@router.post("/cases")
def create_case(
    payload: OpenCaseRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Open (or return the existing) case for a claim with a computed negative net balance."""
    # Look up the claim's tenant first so scope can be authorized before we
    # touch anything else.
    from app.billing.models.claim import Claim  # local import to avoid a module-level cycle

    claim = db.query(Claim).filter(Claim.id == payload.claim_id).one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")

    resolve_multi_agency_tenant_ids(db, user, claim.tenant_id, None, False)

    claim_rows = load_claim_financials(db, [claim.tenant_id], require_exported=False)
    matching = next((r for r in claim_rows if r.claim_id == claim.id), None)
    if matching is None:
        raise HTTPException(status_code=404, detail="Claim not found.")

    net = matching.net_balance
    if net >= 0:
        raise HTTPException(status_code=400, detail="This claim does not currently have a negative net balance.")

    performed_by = getattr(user, "email", None) or str(getattr(user, "id", "unknown-user"))
    case = case_service.open_case_for_claim(
        db,
        tenant_id=claim.tenant_id,
        claim_id=claim.id,
        patient_id=claim.patient_id,
        credit_amount=-net,
        medicare_classification=classify_medicare_reportability(
            resolve_payer_type_for_claim(db, claim.patient_id, claim.payer_name)
        ),
        performed_by=performed_by,
    )
    return _case_to_dict(db, case)


@router.get("/cases")
def list_cases(
    tenant_id: UUID | None = Query(None),
    tenant_ids: str | None = Query(None),
    all_agencies: bool = Query(False),
    status: str | None = Query(None),
    medicare_reportable: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    resolved = resolve_multi_agency_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)
    query = db.query(CreditBalanceCase).filter(CreditBalanceCase.tenant_id.in_([str(t) for t in resolved]))
    if status:
        query = query.filter(CreditBalanceCase.status == status.upper())
    if medicare_reportable:
        query = query.filter(CreditBalanceCase.medicare_classification == medicare_reportable.upper())
    cases = query.order_by(CreditBalanceCase.detected_at.desc()).all()
    return {"cases": [_case_to_dict(db, c) for c in cases]}


@router.get("/cases/{case_id}")
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    case = _get_authorized_case(db, user, case_id)
    return _case_to_dict(db, case)


class CaseActionRequest(BaseModel):
    action: str
    reason: str
    source_transaction_reference: str | None = None
    amount: str | None = None
    repayment_due_at: date | None = None
    repayment_method: str | None = None
    reason_code: str | None = None
    medicare_classification: str | None = None


@router.post("/cases/{case_id}/actions")
def act_on_case(
    case_id: UUID,
    payload: CaseActionRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    case = _get_authorized_case(db, user, case_id)
    performed_by = getattr(user, "email", None) or str(getattr(user, "id", "unknown-user"))
    amount = Decimal(payload.amount) if payload.amount is not None else None
    updated = case_service.perform_action(
        db,
        case,
        payload.action,
        performed_by=performed_by,
        reason=payload.reason,
        source_transaction_reference=payload.source_transaction_reference,
        amount=amount,
        repayment_due_at=payload.repayment_due_at,
        repayment_method=payload.repayment_method,
        reason_code=payload.reason_code,
        medicare_classification=payload.medicare_classification,
    )
    return _case_to_dict(db, updated)


@router.get("/cms-838-export")
def get_cms_838_export(
    tenant_id: UUID | None = Query(None),
    tenant_ids: str | None = Query(None),
    all_agencies: bool = Query(False),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    CMS-838-oriented export -- MEDICARE_REPORTABLE cases only. Given the
    current schema has no MBI/ICN/Type of Bill/admission-discharge/
    Medicare Part fields, those CMS-838 columns are returned as
    "NOT_AVAILABLE_IN_SCHEMA" rather than fabricated; agencies must fill
    them from their PS&R/cost-report records when actually filing CMS-838.
    """
    resolved = resolve_multi_agency_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)
    query = (
        db.query(CreditBalanceCase)
        .filter(CreditBalanceCase.tenant_id.in_([str(t) for t in resolved]))
        .filter(CreditBalanceCase.medicare_classification == "MEDICARE_REPORTABLE")
    )
    cases = query.order_by(CreditBalanceCase.detected_at.desc()).all()

    rows = []
    for case in cases:
        claim = case.claim
        rows.append(
            {
                "provider_number": None,
                "provider_name": None,
                "quarter_ending": None,
                "medicare_part": "NOT_AVAILABLE_IN_SCHEMA",
                "beneficiary_name": case.patient.mrn if case.patient else None,
                "mbi": "NOT_AVAILABLE_IN_SCHEMA",
                "icn": claim.claim_control_number if claim else None,
                "type_of_bill": "NOT_AVAILABLE_IN_SCHEMA",
                "admission_date": "NOT_AVAILABLE_IN_SCHEMA",
                "discharge_date": "NOT_AVAILABLE_IN_SCHEMA",
                "paid_date": None,
                "cost_report_status": "NOT_VERIFIED",
                "medicare_credit_balance_amount": str(case.credit_amount_at_detection),
                "amount_repaid": str(case.amount_repaid),
                "repayment_method": case.repayment_method,
                "reason_code": case.reason_code,
                "case_status": case.status,
                "outstanding_medicare_credit_balance": str(
                    case.credit_amount_at_detection - case.amount_repaid - case.amount_recouped - case.amount_reallocated
                ),
                "case_id": str(case.id),
            }
        )

    return {
        "data_completeness": "PARTIAL",
        "note": "MBI, ICN (payer claim-control number only), Type of Bill, admission/discharge dates, and Medicare Part are not present in the current schema and are marked NOT_AVAILABLE_IN_SCHEMA rather than fabricated.",
        "rows": rows,
    }
