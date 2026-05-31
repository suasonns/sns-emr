from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.enums import CompletionReferenceType
from app.services.audit_logger import log_event
from app.services.task_completion_evidence import complete_task_with_evidence


router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCompletePayload(BaseModel):
    completion_reference_type: CompletionReferenceType = Field(
        ..., json_schema_extra={"example": "DOCUMENT"}
    )
    completion_reference_id: uuid.UUID = Field(
        ..., json_schema_extra={"example": "11111111-1111-1111-1111-111111111111"}
    )


@router.post("/{task_id}/complete", status_code=status.HTTP_200_OK, summary="Complete task with evidence")
def complete_task(
    task_id: uuid.UUID,
    payload: TaskCompletePayload,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    task = complete_task_with_evidence(
        db,
        task_id=task_id,
        completion_reference_type=payload.completion_reference_type,
        completion_reference_id=payload.completion_reference_id,
        completed_by=user.id,
    )

    # Audit log (best-effort)
    try:
        log_event(
            user_id=user.id,
            role=(user.role or "").upper(),
            action="COMPLETE_TASK",
            entity_type="task",
            entity_id=str(task.id),
            db=db,
        )
    except Exception:
        pass

    db.commit()
    return {
        "task_id": str(task.id),
        "status": task.status,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "completion_reference_type": task.completion_reference_type,
        "completion_reference_id": str(task.completion_reference_id) if task.completion_reference_id else None,
    }