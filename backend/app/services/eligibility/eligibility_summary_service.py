from __future__ import annotations

from typing import Any

from app.services.eligibility.eligibility_snapshot_service import (
    build_eligibility_snapshot,
)


def build_eligibility_summary(
    patient: Any,
) -> dict[str, Any]:
    """
    Build a presentation-ready eligibility evidence summary.

    This service does NOT:

    - determine hospice eligibility
    - apply LCD criteria
    - generate recommendations
    - create POCs
    - perform AI analysis

    This service DOES:

    - transform eligibility snapshots into a
      clinician-friendly summary structure
    - provide a reusable summary layer for
      RN ICA, Recertification, Audit Review,
      and future UI components
    """

    snapshot = build_eligibility_snapshot(
        patient,
    )

    functional_status = snapshot.get(
        "functional_status",
        {},
    )

    disease_progression = snapshot.get(
        "disease_progression",
        {},
    )

    nutrition = snapshot.get(
        "nutrition",
        {},
    )

    safety = snapshot.get(
        "safety",
        {},
    )

    caregiver_support = snapshot.get(
        "caregiver_support",
        {},
    )

    communication = snapshot.get(
        "communication",
        {},
    )

    return {
        "summary_type": "ELIGIBILITY_EVIDENCE_SUMMARY",

        "functional_status": [
            {
                "label": "PPS",
                "value": functional_status.get("pps"),
            },
            {
                "label": "KPS",
                "value": functional_status.get("kps"),
            },
            {
                "label": "ADL Dependency Count",
                "value": functional_status.get(
                    "adl_dependency_count"
                ),
            },
            {
                "label": "ADL Dependency Level",
                "value": functional_status.get(
                    "adl_dependency_level"
                ),
            },
            {
                "label": "Bedbound Status",
                "value": functional_status.get(
                    "is_bedbound"
                ),
            },
        ],

        "disease_progression": [
            {
                "label": "FAST Stage",
                "value": disease_progression.get(
                    "fast_stage"
                ),
            },
            {
                "label": "NYHA Class",
                "value": disease_progression.get(
                    "nyha_class"
                ),
            },
        ],

        "nutrition": [
            {
                "label": "Dysphagia",
                "value": nutrition.get(
                    "dysphagia"
                ),
            },
            {
                "label": "Oral Intake Decline",
                "value": nutrition.get(
                    "oral_intake_decline"
                ),
            },
            {
                "label": "Weight Loss (lbs)",
                "value": nutrition.get(
                    "weight_loss_lbs"
                ),
            },
        ],

        "safety": [
            {
                "label": "Fall Risk",
                "value": safety.get(
                    "fall_risk"
                ),
            },
        ],

        "caregiver_support": [
            {
                "label": "Caregiver Stress",
                "value": caregiver_support.get(
                    "caregiver_stress"
                ),
            },
        ],

        "communication": [
            {
                "label": "Communication Ability",
                "value": communication.get(
                    "communication_ability"
                ),
            },
            {
                "label": "Speech Pattern",
                "value": communication.get(
                    "speech_pattern"
                ),
            },
        ],

        "metadata": {
            "source": "eligibility_summary_service",
        },
    }