from __future__ import annotations

from typing import Dict, Set


# =========================================================
# 🔴 TASK → REQUIRED FORM RULES
# =========================================================

TASK_REQUIRED_FORMS: Dict[str, Set[str]] = {

    # RN CLINICAL TASKS
    "RN_ASSESSMENT": {
        "HOPE_ADMISSION",
        "COMPREHENSIVE_ASSESSMENT",
    },

    "FALL_RISK": {
        "FALL_RISK_ASSESSMENT",
    },

    "PAIN_ASSESSMENT": {
        "PAIN_ASSESSMENT",
    },

    "SKIN_CHECK": {
        "SKIN_ASSESSMENT",
    },

    "SAFETY_CHECK": {
        "SAFETY_ASSESSMENT",
    },

    # MSW / SOCIAL WORK
    "PSYCHOSOCIAL_VISIT": {
        "PSYCHOSOCIAL_ASSESSMENT",
        "PSYCHOSOCIAL_VISIT_NOTE",
    },

    # CHAPLAIN
    "SPIRITUAL_VISIT": {
        "SPIRITUAL_ASSESSMENT",
        "SPIRITUAL_VISIT_NOTE",
    }
}