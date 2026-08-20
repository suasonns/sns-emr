from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser, get_current_user
from app.services.safety_assessments import (
    create_safety_assessment,
    get_safety_assessment,
    list_safety_assessments_by_patient,
    update_safety_assessment,
    sign_safety_assessment,
)
from app.schemas.safety_assessment import (
    SafetyAssessmentCreate,
    SafetyAssessmentUpdate,
    SafetyAssessmentRead,
)

router = APIRouter(prefix="/safety-assessments", tags=["Safety Assessments"])


@router.post("", response_model=SafetyAssessmentRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: SafetyAssessmentCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    get_authorized_patient(db, payload.patient_id, user)
    return create_safety_assessment(db, payload)


@router.get("/{assessment_id}", response_model=SafetyAssessmentRead)
def get_by_id(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    assessment = get_safety_assessment(db, assessment_id)
    get_authorized_patient(db, assessment.patient_id, user)
    return assessment


@router.get("/patient/{patient_id}", response_model=list[SafetyAssessmentRead])
def list_by_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    get_authorized_patient(db, patient_id, user)
    return list_safety_assessments_by_patient(db, patient_id)


@router.patch("/{assessment_id}", response_model=SafetyAssessmentRead)
def update(
    assessment_id: UUID,
    payload: SafetyAssessmentUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    assessment = get_safety_assessment(db, assessment_id)
    get_authorized_patient(db, assessment.patient_id, user)
    return update_safety_assessment(db, assessment_id, payload)


@router.post("/{assessment_id}/sign", response_model=SafetyAssessmentRead)
def sign(
    assessment_id: UUID,
    signer_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    # signer_id should come from auth token in production; this keeps it simple for now.
    assessment = get_safety_assessment(db, assessment_id)
    get_authorized_patient(db, assessment.patient_id, user)
    return sign_safety_assessment(db, assessment_id, signer_id)