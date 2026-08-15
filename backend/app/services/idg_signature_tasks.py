# services/idg_signature_tasks.py

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List

from app.models.task import Task
from app.models.enums import TaskType, TaskStatus


def create_signature_tasks(
    db: Session,
    *,
    idg_review,
    disciplines: List[str] = None,
):
    """
    Create IDG signature tasks for missing disciplines.

    SAFE / MINIMAL VERSION:
    - Creates tasks ONLY if they don't already exist
    - Does not duplicate tasks
    """

    if disciplines is None:
        # Default disciplines (adjust later if needed)
        disciplines = ["RN", "MSW", "MD"]

    created_tasks = []

    for discipline in disciplines:
        existing = (
            db.query(Task)
            .filter(
                Task.patient_id == idg_review.patient_id,
                Task.task_type == TaskType.IDG_SIGNATURE_REQUIRED,
                Task.discipline == discipline,
                Task.status == TaskStatus.PENDING,
            )
            .first()
        )

        if existing:
            continue

        task = Task(
            tenant_id=idg_review.tenant_id,
            patient_id=idg_review.patient_id,
            task_type=TaskType.IDG_SIGNATURE_REQUIRED,
            discipline=discipline,
            status=TaskStatus.PENDING,
            origin="IDG",
            due_date=datetime.now(timezone.utc),
        )

        db.add(task)
        created_tasks.append(task)

    # DO NOT COMMIT HERE — caller should control transaction

    return created_tasks
