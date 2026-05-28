from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.task import Task
from app.services.task_service import complete_task
from app.api.schemas.task import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------

class TaskCompletionRequest(BaseModel):
    completion_reference_type: str = Field(
        ..., description="VISIT | NOTE | IDG_MEETING | etc"
    )
    completion_reference_id: UUID


# ------------------------------------------------------------------
# Query endpoints
# ------------------------------------------------------------------

@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """
    List all tasks.
    Used for dashboards, audits, and operational views.
    """
    return (
        db.query(Task)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.get("/escalated", response_model=list[TaskResponse])
def list_escalated_tasks(db: Session = Depends(get_db)):
    """
    List escalated tasks.
    Used for compliance dashboards and survey prep.
    """
    return (
        db.query(Task)
        .filter(Task.status == "ESCALATED")
        .order_by(Task.created_at.desc())
        .all()
    )


# ------------------------------------------------------------------
# Mutation endpoints
# ------------------------------------------------------------------

@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task_endpoint(
    task_id: UUID,
    payload: TaskCompletionRequest,
    db: Session = Depends(get_db),
):
    """
    Complete a task with required evidence.

    This endpoint enforces CMS‑mandated evidence rules.
    """
    try:
        task = complete_task(
            db=db,
            task_id=task_id,
            completion_reference_type=payload.completion_reference_type,
            completion_reference_id=payload.completion_reference_id,
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
