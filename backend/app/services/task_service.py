from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.med_reconciliation import MedReconciliationItem
from app.models.enums import (
    CompletionReferenceType,
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)


# =========================================================
# TASK COMPLETION
# =========================================================

def complete_task(
    *,
    db: Session,
    task_id: UUID,
    completion_reference_type: CompletionReferenceType,
    completion_reference_id: UUID,
    completed_by: UUID | None = None,
) -> Task:
    """
    Compliance-safe task completion.

    REQUIRED:
    - status = COMPLETED
    - completed_at set
    - updated_at set
    - reference stored (audit)
    """

    task = db.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        raise ValueError("Task not found")

    if task.status == "COMPLETED":
        raise ValueError("Task already completed")

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)

    task.completion_reference_type = completion_reference_type
    task.completion_reference_id = completion_reference_id

    if completed_by:
        task.completed_by = completed_by

    db.commit()
    db.refresh(task)

    return task


# =========================================================
# MED SAFETY TASK CREATION
# =========================================================

def create_med_safety_task(
    db: Session,
    item: MedReconciliationItem,
) -> Task:

    task = Task(
        id=uuid.uuid4(),
        tenant_id=item.tenant_id,
        patient_id=item.patient_id,
        title="Medication Safety Review Required",
        description=f"High-risk med or reaction: {item.med_name_raw}",
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(task)

    return task


# =========================================================
# MSW ICA ESCALATION TASKS
# =========================================================

_ACTIVE_TASK_STATUSES = [
    TaskStatus.PENDING,
    TaskStatus.IN_PROGRESS,
    TaskStatus.OVERDUE,
    TaskStatus.ESCALATED,
]



def _upsert_clinical_escalation_task(
    *,
    db: Session,
    tenant_id,
    patient_id,
    reference_type: str,
    discipline: TaskDiscipline,
    assessment_id,
    created_by,
    title: str,
    description: str,
    alert_reason: str,
    clinical_severity: str,
    escalation_reason: str,
) -> Task:
    now = datetime.now(timezone.utc)
    existing = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.patient_id == patient_id)
        .filter(Task.reference_type == reference_type)
        .filter(Task.reference_id == assessment_id)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.status.in_(_ACTIVE_TASK_STATUSES))
        .first()
    )

    if existing:
        existing.title = title
        existing.description = description
        existing.task_type = TaskType.CLINICAL_FOLLOWUP
        existing.origin = TaskOrigin.SYSTEM
        existing.discipline = discipline
        existing.regulatory_basis = TaskRegulatoryBasis.CONDITION_TRIGGER
        existing.status = TaskStatus.PENDING
        existing.priority = "URGENT"
        existing.clinical_severity = clinical_severity
        existing.assigned_role = "CLINICAL_SUPERVISOR_CASE_MANAGER"
        existing.notification_required = True
        existing.reference_type = reference_type
        existing.reference_id = assessment_id
        existing.due_at = now
        existing.escalation_level = 1
        existing.escalated_at = now
        existing.escalation_reason = escalation_reason
        existing.updated_at = now
        return existing

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        created_by=created_by,
        title=title,
        description=description,
        task_type=TaskType.CLINICAL_FOLLOWUP,
        origin=TaskOrigin.SYSTEM,
        discipline=discipline,
        regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
        alert_reason=alert_reason,
        status=TaskStatus.PENDING,
        priority="URGENT",
        clinical_severity=clinical_severity,
        assigned_role="CLINICAL_SUPERVISOR_CASE_MANAGER",
        notification_required=True,
        reference_type=reference_type,
        reference_id=assessment_id,
        due_at=now,
        escalation_level=1,
        escalated_at=now,
        escalation_reason=escalation_reason,
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    return task



def create_suicide_risk_escalation_task(
    *,
    db: Session,
    tenant_id,
    patient_id,
    assessment_id,
    created_by,
    risk_summary: str,
) -> Task:
    return _upsert_clinical_escalation_task(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        reference_type="msw_ica_assessment",
        discipline=TaskDiscipline.MSW,
        assessment_id=assessment_id,
        created_by=created_by,
        title="URGENT: MSW ICA suicide risk escalation",
        description=(
            "Immediate MSW ICA suicide-risk follow-up required. "
            f"Documented concern: {risk_summary}. Notify the Clinical Supervisor/Case Manager and attending physician now."
        ),
        alert_reason="TJC Policy 2-067 / CHAP 1-019 / ACHC 4-047 - Suicide Risk",
        clinical_severity="CRITICAL",
        escalation_reason="TJC Policy 2-067 / CHAP 1-019 / ACHC 4-047 - Suicide Risk",
    )



def create_abuse_neglect_exploitation_task(
    *,
    db: Session,
    tenant_id,
    patient_id,
    assessment_id,
    created_by,
    categories: list[str],
) -> Task:
    category_text = ", ".join(categories) if categories else "Abuse/Neglect/Exploitation"
    return _upsert_clinical_escalation_task(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        reference_type="msw_ica_assessment",
        discipline=TaskDiscipline.MSW,
        assessment_id=assessment_id,
        created_by=created_by,
        title="URGENT: MSW ICA abuse/neglect/exploitation escalation",
        description=(
            "Immediate mandated-reporter follow-up required for suspected abuse/neglect/exploitation. "
            f"Selected categories: {category_text}. Document external reporting actions to APS, law enforcement, or the applicable agency."
        ),
        alert_reason="TJC Policy 2-038 - Abuse/Neglect/Exploitation",
        clinical_severity="HIGH",
        escalation_reason="TJC Policy 2-038 - Abuse/Neglect/Exploitation",
    )



def create_spiritual_care_suicide_risk_escalation_task(
    *,
    db: Session,
    tenant_id,
    patient_id,
    assessment_id,
    created_by,
    risk_summary: str,
) -> Task:
    return _upsert_clinical_escalation_task(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        reference_type="scica_assessment",
        discipline=TaskDiscipline.SC,
        assessment_id=assessment_id,
        created_by=created_by,
        title="URGENT: SCICA suicide risk escalation",
        description=(
            "Immediate spiritual-care suicide-risk follow-up required. "
            f"Documented concern: {risk_summary}. Notify the Clinical Supervisor/Case Manager and attending physician now."
        ),
        alert_reason="TJC Policy 2-067 - Suicide Risk (Spiritual Care)",
        clinical_severity="CRITICAL",
        escalation_reason="TJC Policy 2-067 - Suicide Risk (Spiritual Care)",
    )
