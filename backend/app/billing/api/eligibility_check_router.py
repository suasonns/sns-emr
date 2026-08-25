from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_request_dependency import get_db_tenant_with_request_state
from app.models.patient_insurance import PatientInsurance
from app.billing.models.payer_eligibility_check import PayerEligibilityCheck

router = APIRouter(prefix="/billing", tags=["Billing Eligibility"])

VALID_RESULT_STATUSES = {"ACTIVE", "INACTIVE", "UNKNOWN", "ERROR"}


class EligibilityCheckCreate(BaseModel):
    result_status: str
    check_method: str = "MANUAL"
    payer_response_code: str | None = None
    plan_begin_date: date | None = None
    plan_end_date: date | None = None
    notes: str | None = None
    next_verification_due: date | None = None


def _get_insurance(db: Session, patient_insurance_id: str) -> PatientInsurance:
    insurance = db.get(PatientInsurance, patient_insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Patient insurance record not found")
    return insurance


@router.get("/patient-insurances/{patient_insurance_id}/eligibility-checks")
def list_eligibility_checks(
    patient_insurance_id: str,
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    """
    Real eligibility verification history for a patient's insurance
    coverage (see app.billing.models.payer_eligibility_check.PayerEligibilityCheck).
    """
    insurance = _get_insurance(db, patient_insurance_id)
    checks = (
        db.query(PayerEligibilityCheck)
        .filter(PayerEligibilityCheck.patient_insurance_id == insurance.id)
        .order_by(PayerEligibilityCheck.checked_at.desc())
        .all()
    )
    return {
        "patient_insurance_id": str(insurance.id),
        "eligibility_status": insurance.eligibility_status,
        "next_verification_due": (
            insurance.next_verification_due.isoformat()
            if insurance.next_verification_due
            else None
        ),
        "checks": [
            {
                "id": str(c.id),
                "checked_at": c.checked_at.isoformat() if c.checked_at else None,
                "check_method": c.check_method,
                "result_status": c.result_status,
                "payer_response_code": c.payer_response_code,
                "plan_begin_date": c.plan_begin_date.isoformat() if c.plan_begin_date else None,
                "plan_end_date": c.plan_end_date.isoformat() if c.plan_end_date else None,
                "notes": c.notes,
                "checked_by": c.checked_by,
            }
            for c in checks
        ],
    }


@router.post("/patient-insurances/{patient_insurance_id}/eligibility-checks")
def record_eligibility_check(
    patient_insurance_id: str,
    payload: EligibilityCheckCreate,
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    """
    Records a real eligibility verification result (manual today --
    phone/portal check logged by a biller; BATCH_270_271 is reserved for
    a future automated clearinghouse integration that does not exist
    yet) and updates the patient insurance's current eligibility_status /
    next_verification_due from it.
    """
    result_status = payload.result_status.upper().strip()
    if result_status not in VALID_RESULT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"result_status must be one of {sorted(VALID_RESULT_STATUSES)}",
        )

    insurance = _get_insurance(db, patient_insurance_id)

    check = PayerEligibilityCheck(
        id=str(uuid4()),
        tenant_id=insurance.tenant_id,
        patient_insurance_id=insurance.id,
        checked_at=datetime.now(timezone.utc),
        check_method=payload.check_method.upper().strip() or "MANUAL",
        result_status=result_status,
        payer_response_code=payload.payer_response_code,
        plan_begin_date=payload.plan_begin_date,
        plan_end_date=payload.plan_end_date,
        notes=payload.notes,
        checked_by=str(getattr(user, "user_id", None) or getattr(user, "id", "")),
    )
    db.add(check)

    insurance.eligibility_status = result_status
    insurance.verified_at = check.checked_at
    if payload.next_verification_due:
        insurance.next_verification_due = payload.next_verification_due

    db.commit()
    db.refresh(check)

    return {
        "id": str(check.id),
        "patient_insurance_id": str(insurance.id),
        "eligibility_status": insurance.eligibility_status,
        "checked_at": check.checked_at.isoformat(),
        "result_status": check.result_status,
        "next_verification_due": (
            insurance.next_verification_due.isoformat()
            if insurance.next_verification_due
            else None
        ),
    }
