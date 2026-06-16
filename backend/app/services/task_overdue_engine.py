from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Dict
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus, TaskType


# =========================================================
# TENANT CONFIGURATION
# =========================================================

DEV_TENANT_REAL_ID = UUID("01271980-0000-0000-0000-000005101977")
DEV_TENANT_DUMMY_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
DEV_TENANT_DUMMY_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
DEV_TENANT_A_ID = UUID("5224ceb6-e29d-4841-858e-e77f1b67fe65")
DEV_TENANT_B_ID = UUID("85282f8b-fd5b-45e6-bb82-45394ef7a2f8")


# =========================================================
# CONFIGURATION
# =========================================================

OVERDUE_DAYS = 0
ESCALATION_LEVEL_1 = 2
ESCALATION_LEVEL_2 = 5
ESCALATION_LEVEL_3 = 10

NOTICE_3_DAY = 3
NOTICE_1_DAY = 1


# =========================================================
# SYSTEM ACTOR
# =========================================================

SYSTEM_ENGINE_USER_ID = UUID("a84628a1-0027-5d1e-81ca-c40d31c86c31")
SYSTEM_ENGINE_ROLE = "SYSTEM_ENGINE"


# =========================================================
# ENUM / STATUS HELPERS
# =========================================================

def _pending_status() -> str:
    if hasattr(TaskStatus, "PENDING"):
        return TaskStatus.PENDING.value if hasattr(TaskStatus.PENDING, "value") else "PENDING"
    return "PENDING"


def _overdue_status() -> str:
    if hasattr(TaskStatus, "OVERDUE"):
        return TaskStatus.OVERDUE.value if hasattr(TaskStatus.OVERDUE, "value") else "OVERDUE"
    return "OVERDUE"


def _completed_status() -> str:
    if hasattr(TaskStatus, "COMPLETED"):
        return TaskStatus.COMPLETED.value if hasattr(TaskStatus.COMPLETED, "value") else "COMPLETED"
    return "COMPLETED"


# =========================================================
# READ MODEL
# =========================================================

def evaluate_task_timeliness(
    *,
    db: Session,
    tenant_id: UUID,
    as_of: date | None = None,
) -> Dict[str, int]:
    """
    Enterprise read model for dashboard / reporting.

    Returns counts for:
    - PENDING
    - OVERDUE
    - COMPLETED
    - DUE_TODAY
    - DUE_IN_1_DAY
    - DUE_IN_3_DAYS
    """
    if as_of is None:
        as_of = datetime.now(timezone.utc).date()

    rows = (
        db.query(Task.status, func.count(Task.id))
        .filter(Task.tenant_id == tenant_id)
        .group_by(Task.status)
        .all()
    )

    counts: Dict[str, int] = {
        "PENDING": 0,
        "OVERDUE": 0,
        "COMPLETED": 0,
        "DUE_TODAY": 0,
        "DUE_IN_1_DAY": 0,
        "DUE_IN_3_DAYS": 0,
    }

    for status_value, count_value in rows:
        counts[str(status_value)] = int(count_value)

    counts["DUE_TODAY"] = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == _pending_status(),
            Task.due_date == as_of,
        )
        .scalar()
        or 0
    )

    counts["DUE_IN_1_DAY"] = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == _pending_status(),
            Task.due_date == (as_of.replace() if False else as_of),  # no-op to keep type clear
        )
        .scalar()
        or 0
    )
    # correct 1-day / 3-day counts below
    counts["DUE_IN_1_DAY"] = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == _pending_status(),
            Task.due_date == (as_of.fromordinal(as_of.toordinal() + 1)),
        )
        .scalar()
        or 0
    )

    counts["DUE_IN_3_DAYS"] = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == _pending_status(),
            Task.due_date == (as_of.fromordinal(as_of.toordinal() + 3)),
        )
        .scalar()
        or 0
    )

    return counts


# =========================================================
# MAIN ENGINE
# =========================================================

