from __future__ import annotations

from typing import Any

from app.services.eligibility.evidence_harvester import (
    harvest_clinical_facts,
)


def build_eligibility_snapshot(
    patient: Any,
) -> dict[str, Any]:
    """
    Build a normalized eligibility evidence snapshot.

    This service does NOT:

    - determine eligibility
    - apply LCD criteria
    - score patients
    - make recommendations

    This service DOES:

    - collect harvested evidence
    - normalize evidence
    - provide a reusable evidence package
      for rules, recertification, audit
      support, and future AI-assist workflows
    """

    facts = harvest_clinical_facts(
        patient,
    )

    return {
        "functional_status": {
            "pps": facts.get("pps"),
            "kps": facts.get("kps"),

            "adl_dependency_count": (
                facts.get("adl_dependency_count")
            ),

            "adl_dependency_level": (
                facts.get("adl_dependency_level")
            ),

            "is_bedbound": (
                facts.get("is_bedbound")
            ),
        },

        "disease_progression": {
            "fast_stage": (
                facts.get("fast_stage")
            ),

            "nyha_class": (
                facts.get("nyha_class")
            ),
        },

        "nutrition": {
            "oral_intake_decline": (
                facts.get("oral_intake_decline")
            ),

            "weight_loss_lbs": (
                facts.get("weight_loss_lbs")
            ),

            "dysphagia": (
                facts.get("dysphagia")
            ),
        },

        "safety": {
            "fall_risk": (
                facts.get("fall_risk")
            ),
        },

        "caregiver_support": {
            "caregiver_stress": (
                facts.get("caregiver_stress")
            ),
        },

        "communication": {
            "communication_ability": (
                facts.get("communication_ability")
            ),

            "speech_pattern": (
                facts.get("speech_pattern")
            ),
        },

        "snapshot_metadata": {
            "source": "eligibility_snapshot_service",
        },
    }