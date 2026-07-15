from __future__ import annotations

from typing import Any

from app.services.eligibility.adl_dependency_service import (
    build_adl_evidence,
)

# =========================================================
# PUBLIC API
# =========================================================

def harvest_clinical_facts(patient: Any) -> dict[str, Any]:
    """
    Harvest normalized eligibility facts from patient-level
    clinical data sources.

    Phase 1 Facts:

    - PPS
    - KPS
    - FAST
    - NYHA

    This service MUST NOT:

    - Query databases
    - Apply LCD rules
    - Determine eligibility
    - Perform enforcement

    Responsibility:

        Clinical Data
               ↓
        Evidence Harvest
               ↓
        RuleContext.facts
    """

    facts = {
        # Existing
        "pps": None,
        "kps": None,
        "fast_stage": None,
        "nyha_class": None,

        # Parkinson Evidence
        "adl_dependency_count": None,
        "adl_dependency_level": None,

        "is_bedbound": None,

        "dysphagia": None,

        "oral_intake_decline": None,
        "weight_loss_lbs": None,

        "fall_risk": None,

        "caregiver_stress": None,

        "communication_ability": None,
        "speech_pattern": None,
    }

    sources = _candidate_sources(patient)

    facts["pps"] = _first_value(
        sources,
        [
            "pps",
            "pps_score",
        ],
    )

    facts["kps"] = _first_value(
        sources,
        [
            "kps",
            "kps_score",
        ],
    )

    facts["fast_stage"] = _first_value(
        sources,
        [
            "fast",
            "fast_stage",
            "fast_score",
        ],
    )

    facts["nyha_class"] = _first_value(
        sources,
        [
            "nyha",
            "nyha_class",
        ],
    )
    
    # ---------------------------------------------------------
    # ADL Eligibility Evidence
    # ---------------------------------------------------------

    explicit_adl_count = _first_value(
        sources,
        [
            "adl_dependency_count",
        ],
    )

    explicit_adl_level = _first_value(
        sources,
        [
            "adl_dependency_level",
            "adl_level",
        ],
    )

    adl_payload = (
        _first_value(
            sources,
            [
                "adls",
            ],
        )
        or {}
    )

    adl_evidence = build_adl_evidence(
        adl_payload,
    )

    facts["adl_dependency_count"] = (
        explicit_adl_count
        if not _empty(explicit_adl_count)
        else adl_evidence["adl_dependency_count"]
    )

    facts["adl_dependency_level"] = (
        explicit_adl_level
        if not _empty(explicit_adl_level)
        else adl_evidence["adl_dependency_level"]
    )

    facts["is_bedbound"] = _first_value(
        sources,
        [
            "is_bedbound",
            "bedbound",
        ],
    )

    facts["dysphagia"] = _first_value(
        sources,
        [
            "dysphagia",
        ],
    )

    facts["oral_intake_decline"] = _first_value(
        sources,
        [
            "oral_intake_decline",
        ],
    )

    facts["weight_loss_lbs"] = _first_value(
        sources,
        [
            "weight_loss_lbs",
        ],
    )

    facts["fall_risk"] = _first_value(
        sources,
        [
            "fall_risk",
        ], 
    )

    facts["caregiver_stress"] = _first_value(
        sources,
        [
            "caregiver_stress",
        ],
    )

    facts["communication_ability"] = _first_value(
        sources,
        [
            "communication_ability",
        ],
    )

    facts["speech_pattern"] = _first_value(
        sources,
        [
            "speech_pattern",
        ],
    )
    
    return facts


# =========================================================
# SOURCE DISCOVERY
# =========================================================

def _candidate_sources(patient: Any) -> list[dict[str, Any]]:
    """
    Collect possible fact containers.

    Supports:

    - patient attributes
    - dict payloads
    - assessment payloads
    - form payloads

    Future-safe.
    """

    sources: list[dict[str, Any]] = []

    if isinstance(patient, dict):
        sources.append(patient)

    if hasattr(patient, "__dict__"):
        sources.append(vars(patient))

    for attribute_name in (
        "assessment",
        "assessment_data",
        "clinical_data",
        "facts",
        "content",
        "functional_assessment",
        "functional_scores",
        "scores",
    ):
        value = getattr(patient, attribute_name, None)

        if isinstance(value, dict):
            sources.append(value)

    return sources


# =========================================================
# EXTRACTION HELPERS
# =========================================================

def _first_value(
    sources: list[dict[str, Any]],
    keys: list[str],
) -> Any:
    """
    Return first non-empty value found across
    all candidate sources.
    """

    for source in sources:
        value = _find_nested(source, keys)

        if not _empty(value):
            return value

    return None


def _find_nested(
    obj: Any,
    keys: list[str],
) -> Any:
    """
    Recursive nested search.

    Supports:

    dict
    list
    nested assessment payloads
    """

    if isinstance(obj, dict):

        for key in keys:
            if key in obj and not _empty(obj[key]):
                return obj[key]

        for value in obj.values():
            result = _find_nested(value, keys)

            if not _empty(result):
                return result

    elif isinstance(obj, list):

        for item in obj:
            result = _find_nested(item, keys)

            if not _empty(result):
                return result

    return None


def _empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return len(value) == 0

    if isinstance(value, dict):
        return len(value) == 0

    return False