from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.domain.care_model_engine import (
    determine_care_model,
    should_anchor_poc_from_rn_visit,
)
from app.domain.visits import normalize_visit_type as normalize_domain_visit_type
from app.models.enums import (
    CompletionReferenceType,
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit
from app.models.clinical_note import ClinicalNote  # ✅ FIXED

from app.services.benefit_period_resolver import get_active_benefit_period
from app.services.task_completion_evidence import complete_task_with_evidence

logger = logging.getLogger("sns_emr")


# ================== CONSTANTS ==================

SEVERITY_RANK = {
    "None": 0,
    "Mild": 1,
    "Moderate": 2,
    "Severe": 3,
}


def severity(value: str) -> int:
    return SEVERITY_RANK.get(value, 0)


# ================== HELPERS ==================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _date_to_utc_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _task_type_poc_update() -> TaskType | str:
    return getattr(TaskType, "POC_UPDATE", "POC_UPDATE")


def _open_status() -> TaskStatus | str:
    return getattr(TaskStatus, "PENDING", "PENDING")


def _completed_status() -> TaskStatus | str:
    return getattr(TaskStatus, "COMPLETED", "COMPLETED")


def _origin_manual() -> TaskOrigin | str:
    return getattr(TaskOrigin, "MANUAL", "MANUAL")


def _origin_periodic() -> TaskOrigin | str:
    return getattr(TaskOrigin, "PERIODIC", "PERIODIC")


def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:
    return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")


def _reference_type_visit() -> CompletionReferenceType | str:
    return getattr(CompletionReferenceType, "VISIT", "VISIT")


def _discipline_rn() -> TaskDiscipline | str:
    return getattr(TaskDiscipline, "RN", "RN")

def _task_already_completed_for_visit(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    visit_id: UUID,
) -> bool:
    """
    Determine whether this visit has already satisfied a POC_UPDATE task.

    This prevents repeat visit-finalization calls from creating duplicate
    POC_UPDATE tasks after the first one is completed.
    """

    existing = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == _task_type_poc_update())
        .filter(Task.completion_reference_type == _reference_type_visit())
        .filter(Task.completion_reference_id == visit_id)
        .first()
    )

    return existing is not None
    
# ================== MAIN ENTRY ==================

def on_visit_finalized_apply_poc_policy(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:

    if patient is None or visit is None:
        return

    if not getattr(patient, "id", None):
        return

    if not getattr(visit, "id", None):
        return

    tenant_id = (
        getattr(patient, "tenant_id", None)
        or getattr(visit, "tenant_id", None)
    )

    if tenant_id is None:
        logger.warning(
            "POC update automation skipped because tenant_id is missing "
            "for patient_id=%s visit_id=%s",
            getattr(patient, "id", None),
            getattr(visit, "id", None),
        )
        return

    # ✅ RN FILTER
    visit_type = (
        getattr(visit, "visit_discipline", None)
        or getattr(visit, "visit_type", None)
    )

    if not visit_type:
        return

    try:
        if normalize_domain_visit_type(str(visit_type)) != "RN":
            return
    except Exception:
        return

    visit_time = getattr(visit, "visit_datetime", _utcnow())
    visit_time = (
        visit_time.astimezone(timezone.utc)
        if getattr(visit_time, "tzinfo", None)
        else visit_time.replace(tzinfo=timezone.utc)
    )
    visit_day = visit_time.date()

    acuity = (
        getattr(visit, "acuity_state_at_visit", None)
        or getattr(patient, "acuity_state", None)
        or "ROUTINE"
    )
    acuity = str(acuity).upper()

    # ================== LOAD NOTES ==================

    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.visit_id == visit.id)
        .all()
    )

    # ================== ROS DETECTION ==================

    symptoms = []

    for note in notes:
        content = note.content or {}
        ros = content.get("ros", {})

        for _name, values in ros.items():
            symptoms.append(
                {
                    "current": values.get("current"),
                    "previous": values.get("previous"),
                }
            )

    has_new_issue = False
    has_update = False

    for symptom in symptoms:
        current = SEVERITY_RANK.get(
            symptom["current"] or "None",
            0,
        )
        previous = SEVERITY_RANK.get(
            symptom["previous"] or "None",
            0,
        )

        if previous == 0 and current >= 2:
            has_new_issue = True
        elif current != previous:
            has_update = True

    visit.has_new_issue = has_new_issue
    visit.has_existing_issue_update = has_update
    visit.acuity = acuity

    # ================== DECISION ==================

    decision = determine_care_model(
        has_chha=getattr(patient, "has_chha", False),
        has_lvn=getattr(patient, "has_lvn", False),
        has_wounds=getattr(patient, "has_wounds", False),
        acuity_state=acuity,
    )

    should_anchor = should_anchor_poc_from_rn_visit(
        visit=visit,
        decision=decision,
    )

    benefit_period = get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        as_of_date=visit_day,
    )

    benefit_period_id = (
        benefit_period.id
        if benefit_period
        else None
    )

    # ================== CRISIS ==================

    if acuity == "CRISIS":

        if _task_already_completed_for_visit(
            db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            visit_id=visit.id,
        ):
            return

        existing = (
            db.query(Task)
            .filter(Task.tenant_id == tenant_id)
            .filter(Task.patient_id == patient.id)
            .filter(Task.task_type == _task_type_poc_update())
            .filter(Task.status == _open_status())
            .first()
        )

        if existing:
            complete_task_with_evidence(
                db,
                task_id=existing.id,
                completion_reference_type=_reference_type_visit(),
                completion_reference_id=visit.id,
                completed_by=finalized_by_user_id,
                completed_at=visit_time,
            )
            return

        task = Task(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            benefit_period_id=benefit_period_id,
            created_by=finalized_by_user_id,
            task_type=_task_type_poc_update(),
            status=_open_status(),
            origin=_origin_manual(),
            discipline=_discipline_rn(),
            regulatory_basis=_regulatory_basis_poc_update(),
            alert_reason="POC update required due to crisis RN visit",
            due_date=visit_day,
            due_at=visit_time,
            created_at=_utcnow(),
        )

        db.add(task)
        db.flush()

        complete_task_with_evidence(
            db,
            task_id=task.id,
            completion_reference_type=_reference_type_visit(),
            completion_reference_id=visit.id,
            completed_by=finalized_by_user_id,
            completed_at=visit_time,
        )

        return

    # ================== ROUTINE ==================

    if acuity != "ROUTINE":
        return

    if not should_anchor:
        return

    existing = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.patient_id == patient.id)
        .filter(Task.task_type == _task_type_poc_update())
        .filter(Task.status == _open_status())
        .first()
    )

    if existing:
        return

    due_at = visit_time + timedelta(days=14)
    due_date = due_at.date()

    task = Task(
        id=uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        benefit_period_id=benefit_period_id,
        created_by=finalized_by_user_id,
        task_type=_task_type_poc_update(),
        status=_open_status(),
        origin=_origin_periodic(),
        discipline=_discipline_rn(),
        regulatory_basis=_regulatory_basis_poc_update(),
        alert_reason="POC update required after routine supervisory RN visit",
        due_date=due_date,
        due_at=due_at,
        created_at=_utcnow(),
    )

    db.add(task)
    db.flush()