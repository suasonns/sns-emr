from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.models.task import Task

logger = logging.getLogger(__name__)

HUV_DISCIPLINES = {"RN", "MD", "NP"}
SFV_DISCIPLINES = {"AIDE", "SW", "CHAPLAIN"}


def auto_complete_tasks_for_visit(
    db: Session,
    *,
    visit,
    completed_by=None,
):
    """
    Completes the oldest matching PENDING task when a visit is finalized.
    Matches using visit.visit_type and visit.visit_datetime.
    Accepts visit_type in any case (rn/RN/Rn).

    For visit-driven tasks (HUV/SFV), we only complete tasks that are due
    on or before the visit date.

    NOTE:
    This function does NOT commit. Caller should commit once at the end of finalize.
    """
    discipline = (getattr(visit, "visit_type", "") or "").strip().upper()
    if not discipline:
        logger.warning(
            "Visit %s has empty visit_type; cannot auto-complete tasks.",
            str(getattr(visit, "id", None)),
        )
        return None

    patient_id = visit.patient_id

    visit_date = (
        visit.visit_datetime.date()
        if getattr(visit, "visit_datetime", None)
        else datetime.utcnow().date()
    )

    task_type = "HUV" if discipline in HUV_DISCIPLINES else "SFV"

    q = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.discipline == discipline,
            Task.task_type == task_type,
            Task.status == "PENDING",
            Task.due_date <= visit_date,
        )
        .order_by(Task.due_date.asc())
    )

    # Filter by benefit_period_id only if visit has it and it's not null
    if getattr(visit, "benefit_period_id", None) is not None:
        q = q.filter(Task.benefit_period_id == visit.benefit_period_id)

    task = q.first()
    if not task:
        logger.info(
            "No matching task found for visit=%s patient=%s discipline=%s task_type=%s visit_date=%s",
            str(getattr(visit, "id", None)),
            str(patient_id),
            discipline,
            task_type,
            str(visit_date),
        )
        return None

    if task.status != "PENDING":
        logger.warning(
            "Task %s not PENDING (status=%s). Skipping completion.",
            str(task.id),
            str(task.status),
        )
        return None

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = "VISIT"
    task.completion_reference_id = str(visit.id)

    logger.info("Completed task %s using visit %s", str(task.id), str(visit.id))
    return task


def complete_idg_review_task_for_meeting(
    db: Session,
    *,
    meeting,
    completed_by=None,
):
    """
    Completes the oldest PENDING IDG_REVIEW task when an IDG meeting is finalized.

    IMPORTANT:
    - IDG meetings can occur before the due date; therefore we do NOT require
      Task.due_date <= meeting_date.
    - Completes the oldest pending IDG_REVIEW task (scoped to benefit_period_id when available),
      links evidence to the meeting, and creates the next IDG_REVIEW due +14 days.

    Assumes enums:
      - tasks_task_type_enum contains 'IDG_REVIEW'
      - tasks_regulatory_basis_enum contains 'IDG'
      - tasks_completion_ref_enum contains 'IDG_MEETING'
    """
    patient_id = meeting.patient_id

    meeting_date = (
        meeting.meeting_date.date()
        if hasattr(meeting.meeting_date, "date")
        else meeting.meeting_date
    )

    q = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == "IDG_REVIEW",
            Task.status == "PENDING",
        )
        .order_by(Task.due_date.asc())
    )

    if getattr(meeting, "benefit_period_id", None) is not None:
        q = q.filter(Task.benefit_period_id == meeting.benefit_period_id)

    task = q.first()
    if not task:
        logger.info(
            "No IDG_REVIEW task found for meeting=%s patient=%s",
            str(getattr(meeting, "id", None)),
            str(patient_id),
        )
        return None

    # Complete current task with evidence
    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = "IDG_MEETING"
    task.completion_reference_id = str(meeting.id)

    # Create next task due 14 days later (based on completed task due_date)
    next_due = (task.due_date or meeting_date) + timedelta(days=14)

    next_task = Task(
        patient_id=patient_id,
        benefit_period_id=getattr(meeting, "benefit_period_id", None),
        task_type="IDG_REVIEW",
        origin="PERIODIC",
        discipline=(getattr(task, "discipline", None) or "RN"),
        regulatory_basis=(getattr(task, "regulatory_basis", None) or "IDG"),
        due_date=next_due,
        status="PENDING",
    )
    db.add(next_task)

    # DO NOT commit here – IDG finalize service commits once
    return task


