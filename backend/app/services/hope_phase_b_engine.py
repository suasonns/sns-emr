from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.enums import (
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.sfv_requirement import SFVRequirement
from app.models.task import Task

logger = logging.getLogger(__name__)


SOURCE_INITIAL_RN_ICA = "INITIAL_RN_ICA"
SOURCE_HUV1 = "HUV1"
SOURCE_HUV2 = "HUV2"

TASK_TYPE_SFV = "SFV"
TASK_TYPE_HUV1 = "HUV1"
TASK_TYPE_HUV2 = "HUV2"

SFV_ALERT_PREFIX = "SFV"
HUV_ALERT_PREFIX = "HUV"

DISCIPLINE_RN = "RN"
DISCIPLINE_LVN = "LVN"
DISCIPLINE_LPN = "LPN"

VISIT_MODE_IN_PERSON = "IN_PERSON"

MODERATE_OR_SEVERE = {"MODERATE", "SEVERE"}


@dataclass
class TriggerOutcome:
    requirement_id: Optional[str]
    task_id: Optional[str]
    created: bool
    reason: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pick_enum_member(enum_cls, *candidate_names: str):
    for name in candidate_names:
        if hasattr(enum_cls, name):
            return getattr(enum_cls, name)
    raise ValueError(f"{enum_cls.__name__} does not contain any of: {candidate_names}")


def _set_if_present(obj, **values) -> None:
    for key, value in values.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def _normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    return text or None


def _normalize_visit_mode(value: Any) -> str | None:
    code = _normalize_code(value)
    if code in {"IN_PERSON", "INPERSON", "FACE_TO_FACE"}:
        return VISIT_MODE_IN_PERSON
    return code


def _normalize_discipline(value: Any) -> str | None:
    code = _normalize_code(value)
    if code == "LPN/LVN":
        return DISCIPLINE_LVN
    return code


def _day_number_from_election(election_datetime: datetime, visit_datetime: datetime) -> int:
    election_date = election_datetime.date()
    visit_date = visit_datetime.date()
    return (visit_date - election_date).days


def _task_due_date(window_end_datetime: datetime):
    return window_end_datetime.date()


def _task_status_pending():
    return _pick_enum_member(TaskStatus, "PENDING")


def _task_status_completed():
    return _pick_enum_member(TaskStatus, "COMPLETED")


def _task_origin_system():
    return _pick_enum_member(TaskOrigin, "SYSTEM")


def _task_regulatory_basis():
    return _pick_enum_member(
        TaskRegulatoryBasis,
        "CLINICAL_REVIEW",
        "MEDICATION_RECONCILIATION",
        "CONDITION_TRIGGER",
    )


def _task_type_member(task_type_name: str):
    return _pick_enum_member(TaskType, task_type_name)


def _open_status_members():
    members = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            members.append(getattr(TaskStatus, candidate))
    return members


def _huv_alert_reason(task_type_name: str, trigger_reference_id) -> str:
    return f"{HUV_ALERT_PREFIX}:{task_type_name}:{trigger_reference_id}"


def _sfv_alert_reason(trigger_source_type: str, trigger_reference_id) -> str:
    return f"{SFV_ALERT_PREFIX}:{trigger_source_type}:{trigger_reference_id}"


def _is_moderate_or_severe(value: Any) -> bool:
    code = _normalize_code(value)
    return code in MODERATE_OR_SEVERE


def _symptom_group_from_inputs(pain_impact: Any, non_pain_impact: Any) -> str | None:
    pain_flag = _is_moderate_or_severe(pain_impact)
    non_pain_flag = _is_moderate_or_severe(non_pain_impact)

    if pain_flag and non_pain_flag:
        return "BOTH"
    if pain_flag:
        return "PAIN"
    if non_pain_flag:
        return "NON_PAIN"
    return None


def validate_huv_visit_completion(
    *,
    election_datetime: datetime,
    completed_visit_datetime: datetime,
    discipline: str,
    task_type_name: str,
) -> None:
    normalized_discipline = _normalize_discipline(discipline)
    if normalized_discipline != DISCIPLINE_RN:
        raise ValueError("HUV must be completed by RN")

    day_number = _day_number_from_election(election_datetime, completed_visit_datetime)

    if task_type_name == TASK_TYPE_HUV1:
        if day_number < 6 or day_number > 15:
            raise ValueError("HUV1 must be completed on or between days 6 and 15")
        return

    if task_type_name == TASK_TYPE_HUV2:
        if day_number < 16 or day_number > 30:
            raise ValueError("HUV2 must be completed on or between days 16 and 30")
        return

    raise ValueError("Invalid HUV task type")


def _get_existing_open_task(
    *,
    db: Session,
    tenant_id,
    patient_id,
    alert_reason: str,
    task_type_name: str,
):
    open_statuses = _open_status_members()
    task_type = _task_type_member(task_type_name)

    return (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.patient_id == patient_id)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.task_type == task_type)
        .filter(Task.status.in_(open_statuses))
        .first()
    )


