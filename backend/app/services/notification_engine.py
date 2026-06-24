from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification


# =========================================================
# MAIN NOTIFICATION CREATOR
# =========================================================

def create_notification(
    db: Session,
    *,
    tenant_id,
    user_id,
    patient_id: Optional[str],
    title: str,
    message: str,
    notification_type: str,
    source_type: str,
    source_id,
) -> None:
    """
    Create an in-app notification.

    Enterprise guarantees:
    - Safe: will not crash if user_id is missing
    - Traceable: linked to source object
    - Structured: supports filtering and audit
    """

    if not user_id or not tenant_id:
        return  # ✅ HARD SAFETY — do not create invalid records

    notification = Notification(
        id=uuid4(),

        # ✅ TENANT / OWNERSHIP
        tenant_id=tenant_id,
        user_id=user_id,
        patient_id=patient_id,

        # ✅ MESSAGE
        title=title,
        message=message,

        # ✅ CLASSIFICATION
        notification_type=notification_type,

        # ✅ TRACEABILITY
        source_type=source_type,
        source_id=source_id,

        # ✅ STATE
        is_read=False,
        read_at=None,

        # ✅ TIME
        created_at=datetime.utcnow(),
    )

    db.add(notification)