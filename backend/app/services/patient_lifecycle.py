# app/services/patient_lifecycle.py

ALLOWED_PATIENT_TRANSITIONS = {
    "ACTIVE": {"DISCHARGED", "DECEASED"},
    "DISCHARGED": set(),
    "DECEASED": set(),
}


def validate_patient_transition(old_status: str, new_status: str) -> None:
    """
    Enforce legal patient lifecycle transitions.

    Allowed:
      ACTIVE -> DISCHARGED
      ACTIVE -> DECEASED

    Blocked:
      DISCHARGED -> *
      DECEASED -> *
    """
    # Allow no-op updates
    if old_status == new_status:
        return

    allowed = ALLOWED_PATIENT_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Illegal patient status transition: {old_status} → {new_status}"
        )