from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.document_notification import DocumentNotification
from app.services.audit_events import audit_event
from app.services.recipient_resolution import resolve_patient_recipients


def create_document_notifications(db, *, tenant_id: str, document_id, patient_id, actor_user_id: str, actor_role: str):
    recipients = resolve_patient_recipients(db, patient_id)

    for r in recipients:
        db.add(
            DocumentNotification(
                id=uuid.uuid4(),
                document_id=document_id,
                recipient_role=r.role,
                recipient_user_id=r.user_id,
                notified_at=datetime.now(timezone.utc),
            )
        )

        audit_event(
            db=db,
            tenant_id=tenant_id,
            user_id=actor_user_id,
            role=actor_role,
            action="DOC_NOTIFIED",
            entity_type="DOCUMENT",
            entity_id=str(document_id),
            meta={"recipient_role": r.role, "recipient_user_id": r.user_id},
        )