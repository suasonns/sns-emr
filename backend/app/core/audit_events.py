from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session


def log_support_lookup(
    *,
    db: Session,
    actor_id: str,
    session_reference: str,
    ip_address: str | None,
):
    """
    Immutable audit entry for support session lookups.
    NON-CLINICAL.
    """

    db.execute(
        text(
            """
            INSERT INTO audit_events (
                event_type,
                actor_id,
                reference,
                ip_address,
                created_at
            )
            VALUES (
                'SUPPORT_SESSION_LOOKUP',
                :actor_id,
                :reference,
                :ip_address,
                :created_at
            )
            """
        ),
        {
            "actor_id": actor_id,
            "reference": session_reference,
            "ip_address": ip_address,
            "created_at": datetime.now(timezone.utc),
        },
    )
    db.commit()