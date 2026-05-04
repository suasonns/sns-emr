from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.certification import Certification
from app.models.benefit_period import BenefitPeriod
from app.services.recert_f2f_enforcement import (
    bp_index_date_derived,
    require_f2f_completed_for_bp3_plus,
    complete_task_with_evidence,
)


def create_or_finalize_cert(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    signed_by_role,
    signed_by_user_id=None,
):
    bp = db.query(BenefitPeriod).filter(BenefitPeriod.id == benefit_period_id).first()
    if not bp:
        raise HTTPException(status_code=404, detail="Benefit period not found")

    role = (signed_by_role or "").upper()
    if role not in ("MD", "NP"):
        raise HTTPException(status_code=400, detail="signed_by_role must be MD or NP")

    idx = bp_index_date_derived(db, patient_id, benefit_period_id)

    # ✅ BP3+ enforcement: F2F must be completed before recertification
    if idx >= 3:
        require_f2f_completed_for_bp3_plus(
            db,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
        )

    # ✅ Timing guard: certification/recertification cannot be signed >15 days early
    now = datetime.utcnow()
    signed_at = now
    effective_date = bp.start_date

    earliest_allowed = datetime.combine(
        effective_date - timedelta(days=15),
        datetime.min.time(),
    )

    if signed_at < earliest_allowed:
        raise HTTPException(
            status_code=400,
            detail="Certification/recertification cannot be signed more than 15 days before period start.",
        )

    cert_type = "INITIAL" if idx == 1 else "RECERT"

    cert = Certification(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        cert_type=cert_type,
        signed_at=signed_at,
        effective_date=effective_date,
        signed_by_role=role,
        signed_by_user_id=signed_by_user_id,
        status="FINALIZED",
    )

    db.add(cert)
    db.flush()  # get cert.id for task evidence

    # ✅ Complete the correct task with evidence
    task_type = "CERTIFICATION" if idx == 1 else "RECERTIFICATION"
    complete_task_with_evidence(
        db,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        task_type=task_type,
        ref_type="CERTIFICATION",
        ref_id=str(cert.id),
    )

    db.commit()
    db.refresh(cert)
    return cert
