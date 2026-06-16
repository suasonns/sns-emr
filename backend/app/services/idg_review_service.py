"""
Enterprise-grade IDG review lifecycle service.

Authoritative entity:
- IDGReview (CMS CoPs §418.56)

Responsibilities:
- Create IDG review
- Finalize IDG (authoritative compliance gate)
- Trigger downstream compliance workflows:
    - Complete IDG_REVIEW task
    - Auto-complete ICA tasks (RN/MSW/SC/Bereavement)
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.models.idg_review import IDGReview

from app.services.idg_enforcement import validate_idg_ready_to_finalize
from app.services.idg_review_tasks import complete_current_idg_review_task
from app.services.task_completion import complete_task


# =========================================================
# CREATE IDG REVIEW
# =========================================================

def create_idg_review(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    review_date: date,
    summary: str,
    poc_action: str,
    created_by: Optional[str] = None,
) -> IDGReview:

    review = IDGReview(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        review_date=review_date,
        summary=summary,
        poc_action=poc_action,
        created_by=created_by,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


# =========================================================
# FINALIZE IDG REVIEW (AUTHORITATIVE GATE)
# =========================================================

def finalize_idg_review(
    db: Session,
    *,
    idg_review_id,
    finalized_by: Optional[str] = None,
) -> IDGReview:

    print("✅ [DEBUG] finalize_idg_review CALLED:", idg_review_id)

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise HTTPException(status_code=404, detail="IDG review not found")

    if review.is_finalized:
        raise HTTPException(status_code=400, detail="IDG review already finalized")

    # -----------------------------------------------------
    # 1. HARD ENFORCEMENT (CMS GATE)
    # -----------------------------------------------------
    validate_idg_ready_to_finalize(db, idg_review_id=idg_review_id)

    print("✅ [DEBUG] IDG passed validation:", review.id)

    # -----------------------------------------------------
    # 2. FINALIZE IDG
    # -----------------------------------------------------
    review.is_finalized = True
    review.finalized_by = finalized_by
    review.finalized_at = date.today()

    print("✅ [DEBUG] IDG marked finalized:", review.id)

    # -----------------------------------------------------
    # 3. COMPLETE IDG TASK
    # -----------------------------------------------------
    try:
        complete_current_idg_review_task(db, idg_review=review)
    except Exception as e:
        print(f"[WARN] Failed to complete IDG task: {str(e)}")

    # -----------------------------------------------------
    # 4. AUTO-COMPLETE ICA TASKS (FINAL FIX)
    # -----------------------------------------------------
    try:
        print("✅ [DEBUG] Starting ICA auto-completion")
        _auto_complete_ica_tasks_from_idg(db, review=review)
    except Exception as e:
        print(f"[WARN] ICA auto-completion failed: {str(e)}")

    # -----------------------------------------------------
    # 5. COMMIT
    # -----------------------------------------------------
    db.commit()
    db.refresh(review)

    return review


# =========================================================
# ICA AUTO-CLOSURE ENGINE (PRODUCTION VERSION)
# =========================================================

def _auto_complete_ica_tasks_from_idg(db: Session, *, review: IDGReview) -> None:

    print("✅ [DEBUG] ICA AUTO-COMPLETE FUNCTION RUNNING")

    query = text("""
        SELECT id, task_type
        FROM tasks
        WHERE patient_id = :patient_id
        AND (benefit_period_id IS NULL OR benefit_period_id = :benefit_period_id)
        AND status != 'COMPLETED'
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
            "benefit_period_id": review.benefit_period_id,
        }
    ).fetchall()

    print(f"✅ [DEBUG] ICA tasks found: {len(results)}")

    for row in results:
        task_id = row[0]
        task_type = row[1]

        try:
            print(f"✅ [DEBUG] Completing ICA task: {task_type} | {task_id}")

            complete_task(
                db=db,
                task_id=task_id,
                completion_reference_type="IDG",
                completion_reference_id=review.id,
            )

        except Exception as e:
            print(f"[WARN] Failed ICA task {task_id}: {str(e)}")
            continue