def _create_task_if_missing(
    *,
    db: Session,
    tenant_id,
    patient_id,
    task_type_name: str,
    alert_reason: str,
    reference_id,
    due_at: datetime,
    escalation_reason: str,
    discipline: str = DISCIPLINE_RN,
):
    existing = _get_existing_open_task(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        alert_reason=alert_reason,
        task_type_name=task_type_name,
    )
    if existing:
        return existing

    now = _utcnow()
    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=_task_type_member(task_type_name),
        origin=_task_origin_system(),
        discipline=discipline,
        regulatory_basis=_task_regulatory_basis(),
        due_date=_task_due_date(due_at),
        status=_task_status_pending(),
        created_at=now,
        updated_at=now,
        created_by=None,
    )

    _set_if_present(
        task,
        due_at=due_at,
        sla_start_at=now,
        sla_due_at=due_at,
        alert_reason=alert_reason,
        reference_type="VISIT",
        reference_id=reference_id,
        assigned_role=discipline,
        escalation_reason=escalation_reason,
        is_overdue=False,
    )

    db.add(task)
    db.flush()
    return task


def create_huv_tasks_from_initial_rn_ica(
    *,
    db: Session,
    tenant_id,
    patient_id,
    initial_rn_ica_visit_id,
    election_datetime: datetime,
):
    huv1_window_end = election_datetime + timedelta(days=15)
    huv2_window_end = election_datetime + timedelta(days=30)

    huv1_task = _create_task_if_missing(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type_name=TASK_TYPE_HUV1,
        alert_reason=_huv_alert_reason(TASK_TYPE_HUV1, initial_rn_ica_visit_id),
        reference_id=initial_rn_ica_visit_id,
        due_at=huv1_window_end,
        escalation_reason="HUV1 required on or between days 6 and 15 after INITIAL_RN_ICA",
        discipline=DISCIPLINE_RN,
    )

    huv2_task = _create_task_if_missing(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type_name=TASK_TYPE_HUV2,
        alert_reason=_huv_alert_reason(TASK_TYPE_HUV2, initial_rn_ica_visit_id),
        reference_id=initial_rn_ica_visit_id,
        due_at=huv2_window_end,
        escalation_reason="HUV2 required on or between days 16 and 30 after INITIAL_RN_ICA",
        discipline=DISCIPLINE_RN,
    )

    return {
        "huv1_task_id": str(huv1_task.id),
        "huv2_task_id": str(huv2_task.id),
    }


def _find_existing_sfv_requirement(
    *,
    db: Session,
    patient_id,
    trigger_source_type: str,
    trigger_reference_id,
):
    return (
        db.query(SFVRequirement)
        .filter(SFVRequirement.patient_id == patient_id)
        .filter(SFVRequirement.trigger_source_type == trigger_source_type)
        .filter(SFVRequirement.trigger_reference_id == trigger_reference_id)
        .first()
    )


def maybe_trigger_sfv_from_hope_timepoint(
    *,
    db: Session,
    tenant_id,
    patient_id,
    trigger_source_type: str,
    trigger_reference_id,
    trigger_datetime: datetime,
    pain_impact: Any,
    non_pain_impact: Any,
) -> TriggerOutcome:
    if trigger_source_type not in {SOURCE_INITIAL_RN_ICA, SOURCE_HUV1, SOURCE_HUV2}:
        raise ValueError("SFV trigger source must be INITIAL_RN_ICA, HUV1, or HUV2")

    symptom_group = _symptom_group_from_inputs(pain_impact, non_pain_impact)
    if symptom_group is None:
        return TriggerOutcome(
            requirement_id=None,
            task_id=None,
            created=False,
            reason="No moderate or severe symptom impact; SFV not required",
        )

    existing_requirement = _find_existing_sfv_requirement(
        db=db,
        patient_id=patient_id,
        trigger_source_type=trigger_source_type,
        trigger_reference_id=trigger_reference_id,
    )
    if existing_requirement:
        return TriggerOutcome(
            requirement_id=str(existing_requirement.id),
            task_id=str(existing_requirement.task_id) if existing_requirement.task_id else None,
            created=False,
            reason="SFV requirement already exists for this trigger",
        )

    due_at = trigger_datetime + timedelta(days=2)

    sfv_task = _create_task_if_missing(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type_name=TASK_TYPE_SFV,
        alert_reason=_sfv_alert_reason(trigger_source_type, trigger_reference_id),
        reference_id=trigger_reference_id,
        due_at=due_at,
        escalation_reason=f"SFV required within 2 calendar days after {trigger_source_type} due to moderate/severe symptom impact",
        discipline=DISCIPLINE_RN,
    )

    requirement = SFVRequirement(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        trigger_source_type=trigger_source_type,
        trigger_reference_id=trigger_reference_id,
        trigger_symptom_group=symptom_group,
        trigger_datetime=trigger_datetime,
        due_at=due_at,
        task_id=sfv_task.id,
        status="OPEN",
        created_at=_utcnow(),
        updated_at=_utcnow(),
        created_by=None,
    )

    db.add(requirement)
    db.flush()

    return TriggerOutcome(
        requirement_id=str(requirement.id),
        task_id=str(sfv_task.id),
        created=True,
        reason="SFV requirement and task created",
    )


