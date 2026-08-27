from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.database import get_db
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.billing.security import require_automated_billing
from app.db_request_dependency import get_db_tenant_with_request_state
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_insurance import PatientInsurance
from app.billing.models.payer_eligibility_check import PayerEligibilityCheck

router = APIRouter(prefix="/billing", tags=["Billing Eligibility"])

VALID_RESULT_STATUSES = {"ACTIVE", "INACTIVE", "UNKNOWN", "ERROR"}


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


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


@router.get("/eligibility-roster")
def list_eligibility_roster(
    payer_name: str | None = None,
    status: str | None = None,
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only roster of real ``patient_insurances`` rows for
    the Eligibility Verification page: coverage status table plus the
    summary counts and "upcoming reverifications" panel it needs. There is
    no automated 270/271 clearinghouse feed in this system yet (see
    app.billing.models.payer_eligibility_check.PayerEligibilityCheck) --
    every eligibility_status here comes from a real, previously-recorded
    PayerEligibilityCheck (manual or, in the future, batch).
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    base_query = (
        db.query(
            PatientInsurance.id.label("insurance_id"),
            PatientInsurance.patient_id.label("patient_id"),
            PatientInsurance.payer_name.label("payer_name"),
            PatientInsurance.subscriber_id.label("subscriber_id"),
            PatientInsurance.eligibility_status.label("eligibility_status"),
            PatientInsurance.verified_at.label("verified_at"),
            PatientInsurance.next_verification_due.label("next_verification_due"),
            Patient.mrn.label("mrn"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
        )
        .join(Patient, Patient.id == PatientInsurance.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(
            PatientInsurance.tenant_id == scoped_tenant_id,
            PatientInsurance.is_active.is_(True),
        )
    )

    all_statuses = [
        r.eligibility_status for r in base_query.with_entities(PatientInsurance.eligibility_status).all()
    ]
    total_active = len(all_statuses)
    eligible_count = sum(1 for s in all_statuses if str(s or "").upper() == "ACTIVE")
    inactive_count = sum(1 for s in all_statuses if str(s or "").upper() == "INACTIVE")
    pending_count = sum(1 for s in all_statuses if str(s or "").upper() in {"UNKNOWN", "ERROR"})

    query = base_query
    if payer_name:
        query = query.filter(PatientInsurance.payer_name.ilike(f"%{payer_name}%"))
    if status:
        query = query.filter(PatientInsurance.eligibility_status == status.upper())

    rows = (
        query.order_by(PatientInsurance.next_verification_due.asc().nullslast())
        .limit(limit)
        .all()
    )

    results = []
    for r in rows:
        results.append(
            {
                "insurance_id": str(r.insurance_id),
                "patient_id": str(r.patient_id),
                "patient_name": _patient_name(
                    r.patient_first_name, r.patient_middle_name, r.patient_last_name
                ),
                "mrn": r.mrn,
                "payer_name": r.payer_name,
                "subscriber_id": r.subscriber_id,
                "eligibility_status": r.eligibility_status,
                "verified_at": r.verified_at.isoformat() if r.verified_at else None,
                "next_verification_due": (
                    r.next_verification_due.isoformat() if r.next_verification_due else None
                ),
            }
        )

    today = date.today()
    upcoming_cutoff = today + timedelta(days=7)
    upcoming = [
        {
            "insurance_id": r["insurance_id"],
            "mrn": r["mrn"],
            "patient_name": r["patient_name"],
            "next_verification_due": r["next_verification_due"],
            "days_until_due": (
                date.fromisoformat(r["next_verification_due"]) - today
            ).days,
        }
        for r in results
        if r["next_verification_due"]
        and today <= date.fromisoformat(r["next_verification_due"]) <= upcoming_cutoff
    ]

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "total_active": total_active,
        "eligible_count": eligible_count,
        "pending_count": pending_count,
        "inactive_count": inactive_count,
        "roster": results,
        "upcoming_reverifications": upcoming,
    }
