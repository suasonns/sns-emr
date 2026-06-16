from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.core.task_completion_guard import assert_task_completion_is_valid
from app.models.task import Task
from app.models.visit import Visit
from app.models.enums import TaskStatus, TaskType
from app.api.schemas.task_write import TaskCompleteJSONRequest
from app.services.task_completion_service import complete_task_with_evidence
from app.services.audit_logger import log_event

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete task (JSON-only)",
)
def complete_task(
    payload: TaskCompleteJSONRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    # =========================================================
    # TENANT VALIDATION
    # =========================================================
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")

    # =========================================================
    # LOAD TASK
    # =========================================================
    task = (
        db.query(Task)
        .filter(
            Task.id == payload.task_id,
            Task.tenant_id == str(tenant_id)
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # =========================================================
    # IDEMPOTENCY GUARD
    # =========================================================
    if task.status == TaskStatus.COMPLETED:
        return task

    # =========================================================
    # BLOCK MANUAL BEREAVEMENT COMPLETION
    # =========================================================
    if task.task_type == TaskType.INITIAL_BEREAVEMENT:
        raise HTTPException(
            status_code=400,
            detail="Bereavement tasks must be completed via interdisciplinary documentation, not manual completion"
        )

    # =========================================================
    # VALIDATE REFERENCE (VISIT REQUIRED)
    # =========================================================
    if payload.completion_reference_type != "VISIT":
        raise HTTPException(
            status_code=422,
            detail="Only VISIT-based completion is allowed"
        )

    visit = (
        db.query(Visit)
        .filter(
            Visit.id == payload.completion_reference_id,
            Visit.tenant_id == str(tenant_id)
        )
        .first()
    )

    if not visit:
        raise HTTPException(status_code=404, detail="Referenced visit not found")

    if str(visit.patient_id) != str(task.patient_id):
        raise HTTPException(
            status_code=400,
            detail="Visit does not belong to the same patient as the task"
        )

    # =========================================================
    # DISCIPLINE VALIDATION (COMPLIANCE CRITICAL)
    # =========================================================
    visit_type = (visit.visit_type or "").upper()

    allowed_mapping = {
        TaskType.INITIAL_RN_ICA: ["RN"],
        TaskType.INITIAL_MSW_ICA: ["SW"],
        TaskType.INITIAL_SC_ICA: ["CHAPLAIN"],
    }

    if task.task_type in allowed_mapping:
        allowed_disciplines = allowed_mapping[task.task_type]

        if visit_type not in allowed_disciplines:
            raise HTTPException(
                status_code=400,
                detail=f"{task.task_type.value} can only be completed by {allowed_disciplines}"
            )

    # =========================================================
    # COMPLETE TASK WITH EVIDENCE
    # =========================================================
    complete_task_with_evidence(
        db=db,
        task=task,
        reference_type=payload.completion_reference_type,
        reference_id=payload.completion_reference_id,
        user_id=getattr(user, "id", None),
    )

    # =========================================================
    # POST-COMPLETION VALIDATION (CRITICAL)
    # =========================================================
    assert_task_completion_is_valid(
        status=task.status,
        completed_at=task.completed_at,
        completion_reference_type=task.completion_reference_type,
        completion_reference_id=task.completion_reference_id,
    )

    # =========================================================
    # AUDIT LOGGING
    # =========================================================
    try:
        log_event(
            user_id=user.id,
            role=(getattr(user, "role", "") or "").upper(),
            action="COMPLETE_TASK",
            entity_type="task",
            entity_id=str(task.id),
            db=db,
        )
    except Exception:
        pass

    db.commit()
    db.refresh(task)

    return task