def complete_sfv_requirement_from_visit(
    *,
    db: Session,
    sfv_requirement_id,
    completing_visit_id,
    completing_visit_datetime: datetime,
    discipline: str,
    visit_mode: str,
):
    requirement = (
        db.query(SFVRequirement)
        .filter(SFVRequirement.id == sfv_requirement_id)
        .first()
    )
    if not requirement:
        raise ValueError("SFV requirement not found")

    if requirement.status == "COMPLETED":
        return requirement

    normalized_mode = _normalize_visit_mode(visit_mode)
    if normalized_mode != VISIT_MODE_IN_PERSON:
        raise ValueError("SFV must be completed by an in-person visit")

    normalized_discipline = _normalize_discipline(discipline)
    if normalized_discipline not in {DISCIPLINE_RN, DISCIPLINE_LVN, DISCIPLINE_LPN}:
        raise ValueError("SFV must be completed by RN or LPN/LVN")

    if str(completing_visit_id) == str(requirement.trigger_reference_id):
        raise ValueError("SFV must be a separate visit from the triggering INITIAL_RN_ICA/HUV")

    requirement.completed_visit_id = completing_visit_id
    requirement.completed_at = completing_visit_datetime
    requirement.status = "COMPLETED"
    requirement.updated_at = _utcnow()

    if requirement.task_id:
        task = db.query(Task).filter(Task.id == requirement.task_id).first()
        if task:
            task.status = _task_status_completed()
            _set_if_present(
                task,
                completed_at=completing_visit_datetime,
                completion_reference_type="VISIT",
                completion_reference_id=completing_visit_id,
                is_overdue=False,
            )
            task.updated_at = _utcnow()

    return requirement


def process_initial_rn_ica_finalize(
    *,
    db: Session,
    tenant_id,
    patient_id,
    initial_rn_ica_visit_id,
    election_datetime: datetime,
    j2051_pain_impact: Any,
    j2051_non_pain_impact: Any,
):
    huv_result = create_huv_tasks_from_initial_rn_ica(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        initial_rn_ica_visit_id=initial_rn_ica_visit_id,
        election_datetime=election_datetime,
    )

    sfv_result = maybe_trigger_sfv_from_hope_timepoint(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=initial_rn_ica_visit_id,
        trigger_datetime=election_datetime,
        pain_impact=j2051_pain_impact,
        non_pain_impact=j2051_non_pain_impact,
    )

    return {
        **huv_result,
        "sfv_requirement_id": sfv_result.requirement_id,
        "sfv_task_id": sfv_result.task_id,
        "sfv_created": sfv_result.created,
        "sfv_reason": sfv_result.reason,
    }


def process_huv_finalize(
    *,
    db: Session,
    tenant_id,
    patient_id,
    huv_task_type: str,
    huv_visit_id,
    election_datetime: datetime,
    completed_visit_datetime: datetime,
    discipline: str,
    j2051_pain_impact: Any,
    j2051_non_pain_impact: Any,
):
    if huv_task_type not in {TASK_TYPE_HUV1, TASK_TYPE_HUV2}:
        raise ValueError("HUV task type must be HUV1 or HUV2")

    validate_huv_visit_completion(
        election_datetime=election_datetime,
        completed_visit_datetime=completed_visit_datetime,
        discipline=discipline,
        task_type_name=huv_task_type,
    )

    return maybe_trigger_sfv_from_hope_timepoint(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        trigger_source_type=huv_task_type,
        trigger_reference_id=huv_visit_id,
        trigger_datetime=completed_visit_datetime,
        pain_impact=j2051_pain_impact,
        non_pain_impact=j2051_non_pain_impact,
    )