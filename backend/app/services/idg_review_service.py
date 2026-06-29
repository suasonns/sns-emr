from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def finalize_idg_review(
    db: Session,
    *,
    idg_review_id,
    finalized_by: Optional[str] = None,
) -> IDGReview:

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise HTTPException(404, "IDG review not found")

    if review.is_finalized:
        raise HTTPException(400, "IDG already finalized")

    try:
        # -----------------------------------------------------
        # 1. HARD ENFORCEMENT
        # -----------------------------------------------------
        validate_idg_ready_to_finalize(db, idg_review_id=idg_review_id)

        # -----------------------------------------------------
        # 2. FINALIZE
        # -----------------------------------------------------
        review.is_finalized = True
        review.finalized_by = finalized_by
        review.finalized_at = datetime.now(timezone.utc)

        # -----------------------------------------------------
        # 3. COMPLETE IDG TASK (MUST SUCCEED)
        # -----------------------------------------------------
        complete_current_idg_review_task(db, idg_review=review)

        # -----------------------------------------------------
        # 4. AUTO-COMPLETE ICA TASKS
        # -----------------------------------------------------
        _auto_complete_ica_tasks_from_idg(
            db,
            review=review,
            finalized_by=finalized_by,
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("IDG finalization failed")
        raise HTTPException(500, "IDG finalization failed")

    db.refresh(review)
    return review


def _auto_complete_ica_tasks_from_idg(
    db: Session,
    *,
    review: IDGReview,
    finalized_by: Optional[str],
) -> None:

    query = text("""
        SELECT id, task_type
        FROM tasks
        WHERE patient_id = :patient_id
        AND tenant_id = :tenant_id
        AND (benefit_period_id IS NULL OR benefit_period_id = :benefit_period_id)
        AND status IN ('PENDING','IN_PROGRESS','OVERDUE')
        AND task_type::text IN (
            'INITIAL_RN_ICA',
            'INITIAL_MSW_ICA',
            'INITIAL_SC_ICA',
            'INITIAL_BEREAVEMENT'
        )
    """)

    results = db.execute(
        query,
        {
            "patient_id": review.patient_id,
            "tenant_id": review.tenant_id,
            "benefit_period_id": review.benefit_period_id,
        }
    ).fetchall()

    for row in results:
        try:
            complete_task(
                db=db,
                task_id=row[0],
                completion_reference_type="IDG",
                completion_reference_id=review.id,
                completed_by=finalized_by,
                completion_reason="AUTO_CLOSED_BY_IDG",
            )
        except Exception:
            logger.exception(f"ICA task failed: {row[0]}")
