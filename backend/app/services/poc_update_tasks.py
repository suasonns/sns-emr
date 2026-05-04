from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.patient import Patient
from app.models.benefit_period import BenefitPeriod


def _active_benefit_period_id(db: Session, patient_id, on_date):
    bp = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.start_date <= on_date,
            BenefitPeriod.end_date >= on_date,
        )
        .order_by(BenefitPeriod.start_date.desc())
        .first()
    )
    return bp.id if bp else None


def _ensure_poc_task(db: Session, *, patient_id, due_date, benefit_period_id, created_by, origin):
    existing = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.regulatory_basis == "POC_UPDATE",
            Task.discipline == "RN",
            Task.due_date == due_date,
            Task.status.in_(["PENDING", "OVERDUE", "ESCALATED"]),
        )
        .first()
    )
    if existing:
        return existing

    t = Task(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        task_type="OTHER",
        origin=origin,              # PERIODIC (routine) or MANUAL (crisis)
        discipline="RN",
        regulatory_basis="POC_UPDATE",
        due_date=due_date,
        status="PENDING",
        created_by=created_by,
    )
    db.add(t)
    return t


def _complete_due_poc_task(db: Session, *, patient_id, visit_date, visit_id):
    task = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.regulatory_basis == "POC_UPDATE",
            Task.discipline == "RN",
            Task.status == "PENDING",
            Task.due_date <= visit_date,
        )
        .order_by(Task.due_date.asc())
        .first()
    )
    if not task:
        return None

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = "VISIT"
    task.completion_reference_id = str(visit_id)
    return task


def handle_poc_update_on_visit_finalize(db: Session, *, visit, user_id):
    visit_type = (visit.visit_type or "").strip().upper()
    if visit_type != "RN":
        return {"mode": "SKIP_NON_RN", "created": 0, "completed": 0}

    patient = db.query(Patient).filter(Patient.id == visit.patient_id).first()
    if not patient:
        return {"mode": "NO_PATIENT", "created": 0, "completed": 0}

    visit_date = visit.visit_datetime.date() if visit.visit_datetime else datetime.utcnow().date()
    bp_id = _active_benefit_period_id(db, visit.patient_id, visit_date)

    created = 0
    completed = 0

    # CRISIS: every RN visit
    if (patient.acuity_state or "ROUTINE").strip().upper() == "CRISIS":
        _ensure_poc_task(
            db,
            patient_id=visit.patient_id,
            due_date=visit_date,
            benefit_period_id=bp_id,
            created_by=user_id,
            origin="MANUAL",
        )
        created += 1

        done = _complete_due_poc_task(
            db,
            patient_id=visit.patient_id,
            visit_date=visit_date,
            visit_id=visit.id,
        )
        if done:
            completed += 1

        db.commit()
        return {"mode": "CRISIS", "created": created, "completed": completed}

    # ROUTINE: supervisory RN visit schedules cadence
    if getattr(visit, "is_supervisory", False):
        done = _complete_due_poc_task(
            db,
            patient_id=visit.patient_id,
            visit_date=visit_date,
            visit_id=visit.id,
        )
        if done:
            completed += 1

        next_due = visit_date + timedelta(days=14)
        _ensure_poc_task(
            db,
            patient_id=visit.patient_id,
            due_date=next_due,
            benefit_period_id=bp_id,
            created_by=user_id,
            origin="PERIODIC",
        )
        created += 1

        db.commit()
        return {"mode": "ROUTINE_SUPERVISORY", "created": created, "completed": completed}

    return {"mode": "ROUTINE_NON_SUP", "created": 0, "completed": 0}