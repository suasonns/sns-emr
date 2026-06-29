# app/services/poc_update_tasks.py

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy


logger = logging.getLogger("sns_emr")


def handle_poc_update_on_visit_finalize(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:
    """
    Legacy wrapper for older call sites.

    Canonical behavior lives in:
    app.services.poc_update_automation.on_visit_finalized_apply_poc_policy

    Purpose:
    - prevent drift between “tasks” and “automation” modules
    - provide safe boundary for older integrations

    This wrapper:
    - adds defensive guards
    - adds logging for audit trace
    - isolates failures to avoid breaking upstream flows
    """

    # =========================================================
    # VALIDATION GUARD
    # =========================================================
    if db is None:
        logger.error("POC_UPDATE wrapper called with db=None")
        return

    if visit is None:
        logger.warning("POC_UPDATE wrapper called with visit=None")
        return

    if patient is None or not getattr(patient, "id", None):
        logger.warning(
            "POC_UPDATE wrapper called with invalid patient visit_id=%s",
            str(getattr(visit, "id", None)),
        )
        return

    # =========================================================
    # TRACE LOG (COMPLIANCE CRITICAL)
    # =========================================================
    logger.info(
        "POC_UPDATE wrapper invoked visit_id=%s patient_id=%s finalized_by=%s",
        str(getattr(visit, "id", None)),
        str(getattr(patient, "id", None)),
        str(finalized_by_user_id),
    )

    # =========================================================
    # SAFE EXECUTION
    # =========================================================
    try:
        on_visit_finalized_apply_poc_policy(
            db,
            visit=visit,
            patient=patient,
            finalized_by_user_id=finalized_by_user_id,
        )

    except Exception as exc:
        # ✅ CRITICAL: do NOT crash calling workflow
        logger.exception(
            "POC_UPDATE automation failed visit_id=%s patient_id=%s error=%s",
            str(getattr(visit, "id", None)),
            str(getattr(patient, "id", None)),
            exc,
        )