def handle_poc_update_for_visit(db: Session, *, visit, user_id):
    """
    POC_UPDATE policy:

    ROUTINE:
      - Only RN supervisory visits trigger POC_UPDATE workflow.
      - Create next POC_UPDATE due +14 days (origin PERIODIC).
      - (Optionally) complete oldest pending POC_UPDATE if one exists.

    CRISIS:
      - Every finalized RN visit triggers a same-day POC_UPDATE and completes it immediately
        (origin MANUAL) with VISIT evidence.

    Evidence requirements when completed:
      - status = COMPLETED
      - completed_at set
      - completion_reference_type = VISIT
      - completion_reference_id = visit.id
    """
    logger.info(
        "POC_UPDATE handler entered: visit_id=%s visit_type=%s is_supervisory=%s patient_id=%s",
        str(getattr(visit, "id", None)),
        str(getattr(visit, "visit_type", None)),
        str(getattr(visit, "is_supervisory", None)),
        str(getattr(visit, "patient_id", None)),
    )

    discipline = (getattr(visit, "visit_type", "") or "").strip().upper()
    if discipline != "RN":
        logger.info("POC_UPDATE exit: non-RN visit")
        return None

    patient_id = visit.patient_id

    visit_date = (
        visit.visit_datetime.date()
        if getattr(visit, "visit_datetime", None)
        else datetime.utcnow().date()
    )

    # Load patient safely (avoid relying on relationship wiring)
    from app.models.patient import Patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        logger.warning("POC_UPDATE exit: patient not found for visit=%s", str(getattr(visit, "id", None)))
        return None

    acuity = (getattr(patient, "acuity_state", None) or "ROUTINE").upper()
    logger.info("POC_UPDATE acuity=%s", acuity)

    # --- CRISIS: create and complete same-day POC_UPDATE linked to this visit ---
    if acuity == "CRISIS":
        # Prevent duplicates for the same visit (keyed by evidence link)
        existing = (
            db.query(Task)
            .filter(
                Task.patient_id == patient_id,
                Task.task_type == "POC_UPDATE",
                Task.origin == "MANUAL",
                Task.completion_reference_type == "VISIT",
                Task.completion_reference_id == str(visit.id),
            )
            .first()
        )
        if existing:
            logger.info("POC_UPDATE CRISIS: already exists for this visit")
            return existing

        task = Task(
            patient_id=patient_id,
            benefit_period_id=getattr(visit, "benefit_period_id", None),
            task_type="POC_UPDATE",
            origin="MANUAL",
            discipline="RN",
            regulatory_basis="POC_UPDATE",
            due_date=visit_date,
            status="COMPLETED",
            completed_at=datetime.utcnow(),
            completion_reference_type="VISIT",
            completion_reference_id=str(visit.id),
            created_by=user_id,
        )
        db.add(task)
        logger.info("POC_UPDATE CRISIS created+completed for visit_id=%s", str(visit.id))
        return task

    # --- ROUTINE: only supervisory RN visits trigger ---
    if not getattr(visit, "is_supervisory", False):
        logger.info("POC_UPDATE ROUTINE exit: not supervisory")
        return None

    expected_next_due = visit_date + timedelta(days=14)

    # Duplicate safety: ensure only one PERIODIC task exists for patient+due_date
    already_created_next = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == "POC_UPDATE",
            Task.origin == "PERIODIC",
            Task.due_date == expected_next_due,
        )
        .first()
    )
    if already_created_next:
        logger.info("POC_UPDATE ROUTINE: next task already exists due=%s", str(expected_next_due))
        return already_created_next

    # Optionally complete the oldest pending POC_UPDATE (if any)
    existing_pending = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == "POC_UPDATE",
            Task.status == "PENDING",
        )
        .order_by(Task.due_date.asc())
        .first()
    )
    if existing_pending:
        existing_pending.status = "COMPLETED"
        existing_pending.completed_at = datetime.utcnow()
        existing_pending.completion_reference_type = "VISIT"
        existing_pending.completion_reference_id = str(visit.id)
        logger.info("POC_UPDATE ROUTINE: completed prior pending task_id=%s", str(existing_pending.id))

    # Create next POC_UPDATE due +14 days
    next_task = Task(
        patient_id=patient_id,
        benefit_period_id=getattr(visit, "benefit_period_id", None),
        task_type="POC_UPDATE",
        origin="PERIODIC",
        discipline="RN",
        regulatory_basis="POC_UPDATE",
        due_date=expected_next_due,
        status="PENDING",
        created_by=user_id,
    )
    db.add(next_task)

    logger.info("POC_UPDATE ROUTINE created next task due=%s", str(expected_next_due))
    return next_task