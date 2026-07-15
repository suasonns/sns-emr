from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant

from app.services.poc_service import create_plan_of_care as create_plan_of_care_service


router = APIRouter(
    prefix="/plan-of-care",
    tags=["plan-of-care"],
)


# =========================================================
# DEPENDENCY WRAPPER
# =========================================================

def get_db_with_request_state(
    db: Session = Depends(get_db_tenant),
):
    yield db


def require_tenant_user(user=Depends(get_current_user)):
    if getattr(user, "is_superuser", False) or getattr(user, "is_management", False):
        raise HTTPException(
            status_code=403,
            detail="Tenant-scoped endpoint not allowed for system accounts",
        )
    return user


def _tenant_id_uuid(user) -> uuid.UUID:
    if not getattr(user, "tenant_id", None):
        raise HTTPException(401, "Missing tenant")

    return uuid.UUID(str(user.tenant_id))


# =========================================================
# REQUEST SCHEMA
# =========================================================

class PlanOfCareCreate(BaseModel):
    visit_id: str

    patient_id: str

    problem_id: str

    relation_to_dx: str

    goal: str

    intervention: str

    frequency: Optional[str] = None

    clinical_context: str


# =========================================================
# CREATE PLAN OF CARE
# =========================================================

@router.post("/")
def create_plan_of_care(
    payload: PlanOfCareCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    user_id = (
        getattr(user, "user_id", None)
        or getattr(user, "id", None)
        or getattr(user, "sub", None)
    )

    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Invalid user identity",
        )

    if not payload.goal:
        raise HTTPException(
            status_code=400,
            detail="goal is required",
        )

    if not payload.intervention:
        raise HTTPException(
            status_code=400,
            detail="intervention is required",
        )

    if not payload.clinical_context:
        raise HTTPException(
            status_code=400,
            detail="clinical_context is required",
        )

    poc_content = {
        "visit_id": payload.visit_id,
        "patient_id": payload.patient_id,
        "problem_id": payload.problem_id,
        "relation_to_dx": payload.relation_to_dx,
        "goal": payload.goal,
        "intervention": payload.intervention,
        "frequency": payload.frequency,
        "clinical_context": payload.clinical_context,
    }

    poc = create_plan_of_care_service(
        db=db,
        tenant_id=tenant_id,
        patient_id=uuid.UUID(payload.patient_id),
        created_by_user_id=user_id,
        poc_content=poc_content,
    )

    return {
        "status": "success",
        "plan_of_care_id": str(poc.id),
    }