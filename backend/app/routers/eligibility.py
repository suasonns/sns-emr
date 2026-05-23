"""
Enterprise-grade Eligibility API.

Responsibilities:
- Manage eligibility ruleset definitions (LCD logic containers)
- Evaluate eligibility using stored rulesets
- Persist eligibility assessments for audit and IDG use

Design goals:
- Compliance-first (CMS / ACHC / Joint Commission)
- Strong request/response validation
- Clear separation of definition vs evaluation vs assessment
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.eligibility import EligibilityRuleset, EligibilityAssessment

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


# ---------------------------------------------------------------------
# Pydantic Schemas (ENTERPRISE SAFETY)
# ---------------------------------------------------------------------

class RulesetCreateRequest(BaseModel):
    ruleset_id: str = Field(..., description="Logical identifier for the ruleset")
    ruleset_version: str = Field(..., description="Semantic version of the ruleset")
    condition: str = Field(..., description="Primary condition (e.g., COPD, CHF)")
    jurisdiction: str = Field(default="ANY")
    ruleset_json: Dict[str, Any]
    created_by: str | None = None
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


class AssessmentCreateRequest(BaseModel):
    patient_id: str
    ruleset_id: str
    ruleset_version: str
    eligible: bool
    score: int
    observations_snapshot: Dict[str, Any]
    created_by: str | None = None


class AssessmentResponse(BaseModel):
    id: str


# ---------------------------------------------------------------------
# Ruleset Management
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

    return [
        RulesetResponse(
            id=str(r.id),
            ruleset_id=r.ruleset_id,
            ruleset_version=r.ruleset_version,
            condition=r.condition,
            jurisdiction=r.jurisdiction,
            is_active=r.is_active,
        )
        for r in rows
    ]


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
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return RulesetResponse(
        id=str(row.id),
        ruleset_id=row.ruleset_id,
        ruleset_version=row.ruleset_version,
        condition=row.condition,
        jurisdiction=row.jurisdiction,
        is_active=row.is_active,
    )


# ---------------------------------------------------------------------
# Eligibility Evaluation (NON-PERSISTENT)
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active eligibility ruleset not found",
        )

    # -----------------------------------------------------------------
    # PLACEHOLDER LOGIC (SAFE, EXPLICIT)
    # Replace with full LCD rule engine next
    # -----------------------------------------------------------------
    observations = payload.observations
    eligible = bool(observations)
    score = 70 if eligible else 0

    return EvaluationResponse(
        ruleset_id=ruleset.ruleset_id,
        ruleset_version=ruleset.ruleset_version,
        eligible=eligible,
        score=score,
        observations_snapshot=observations,
    )


# ---------------------------------------------------------------------
# Eligibility Assessment (PERSISTENT, AUDIT-CRITICAL)
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
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return AssessmentResponse(id=str(row.id))