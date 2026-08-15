# services/idg_signature_actions.py

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.idg_attendee import IDGAttendee
from app.models.idg_review import IDGReview
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus


def sign_idg(
    db: Session,
    *,
    idg_review_id,
    user_id,
):

    # =====================================================
    # ✅ FIND ATTENDEE
    # =====================================================

    attendee = (
        db.query(IDGAttendee)
        .filter(
            IDGAttendee.idg_review_id == idg_review_id,
            IDGAttendee.user_id == user_id,
        )
        .first()
    )

    if not attendee:
        return {
            "success": False,
            "error": "ATTENDEE_NOT_FOUND",
        }

    # =====================================================
    # ✅ PREVENT DUPLICATE SIGN (IDEMPOTENT)
    # =====================================================

    if attendee.signed:
        return {
            "success": True,
            "message": "ALREADY_SIGNED",
        }

    # =====================================================
    # ✅ GET RELATED IDG REVIEW (FOR PATIENT CONTEXT)
    # =====================================================

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        return {
            "success": False,
            "error": "IDG_REVIEW_NOT_FOUND",
        }

    # =====================================================
    # ✅ SIGN RECORD
    # =====================================================

    now = datetime.now(timezone.utc)

    attendee.signed = True
    attendee.signed_at = now

    # =====================================================
    # ✅ AUTO-CLOSE SIGNATURE TASKS
    # =====================================================

    tasks = (
        db.query(Task)
        .filter(
            Task.patient_id == review.patient_id,
            Task.task_type == TaskType.IDG_SIGNATURE_REQUIRED,
            Task.status == TaskStatus.PENDING,
        )
        .all()
    )

    for task in tasks:

        # ✅ STRICT DISCIPLINE MATCH (SAFER)
        if task.discipline != attendee.discipline:
            continue

        task.status = TaskStatus.COMPLETE
        task.completed_at = now
        task.completed_by = user_id

    # =====================================================
    # ✅ COMMIT TRANSACTION
    # =====================================================

    db.commit()

    return {
        "success": True
    }
