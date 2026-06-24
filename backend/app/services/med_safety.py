from __future__ import annotations

from typing import Optional

from app.models.med_reconciliation import MedReconciliationItem


# =========================================================
# CONSTANTS — HIGH RISK DEFINITIONS
# =========================================================

HIGH_RISK_DRUGS = {
    "insulin": "HYPOGLYCEMIA",
    "morphine": "RESPIRATORY_DEPRESSION",
    "hydromorphone": "RESPIRATORY_DEPRESSION",
    "fentanyl": "RESPIRATORY_DEPRESSION",
    "potassium": "ARRHYTHMIA",
    "zoledronic acid": "RENAL_RISK",
    "clonidine": "HYPOTENSION",
    "hydralazine": "HYPOTENSION",
    "labetalol": "HYPOTENSION",
}

CRITICAL_REACTIONS = [
    "anaphylaxis",
    "airway swelling",
    "respiratory depression",
    "cardiac arrest",
    "coma",
]


# =========================================================
# SAFETY ENGINE
# =========================================================

def evaluate_medication_safety(
    item: MedReconciliationItem,
) -> MedReconciliationItem:
    """
    Evaluate medication risk.

    IMPORTANT:
    - NEVER blocks medication insertion
    - ONLY flags + escalates for review
    - ALWAYS deterministic (survey-safe)
    """

    # ✅ Normalize inputs
    med_name = (item.med_name_raw or "").lower()
    reaction = (item.reaction_description or "").lower()
    severity = (item.severity or "").upper()

    # ✅ Reset flags to avoid stale values
    item.requires_immediate_review = False
    item.is_critical_reaction = False

    # -----------------------------------------------------
    # HIGH-RISK DRUG DETECTION
    # -----------------------------------------------------
    for drug, risk in HIGH_RISK_DRUGS.items():
        if drug in med_name:
            item.requires_immediate_review = True

            if hasattr(item, "safety_risk_category"):
                item.safety_risk_category = risk

            if hasattr(item, "safety_trigger_reason"):
                item.safety_trigger_reason = f"High-risk drug detected: {drug}"

            break

    # -----------------------------------------------------
    # CRITICAL REACTION DETECTION
    # -----------------------------------------------------
    for crit in CRITICAL_REACTIONS:
        if crit in reaction:
            item.is_critical_reaction = True
            item.requires_immediate_review = True

            if hasattr(item, "safety_trigger_reason"):
                item.safety_trigger_reason = f"Critical reaction detected: {crit}"

            break

    # -----------------------------------------------------
    # SEVERITY ESCALATION
    # -----------------------------------------------------
    if severity == "SEVERE":
        item.is_critical_reaction = True
        item.requires_immediate_review = True

        if hasattr(item, "safety_trigger_reason"):
            item.safety_trigger_reason = "Severity marked as SEVERE"

    return item