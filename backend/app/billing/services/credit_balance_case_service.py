"""
Credit-balance case lifecycle -- controlled resolution workflow layered
over the read-only claim-level calculation in credit_balance_service.

A CreditBalanceCase is only created once a biller opens one for a claim
whose computed net balance is negative (see open_case_for_claim). A
calculated negative balance is NEVER auto-confirmed -- it always starts
POTENTIAL and a qualified billing user must review it (per business
rule). Every status change and non-status action is written to
CreditBalanceCaseEvent as a durable, immutable audit trail (reason +
performer + timestamp + before/after amounts + source transaction
reference required).

This module does not touch clinical records, does not modify the
original remittance/payment/adjustment rows, and does not create a
second financial ledger -- it only tracks investigation/resolution state
that references the authoritative Claim/Payment rows.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.billing.models.credit_balance_case import (
    MEDICARE_CLASSIFICATIONS,
    CreditBalanceCase,
    CreditBalanceCaseEvent,
)

CONFIRM_CREDIT = "CONFIRM_CREDIT"
REJECT_CREDIT = "REJECT_CREDIT"
REQUEST_INVESTIGATION = "REQUEST_INVESTIGATION"
DETERMINE_REPAYMENT_REQUIRED = "DETERMINE_REPAYMENT_REQUIRED"
INITIATE_REFUND = "INITIATE_REFUND"
RECORD_REFUND = "RECORD_REFUND"
REQUEST_RECOUPMENT = "REQUEST_RECOUPMENT"
RECORD_RECOUPMENT = "RECORD_RECOUPMENT"
REQUEST_REALLOCATION = "REQUEST_REALLOCATION"
RECORD_REALLOCATION = "RECORD_REALLOCATION"
CORRECT_MISPOSTING = "CORRECT_MISPOSTING"
RECORD_CORRESPONDENCE = "RECORD_CORRESPONDENCE"
CLOSE_CASE = "CLOSE_CASE"
RECLASSIFY_MEDICARE = "RECLASSIFY_MEDICARE"

# Enumerated root causes a biller may attach to a case's reason_code.
# The system NEVER auto-assigns one of these -- "potential_duplicate_
# payment" (see app.billing.services.claim_financials.
# find_potential_duplicate_payment_claim_ids) is only a mechanical
# detection signal; a human reviewer picks the actual cause from this
# list once they've investigated.
DUPLICATE_PAYMENT_REASON_CODES = {
    "DUPLICATE_PAYMENT",
    "POSTING_ERROR",
    "COB_ISSUE",
    "MSP_ISSUE",
    "RECOUPMENT_TIMING",
    "OTHER",
}

# Actions that change status; the value is {from_status: to_status}. An
# action not present here (CORRECT_MISPOSTING, RECORD_CORRESPONDENCE,
# RECLASSIFY_MEDICARE) never changes status -- it only appends an
# audit event and/or updates a non-status field.
_STATUS_TRANSITIONS: dict[str, dict[str, str]] = {
    CONFIRM_CREDIT: {"POTENTIAL": "CONFIRMED", "UNDER_REVIEW": "CONFIRMED"},
    REJECT_CREDIT: {"POTENTIAL": "NOT_A_CREDIT_BALANCE", "UNDER_REVIEW": "NOT_A_CREDIT_BALANCE"},
    REQUEST_INVESTIGATION: {"POTENTIAL": "UNDER_REVIEW"},
    DETERMINE_REPAYMENT_REQUIRED: {"CONFIRMED": "REPAYMENT_REQUIRED"},
    INITIATE_REFUND: {"REPAYMENT_REQUIRED": "REFUND_PENDING"},
    RECORD_REFUND: {"REFUND_PENDING": "RESOLVED_REPAID"},
    REQUEST_RECOUPMENT: {"REPAYMENT_REQUIRED": "RECOUPMENT_PENDING"},
    RECORD_RECOUPMENT: {"RECOUPMENT_PENDING": "RESOLVED_RECOUPED"},
    REQUEST_REALLOCATION: {"CONFIRMED": "REALLOCATION_PENDING", "REPAYMENT_REQUIRED": "REALLOCATION_PENDING"},
    RECORD_REALLOCATION: {"REALLOCATION_PENDING": "RESOLVED_REALLOCATED"},
    CLOSE_CASE: {
        "RESOLVED_REPAID": "CLOSED",
        "RESOLVED_RECOUPED": "CLOSED",
        "RESOLVED_REALLOCATED": "CLOSED",
        "NOT_A_CREDIT_BALANCE": "CLOSED",
    },
}

# Actions that never change status but are still valid at any point before
# a case is CLOSED (append-only audit note / metadata update).
_NON_TRANSITION_ACTIONS = {CORRECT_MISPOSTING, RECORD_CORRESPONDENCE, RECLASSIFY_MEDICARE}

ALL_ACTIONS = set(_STATUS_TRANSITIONS) | _NON_TRANSITION_ACTIONS


def _now():
    return datetime.now(timezone.utc)


def open_case_for_claim(
    db: Session,
    *,
    tenant_id: UUID,
    claim_id: UUID,
    patient_id: UUID,
    credit_amount: Decimal,
    medicare_classification: str,
    performed_by: str,
    reason: str = "System-detected negative claim balance (Total Charges - Posted Payments - Adjustments - Write-offs < 0).",
) -> CreditBalanceCase:
    """
    Create a new POTENTIAL case for a claim, or return the existing one if
    a case already exists for this claim (idempotent -- a claim never has
    more than one active case).
    """
    existing = db.query(CreditBalanceCase).filter(CreditBalanceCase.claim_id == claim_id).one_or_none()
    if existing is not None:
        return existing

    case = CreditBalanceCase(
        tenant_id=tenant_id,
        claim_id=claim_id,
        patient_id=patient_id,
        status="POTENTIAL",
        medicare_classification=medicare_classification,
        credit_amount_at_detection=credit_amount,
    )
    db.add(case)
    db.flush()

    db.add(
        CreditBalanceCaseEvent(
            case_id=case.id,
            action="CASE_OPENED",
            previous_status=None,
            new_status="POTENTIAL",
            reason=reason,
            performed_by=performed_by,
            amount_before=None,
            amount_after=credit_amount,
        )
    )
    db.commit()
    db.refresh(case)
    return case


def perform_action(
    db: Session,
    case: CreditBalanceCase,
    action: str,
    *,
    performed_by: str,
    reason: str,
    source_transaction_reference: str | None = None,
    amount: Decimal | None = None,
    repayment_due_at: date | None = None,
    repayment_method: str | None = None,
    reason_code: str | None = None,
    medicare_classification: str | None = None,
) -> CreditBalanceCase:
    """
    Apply one lifecycle action to a case, validating the transition and
    recording an immutable audit event. Raises HTTPException(409) for an
    invalid transition/action.
    """
    action = (action or "").strip().upper()
    if action not in ALL_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown credit-balance case action '{action}'.")

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="A reason is required for every credit-balance case action.")

    previous_status = case.status
    new_status = previous_status
    amount_before = case.credit_amount_at_detection
    amount_after = amount_before

    if action in _STATUS_TRANSITIONS:
        allowed = _STATUS_TRANSITIONS[action]
        if previous_status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot perform '{action}' on a case in status '{previous_status}'.",
            )
        new_status = allowed[previous_status]
        case.status = new_status

        now = _now()
        if action == REQUEST_INVESTIGATION:
            case.review_started_at = now
        elif action == CONFIRM_CREDIT:
            case.confirmed_at = now
            # Formal identification happens at confirmation -- NOT at the
            # moment the calculation first produced a negative balance.
            case.identified_at = now
        elif action == DETERMINE_REPAYMENT_REQUIRED:
            case.repayment_due_at = repayment_due_at
        elif action == INITIATE_REFUND:
            pass
        elif action == RECORD_REFUND:
            amount_after = amount if amount is not None else amount_before
            case.amount_repaid = amount_after
            case.repaid_at = now
            case.resolved_at = now
            if repayment_method:
                case.repayment_method = repayment_method
        elif action == REQUEST_RECOUPMENT:
            pass
        elif action == RECORD_RECOUPMENT:
            amount_after = amount if amount is not None else amount_before
            case.amount_recouped = amount_after
            case.recouped_at = now
            case.resolved_at = now
        elif action == REQUEST_REALLOCATION:
            pass
        elif action == RECORD_REALLOCATION:
            amount_after = amount if amount is not None else amount_before
            case.amount_reallocated = amount_after
            case.reallocated_at = now
            case.resolved_at = now
        elif action == REJECT_CREDIT:
            case.resolved_at = now
        elif action == CLOSE_CASE:
            pass
    else:
        # Non-transition actions: audit note / metadata only.
        if action == RECLASSIFY_MEDICARE:
            if not medicare_classification:
                raise HTTPException(status_code=400, detail="medicare_classification is required for RECLASSIFY_MEDICARE.")
            if medicare_classification.upper() not in MEDICARE_CLASSIFICATIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"medicare_classification must be one of {sorted(MEDICARE_CLASSIFICATIONS)}.",
                )
            case.medicare_classification = medicare_classification.upper()

    if reason_code:
        if reason_code.upper() not in DUPLICATE_PAYMENT_REASON_CODES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"reason_code must be one of {sorted(DUPLICATE_PAYMENT_REASON_CODES)}; "
                    "the system does not infer a root cause automatically."
                ),
            )
        case.reason_code = reason_code.upper()

    db.add(
        CreditBalanceCaseEvent(
            case_id=case.id,
            action=action,
            previous_status=previous_status,
            new_status=new_status if action in _STATUS_TRANSITIONS else None,
            reason=reason,
            performed_by=performed_by,
            source_transaction_reference=source_transaction_reference,
            amount_before=amount_before,
            amount_after=amount_after,
        )
    )
    db.commit()
    db.refresh(case)
    return case
