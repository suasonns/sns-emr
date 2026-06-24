from __future__ import annotations

from typing import Any, Dict

from app.domain.care_model_engine import determine_care_model


def _safe_enum_value(enum_obj: Any, default: str = "UNKNOWN") -> str:
    """
    Safely extract value from enum-like objects.

    Prevents runtime failures when:
    - enum is None
    - object is not an enum
    - value attribute is missing

    Returns:
        string value or fallback default
    """
    if enum_obj is None:
        return default

    return getattr(enum_obj, "value", str(enum_obj))


def get_patient_care_model(patient) -> Dict[str, Any]:
    """
    Enterprise-safe care model resolver.

    Purpose:
    - Normalize domain decision output
    - Provide stable API contract
    - Prevent runtime failures
    - Enforce Phase 1 POC policy alignment

    Important Phase 1 rule:
    - This layer must not propagate legacy drift such as:
        "any RN visit anchors POC"
    - Actual POC scheduling is enforced in automation layer
    """

    decision = determine_care_model(
        has_chha=bool(getattr(patient, "has_chha", False)),
        has_lvn=bool(getattr(patient, "has_lvn", False)),
        has_wounds=bool(getattr(patient, "has_wounds", False)),
        acuity_state=getattr(patient, "acuity_state", None),
    )

    if decision is None:
        return {
            "care_model": "UNKNOWN",
            "supervisory_required": False,
            "poc_trigger_policy": "UNKNOWN",
            "poc_due_days": 14,
            "has_support_staff": False,
            "has_wounds": False,
            "acuity_state": "ROUTINE",
            "reason": "care model decision unavailable",
        }

    # ---------------------------------------------------------
    # Normalize all outputs safely
    # ---------------------------------------------------------
    care_model = _safe_enum_value(decision.care_model)
    poc_trigger_policy = _safe_enum_value(decision.poc_trigger_policy)
    acuity_state = _safe_enum_value(decision.acuity_state, "ROUTINE")

    # ---------------------------------------------------------
    # Phase 1 Enforcement (Presentation Layer)
    # ---------------------------------------------------------
    # Even if domain says "any RN visit anchors",
    # we DO NOT expose that behavior as authoritative.
    #
    # Final authority = poc_update_automation layer
    #
    # Here we normalize messaging only.
    # ---------------------------------------------------------
    if poc_trigger_policy.upper() in ("ANY_RN", "ANY_RN_VISIT"):
        poc_trigger_policy = "SUPERVISORY_RN_REQUIRED_FOR_PERIODIC"

    return {
        "care_model": care_model,
        "supervisory_required": bool(getattr(decision, "supervisory_required", False)),
        "poc_trigger_policy": poc_trigger_policy,
        "poc_due_days": int(getattr(decision, "poc_due_days", 14) or 14),
        "has_support_staff": bool(getattr(decision, "has_support_staff", False)),
        "has_wounds": bool(getattr(decision, "has_wounds", False)),
        "acuity_state": acuity_state,
        "reason": str(getattr(decision, "reason", "") or ""),
    }
