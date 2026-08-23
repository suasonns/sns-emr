# app/services/clinical_reasoning_bridge.py

"""
Shared entry point into the Clinical Reasoning Engine used by every
discipline's finalize/lock endpoint: RN/LVN visit finalize
(app/api/visits.py), MSW/SC ICA lock (app/api/visits.py), and MD/NP F2F
finalize (app/api/f2f.py). Kept as a standalone module (rather than living
in visits.py) so app/api/f2f.py does not need to import from
app/api/visits.py.

This is intentionally the ONE place a reasoning_record is looked up or
created and the engine is invoked, so every discipline feeds the same
findings / clinical_interpretations / clinical_reasoning_results / IDG
Intelligence stream -- one shared source of clinical intelligence for the
whole care team, per product decision.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.clinical_reasoning_engine import ClinicalReasoningEngine
from app.services.reasoning_result_to_recommendation_service import (
    ReasoningResultToRecommendationService,
)

logger = logging.getLogger(__name__)

clinical_reasoning_engine = ClinicalReasoningEngine()
reasoning_recommendation_service = ReasoningResultToRecommendationService()


def get_or_create_clinical_reasoning_record(
    db: Session,
    patient_id: UUID,
    episode_id: UUID,
) -> UUID:
    """
    Lookup/creation for the clinical_reasoning_records row backing one
    (patient, episode) pair. episode_id is a generic key: a Visit id for
    RN/LVN visits, an MswIcaAssessment/ScicaAssessment id for MSW/SC, or
    an F2FEncounter id for MD/NP F2F -- whichever document is being
    finalized/locked is this "episode" for reasoning purposes.
    """
    existing = db.execute(
        text(
            """
            SELECT id
            FROM clinical_reasoning_records
            WHERE patient_id = :patient_id
              AND episode_id = :episode_id
              AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "patient_id": patient_id,
            "episode_id": episode_id,
        },
    ).scalar_one_or_none()

    if existing:
        return existing

    created = db.execute(
        text(
            """
            INSERT INTO clinical_reasoning_records (
                patient_id,
                episode_id,
                status,
                requires_poc_update,
                requires_physician_review,
                requires_idg_review
            )
            VALUES (
                :patient_id,
                :episode_id,
                'active',
                FALSE,
                FALSE,
                FALSE
            )
            RETURNING id
            """
        ),
        {
            "patient_id": patient_id,
            "episode_id": episode_id,
        },
    ).scalar_one()

    return created


def run_clinical_reasoning(
    db: Session,
    patient_id: UUID,
    tenant_id: UUID,
    episode_id: UUID,
    assessment_payload: Dict[str, Any],
    request_id: str,
    log_label: str,
) -> None:
    if not assessment_payload:
        logger.info(
            "CLINICAL_REASONING_SKIPPED_EMPTY_PAYLOAD %s patient_id=%s episode_id=%s request_id=%s",
            log_label,
            str(patient_id),
            str(episode_id),
            request_id,
        )
        return

    reasoning_record_id = get_or_create_clinical_reasoning_record(
        db=db,
        patient_id=patient_id,
        episode_id=episode_id,
    )

    result = clinical_reasoning_engine.process_assessment(
        db=db,
        reasoning_record_id=reasoning_record_id,
        assessment_data=assessment_payload,
        reset_existing=True,
        commit=False,
    )

    recommendation_result = reasoning_recommendation_service.generate_for_patient(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        commit=False,
    )

    logger.info(
        "CLINICAL_REASONING_COMPLETED %s episode_id=%s reasoning_record_id=%s result=%s "
        "recommendation_result=%s request_id=%s",
        log_label,
        str(episode_id),
        str(reasoning_record_id),
        result,
        recommendation_result,
        request_id,
    )
