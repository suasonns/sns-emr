import uuid
from datetime import date, timedelta

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskStatus,
)
from app.services.task_overdue_engine import run_overdue_engine


def test_overdue_engine_marks_tasks(db_session):
    """
    Enterprise test:

    Verifies that a pending task whose due date
    is in the past is marked OVERDUE by the engine.
    """

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # -----------------------------------------------------
    # Create patient required by FK constraints
    # -----------------------------------------------------
    patient = Patient(
        tenant_id=tenant_id,
        mrn=f"TEST-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        created_by=user_id,
    )

    db_session.add(patient)
    db_session.flush()

    # -----------------------------------------------------
    # Create valid task
    # -----------------------------------------------------
    task = Task(
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.INITIAL_RN_ICA,
        origin=TaskOrigin.SYSTEM,
        discipline=TaskDiscipline.RN,
        status=TaskStatus.PENDING,
        due_date=date.today() - timedelta(days=3),
    )

    db_session.add(task)
    db_session.commit()

    # -----------------------------------------------------
    # Run engine
    # -----------------------------------------------------
    run_overdue_engine(
        db=db_session,
        tenant_id=tenant_id,
    )

    db_session.refresh(task)

    # -----------------------------------------------------
    # Verify
    # -----------------------------------------------------
    assert task.status == TaskStatus.OVERDUE