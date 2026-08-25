# services/bereavement_poc_catalog.py

"""
Risk-tiered goal/intervention catalog and 13-month action-plan generator for
the Bereavement Plan of Care (see chart-section-bereavement-poc and
models/bereavement_poc.py).

The 13-month contact schedule mirrors standard hospice bereavement program
practice under CMS COPs 418.64(d), which requires bereavement services be
available to the family for at least 13 months following the patient's
death. Higher risk levels get additional early touchpoints layered on top of
the same baseline schedule, rather than a different schedule entirely, so a
POC that's later re-leveled keeps its existing completed contacts intact.
"""

from __future__ import annotations

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Goals & interventions catalog, keyed by risk level. Each entry starts
# unselected in the UI except where noted; the clinician tailors the plan to
# the individual bereaved from this starting point.
# ---------------------------------------------------------------------------
BEREAVEMENT_POC_GOALS: dict[str, list[dict]] = {
    "LOW": [
        {"key": "receive_standard_support", "label": "Bereaved will receive standard bereavement mailings and support materials"},
        {"key": "aware_of_resources", "label": "Bereaved will be aware of community grief resources and support groups"},
    ],
    "MODERATE": [
        {"key": "receive_standard_support", "label": "Bereaved will receive standard bereavement mailings and support materials"},
        {"key": "identify_coping_strategies", "label": "Bereaved will identify and utilize healthy coping strategies"},
        {"key": "maintain_support_engagement", "label": "Bereaved will remain engaged with family/social support system"},
    ],
    "HIGH": [
        {"key": "remain_safe", "label": "Bereaved will remain safe and free from harm"},
        {"key": "engage_professional_support", "label": "Bereaved will engage with professional counseling/mental health support"},
        {"key": "identify_coping_strategies", "label": "Bereaved will identify and utilize healthy coping strategies"},
        {"key": "maintain_support_engagement", "label": "Bereaved will remain engaged with family/social support system"},
    ],
}

BEREAVEMENT_POC_INTERVENTIONS: dict[str, list[dict]] = {
    "LOW": [
        {"key": "sympathy_card", "label": "Post-death sympathy card"},
        {"key": "post_death_assessment", "label": "Post-death bereavement assessment"},
        {"key": "mail_bereavement_letters", "label": "Provide standard post-death bereavement mailings"},
        {"key": "encourage_grief_expression", "label": "Encourage/support expression of grief"},
        {"key": "provide_resource_list", "label": "Provide community grief support and counseling resource list"},
    ],
    "MODERATE": [
        {"key": "sympathy_card", "label": "Post-death sympathy card"},
        {"key": "post_death_assessment", "label": "Post-death bereavement assessment"},
        {"key": "mail_bereavement_letters", "label": "Provide standard post-death bereavement mailings"},
        {"key": "encourage_grief_expression", "label": "Encourage/support expression of grief"},
        {"key": "increased_phone_contact", "label": "Increase phone contact frequency beyond standard schedule"},
        {"key": "offer_counseling_referral", "label": "Offer referral to grief counseling or support group"},
        {"key": "monitor_risk_factors", "label": "Monitor for escalating risk factors at each contact"},
    ],
    "HIGH": [
        {"key": "sympathy_card", "label": "Post-death sympathy card"},
        {"key": "immediate_followup_48h", "label": "Immediate chaplain/counselor follow-up within 48 hours"},
        {"key": "safety_assessment", "label": "Conduct safety assessment at each contact"},
        {"key": "refer_crisis_resources", "label": "Refer to community mental health/crisis resources"},
        {"key": "weekly_contact_first_month", "label": "Weekly contact for the first 4 weeks"},
        {"key": "notify_idg", "label": "Notify IDG of high-risk bereavement status"},
        {"key": "offer_counseling_referral", "label": "Offer referral to grief counseling or support group"},
        {"key": "encourage_grief_expression", "label": "Encourage/support expression of grief"},
    ],
}


