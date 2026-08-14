from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.eligibility import (
    EligibilityRuleset,
    EligibilityAssessment,
)
from app.services.eligibility.engine import evaluate_hospice_eligibility

router = APIRouter(
    prefix="/eligibility",
    tags=["Eligibility"],
)


# ---------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------

class RulesetCreateRequest(BaseModel):
    ruleset_id: str
    ruleset_version: str
    condition: str
    jurisdiction: Optional[str] = Field(default="ANY")
    ruleset_json: Dict[str, Any]
    created_by: Optional[str] = None
    is_active: bool = True


class RulesetResponse(BaseModel):
    id: str
    ruleset_id: str
    ruleset_version: str
    condition: str
    jurisdiction: str
    is_active: bool


class EvaluationRequest(BaseModel):
    patient_id: str
    observations: Dict[str, Any]


class EvaluationResponse(BaseModel):
    ruleset_id: str
    ruleset_version: str
    eligible: bool
    score: int
    observations_snapshot: Dict[str, Any]


class LCDEvaluateRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    facts: Dict[str, Any] = Field(default_factory=dict)
    admission_date: Optional[str] = None


class AssessmentCreateRequest(BaseModel):
    patient_id: str
    ruleset_id: str
    ruleset_version: str
    eligible: bool
    score: int
    observations_snapshot: Dict[str, Any]
    created_by: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: str


# ---------------------------------------------------------------------
# RULESET MANAGEMENT
# ---------------------------------------------------------------------

@router.get(
    "/rulesets",
    response_model=List[RulesetResponse],
)
def list_rulesets(db: Session = Depends(get_db)):
    rows = (
        db.query(EligibilityRuleset)
        .order_by(EligibilityRuleset.created_at.desc())
        .all()
    )
    return rows


@router.post(
    "/rulesets",
    response_model=RulesetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ruleset(
    payload: RulesetCreateRequest,
    db: Session = Depends(get_db),
):
    row = EligibilityRuleset(
        ruleset_id=payload.ruleset_id,
        ruleset_version=payload.ruleset_version,
        condition=payload.condition,
        jurisdiction=payload.jurisdiction,
        ruleset_json=payload.ruleset_json,
        created_by=payload.created_by,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row


# ---------------------------------------------------------------------
# ELIGIBILITY EVALUATION (NON-PERSISTENT)
# ---------------------------------------------------------------------

@router.post(
    "/evaluate/{ruleset_id}",
    response_model=EvaluationResponse,
)
def evaluate_ruleset(
    ruleset_id: str,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
):
    ruleset = (
        db.query(EligibilityRuleset)
        .filter(
            EligibilityRuleset.ruleset_id == ruleset_id,
            EligibilityRuleset.is_active.is_(True),
        )
        .order_by(EligibilityRuleset.created_at.desc())
        .first()
    )

    if not ruleset:
        raise HTTPException(
            status_code=404,
            detail=f"Active ruleset not found: {ruleset_id}",
        )

    # VERY SIMPLE evaluation placeholder (you will replace with engine)
    score = 0
    for key, value in payload.observations.items():
        if isinstance(value, bool) and value:
            score += 1

    eligible = score >= 2  # placeholder logic

    return {
        "ruleset_id": ruleset.ruleset_id,
        "ruleset_version": ruleset.ruleset_version,
        "eligible": eligible,
        "score": score,
        "observations_snapshot": payload.observations,
    }


@router.post(
    "/lcd-evaluate",
    status_code=status.HTTP_200_OK,
)
def evaluate_lcd(
    payload: LCDEvaluateRequest,
    db: Session = Depends(get_db),
):
    """Evaluate the selected hospice LCD against the supplied patient and evidence facts."""
    del db
    patient_data = dict(payload.patient or {})
    for key, value in (payload.facts or {}).items():
        if key not in patient_data:
            patient_data[key] = value

    patient_obj = SimpleNamespace(**patient_data)
    admission_date = payload.admission_date or datetime.utcnow().date().isoformat()

    return evaluate_hospice_eligibility(patient_obj, admission_date)


# ---------------------------------------------------------------------
# ELIGIBILITY ASSESSMENT (PERSISTENT / AUDIT)
# ---------------------------------------------------------------------

@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    payload: AssessmentCreateRequest,
    db: Session = Depends(get_db),
):
    row = EligibilityAssessment(
        patient_id=payload.patient_id,
        ruleset_id=payload.ruleset_id,
        ruleset_version=payload.ruleset_version,
        eligible=payload.eligible,
        score=payload.score,
        observations_snapshot=payload.observations_snapshot,
        created_by=payload.created_by,
        created_at=datetime.utcnow(),
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": str(row.id),
    }