import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.task import Task


router = APIRouter(prefix="/task-scheduling", tags=["task-scheduling"])


class TaskScheduleUpdate(BaseModel):
    scheduled_start_at: datetime


@router.patch("/tasks/{task_id}", summary="Schedule a task time (after staff confirms availability)")
def schedule_task(
    task_id: uuid.UUID,
    payload: TaskScheduleUpdate,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.scheduled_start_at = payload.scheduled_start_at
    task.schedule_status = "SCHEDULED"

    db.commit()
    db.refresh(task)
    return task