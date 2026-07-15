from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


REGISTRY_FILE = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "config"
    / "eligibility_evidence_registry.json"
)


class EligibilityRegistryError(Exception):
    """
    Raised when the eligibility registry
    is missing or malformed.
    """


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    """
    Load and validate the eligibility evidence registry.
    """

    if not REGISTRY_FILE.exists():
        raise EligibilityRegistryError(
            f"Registry file not found: {REGISTRY_FILE}"
        )

    with REGISTRY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    _validate_registry(data)

    return data


def reload_registry() -> dict[str, Any]:
    """
    Clear cache and reload registry.
    Useful during development.
    """

    load_registry.cache_clear()

    return load_registry()


def get_registry_version() -> str | None:
    registry = load_registry()

    return registry.get("version")


def get_registry_status() -> str | None:
    registry = load_registry()

    return registry.get("status")


def get_evidence_categories() -> dict[str, Any]:
    registry = load_registry()

    return registry.get(
        "evidence_categories",
        {},
    )


def get_evidence_fields() -> dict[str, Any]:
    registry = load_registry()

    return registry.get(
        "evidence_fields",
        {},
    )


def get_evidence_definition(
    field_name: str,
) -> dict[str, Any] | None:
    return get_evidence_fields().get(
        field_name,
    )


def evidence_exists(
    field_name: str,
) -> bool:
    return (
        field_name
        in get_evidence_fields()
    )


def is_harvest_enabled(
    field_name: str,
) -> bool:
    definition = get_evidence_definition(
        field_name,
    )

    if not definition:
        return False

    return bool(
        definition.get(
            "harvest",
            False,
        )
    )


def is_required_when_visible(
    field_name: str,
) -> bool:
    definition = get_evidence_definition(
        field_name,
    )

    if not definition:
        return False

    return bool(
        definition.get(
            "required_when_visible",
            False,
        )
    )


def get_category(
    field_name: str,
) -> str | None:
    definition = get_evidence_definition(
        field_name,
    )

    if not definition:
        return None

    return definition.get(
        "category"
    )


def get_workflows(
    field_name: str,
) -> list[str]:
    definition = get_evidence_definition(
        field_name,
    )

    if not definition:
        return []

    workflows = definition.get(
        "workflows",
        [],
    )

    if not isinstance(
        workflows,
        list,
    ):
        return []

    return workflows


def _validate_registry(
    registry: dict[str, Any],
) -> None:
    if not isinstance(
        registry,
        dict,
    ):
        raise EligibilityRegistryError(
            "Eligibility registry must be a JSON object."
        )

    if (
        "evidence_categories"
        not in registry
    ):
        raise EligibilityRegistryError(
            "Missing evidence_categories section."
        )

    if (
        "evidence_fields"
        not in registry
    ):
        raise EligibilityRegistryError(
            "Missing evidence_fields section."
        )

    evidence_fields = registry.get(
        "evidence_fields"
    )

    if not isinstance(
        evidence_fields,
        dict,
    ):
        raise EligibilityRegistryError(
            "evidence_fields must be an object."
        )

    for (
        field_name,
        definition,
    ) in evidence_fields.items():

        if not isinstance(
            definition,
            dict,
        ):
            raise EligibilityRegistryError(
                f"{field_name}: definition must be an object."
            )

        required_keys = [
            "label",
            "category",
            "harvest",
            "required_when_visible",
            "workflows",
        ]

        for required_key in required_keys:
            if required_key not in definition:
                raise EligibilityRegistryError(
                    f"{field_name}: missing key '{required_key}'."
                )