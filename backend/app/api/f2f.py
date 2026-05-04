from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.auth import CurrentUser

from app.models.f2f_encounter import F2FEncounter
from app.services.f2f_service import create_f2f, finalize_f2f

router = APIRouter(prefix="/f2f", tags=["F2F"])


@router.post("/", summary="Create F2F encounter (draft)")
def create_f2f_endpoint(
    patient_id: str,
    benefit_period_id: str,
    encounter_date: date,
    performed_by_role: str,
    summary: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    f2f = create_f2f(
        db=db,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        encounter_date=encounter_date,
        performed_by_role=performed_by_role,
        performed_by_user_id=user.user_id,
        summary=summary,
    )
    return {
        "id": str(f2f.id),
        "status": f2f.status,
        "encounter_date": str(f2f.encounter_date),
    }


@router.post("/{f2f_id}/finalize", summary="Finalize F2F encounter and complete F2F task")
def finalize_f2f_endpoint(
    f2f_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["NP", "MD", "Administrator"])),
):
    f2f = db.query(F2FEncounter).filter(F2FEncounter.id == f2f_id).first()
    if not f2f:
        raise HTTPException(status_code=404, detail="F2F encounter not found")

    f2f = finalize_f2f(db=db, f2f=f2f)
    return {
        "id": str(f2f.id),
        "status": f2f.status,
        "finalized_at": str(f2f.finalized_at),
    }