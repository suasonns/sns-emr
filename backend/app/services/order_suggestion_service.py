# backend/app/services/order_suggestion_service.py

from __future__ import annotations

from typing import Any

from app.models.clinical_note import ClinicalNote
from app.services.poc_generation_service import generate_initial_poc_draft

ORDER_SUGGESTION_SERVICE_VERSION = "1.0.0"

# Maps a Plan-of-Care problem code -- already detected by
# poc_generation_service's respiratory/skin/nutrition/fall-risk rules -- to
# one or more suggested non-medication order drafts (DME / Supply /
# Treatment / Diet). Deliberately reuses the exact same clinical-finding
# detection the POC engine already uses, rather than re-implementing it, so
# the two engines never disagree about what was found in the assessment.
_ORDER_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "RESPIRATORY": [
        {
            "order_type": "DME",
            "sub_type": "NEW",
            "order_text": "Oxygen concentrator with portable tank as needed for dyspnea/hypoxia",
            "indication": "Respiratory distress/dyspnea documented on RN ICA",
        },
    ],
    "SKIN_INTEGRITY": [
        {
            "order_type": "TREATMENT",
            "sub_type": "NEW",
            "order_text": "Wound care per protocol; RN to assess, cleanse, and dress wound each visit",
            "indication": "Skin/wound integrity concern documented on RN ICA",
        },
        {
            "order_type": "SUPPLY",
            "sub_type": "NEW",
            "order_text": "Wound care dressing supplies (per wound care protocol)",
            "indication": "Skin/wound integrity concern documented on RN ICA",
        },
    ],
    "NUTRITION": [
        {
            "order_type": "DIET",
            "sub_type": "NEW",
            "order_text": "Nutritional supplement / diet as tolerated, per hospice comfort-focused nutrition plan",
            "indication": "Nutritional decline documented on RN ICA",
        },
    ],
    "SAFETY_FALL_RISK": [
        {
            "order_type": "DME",
            "sub_type": "NEW",
            "order_text": "Hospital bed with side rails for safety and positioning",
            "indication": "Fall risk/safety concern documented on RN ICA",
        },
        {
            "order_type": "DME",
            "sub_type": "NEW",
            "order_text": "Bedside commode",
            "indication": "Fall risk/safety concern documented on RN ICA",
        },
    ],
}


def generate_order_suggestions(note: ClinicalNote) -> dict[str, Any]:
    """Generate suggest-only, non-persistent DME/Supply/Treatment/Diet order
    drafts from the same clinical findings the POC-generation engine detects.

    Mirrors the POC-generation design intentionally:
    - Generates suggestions only. Never persists a `PatientOrder`.
    - Never auto-applies. A clinician must take an explicit "Add to Orders"
      action (see `app/api/routes/rnica_poc.py`) for a suggestion to become
      a real order -- consistent with the "POC changes remain strictly
      clinician-initiated" Master Sync Rule already enforced for POC.
    """
    draft = generate_initial_poc_draft(note)
    suggestions: list[dict[str, Any]] = []
    for poc in draft.get("pocs", []):
        problem = poc.get("problem") or {}
        code = problem.get("code")
        templates = _ORDER_TEMPLATES.get(code)
        if not templates:
            continue
        for index, template in enumerate(templates):
            suggestions.append(
                {
                    "suggestion_key": f"{poc.get('poc_id')}_ORDER_{index + 1}",
                    "rule_key": code,
                    "problem_label": problem.get("label"),
                    "order_type": template["order_type"],
                    "sub_type": template["sub_type"],
                    "order_text": template["order_text"],
                    "indication": template["indication"],
                    "evidence": poc.get("evidence", []),
                }
            )

    return {
        "status": "SUGGESTIONS_GENERATED",
        "suggestions": suggestions,
        "generated_at": draft.get("generated_at"),
        "generator": {
            "service": "order_suggestion_service",
            "version": ORDER_SUGGESTION_SERVICE_VERSION,
            "mode": "suggest_only",
            "requires_clinician_review": True,
            "auto_applied": False,
        },
    }
