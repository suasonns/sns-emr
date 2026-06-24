from __future__ import annotations

import logging
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =========================================================
# Communications Log -> Task Bridge
# =========================================================
#
# Design goals:
# - Must NEVER block comm log creation
# - Must be best-effort and safe
# - Must only create tasks for clinically relevant recipients
# - Must avoid duplicate same-day follow-up tasks
# - Must remain tenant-safe
#
# Trigger behavior:
# - For CHANGE_OF_CONDITION reports, create CLINICAL_FOLLOWUP tasks
# - Assign only to patient-linked clinical staff already known in tasks
# - Do NOT create tasks for admin/DPCS here (they are notified, not task owners)
# =========================================================


CLINICAL_DISCIPLINES = {"RN", "LVN", "MSW", "BSW", "LCSW", "SC", "CHHA"}


def _extract_trigger_type(commlog) -> str | None:
    """
    Safely extract trigger_type from details payload.
    """
    details = getattr(commlog, "details", None)

    if isinstance(details, dict):
        return details.get("trigger_type")

    return None


def _resolve_patient_clinical_assignees(
    db: Session,
    *,
    patient_id,
    tenant_id,
) -> list[tuple]:
    """
    Return distinct (assigned_user_id, discipline) pairs from existing task assignments.

    This uses the current system reality:
    - patient assignments are currently inferred from tasks
    - only clinical disciplines should receive follow-up tasks
    """
    rows = db.execute(
        text(
            """
            SELECT DISTINCT assigned_user_id, discipline::text
            FROM tasks
            WHERE patient_id = :patient_id
              AND tenant_id = :tenant_id
              AND assigned_user_id IS NOT NULL
              AND discipline IN (
                  'RN'::tasks_discipline_enum,
                  'LVN'::tasks_discipline_enum,
                  'MSW'::tasks_discipline_enum,
                  'BSW'::tasks_discipline_enum,
                  'LCSW'::tasks_discipline_enum,
                  'SC'::tasks_discipline_enum,
                  'CHHA'::tasks_discipline_enum
              )
            """
        ),
        {
            "patient_id": patient_id,
            "tenant_id": tenant_id,
        },
    ).fetchall()

    return rows


def _followup_task_exists_for_today(
    db: Session,
    *,
    patient_id,
    tenant_id,
    assigned_user_id,
    discipline: str,
    commlog_id,
) -> bool:
    """
    Prevent duplicate same-day follow-up tasks for the same comm log + assignee.
    """
    existing = db.execute(
        text(
            """
            SELECT 1
            FROM tasks
            WHERE patient_id = :patient_id
              AND tenant_id = :tenant_id
              AND assigned_user_id = :assigned_user_id
              AND discipline = CAST(:discipline AS tasks_discipline_enum)
              AND task_type = 'CLINICAL_FOLLOWUP'::tasks_task_type_enum
              AND origin = 'SYSTEM'::tasks_origin_enum
              AND regulatory_basis = 'CONDITION_TRIGGER'::tasks_regulatory_basis_enum
              AND due_date = CURRENT_DATE
              AND alert_reason = :alert_reason
              AND status IN (
                    'PENDING'::tasks_status_enum,
                    'OVERDUE'::tasks_status_enum,
                    'ESCALATED'::tasks_status_enum
              )
            LIMIT 1
            """
        ),
        {
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "assigned_user_id": assigned_user_id,
            "discipline": discipline,
            "alert_reason": f"COMM_LOG:{commlog_id}",
        },
    ).fetchone()

    return existing is not None


def _create_followup_task(
    db: Session,
    *,
    patient_id,
    tenant_id,
    assigned_user_id,
    discipline: str,
    commlog,
) -> None:
    """
    Insert one follow-up task row.
    """
    db.execute(
        text(
            """
            INSERT INTO tasks (
                id,
                patient_id,
                assigned_user_id,
                task_type,
                origin,
                discipline,
                regulatory_basis,
                due_date,
                status,
                created_at,
                updated_at,
                tenant_id,
                created_by,
                alert_reason
            )
            VALUES (
                :id,
                :patient_id,
                :assigned_user_id,
                'CLINICAL_FOLLOWUP'::tasks_task_type_enum,
                'SYSTEM'::tasks_origin_enum,
                CAST(:discipline AS tasks_discipline_enum),
                'CONDITION_TRIGGER'::tasks_regulatory_basis_enum,
                CURRENT_DATE,
                'PENDING'::tasks_status_enum,
                NOW(),
                NOW(),
                :tenant_id,
                :created_by,
                :alert_reason
            )
            """
        ),
        {
            "id": uuid.uuid4(),
            "patient_id": patient_id,
            "assigned_user_id": assigned_user_id,
            "discipline": discipline,
            "tenant_id": tenant_id,
            "created_by": getattr(commlog, "created_by", None),
            "alert_reason": f"COMM_LOG:{commlog.id}",
        },
    )


def handle_commlog_for_tasks(db: Session, commlog) -> None:
    """
    Best-effort task automation triggered by Communications Log events.

    Current logic:
    - If trigger_type == CHANGE_OF_CONDITION:
        create CLINICAL_FOLLOWUP tasks for assigned clinical users
    - If no patient clinical assignees are found:
        log and exit safely
    - Never commit here (router owns transaction)
    """

    patient_id = getattr(commlog, "patient_id", None)
    tenant_id = getattr(commlog, "tenant_id", None)

    if not patient_id or not tenant_id:
        logger.warning(
            "COMMLOG TASK BRIDGE SKIPPED: missing patient_id or tenant_id commlog_id=%s",
            getattr(commlog, "id", None),
        )
        return

    trigger_type = _extract_trigger_type(commlog)

    if trigger_type != "CHANGE_OF_CONDITION":
        logger.info(
            "COMMLOG TASK BRIDGE SKIPPED: trigger_type=%s commlog_id=%s",
            trigger_type,
            getattr(commlog, "id", None),
        )
        return

    assignees = _resolve_patient_clinical_assignees(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
    )

    if not assignees:
        logger.warning(
            "COMMLOG TASK BRIDGE: no patient clinical assignees found patient_id=%s tenant_id=%s commlog_id=%s",
            str(patient_id),
            str(tenant_id),
            str(getattr(commlog, "id", None)),
        )
        return

    created_count = 0

    for assigned_user_id, discipline in assignees:
        if discipline not in CLINICAL_DISCIPLINES:
            continue

        if _followup_task_exists_for_today(
            db,
            patient_id=patient_id,
            tenant_id=tenant_id,
            assigned_user_id=assigned_user_id,
            discipline=discipline,
            commlog_id=commlog.id,
        ):
            continue

        _create_followup_task(
            db,
            patient_id=patient_id,
            tenant_id=tenant_id,
            assigned_user_id=assigned_user_id,
            discipline=discipline,
            commlog=commlog,
        )
        created_count += 1

    logger.info(
        "COMMLOG TASK BRIDGE COMPLETE: patient_id=%s tenant_id=%s commlog_id=%s tasks_created=%s",
        str(patient_id),
        str(tenant_id),
        str(commlog.id),
        created_count,
    )
