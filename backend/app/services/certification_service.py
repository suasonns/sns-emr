# services/certification_service.py

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification

from app.services.recert_f2f_enforcement import (
    bp_index_date_derived,
    complete_task_with_evidence,
    require_f2f_completed_for_bp3_plus,
)


def create_or_finalize_cert(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    signed_by_role,
    signed_by_user_id=None,
):
    bp = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.id == benefit_period_id)
        .first()
    )

    if not bp:
        raise HTTPException(
            status_code=404,
            detail="Benefit period not found",
        )

    if str(bp.patient_id) != str(patient_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Benefit period does not belong "
                "to the specified patient."
            ),
        )

    role = (signed_by_role or "").upper()

    if role not in ("MD", "NP"):
        raise HTTPException(
            status_code=400,
            detail="signed_by_role must be MD or NP",
        )

    existing_cert = (
        db.query(Certification)
        .filter(
            Certification.patient_id == patient_id,
            Certification.benefit_period_id == benefit_period_id,
            Certification.status == "FINALIZED",
        )
        .order_by(Certification.signed_at.desc())
        .first()
    )

    if existing_cert:
        return existing_cert

    idx = bp_index_date_derived(
        db,
        patient_id,
        benefit_period_id,
    )

    if idx >= 3:
        require_f2f_completed_for_bp3_plus(
            db,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
        )

    signed_at = datetime.utcnow()
    effective_date = bp.start_date

    earliest_allowed = datetime.combine(
        effective_date - timedelta(days=15),
        datetime.min.time(),
    )

    if signed_at < earliest_allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Certification/recertification "
                "cannot be signed more than 15 days "
                "before period start."
            ),
        )

    cert_type = (
        "INITIAL"
        if idx == 1
        else "RECERT"
    )

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
    db.flush()

    task_type = (
        "CERTIFICATION"
        if idx == 1
        else "RECERTIFICATION"
    )

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