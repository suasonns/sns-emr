from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.core.db import get_db

router = APIRouter()


# =========================================================
# GET USER NOTIFICATIONS
# =========================================================

@router.get("/notifications", response_model=List[dict])
def get_notifications(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "source_type": n.source_type,
            "source_id": n.source_id,
        }
        for n in notifications
    ]


# =========================================================
# GET UNREAD COUNT
# =========================================================

@router.get("/notifications/unread-count")
def get_unread_count(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .filter(Notification.is_read == False)
        .count()
    )

    return {"unread_count": count}


# =========================================================
# MARK ONE AS READ
# =========================================================

@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = notification.read_at or notification.created_at

    db.commit()

    return {"success": True}


# =========================================================
# MARK ALL AS READ
# =========================================================

@router.patch("/notifications/read-all")
def mark_all_read(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .filter(Notification.is_read == False)
        .all()
    )

    for n in notifications:
        n.is_read = True
        n.read_at = n.read_at or n.created_at

    db.commit()

    return {"success": True}