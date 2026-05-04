from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from dateutil import parser

from app.core.database import get_db
from app.core.permissions import require_roles
from app.services.benefit_period_service import create_benefit_period

router = APIRouter(prefix="/benefits", tags=["Benefits"])


@router.post("/", summary="Create benefit period")
def create_benefit_period_endpoint(
    patient_id: str,
    start_date: str,      # ✅ string input
    period_number: int,   # ✅ required
    db: Session = Depends(get_db),
    user=Depends(require_roles(["RN", "Administrator"])),
):
    try:
        parsed_start_date: date = parser.parse(start_date).date()
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid date format. Use 'May 1 2026' or '2026-05-01'."
        )

    bp = create_benefit_period(
        db,
        patient_id=patient_id,
        start_date=parsed_start_date,
        period_number=period_number,
    )

    return {
        "id": bp.id,
        "patient_id": bp.patient_id,
        "start_date": bp.start_date,
        "end_date": bp.end_date,
        "period_number": bp.period_number,
        "status": bp.status,
    }