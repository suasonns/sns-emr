from __future__ import annotations

from fastapi import HTTPException, status


# =========================================================
# CONSTANTS
# =========================================================

VALID_ROLES = {
    "RN",
    "LVN",
    "LPN",
    "MD",
    "NP",
    "SW",
    "CHAPLAIN",
    "MEDICAL_DIRECTOR",
    "ALTERNATE_MEDICAL_DIRECTOR",
    "MEDICAL_DIRECTOR_DESIGNEE",
}

VALID_VISIT_TYPES = {
    "RN",
    "LVN",
    "NP",
    "MD",
    "SW",
    "CHAPLAIN",
    "CHHA",
    "AIDE",
}

VALID_ACTIONS = {
    "document",
    "finalize",
    "review",
}


# =========================================================
# NORMALIZATION
# =========================================================

def _normalize(value: str) -> str:
    return value.strip().upper()


# =========================================================
# AUTHORIZATION
# =========================================================

def authorize_documentation(
    *,
    user_role: str,
    visit_type: str,
    action: str = "document",
):
    """
    Enterprise-grade clinical authorization.

    Guarantees:
    ✅ role validation
    ✅ visit_type validation
    ✅ action validation
    ✅ discipline enforcement
    ✅ future extensibility (F2F / CTI / attestation)
    """

    # -----------------------------------------------------
    # Normalize inputs
    # -----------------------------------------------------
    user_role = _normalize(user_role)
    visit_type = _normalize(visit_type)
    action = _normalize(action)

    # -----------------------------------------------------
    # Validate role
    # -----------------------------------------------------
    if user_role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid user role: {user_role}",
        )

    # -----------------------------------------------------
    # Validate visit_type
    # -----------------------------------------------------
    if visit_type not in VALID_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visit type: {visit_type}",
        )

    # -----------------------------------------------------
    # Validate action
    # -----------------------------------------------------
    if action not in VALID_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid action: {action}",
        )

    # -----------------------------------------------------
    # RN VISIT RULES
    # -----------------------------------------------------
    if visit_type == "RN":
        if user_role not in {"RN", "NP", "MD", "MEDICAL_DIRECTOR"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only RN/NP/MD can document RN visits",
            )

    # -----------------------------------------------------
    # CHHA / AIDE RULES
    # -----------------------------------------------------
    if visit_type in {"CHHA", "AIDE"}:
        if user_role not in {"RN", "LVN", "LPN"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only nursing staff can document CHHA/AIDE visits",
            )

    # -----------------------------------------------------
    # SOCIAL WORK
    # -----------------------------------------------------
    if visit_type == "SW" and user_role != "SW":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SW can document social work visits",
        )

    # -----------------------------------------------------
    # CHAPLAIN
    # -----------------------------------------------------
    if visit_type == "CHAPLAIN" and user_role != "CHAPLAIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Chaplain can document chaplain visits",
        )

    # -----------------------------------------------------
    # PHYSICIAN VISITS
    # -----------------------------------------------------
    if visit_type in {"MD", "NP"}:
        if user_role not in {
            "MD",
            "NP",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only physician/NP roles can document MD/NP visits",
            )

    # -----------------------------------------------------
    # FINALIZATION RULES
    # -----------------------------------------------------
    if action == "FINALIZE":
        if user_role not in {
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to finalize clinical documentation",
            )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------
    return True