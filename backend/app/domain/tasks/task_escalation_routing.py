# =========================================================
# ESCALATION ROUTING RULES
# =========================================================

ESCALATION_ROUTING = {
    "CRITICAL": {
        1: {"role": "RN", "notify": True},
        2: {"role": "SUPERVISOR", "notify": True},
        3: {"role": "DPCS", "notify": True},
    },
    "HIGH": {
        1: {"role": "RN", "notify": True},
        2: {"role": "SUPERVISOR", "notify": True},
    },
    "MEDIUM": {
        1: {"role": "RN", "notify": True},
    },
}