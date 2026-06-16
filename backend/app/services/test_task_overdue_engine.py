import uuid
from datetime import date, timedelta

from app.services.task_overdue_engine import run_overdue_engine
from app.models.task import Task


def test_overdue_engine_marks_tasks(db_session):
    """
    Enterprise test:
    - creates a pending task in DB
    - runs overdue engine
    - verifies status changes correctly
    """

    tenant_id = uuid.uuid4()

    # -----------------------------------------------------
    # create test task
    # -----------------------------------------------------
    task = Task(
        tenant_id=tenant_id,
        task_type="INITIAL_RN_ICA",
        status="PENDING",
        due_date=date.today() - timedelta(days=3),
    )

    db_session.add(task)
    db_session.commit()

    # -----------------------------------------------------
    # run engine
    # -----------------------------------------------------
    run_overdue_engine(
        db=db_session,
        tenant_id=tenant_id,
    )

    db_session.refresh(task)

    # -----------------------------------------------------
    # ASSERT
    # -----------------------------------------------------
    assert task.status == "OVERDUE"