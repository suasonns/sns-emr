"""Shared, versioned Hospice Clinical Context.

This is the one server-side resolved view of a patient's hospice-relevant
state that every downstream consumer (RNICA panel, narrative builder, future
Draft Builder, future Narrative Quality Gate, billing-readiness surfacing)
should read from -- instead of each caller re-querying and re-adapting the
same underlying engines with slightly different fallback behavior.

This module does NOT implement new clinical logic. It calls the existing,
already-verified engines in `rnica_intelligence.py`
(`app.services.eligibility.engine`, `PatientDiagnosis` relatedness rows,
`diagnosis_recommendations`, `billing_readiness_service`) and wraps each
section with:

  - an explicit, visible failure code (never a silent fallback) when a
    section's engine raises or is unavailable
  - version/identity metadata (context_version, pipeline_run_id,
    generated_at, patient_id) so callers can detect staleness later

It is intentionally NOT a new medical-record source of truth: it does not
duplicate or override the authoritative diagnosis, certification, or
billing records -- it resolves and republishes them with provenance.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Bump when the shape of the context materially changes so consumers /
# stale-artifact invalidation (not yet implemented) can detect drift.
CONTEXT_VERSION = "hospice-clinical-context-v1"

# Required explicit-failure vocabulary (see PR59/production-directive
# "REMOVE SILENT FALLBACKS" requirement). Every section below sets one of
# these instead of silently returning an empty/default value on failure.
UNAVAILABLE_DIAGNOSIS_CONTEXT = "DIAGNOSIS_CONTEXT_UNAVAILABLE"
UNAVAILABLE_LCD_EVALUATION = "LCD_EVALUATION_UNAVAILABLE"
UNAVAILABLE_LCD_SUPPORT_DETAILS = "LCD_SUPPORT_DETAILS_UNAVAILABLE"
UNAVAILABLE_BILLING_READINESS = "BILLING_READINESS_UNAVAILABLE"
UNAVAILABLE_DRIVER_RECOMMENDATION = "HOSPICE_DRIVER_RECOMMENDATION_UNAVAILABLE"


def build_hospice_clinical_context(db: Session, patient_id: str) -> dict[str, Any]:
    """Build the shared Hospice Clinical Context for one patient.

    Returns a dict with top-level keys:
      context_version, pipeline_run_id, generated_at, patient_id,
      available, unavailable_reason,
      diagnosis_context, related_conditions, why_hospice, disease_burden,
      certification_support, documentation_gaps, hospice_driver_recommendation,
      billing_readiness
    """
    from app.services import rnica_intelligence as ri

    pipeline_run_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    context: dict[str, Any] = {
        "context_version": CONTEXT_VERSION,
        "pipeline_run_id": pipeline_run_id,
        "generated_at": generated_at,
        "patient_id": patient_id,
        "available": False,
        "unavailable_reason": None,
        "diagnosis_context": None,
        "related_conditions": {"terminal": [], "related": [], "unrelated": []},
        "why_hospice": None,
        "disease_burden": None,
        "certification_support": None,
        "documentation_gaps": [],
        "hospice_driver_recommendation": None,
        "billing_readiness": None,
    }

    patient = ri._load_patient_for_reasoning(db, patient_id)
    if patient is None:
        context["unavailable_reason"] = UNAVAILABLE_DIAGNOSIS_CONTEXT
        return context

    from app.services.diagnosis_resolver import resolve_current_diagnosis_context

    diagnosis_resolved = resolve_current_diagnosis_context(db, patient_id)
    if not diagnosis_resolved.get("available"):
        context["unavailable_reason"] = (
            f"{UNAVAILABLE_DIAGNOSIS_CONTEXT}: {diagnosis_resolved.get('unavailable_reason')}"
        )
        context["diagnosis_context"] = diagnosis_resolved
        return context

    context["available"] = True
    primary = diagnosis_resolved["primary"] or {}
    context["diagnosis_context"] = {
        # Kept for backward-compat callers reading the old flat shape --
        # both now resolved through the single authoritative resolver
        # instead of nonexistent Patient attributes.
        "primary_diagnosis_code": primary.get("icd10_code"),
        "primary_diagnosis_description": primary.get("description"),
        "source": diagnosis_resolved.get("primary_source"),
        # Full resolved shape (typed primary/secondary/comorbidities with
        # provenance) for callers that need more than the flat pair.
        "primary": primary,
        "secondary": diagnosis_resolved.get("secondary", []),
        "comorbidities": diagnosis_resolved.get("comorbidities", []),
        "resolver_context_version": diagnosis_resolved.get("context_version"),
    }

    related_conditions = ri._build_related_conditions(db, patient, diagnosis_resolved)
    context["related_conditions"] = related_conditions

    try:
        why_hospice, disease_burden, certification_support, doc_gaps = ri._build_eligibility_sections(
            patient, related_conditions
        )
        context["why_hospice"] = why_hospice
        context["disease_burden"] = disease_burden
        context["certification_support"] = certification_support
        context["documentation_gaps"] = doc_gaps
        if why_hospice is None:
            context["certification_support"] = context["certification_support"] or {
                "unavailable_reason": UNAVAILABLE_LCD_EVALUATION
            }
    except Exception:
        logger.exception("hospice_clinical_context: LCD/eligibility evaluation failed for %s", patient_id)
        context["why_hospice"] = {"unavailable_reason": UNAVAILABLE_LCD_EVALUATION}
        context["certification_support"] = {"unavailable_reason": UNAVAILABLE_LCD_SUPPORT_DETAILS}

    try:
        context["hospice_driver_recommendation"] = ri._build_driver_recommendation(db, patient)
    except Exception:
        logger.exception("hospice_clinical_context: driver recommendation failed for %s", patient_id)
        context["hospice_driver_recommendation"] = {"unavailable_reason": UNAVAILABLE_DRIVER_RECOMMENDATION}

    try:
        context["billing_readiness"] = ri._build_billing_readiness(db, patient)
        if context["billing_readiness"] is None:
            context["billing_readiness"] = {"unavailable_reason": UNAVAILABLE_BILLING_READINESS}
    except Exception:
        logger.exception("hospice_clinical_context: billing readiness failed for %s", patient_id)
        context["billing_readiness"] = {"unavailable_reason": UNAVAILABLE_BILLING_READINESS}

    return context
