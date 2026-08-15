# services/communications_log_service.py

from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models.communications_log import CommunicationsLog
from app.services.communications_log_alerts import create_commlog_alerts
from app.services.commlog_to_task_bridge import handle_commlog_for_tasks
from app.services.idg_intelligence_service import create_or_update_from_communication_log

from app.services.hospitalization_prevention_service import (
    create_or_update_family_concern_from_source,
)

logger = logging.getLogger(__name__)

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
        tenant_id=payload.tenant_id,
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
    # IDG INTELLIGENCE HARVEST (safe)
    # ------------------------------
    try:
        create_or_update_from_communication_log(
            db=db,
            entry=commlog,
        )
    except Exception:
        logger.exception(
            "Failed to harvest communication log into IDG intelligence",
            extra={
                "communication_log_id": str(commlog.id)
            },
        )

    # ------------------------------
    # HOSPITALIZATION PREVENTION
    # ------------------------------
    try:
        create_or_update_family_concern_from_source(
            db=db,
            tenant_id=commlog.tenant_id,
            patient_id=commlog.patient_id,
            benefit_period_id=None,  # future lookup
            concern_text=commlog.summary,
            source_type="COMMUNICATION_LOG",
            source_table="communications_log",
            source_record_id=commlog.id,
            source_discipline="COMMUNICATION_LOG",
            source_author_id=user_id,
            source_note_date=commlog.event_time,
            source_excerpt=commlog.summary,
            reported_source_type=commlog.event_type,
            created_by=user_id,
        )

    except Exception:
        logger.exception(
            "Failed to harvest hospitalization prevention concern",
            extra={
                "communication_log_id": str(commlog.id),
            },
        )
    
    # ------------------------------
    # ALERTS (safe)
    # ------------------------------
    try:
        create_commlog_alerts(
            db=db,
            tenant_id=commlog.tenant_id,
            patient_id=payload.patient_id,
            commlog_id=commlog.id,
            message=payload.summary,
            user_ids=[]
        )
    except Exception:
        logger.exception(
            "Failed to create communication log alerts",
            extra={
                "communication_log_id": str(commlog.id)
            },
        )


    # ------------------------------
    # TASK BRIDGE (safe)
    # ------------------------------
    try:
        handle_commlog_for_tasks(
            db=db,
            commlog=commlog,
        )
    except Exception:
        logger.exception(
            "Failed to process communication log task bridge",
            extra={
                "communication_log_id": str(commlog.id)
            },
        )


    db.commit()
    db.refresh(commlog)

    return commlog