def run_overdue_engine(
    *,
    db: Session,
    tenant_id: UUID,
    actor_user_id: UUID | None = None,
    actor_role: str | None = None,
) -> None:
    """
    Overdue + notification engine.

    Handles:
    - PENDING -> OVERDUE transition when due_date <= today
    - best-effort escalation after overdue thresholds
    - pre-due notification logging at:
        * 3 days before
        * 1 day before
        * due today
    """
    today = date.today()

    actor_user_id = actor_user_id or SYSTEM_ENGINE_USER_ID
    actor_role = actor_role or SYSTEM_ENGINE_ROLE

    print(
        f"✅ [TASK_ENGINE] Running for {today} | "
        f"tenant={tenant_id} | actor={actor_user_id}"
    )

    # ---------------------------------------------------------
    # PRE-DUE NOTIFICATIONS
    # ---------------------------------------------------------
    notify_rows = db.execute(
        text(
            """
            SELECT id, due_date
            FROM tasks
            WHERE tenant_id = :tenant_id
              AND status = :pending_status
              AND due_date IS NOT NULL
              AND (
                    due_date = :today
                 OR due_date = (:today + 1)
                 OR due_date = (:today + 3)
              )
            ORDER BY due_date ASC, id ASC
            """
        ),
        {
            "tenant_id": tenant_id,
            "pending_status": _pending_status(),
            "today": today,
        },
    ).fetchall()

    for row in notify_rows:
        task_id, due_date = row
        days_until_due = (due_date - today).days

        try:
            if days_until_due == NOTICE_3_DAY:
                _notify_task(
                    db=db,
                    task_id=task_id,
                    actor_user_id=actor_user_id,
                    actor_role=actor_role,
                    message="TASK_DUE_IN_3_DAYS",
                )
            elif days_until_due == NOTICE_1_DAY:
                _notify_task(
                    db=db,
                    task_id=task_id,
                    actor_user_id=actor_user_id,
                    actor_role=actor_role,
                    message="TASK_DUE_TOMORROW",
                )
            elif days_until_due == 0:
                _notify_task(
                    db=db,
                    task_id=task_id,
                    actor_user_id=actor_user_id,
                    actor_role=actor_role,
                    message="TASK_DUE_TODAY",
                )
        except Exception as e:
            db.rollback()
            print(f"[WARN] Notification failed for task {task_id}: {str(e)}")

    # ---------------------------------------------------------
    # OVERDUE TRANSITIONS
    # ---------------------------------------------------------
    tasks = db.execute(
        text(
            """
            SELECT id, due_date
            FROM tasks
            WHERE tenant_id = :tenant_id
              AND status = :pending_status
              AND due_date IS NOT NULL
              AND due_date <= :today
            ORDER BY due_date ASC, id ASC
            """
        ),
        {
            "tenant_id": tenant_id,
            "pending_status": _pending_status(),
            "today": today,
        },
    ).fetchall()

    print(f"✅ [TASK_ENGINE] Potential overdue tasks: {len(tasks)}")

    processed = 0
    failed = 0

    for row in tasks:
        task_id, due_date = row

        try:
            _process_single_task(
                db=db,
                tenant_id=tenant_id,
                task_id=task_id,
                due_date=due_date,
                today=today,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
            )
            processed += 1
        except Exception as e:
            db.rollback()
            failed += 1
            print(f"[WARN] Failed to process task {task_id}: {str(e)}")

    print(f"✅ [TASK_ENGINE] Finished | processed={processed} | failed={failed}")


# =========================================================
# TASK PROCESSOR
# =========================================================

def _process_single_task(
    *,
    db: Session,
    tenant_id: UUID,
    task_id: UUID,
    due_date: date,
    today: date,
    actor_user_id: UUID,
    actor_role: str,
) -> None:
    days_overdue = (today - due_date).days

    # Persist business state first
    db.execute(
        text(
            """
            UPDATE tasks
            SET status = :overdue_status
            WHERE id = :task_id
              AND tenant_id = :tenant_id
              AND status = :pending_status
            """
        ),
        {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "pending_status": _pending_status(),
            "overdue_status": _overdue_status(),
        },
    )

    db.commit()

    print(f"✅ [OVERDUE] Task marked overdue: {task_id} ({days_overdue} days)")

    # Non-blocking escalation
    try:
        if days_overdue >= ESCALATION_LEVEL_3:
            _escalate_task(db, task_id, actor_user_id, actor_role, "LEVEL_3")
        elif days_overdue >= ESCALATION_LEVEL_2:
            _escalate_task(db, task_id, actor_user_id, actor_role, "LEVEL_2")
        elif days_overdue >= ESCALATION_LEVEL_1:
            _escalate_task(db, task_id, actor_user_id, actor_role, "LEVEL_1")
    except Exception as e:
        db.rollback()
        print(f"[WARN] Escalation failed: {str(e)}")


# =========================================================
# NOTIFICATION / AUDIT
# =========================================================

def _notify_task(
    *,
    db: Session,
    task_id: UUID,
    actor_user_id: UUID,
    actor_role: str,
    message: str,
) -> None:
    """
    Best-effort notification audit.
    Today this writes to audit_logs.
    Later this can feed UI inbox / dashboard / email / SMS.
    """
    print(f"🔔 [NOTIFY] Task {task_id} → {message}")

    try:
        db.execute(
            text(
                """
                INSERT INTO public.audit_logs (
                    id,
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    role,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :user_id,
                    :action,
                    'task',
                    :entity_id,
                    :role,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "user_id": actor_user_id,
                "action": message,
                "entity_id": task_id,
                "role": actor_role,
            },
        )

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[WARN] Notification audit failed: {str(e)}")


# =========================================================
# ESCALATION / AUDIT
# =========================================================

def _escalate_task(
    db: Session,
    task_id: UUID,
    actor_user_id: UUID,
    actor_role: str,
    level: str,
) -> None:
    print(f"🚨 [ESCALATION] Task {task_id} → {level}")

    try:
        db.execute(
            text(
                """
                INSERT INTO public.audit_logs (
                    id,
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    role,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :user_id,
                    :action,
                    'task',
                    :entity_id,
                    :role,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "user_id": actor_user_id,
                "action": f"TASK_ESCALATED_{level}",
                "entity_id": task_id,
                "role": actor_role,
            },
        )

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[WARN] Audit log failed: {str(e)}")