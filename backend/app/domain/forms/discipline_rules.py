from __future__ import annotations


RN_NP_ONLY_STRUCTURED_MODULES = {
    "skin",
    "fall_risk",
    "safety",
    "functional_scores",
    "orders_support",
}

CLINICAL_COMPREHENSIVE_OWNERS = {"RN", "NP"}

PSYCHOSOCIAL_DISCIPLINES = {"MSW", "SW", "BSW", "LCSW"}
SPIRITUAL_DISCIPLINES = {"SC", "CHAPLAIN"}
SUPPORT_DISCIPLINES = {"CHHA", "AIDE", "VOLUNTEER"}


def validate_form_package(
    *,
    discipline: str,
    form_key: str,
    primary_modules: set[str],
) -> None:
    """
    Enforce discipline-safe ownership for resolved packages.
    """

    discipline = (discipline or "").upper()

    # RN/NP only: HOPE / full structured clinical comprehensive
    if form_key == "RN_HOPE_ADMISSION" and discipline not in CLINICAL_COMPREHENSIVE_OWNERS:
        raise ValueError(f"{discipline} cannot own HOPE admission / clinical comprehensive form")

    # MSW / SC / CHHA / other support roles cannot own RN/NP structured modules
    if discipline in (PSYCHOSOCIAL_DISCIPLINES | SPIRITUAL_DISCIPLINES | SUPPORT_DISCIPLINES):
        conflict = primary_modules.intersection(RN_NP_ONLY_STRUCTURED_MODULES)
        if conflict:
            raise ValueError(
                f"{discipline} cannot own structured clinical modules: {sorted(conflict)}"
            )

    # LVN cannot own HOPE admission / RN-only comprehensive package
    if discipline == "LVN" and form_key == "RN_HOPE_ADMISSION":
        raise ValueError("LVN cannot own HOPE admission / clinical comprehensive form")