from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.safety_assessment import SafetyAssessment
from app.schemas.safety_assessment import (
    SafetyAssessmentCreate,
    SafetyAssessmentUpdate,
    derive_safety_responsibility,
)


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------

def get_safety_assessment(db: Session, assessment_id: UUID) -> SafetyAssessment:
    assessment = (
        db.query(SafetyAssessment)
        .filter(SafetyAssessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Safety assessment not found")
    return assessment


def list_safety_assessments_by_patient(
    db: Session,
    patient_id: UUID,
) -> list[SafetyAssessment]:
    return (
        db.query(SafetyAssessment)
        .filter(SafetyAssessment.patient_id == patient_id)
        .order_by(SafetyAssessment.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------

def create_safety_assessment(
    db: Session,
    payload: SafetyAssessmentCreate,
) -> SafetyAssessment:
    responsibility = derive_safety_responsibility(payload.care_setting)

    assessment = SafetyAssessment(
        patient_id=payload.patient_id,
        care_setting=payload.care_setting,
        safety_responsibility=responsibility,
        data_json=payload.data_json,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------

def update_safety_assessment(
    db: Session,
    assessment_id: UUID,
    payload: SafetyAssessmentUpdate,
) -> SafetyAssessment:
    assessment = get_safety_assessment(db, assessment_id)

    # Policy choice:
    # If you want NO edits after sign, uncomment the block below.
    #
    # if assessment.signed_at is not None:
    #     raise HTTPException(
    #         status_code=409,
    #         detail="Signed safety assessment cannot be modified",
    #     )

    if payload.data_json is not None:
        assessment.data_json = payload.data_json

    db.commit()
    db.refresh(assessment)
    return assessment


# ---------------------------------------------------------------------
# SIGN / LOCK
# ---------------------------------------------------------------------

def sign_safety_assessment(
    db: Session,
    assessment_id: UUID,
    signer_id: UUID,
) -> SafetyAssessment:
    assessment = get_safety_assessment(db, assessment_id)

    # Idempotent sign
    if assessment.signed_at is not None:
        return assessment

    assessment.signed_at = datetime.now(timezone.utc)
    assessment.signed_by = signer_id

    db.commit()
    db.refresh(assessment)
    return assessment