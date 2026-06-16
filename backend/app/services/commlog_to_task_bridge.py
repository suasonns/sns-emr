"""
Communications Log → Task Bridge (Phase 2.2)

Enterprise safety rules:
- This module MUST NOT prevent app startup.
- Communications Log creation must never fail due to task automation.
- Task creation is best-effort and upgradeable.
"""

from __future__ import annotations


def handle_commlog_for_tasks(db, commlog) -> None:
    """
    Best-effort task automation triggered by Communications Log events.

    This function:
    - Never raises import errors
    - Never blocks Communications Log creation
    - Attempts to call the task engine only if a compatible API exists
    """

    # Only trigger for approved event types
    if commlog.event_type not in {
        "Progress Note",
        "Phone Call",
        "On-Call Note",
        "Reminder",
    }:
        return

    try:
        # Lazy import to avoid startup failure
        from app.services import task_engine  # type: ignore

        # Try common task engine function names safely
        for fn_name in (
            "create_task",
            "create_task_item",
            "enqueue_task",
            "add_task",
        ):
            fn = getattr(task_engine, fn_name, None)
            if not callable(fn):
                continue

            # POC review tasks
            if commlog.event_type in {
                "Progress Note",
                "Phone Call",
                "On-Call Note",
            }:
                fn(
                    db=db,
                    task_type="POC_REVIEW",
                    patient_id=commlog.patient_id,
                    origin="COMMUNICATIONS_LOG",
                    origin_id=commlog.id,
                )
                return

            # Reminder tasks
            if commlog.event_type == "Reminder":
                fn(
                    db=db,
                    task_type="REMINDER",
                    patient_id=commlog.patient_id,
                    origin="COMMUNICATIONS_LOG",
                    origin_id=commlog.id,
                )
                return

    except Exception:
        # Compliance rule: automation must never block documentation
        return