from datetime import datetime
from sqlalchemy.orm import Session

from app.models.communications_log import CommunicationsLog
from app.services.communications_log_alerts import create_commlog_alerts
from app.services.commlog_to_task_bridge import handle_commlog_for_tasks


def create_communications_log_entry(
    *,
    db: Session,
    payload,
    user_id,
):
    """
    Create communication log entry.
    Handles alerts + task bridge.
    Never blocks creation.
    """

    commlog = CommunicationsLog(
        patient_id=payload.patient_id,
        event_type=payload.event_type,
        focus_area=payload.focus_area,
        event_time=payload.event_time,
        summary=payload.summary,
        details=payload.details,
        created_by=user_id,
    )

    db.add(commlog)
    db.flush()  # ensures ID exists

    # ------------------------------
    # ALERTS (safe)
    # ------------------------------
    try:
        create_commlog_alerts(
            db=db,
            patient_id=payload.patient_id,
            commlog_id=commlog.id,
            message=payload.summary,
            user_ids=[]  # placeholder for now
        )
    except Exception:
        pass  # NEVER break comm log

    # ------------------------------
    # TASK BRIDGE (safe)
    # ------------------------------
    try:
        handle_commlog_for_tasks(db=db, commlog=commlog)
    except Exception:
        pass

    db.commit()
    db.refresh(commlog)

    return commlog