from __future__ import annotations

from typing import Any


ADL_FIELDS = (
    "bathing",
    "dressing",
    "toileting",
    "transferring",
    "ambulation",
    "feeding",
)

DEPENDENT_VALUES = {
    "dependent",
    "complete",
    "complete_assist",
    "total_assist",
    "max_assist",
    "maximum_assistance",
}

PARTIAL_VALUES = {
    "partial_assist",
    "limited_assist",
    "moderate_assist",
    "min_assist",
    "minimal_assistance",
}


def calculate_adl_dependency_count(
    adls: dict[str, Any] | None,
) -> int:
    """
    Returns the number of ADLs requiring dependency.

    Example:

        bathing      = dependent
        dressing     = dependent
        toileting    = dependent
        transferring = independent
        ambulation   = dependent
        feeding      = dependent

    Result:

        5
    """

    if not adls:
        return 0

    count = 0

    for field in ADL_FIELDS:
        value = _normalize(
            adls.get(field)
        )

        if value in DEPENDENT_VALUES:
            count += 1

    return count


def calculate_adl_dependency_level(
    adls: dict[str, Any] | None,
) -> str:
    """
    Returns a normalized dependency level.

    Levels:

        INDEPENDENT
        LIMITED_ASSISTANCE
        MODERATE_DEPENDENCY
        HIGH_DEPENDENCY
        TOTAL_DEPENDENCY
    """

    dependent_count = calculate_adl_dependency_count(
        adls
    )

    if dependent_count == 0:
        return "INDEPENDENT"

    if dependent_count <= 2:
        return "LIMITED_ASSISTANCE"

    if dependent_count <= 3:
        return "MODERATE_DEPENDENCY"

    if dependent_count <= 5:
        return "HIGH_DEPENDENCY"

    return "TOTAL_DEPENDENCY"


def build_adl_evidence(
    adls: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Normalize ADL data into eligibility evidence.
    """

    normalized_adls = {}

    for field in ADL_FIELDS:
        normalized_adls[field] = (
            adls.get(field)
            if adls
            else None
        )

    return {
        "adl_dependency_count":
            calculate_adl_dependency_count(
                adls
            ),

        "adl_dependency_level":
            calculate_adl_dependency_level(
                adls
            ),

        "adls":
            normalized_adls,
    }


def has_three_or_more_dependent_adls(
    adls: dict[str, Any] | None,
) -> bool:
    """
    Common LCD eligibility threshold.
    """

    return (
        calculate_adl_dependency_count(
            adls
        )
        >= 3
    )


def has_five_or_more_dependent_adls(
    adls: dict[str, Any] | None,
) -> bool:
    """
    Advanced decline threshold used by many
    end-stage neurological conditions.
    """

    return (
        calculate_adl_dependency_count(
            adls
        )
        >= 5
    )


def _normalize(
    value: Any,
) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )