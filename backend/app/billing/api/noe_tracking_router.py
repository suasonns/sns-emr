from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.billing.security import require_automated_billing
from app.billing.services.noe_penalty_service import compute_noe_penalty
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.benefit_period import BenefitPeriod
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet

router = APIRouter(prefix="/billing", tags=["Billing NOE Tracking"])


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@router.get("/noe-tracking")
def list_noe_tracking(
    late_only: bool = Query(
        False, description="Only include periods with a late/overdue NOE (penalty applies or is accruing)."
    ),
    unfiled_only: bool = Query(
        False, description="Only include periods where the NOE has not been filed yet."
    ),
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only NOE (Notice of Election) filing tracker.

    Wires the real ``noe_penalty_service.compute_noe_penalty`` calculator
    (42 CFR 418.24(b) 5-calendar-day rule) against every real INITIAL
    ``benefit_periods`` row for this tenant -- election_date,
    noe_submitted_date, noe_exception_reason are all real persisted
    fields. Only INITIAL periods are evaluated: the NOE filing requirement
    applies to the election effective date, which only exists on
    period_number=1 (RECERT periods do not re-trigger a new NOE).
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    today = date.today()

    query = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.tenant_id == scoped_tenant_id,
            BenefitPeriod.benefit_type == "INITIAL",
        )
        .order_by(BenefitPeriod.election_date.desc())
    )
    benefit_periods = query.limit(limit).all()

    patient_ids = {bp.patient_id for bp in benefit_periods}
    patients_by_id = {
        p.id: p for p in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    } if patient_ids else {}
    facesheets_by_patient = {
        fs.patient_id: fs
        for fs in db.query(PatientFaceSheet).filter(PatientFaceSheet.patient_id.in_(patient_ids)).all()
    } if patient_ids else {}

    results = []
    for bp in benefit_periods:
        if bp.election_date is None:
            # Can't evaluate NOE timeliness without a real election date;
            # never fabricate one -- surface as an explicit data gap instead.
            penalty = None
        else:
            penalty = compute_noe_penalty(
                election_date=bp.election_date,
                noe_submitted_date=bp.noe_submitted_date,
                exception_reason=bp.noe_exception_reason,
                as_of_date=today,
            )

        if late_only and (penalty is None or not penalty.is_late):
            continue
        if unfiled_only and bp.noe_submitted_date is not None:
            continue

        patient = patients_by_id.get(bp.patient_id)
        facesheet = facesheets_by_patient.get(bp.patient_id)

        results.append(
            {
                "patient_id": str(bp.patient_id),
                "patient_name": _patient_name(
                    facesheet.first_name if facesheet else None,
                    facesheet.middle_name if facesheet else None,
                    facesheet.last_name if facesheet else None,
                ),
                "mrn": patient.mrn if patient else None,
                "benefit_period_id": str(bp.id),
                "election_date": bp.election_date.isoformat() if bp.election_date else None,
                "noe_submitted_date": bp.noe_submitted_date.isoformat() if bp.noe_submitted_date else None,
                "noe_exception_reason": bp.noe_exception_reason,
                "noe_filed": bp.noe_submitted_date is not None,
                "is_late": bool(penalty and penalty.is_late),
                "is_exempt": bool(penalty and penalty.is_exempt),
                "non_covered_start": penalty.non_covered_start.isoformat() if penalty and penalty.non_covered_start else None,
                "non_covered_end": penalty.non_covered_end.isoformat() if penalty and penalty.non_covered_end else None,
                "non_covered_days": penalty.non_covered_days if penalty else None,
                "penalty_reason": penalty.reason if penalty else "Missing election_date -- cannot evaluate NOE timeliness",
            }
        )

    late_count = sum(1 for r in results if r["is_late"])
    unfiled_count = sum(1 for r in results if not r["noe_filed"])

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "late_count": late_count,
        "unfiled_count": unfiled_count,
        "noe_tracking": results,
    }
