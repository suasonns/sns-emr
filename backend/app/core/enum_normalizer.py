def normalize_level_of_care(raw: str | None) -> str | None:
    if not raw:
        return None

    value = raw.strip().upper()

    mapping = {
        # ✅ CMS → INTERNAL
        "ROUTINE_HOME_CARE": "RC",
        "CONTINUOUS_HOME_CARE": "CC",
        "GENERAL_INPATIENT": "IP",
        "INPATIENT_RESPITE": "RSP",

        # ✅ variations
        "ROUTINE": "RC",
        "CONTINUOUS": "CC",
        "GIP": "IP",
        "RESPITE": "RSP",
    }

    return mapping.get(value, value)