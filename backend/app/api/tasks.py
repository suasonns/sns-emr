from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.task import TaskResponse
from app.models.task import Task
from app.core.database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """
    List all tasks (including alert_reason if present).
    """
    return db.query(Task).order_by(Task.created_at.desc()).all()


@router.get("/escalated", response_model=list[TaskResponse])
def list_escalated_tasks(db: Session = Depends(get_db)):
    """
    List escalated tasks with alert_reason.
    Used for compliance dashboards and surveys.
    """
    return (
        db.query(Task)
        .filter(Task.status == "ESCALATED")
        .order_by(Task.created_at.desc())
        .all()
    )