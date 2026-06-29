from __future__ import annotations

import logging
from datetime import timedelta
from sqlalchemy.orm import Session

from app.models.sfv_requirement import SFVRequirement

logger = logging.getLogger(__name__)

TRIGGER_LEVELS = {"MODERATE", "SEVERE"}


def create_sfv_requirement_if_needed(
    *,
    db: Session,
    visit,
    symptom_data: dict,
):
    """
    Create ONE SFV requirement per symptom.
    Prevent duplicates.
    """

    if not symptom_data or not isinstance(symptom_data, dict):
        logger.warning(
            "SFV_ENGINE: INVALID symptom_data visit_id=%s",
            str(visit.id),
        )
        return None

    for symptom, severity in symptom_data.items():
        sev = str(severity or "").strip().upper()

        if sev not in TRIGGER_LEVELS:
            continue

        # Prevent duplicate active requirement for same patient + symptom
        existing = (
            db.query(SFVRequirement)
            .filter(
                SFVRequirement.tenant_id == visit.tenant_id,
                SFVRequirement.patient_id == visit.patient_id,
                SFVRequirement.symptom_type == symptom,
                SFVRequirement.status == "PENDING",
            )
            .first()
        )

        if existing:
            logger.info(
                "SFV_ENGINE: EXISTING requirement patient_id=%s symptom=%s",
                str(visit.patient_id),
                symptom,
            )
            return existing

        trigger_dt = getattr(visit, "visit_datetime", None)
        if trigger_dt is None:
            raise ValueError("visit_datetime is required for SFV requirement creation")

        requirement = SFVRequirement(
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            triggering_visit_id=visit.id,
            trigger_source="ASSESSMENT",
            symptom_type=symptom,
            symptom_severity=sev,
            trigger_date=trigger_dt,
            due_date=trigger_dt + timedelta(days=2),
            status="PENDING",
            completed_visit_id=None,
            created_at=trigger_dt,
            updated_at=trigger_dt,
        )

        db.add(requirement)

        logger.info(
            "SFV_ENGINE: CREATED requirement visit_id=%s symptom=%s severity=%s tenant_id=%s",
            str(visit.id),
            symptom,
            sev,
            str(visit.tenant_id),
        )

        return requirement

    return None