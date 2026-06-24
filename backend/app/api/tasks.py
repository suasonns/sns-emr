from __future__ import annotations

import uuid
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.services.task_overdue_engine import run_overdue_engine

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.task import Task
from app.api.schemas.task_read import TaskResponse
from app.tenancy.registry import assert_known_tenant


router = APIRouter(prefix="/tasks", tags=["tasks"])


# =========================================================
# DB DEPENDENCY (AUDIT‑SAFE)
# =========================================================

def get_db_with_request_state(
    request: Request,
    db: Session = Depends(get_db_tenant),
) -> Generator[Session, None, None]:
    request.state.db = db
    try:
        yield db
    finally:
        pass


# =========================================================
# TENANT GUARD
# =========================================================

def require_valid_tenant(user=Depends(get_current_user)):
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    try:
        assert_known_tenant(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return user


# =========================================================
# QUERY ENDPOINTS
# =========================================================

@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_valid_tenant),
):
    tenant_id = str(user.tenant_id)

    return (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.get("/patients/{patient_id}", response_model=list[TaskResponse])
def list_tasks_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_valid_tenant),
):
    tenant_id = str(user.tenant_id)

    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
        )
        .order_by(Task.due_date.asc())
        .all()
    )


@router.get("/escalated", response_model=list[TaskResponse])
def list_escalated_tasks(
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_valid_tenant),
):
    tenant_id = str(user.tenant_id)

    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == "ESCALATED",
        )
        .order_by(Task.created_at.desc())
        .all()
    )


# =========================================================
# RN DASHBOARD
# =========================================================

@router.get(
    "/dashboard",
    response_model=list[TaskResponse],
    summary="RN dashboard (actionable tasks)",
)
def rn_dashboard_tasks(
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_valid_tenant),
):
    tenant_id = user.tenant_id

    print("RN DASHBOARD HIT")
    print(f"tenant_id={tenant_id}")

    updated = run_overdue_engine(
        db=db,
        tenant_id=tenant_id,
    )

    print(f"overdue_engine_updated={updated}")

    db.commit()

    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.status.in_(["PENDING", "OVERDUE", "ESCALATED"]),
        )
        .order_by(Task.due_date.asc(), Task.created_at.asc())
        .all()
    )
