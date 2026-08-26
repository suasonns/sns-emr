from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.services.notification_engine import create_notification


def create_commlog_alerts(
    *,
    db: Session,
    tenant_id: UUID,
    patient_id: UUID,
    commlog_id: UUID,
    message: str,
    user_ids: list[UUID],
) -> None:
    """
    Create in-app alerts when a Communications Log entry is created.

    Privacy rules:
    - caller must pass ONLY patient-assigned users + clinical admin / DPCS
    - never broadcast globally
    - dedupe recipients defensively
    """

    unique_user_ids = list(dict.fromkeys(user_ids))

    for user_id in unique_user_ids:
        create_notification(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=patient_id,
            title="New Communication Log Entry",
            message=message,
            notification_type="COMMUNICATION_LOG",
            source_type="COMMUNICATIONS_LOG",
            source_id=commlog_id,
        )