from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.core.task_completion_guard import assert_task_completion_is_valid

from app.models.task import Task
from app.models.visit import Visit
from app.models.clinical_note import ClinicalNote
from app.models.enums import (
    TaskStatus,
    TaskType,
    CompletionReferenceType,
)

from app.api.schemas.task_write import TaskCompleteJSONRequest
from app.services.task_completion_evidence import complete_task_with_evidence
from app.services.audit_logger import log_event

router = APIRouter(prefix="/tasks", tags=["tasks"])


# =========================================================
# REQUEST MODEL (NOTE-BASED)
# =========================================================

class TaskCompleteByNoteJSONRequest(BaseModel):
    task_id: UUID
    clinical_note_id: UUID


# =========================================================
# HELPERS
# =========================================================

def _tenant_str(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _load_task_for_tenant(
    db: Session,
    *,
    task_id: UUID,
    tenant_id,
) -> Task:
    task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(Task.id == task_id)
        .first()
    )

    if not task or _tenant_str(getattr(task, "tenant_id", None)) != _tenant_str(tenant_id):
        raise HTTPException(status_code=404, detail="Task not found")

    return task


def _load_visit_for_tenant(
    db: Session,
    *,
    visit_id: UUID,
    tenant_id,
) -> Visit:
    visit = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .filter(Visit.id == visit_id)
        .first()
    )

    if not visit or _tenant_str(getattr(visit, "tenant_id", None)) != _tenant_str(tenant_id):
        raise HTTPException(status_code=404, detail="Referenced visit not found")

    return visit


def _load_note_for_tenant(
    db: Session,
    *,
    clinical_note_id: UUID,
    tenant_id,
) -> ClinicalNote:
    note = (
        db.query(ClinicalNote)
        .execution_options(skip_tenant_filter=True)
        .filter(ClinicalNote.id == clinical_note_id)
        .first()
    )

    if not note or _tenant_str(getattr(note, "tenant_id", None)) != _tenant_str(tenant_id):
        raise HTTPException(status_code=404, detail="Clinical note not found")

    return note


def _map_note_family_to_reference_type(note_family: str) -> CompletionReferenceType:
    normalized = str(note_family).strip().upper()

    if normalized == "CLINICAL":
        return CompletionReferenceType.CLINICAL_NOTE

    if normalized == "PSYCHOSOCIAL":
        return CompletionReferenceType.PSYCHOSOCIAL_NOTE

    if normalized == "SPIRITUAL":
        return CompletionReferenceType.SPIRITUAL_NOTE

    return CompletionReferenceType.NOTE

# =========================================================
# EXISTING: VISIT-BASED COMPLETION
# =========================================================

@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete task (VISIT evidence)",
)
def complete_task(
    payload: TaskCompleteJSONRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")

    task = _load_task_for_tenant(
        db,
        task_id=payload.task_id,
        tenant_id=tenant_id,
    )

    if task.status == TaskStatus.COMPLETED:
        return task

    if task.task_type == TaskType.INITIAL_BEREAVEMENT:
        raise HTTPException(
            status_code=400,
            detail="Bereavement tasks must be completed via interdisciplinary documentation",
        )

    if payload.completion_reference_type != CompletionReferenceType.VISIT:
        raise HTTPException(
            status_code=422,
            detail="Only VISIT-based completion is allowed",
        )

    visit = _load_visit_for_tenant(
        db,
        visit_id=payload.completion_reference_id,
        tenant_id=tenant_id,
    )

    if str(visit.patient_id) != str(task.patient_id):
        raise HTTPException(
            status_code=400,
            detail="Visit does not belong to the same patient",
        )

    visit_type = (visit.visit_type or "").strip().upper()
    if not visit_type:
        raise HTTPException(
            status_code=422,
            detail="Visit type is required for completion validation",
        )

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
                detail=f"{task.task_type.value} must be completed by {allowed_disciplines}",
            )

    complete_task_with_evidence(
        db=db,
        task_id=task.id,
        completion_reference_type=payload.completion_reference_type,
        completion_reference_id=payload.completion_reference_id,
        completed_by=getattr(user, "id", None),
    )

    assert_task_completion_is_valid(
        status=task.status,
        completed_at=task.completed_at,
        completion_reference_type=task.completion_reference_type,
        completion_reference_id=task.completion_reference_id,
    )

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


# =========================================================
# NEW: NOTE-BASED COMPLETION
# =========================================================

@router.post(
    "/complete-by-note",
    status_code=status.HTTP_200_OK,
    summary="Complete task (NOTE evidence)",
)
def complete_task_by_note(
    payload: TaskCompleteByNoteJSONRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")

    task = _load_task_for_tenant(
        db,
        task_id=payload.task_id,
        tenant_id=tenant_id,
    )

    if task.status == TaskStatus.COMPLETED:
        return task

    note = _load_note_for_tenant(
        db,
        clinical_note_id=payload.clinical_note_id,
        tenant_id=tenant_id,
    )

    if note.patient_id is not None and str(note.patient_id) != str(task.patient_id):
        raise HTTPException(
            status_code=400,
            detail="Clinical note does not belong to the same patient",
        )

    note_family = getattr(note, "form_family", None)
    if not note_family:
        raise HTTPException(
            status_code=422,
            detail="Clinical note has no form_family assigned",
        )

    reference_type = _map_note_family_to_reference_type(note_family)

    complete_task_with_evidence(
        db=db,
        task_id=task.id,
        completion_reference_type=reference_type,
        completion_reference_id=note.id,
        completed_by=getattr(user, "id", None),
    )

    assert_task_completion_is_valid(
        status=task.status,
        completed_at=task.completed_at,
        completion_reference_type=task.completion_reference_type,
        completion_reference_id=task.completion_reference_id,
    )

    try:
        log_event(
            user_id=user.id,
            role=(getattr(user, "role", "") or "").upper(),
            action="COMPLETE_TASK_BY_NOTE",
            entity_type="task",
            entity_id=str(task.id),
            db=db,
        )
    except Exception:
        pass

    db.commit()
    db.refresh(task)

    return task