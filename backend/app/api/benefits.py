from __future__ import annotations

from datetime import date
from dateutil import parser
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.benefit_period import BenefitPeriod
from app.services.benefit_period_service import rollover_benefit_period

router = APIRouter(prefix="/benefits", tags=["Benefits"])

# Any clinical role may view a patient's benefit periods (needed to select
# the benefit_period_id when preparing a CTI/F2F draft); this is read-only
# and does not grant any certification/order/signature authority.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"]


@router.get("/patients/{patient_id}", summary="List a patient's benefit periods (for CTI/F2F benefit_period_id selection)")
def list_benefit_periods(
    patient_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    try:
        parsed_patient_id = UUID(patient_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid UUID format for patient_id.")

    get_authorized_patient(db, parsed_patient_id, user)

    periods = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.patient_id == parsed_patient_id)
        .filter(BenefitPeriod.tenant_id == user.tenant_id)
        .order_by(BenefitPeriod.period_number.asc())
        .all()
    )
    return [
        {
            "id": str(bp.id),
            "patient_id": str(bp.patient_id),
            "benefit_type": bp.benefit_type,
            "period_number": bp.period_number,
            "election_date": bp.election_date.isoformat() if bp.election_date else None,
            "start_date": bp.start_date.isoformat() if bp.start_date else None,
            "end_date": bp.end_date.isoformat() if bp.end_date else None,
            "is_current": bp.is_current,
        }
        for bp in periods
    ]


@router.post("/", summary="Create or rollover benefit period")
def rollover_benefit_period_endpoint(
    patient_id: str,
    tenant_id: str,
    election_date: str,
    start_date: str,
    benefit_type: str,  # "INITIAL" or "RECERT"
    db: Session = Depends(get_db),
    user=Depends(require_roles(["RN", "Administrator"])),
):
    """
    Enterprise-safe endpoint for benefit period creation / rollover.

    - Automatically determines period_number
    - Enforces only ONE active benefit period
    - Idempotent-safe behavior
    """

    try:
        parsed_start_date: date = parser.parse(start_date).date()
        parsed_election_date: date = parser.parse(election_date).date()
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid date format. Use 'May 1 2026' or '2026-05-01'.",
        )

    try:
        parsed_patient_id = UUID(patient_id)
        parsed_tenant_id = UUID(tenant_id)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid UUID format for patient_id or tenant_id.",
        )

    try:
        bp = rollover_benefit_period(
            db=db,
            tenant_id=parsed_tenant_id,
            patient_id=parsed_patient_id,
            election_date=parsed_election_date,
            start_date=parsed_start_date,
            benefit_type=benefit_type.upper(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to create or rollover benefit period",
        )

    return {
        "id": str(bp.id),
        "patient_id": str(bp.patient_id),
        "tenant_id": str(bp.tenant_id),
        "benefit_type": bp.benefit_type,
        "period_number": bp.period_number,
        "election_date": bp.election_date,
        "start_date": bp.start_date,
        "end_date": bp.end_date,
        "is_current": bp.is_current,
    }
