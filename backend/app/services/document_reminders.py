# app/services/document_reminders.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.document_notification import DocumentNotification
from app.services.audit_events import audit_event


FIRST_REMINDER_DELAY_HOURS = 8
REPEAT_REMINDER_DELAY_HOURS = 24


def get_due_notifications(db: Session) -> List[DocumentNotification]:
    """
    Returns document_notifications that are due for a reminder.
    """
    now = datetime.now(timezone.utc)

    candidates = (
        db.query(DocumentNotification)
        .filter(DocumentNotification.acknowledged_at.is_(None))
        .all()
    )

    due: List[DocumentNotification] = []

    for n in candidates:
        if n.reminder_count == 0:
            due_at = n.notified_at + timedelta(hours=FIRST_REMINDER_DELAY_HOURS)
        else:
            last = n.last_reminder_at or n.notified_at
            due_at = last + timedelta(hours=REPEAT_REMINDER_DELAY_HOURS)

        if now >= due_at:
            due.append(n)

    return due


def run_document_reminders(db: Session, *, tenant_id: str, system_user_id: str):
    """
    Runs reminder logic:
    - sends reminder
    - increments reminder_count
    - updates last_reminder_at
    - writes audit log
    """
    now = datetime.now(timezone.utc)
    due_notifications = get_due_notifications(db)

    for n in due_notifications:
        # --- reminder action (email/page/etc happens elsewhere later) ---

        n.reminder_count += 1
        n.last_reminder_at = now

        audit_event(
            db=db,
            tenant_id=tenant_id,
            user_id=system_user_id,
            role="SYSTEM",
            action="DOC_REMINDER_SENT",
            entity_type="DOCUMENT",
            entity_id=str(n.document_id),
            meta={
                "recipient_role": n.recipient_role,
                "recipient_user_id": n.recipient_user_id,
                "reminder_count": n.reminder_count,
            },
        )