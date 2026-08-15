# services/f2f_service.py

from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.f2f_encounter import F2FEncounter
from app.services.recert_f2f_enforcement import (
    validate_f2f_window,
    complete_task_with_evidence,
)


def create_f2f(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    encounter_date,
    performed_by_role,
    performed_by_user_id=None,
    summary=None,
):
    role = (performed_by_role or "").upper()
    if role not in ("MD", "NP"):
        raise HTTPException(status_code=400, detail="performed_by_role must be MD or NP")

    # Validate CMS timing window (≤30 days prior to BP start for BP3+)
    validate_f2f_window(
        db,
        benefit_period_id=benefit_period_id,
        encounter_date=encounter_date,
    )

    f2f = F2FEncounter(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        encounter_date=encounter_date,
        performed_by_role=role,
        performed_by_user_id=performed_by_user_id,
        summary=summary,
        status="DRAFT",
    )

    db.add(f2f)
    db.commit()
    db.refresh(f2f)
    return f2f


def finalize_f2f(db: Session, *, f2f: F2FEncounter):
    if f2f.status == "FINALIZED":
        return f2f

    validate_f2f_window(
        db,
        benefit_period_id=f2f.benefit_period_id,
        encounter_date=f2f.encounter_date,
    )

    f2f.status = "FINALIZED"
    f2f.finalized_at = datetime.utcnow()

    # ✅ Complete the F2F task with evidence
    complete_task_with_evidence(
        db,
        patient_id=f2f.patient_id,
        benefit_period_id=f2f.benefit_period_id,
        task_type="F2F",
        ref_type="F2F_ENCOUNTER",
        ref_id=str(f2f.id),
    )

    db.commit()
    db.refresh(f2f)
    return f2f