from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_commlog_alerts(
    *,
    db: Session,
    patient_id,
    commlog_id,
    message: str,
    user_ids: list,
) -> None:
    """
    Create in-app alerts when a Communications Log entry is created.
    """

    for user_id in user_ids:
        db.add(
            Notification(
                user_id=user_id,
                patient_id=patient_id,
                source_type="COMMUNICATIONS_LOG",
                source_id=commlog_id,
                message=message,
            )
        )
