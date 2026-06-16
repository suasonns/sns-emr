from __future__ import annotations

from app.domain.care_model_engine import determine_care_model


def get_patient_care_model(patient) -> dict:
    decision = determine_care_model(
        has_chha=bool(getattr(patient, "has_chha", False)),
        has_lvn=bool(getattr(patient, "has_lvn", False)),
        has_wounds=bool(getattr(patient, "has_wounds", False)),
        acuity_state=getattr(patient, "acuity_state", None),
    )

    return {
        "care_model": decision.care_model.value,
        "supervisory_required": decision.supervisory_required,
        "poc_trigger_policy": decision.poc_trigger_policy.value,
        "poc_due_days": decision.poc_due_days,
        "has_support_staff": decision.has_support_staff,
        "has_wounds": decision.has_wounds,
        "acuity_state": decision.acuity_state.value,
        "reason": decision.reason,
    }