def default_goals_for_risk(risk_level: str | None) -> list[dict]:
    catalog = BEREAVEMENT_POC_GOALS.get((risk_level or "LOW").upper(), BEREAVEMENT_POC_GOALS["LOW"])
    return [
        {"key": item["key"], "label": item["label"], "selected": True, "target_date": None, "notes": None}
        for item in catalog
    ]


def default_interventions_for_risk(risk_level: str | None) -> list[dict]:
    catalog = BEREAVEMENT_POC_INTERVENTIONS.get((risk_level or "LOW").upper(), BEREAVEMENT_POC_INTERVENTIONS["LOW"])
    return [{"key": item["key"], "label": item["label"], "selected": True, "notes": None} for item in catalog]


# ---------------------------------------------------------------------------
# 13-month action plan (baseline touchpoint schedule + high-risk extras +
# clinician-optional touchpoints)
# ---------------------------------------------------------------------------
# (month offset in days from date of death, label, default contact type)
# Standard schedule is mailed letters/cards (matches real-world hospice
# bereavement-letter practice); phone/visit contacts are reserved for
# higher-risk or clinician-added touchpoints.
_BASELINE_TOUCHPOINTS: list[tuple[int, str, str]] = [
    (7, "Initial contact / sympathy card", "LETTER"),
    (30, "1 month contact", "LETTER"),
    (90, "3 month contact", "LETTER"),
    (180, "6 month contact", "LETTER"),
    (270, "9 month contact", "LETTER"),
    (365, "12 month contact", "LETTER"),
    (395, "13 month closure contact", "LETTER"),
]

# Extra early touchpoints layered on for HIGH risk, per bereavement_poc_catalog
# HIGH-risk intervention set (weekly contact for the first 4 weeks). These are
# always required/included -- risk is already elevated.
_HIGH_RISK_EXTRA_TOUCHPOINTS: list[tuple[int, str, str]] = [
    (2, "High-risk follow-up (48 hours)", "PHONE"),
    (14, "Weekly check-in", "PHONE"),
    (21, "Weekly check-in", "PHONE"),
]

# Optional, clinician-opt-in touchpoints available at any risk level (unchecked
# by default, matching standard hospice bereavement POC forms which offer
# these as available-but-not-required contacts). A clinician toggles
# `included` on in the UI to activate one for a specific family.
_OPTIONAL_TOUCHPOINTS: list[tuple[int, str, str]] = [
    (14, "Condolence call (optional)", "PHONE"),
    (60, "2 month check-in call (optional)", "PHONE"),
    (240, "8 month volunteer/staff call (optional)", "PHONE"),
]


def default_action_plan(risk_level: str | None, date_of_death: date | None) -> list[dict]:
    """
    Build the default 13-month contact schedule: required baseline
    touchpoints (+ extra required touchpoints for HIGH risk) plus optional,
    clinician-opt-in touchpoints available at any risk level. planned_date is
    computed from date_of_death when available; otherwise left null so the
    clinician fills in dates once the date of death is known.
    """
    required = list(_BASELINE_TOUCHPOINTS)
    if (risk_level or "").upper() == "HIGH":
        required = _HIGH_RISK_EXTRA_TOUCHPOINTS + required

    entries = [(offset, label, contact_type, True, True) for offset, label, contact_type in required]
    entries += [(offset, label, contact_type, False, False) for offset, label, contact_type in _OPTIONAL_TOUCHPOINTS]
    entries.sort(key=lambda e: e[0])

    plan = []
    for offset_days, label, contact_type, required_flag, included_flag in entries:
        planned_date = (date_of_death + timedelta(days=offset_days)) if date_of_death else None
        plan.append(
            {
                "month_offset_days": offset_days,
                "label": label,
                "contact_type": contact_type,
                "required": required_flag,
                "included": included_flag,
                "planned_date": planned_date.isoformat() if planned_date else None,
                "completed_date": None,
                "completed_by": None,
                "notes": None,
            }
        )
    return plan
