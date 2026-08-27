from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.visit import Visit
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus, TaskRegulatoryBasis
from app.models.chha_visit_outcome import CHHAVisitOutcome
from app.models.chha_visit_task_result import CHHAVisitTaskResult
from app.services.evidence.harvest_service import harvest_from_source

logger = logging.getLogger("sns_emr")


def upsert_chha_outcome(
    *,
    db: Session,
    visit: Visit,
    user_id: uuid.UUID,
    payload: Any,
) -> CHHAVisitOutcome:
    """
    Upserts structured CHHA outcome documentation for a single visit.

    Behavior:
    - Valid only for CHHA/AIDE visits
    - Stores one outcome row per visit
    - Replaces child task result rows atomically on update
    - Creates or updates one RN follow-up task per CHHA visit when:
        * pain/change observed
        * condition changed
        * redness / breakdown noted
        * RN notification required
    """

    visit_type = str(getattr(visit, "visit_type", "") or "").upper()
    visit_discipline = str(getattr(visit, "visit_discipline", "") or "").upper()

    if visit_type not in {"AIDE", "CHHA"} and visit_discipline not in {"AIDE", "CHHA"}:
        raise HTTPException(
            status_code=422,
            detail="CHHA outcome can only be recorded for AIDE/CHHA visits",
        )

    outcome = (
        db.query(CHHAVisitOutcome)
        .filter(CHHAVisitOutcome.visit_id == visit.id)
        .first()
    )

    now = datetime.now(timezone.utc)

    if not outcome:
        outcome = CHHAVisitOutcome(
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            visit_id=visit.id,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(outcome)
        db.flush()

    # -------------------------------------------------
    # Update visit-level CHHA outcome
    # -------------------------------------------------
    outcome.poc_reference_id = getattr(payload, "poc_reference_id", None)
    outcome.tolerance_to_care = payload.tolerance_to_care
    outcome.condition_during_visit = payload.condition_during_visit
    outcome.skin_outcome = payload.skin_outcome
    outcome.pain_or_change_observed = payload.pain_or_change_observed
    outcome.rn_notification_required = payload.rn_notification_required
    outcome.rn_notified = payload.rn_notified
    outcome.rn_notified_name = payload.rn_notified_name
    outcome.caregiver_instruction_provided = payload.caregiver_instruction_provided
    outcome.caregiver_understanding_confirmed = payload.caregiver_understanding_confirmed
    outcome.exception_narrative = payload.exception_narrative
    outcome.correction = payload.correction
    outcome.type_of_visit = payload.type_of_visit
    outcome.visit_kind = payload.visit_kind
    outcome.visit_kind_specify = payload.visit_kind_specify
    outcome.reason_for_visit = payload.reason_for_visit
    outcome.visit_date = payload.visit_date
    outcome.time_in = payload.time_in
    outcome.time_out = payload.time_out
    outcome.duration = payload.duration
    outcome.entered_by = payload.entered_by
    outcome.staff_assigned = payload.staff_assigned
    outcome.care_level = payload.care_level
    outcome.updated_at = now
    outcome.updated_by = user_id

    if payload.rn_notified:
        outcome.rn_notified_at = now

    # -------------------------------------------------
    # Replace child task result rows deterministically
    # -------------------------------------------------
    db.query(CHHAVisitTaskResult).filter(
        CHHAVisitTaskResult.outcome_id == outcome.id
    ).delete()

    for item in payload.task_results:
        db.add(
            CHHAVisitTaskResult(
                outcome_id=outcome.id,
                section_code=item.section_code,
                task_code=item.task_code,
                was_assigned=item.was_assigned,
                completed=item.completed,
                refused=item.refused,
                not_done=item.not_done,
                observation_code=item.observation_code,
                result_note=item.result_note,
                created_at=now,
                updated_at=now,
            )
        )

    # -------------------------------------------------
    # Determine whether RN follow-up is required
    # -------------------------------------------------
    needs_rn_followup = (
        payload.pain_or_change_observed
        or payload.condition_during_visit == "CHANGE_OBSERVED"
        or payload.skin_outcome in {"REDNESS", "BREAKDOWN"}
        or payload.rn_notification_required
    )

    if needs_rn_followup:
        # -------------------------------------------------
        # Derive urgency from CHHA findings
        # -------------------------------------------------
        if payload.skin_outcome == "BREAKDOWN":
            priority_value = "HIGH"
            severity_value = "HIGH"
        elif payload.skin_outcome == "REDNESS":
            priority_value = "HIGH"
            severity_value = "MODERATE"
        elif (
            payload.pain_or_change_observed
            or payload.condition_during_visit == "CHANGE_OBSERVED"
        ):
            priority_value = "MEDIUM"
            severity_value = "MODERATE"
        else:
            priority_value = "LOW"
            severity_value = "LOW"

        # -------------------------------------------------
        # ONE pending RN follow-up per VISIT (not per patient)
        # -------------------------------------------------
        query = (
            db.query(Task)
            .filter(
                Task.tenant_id == visit.tenant_id,
                Task.patient_id == visit.patient_id,
                Task.task_type == TaskType.CLINICAL_FOLLOWUP,
                Task.status == TaskStatus.PENDING,
            )
        )

        if hasattr(Task, "alert_reason"):
            query = query.filter(Task.alert_reason == "CHHA_OUTCOME_ALERT")

        if hasattr(Task, "reference_id"):
            query = query.filter(Task.reference_id == visit.id)

        existing = query.first()

        if existing:
            # -------------------------------------------------
            # Update existing RN alert for this visit
            # -------------------------------------------------
            if hasattr(existing, "discipline"):
                existing.discipline = "RN"

            if hasattr(existing, "origin"):
                existing.origin = "SYSTEM"

            if hasattr(existing, "regulatory_basis"):
                existing.regulatory_basis = TaskRegulatoryBasis.CONDITION_TRIGGER

            if hasattr(existing, "alert_reason"):
                existing.alert_reason = "CHHA_OUTCOME_ALERT"

            if hasattr(existing, "priority"):
                existing.priority = priority_value

            if hasattr(existing, "clinical_severity"):
                existing.clinical_severity = severity_value

            if hasattr(existing, "reference_type"):
                existing.reference_type = "VISIT"

            if hasattr(existing, "reference_id"):
                existing.reference_id = visit.id

            if hasattr(existing, "due_date"):
                existing.due_date = now.date()

            if hasattr(existing, "due_at"):
                existing.due_at = now

            if hasattr(existing, "sla_start_at") and not getattr(existing, "sla_start_at", None):
                existing.sla_start_at = now

            if hasattr(existing, "sla_due_at"):
                existing.sla_due_at = now + timedelta(hours=4)

            if hasattr(existing, "updated_at"):
                existing.updated_at = now

        else:
            # -------------------------------------------------
            # Create new RN alert for this visit
            # -------------------------------------------------
            task = Task(
                id=uuid.uuid4(),
                tenant_id=visit.tenant_id,
                patient_id=visit.patient_id,
                task_type=TaskType.CLINICAL_FOLLOWUP,
                status=TaskStatus.PENDING,
                regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
                due_date=now.date(),
                due_at=now,
                sla_start_at=now,
                sla_due_at=now + timedelta(hours=4),
                created_at=now,
                updated_at=now,
                created_by=user_id,
            )

            if hasattr(task, "discipline"):
                task.discipline = "RN"

            if hasattr(task, "origin"):
                task.origin = "SYSTEM"

            if hasattr(task, "alert_reason"):
                task.alert_reason = "CHHA_OUTCOME_ALERT"

            if hasattr(task, "priority"):
                task.priority = priority_value

            if hasattr(task, "clinical_severity"):
                task.clinical_severity = severity_value

            if hasattr(task, "reference_type"):
                task.reference_type = "VISIT"

            if hasattr(task, "reference_id"):
                task.reference_id = visit.id

            db.add(task)

    # ------------------------------
    # AI EVIDENCE HARVESTER (safe, isolated -- see harvest_service docstring)
    # ------------------------------
    try:
        harvest_from_source(
            db=db,
            tenant_id=outcome.tenant_id,
            patient_id=outcome.patient_id,
            source_type="CHHA_VISIT_OUTCOME",
            source_record_id=outcome.id,
            visit_id=outcome.visit_id,
            discipline="CHHA",
            recorded_at=now,
            text=outcome.exception_narrative or "",
            recorded_by_user_id=user_id,
            commit=False,
        )
    except Exception:
        logger.exception(
            "Failed to harvest CHHA visit outcome into AI evidence registry",
            extra={"chha_visit_outcome_id": str(outcome.id)},
        )

    return outcome