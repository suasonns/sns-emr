from __future__ import annotations

from fastapi import HTTPException, status


# =========================================================
# CONSTANTS
# =========================================================

VALID_ROLES = {
    "RN",
    "LVN",
    "LPN",
    "CHHA",
    "VOLUNTEER",
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
    "VOLUNTEER",
}

VALID_ACTIONS = {
    "DOCUMENT",
    "FINALIZE",
    "REVIEW",
}


# =========================================================
# NORMALIZATION
# =========================================================

def _normalize(value: str) -> str:
    return str(value).strip().upper()


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

    Rules:

    RN
        RN, NP, MD, Medical Director

    CHHA
        CHHA documents CHHA
        RN/LVN/LPN may also document

    Volunteer
        Volunteer documents volunteer

    Social Work
        SW documents SW

    Chaplain
        Chaplain documents Chaplain

    Physician
        MD/NP and Medical Director roles

    Finalization
        RN/NP/MD/Medical Director roles only
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
    # Validate visit type
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
    # RN
    # -----------------------------------------------------
    if visit_type == "RN":
        if user_role not in {
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only RN/NP/MD roles can document RN visits",
            )

    # -----------------------------------------------------
    # CHHA / AIDE
    # -----------------------------------------------------
    elif visit_type in {"CHHA", "AIDE"}:
        if user_role not in {
            "CHHA",
            "RN",
            "LVN",
            "LPN",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to document CHHA visits",
            )

    # -----------------------------------------------------
    # VOLUNTEER
    # -----------------------------------------------------
    elif visit_type == "VOLUNTEER":
        if user_role not in {
            "VOLUNTEER",
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to document volunteer visits",
            )

    # -----------------------------------------------------
    # SOCIAL WORK
    # -----------------------------------------------------
    elif visit_type == "SW":
        if user_role not in {
            "SW",
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to document social work visits",
            )

    # -----------------------------------------------------
    # CHAPLAIN
    # -----------------------------------------------------
    elif visit_type == "CHAPLAIN":
        if user_role != "CHAPLAIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only chaplain may document chaplain visits",
            )

    # -----------------------------------------------------
    # PHYSICIAN / NP
    # -----------------------------------------------------
    elif visit_type in {"MD", "NP"}:
        if user_role not in {
            "MD",
            "NP",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only physician roles may document MD/NP visits",
            )

    # -----------------------------------------------------
    # LVN
    # -----------------------------------------------------
    elif visit_type == "LVN":
        if user_role not in {
            "LVN",
            "LPN",
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to document LVN visits",
            )

    # -----------------------------------------------------
    # Finalization
    # -----------------------------------------------------
    if action == "FINALIZE":
        if user_role not in {
            "RN",
            "NP",
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to finalize clinical documentation",
            )

    return True