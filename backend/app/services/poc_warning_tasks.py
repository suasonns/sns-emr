from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.benefit_period import BenefitPeriod  # adjust if your model path differs


WARN_DISCIPLINES = ["RN", "NP", "MD"]


def _get_current_benefit_period_id(db: Session, patient_id):
    """
    Picks the active benefit period for the patient.
    Uses start_date/end_date window if those fields exist.
    """
    today = datetime.utcnow().date()

    q = db.query(BenefitPeriod).filter(BenefitPeriod.patient_id == patient_id)

    # If your BenefitPeriod has date windows, select active
    if hasattr(BenefitPeriod, "start_date") and hasattr(BenefitPeriod, "end_date"):
        q = q.filter(BenefitPeriod.start_date <= today).filter(
            (BenefitPeriod.end_date == None) | (BenefitPeriod.end_date >= today)  # noqa: E711
        )

        bp = q.order_by(BenefitPeriod.start_date.desc()).first()
    else:
        # fallback: latest by created_at if no date window fields exist
        bp = q.order_by(BenefitPeriod.created_at.desc()).first()

    if not bp:
        # Hard fail is survey-safe: don't create malformed tasks missing benefit period
        raise ValueError("No benefit period found for patient; create a benefit period first.")

    return bp.id


def _has_open_task(db: Session, patient_id, benefit_period_id, task_type: str, discipline: str) -> bool:
    q = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.benefit_period_id == benefit_period_id)
        .filter(Task.task_type == task_type)
        .filter(Task.discipline == discipline)
        .filter(Task.status != "COMPLETED")
    )
    return db.query(q.exists()).scalar()


def warn_rn_np_md(
    *,
    db: Session,
    patient_id,
    task_type: str,
    due_date: date,
    origin: str,
    message: str,
    reference_type=None,
    reference_id=None,
):
    """
    Creates up to 3 tasks: RN, NP, MD.
    Uses benefit_period_id + regulatory_basis (required by schema).
    Dedupes against existing open tasks.
    """
    benefit_period_id = _get_current_benefit_period_id(db, patient_id)

    for d in WARN_DISCIPLINES:
        if _has_open_task(db, patient_id, benefit_period_id, task_type, d):
            continue

        t = Task(
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            discipline=d,
            task_type=task_type,
            origin=origin,                  # must be ADMISSION/PERIODIC/MANUAL
            regulatory_basis="POC_UPDATE",  # required by schema
            status="PENDING",
            due_date=due_date,
            completion_reference_type=reference_type,
            completion_reference_id=str(reference_id) if reference_id else None,
        )

        # Task model currently has no notes/details column; message is not stored yet.
        # You can store message later if you add Task.details or Task.notes.
        db.add(t)