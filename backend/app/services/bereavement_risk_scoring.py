# services/bereavement_risk_scoring.py

"""
Shared risk-item catalog and scoring logic for the Comprehensive Bereavement
Assessment. Kept separate from the API/model layer so the same catalog can
back the Post-Death Assessment reassessment later (chart-section-bereavement
follow-on work) without duplicating the item list.
"""

from __future__ import annotations

# Each entry: (key, points, label, requires_note)
# requires_note items surface a free-text box in the UI (e.g. "Other").
BEREAVEMENT_RISK_ITEMS: list[dict] = [
    {"key": "suicide_ideation", "points": 10, "label": "Suicide ideation/intent"},
    {
        "key": "children_adolescents_affected",
        "points": 5,
        "label": "Children or adolescents affected",
        "note_hint": "If yes, list names and ages in the narrative",
    },
    {"key": "substance_abuse", "points": 2, "label": "Possible alcohol/substance abuse"},
    {"key": "mental_health_history", "points": 2, "label": "History of mental health concerns"},
    {"key": "extreme_dependency", "points": 2, "label": "Extreme dependency"},
    {"key": "extreme_anger_guilt_fear", "points": 2, "label": "Extreme anger, guilt, or fear"},
    {"key": "ambivalent_conflicted_relationship", "points": 2, "label": "Ambivalent/conflicted relationship"},
    {"key": "family_violence_history", "points": 2, "label": "History of family violence"},
    {"key": "sense_of_hopelessness", "points": 2, "label": "Sense of hopelessness"},
    {"key": "estranged_isolated_support", "points": 2, "label": "Estranged/isolated from support system"},
    {"key": "inadequate_coping_skills", "points": 2, "label": "Inadequate coping skills"},
    {
        "key": "multiple_losses",
        "points": 2,
        "label": "Multiple losses",
        "note_hint": "List recent losses in the narrative",
    },
    {"key": "difficulty_coping_past_losses", "points": 2, "label": "Difficulty coping with past losses"},
    {"key": "traumatic_death_circumstances", "points": 2, "label": "Traumatic death circumstances"},
    {"key": "inadequate_financial_resources", "points": 2, "label": "Inadequate financial resources"},
    {"key": "preexisting_health_concerns", "points": 1, "label": "Pre-existing health concerns or change in health status"},
    {"key": "neglect_of_appearance", "points": 1, "label": "Neglect of appearance"},
    {"key": "exhaustion", "points": 1, "label": "Exhaustion"},
    {"key": "signs_of_spiritual_distress", "points": 1, "label": "Signs of spiritual distress"},
    {"key": "unprepared_for_death", "points": 1, "label": "Unprepared for death"},
    {"key": "anticipatory_grief", "points": 1, "label": "Anticipatory grief"},
    {"key": "legal_concerns", "points": 1, "label": "Legal concerns"},
    {"key": "other", "points": 1, "label": "Other", "requires_note": True},
]

_ITEM_POINTS = {item["key"]: item["points"] for item in BEREAVEMENT_RISK_ITEMS}
_HIGH_FORCING_KEYS = {item["key"] for item in BEREAVEMENT_RISK_ITEMS if item["points"] == 10}


def score_bereavement_risk(risk_items: dict) -> tuple[int, str]:
    """
    risk_items: {item_key: {"checked": bool, ...}}
    Returns (total_score, risk_level) where risk_level is LOW | MODERATE | HIGH.

    Any checked 10-point item (e.g. suicide ideation/intent) forces HIGH
    regardless of total, consistent with standard hospice bereavement risk
    policy that treats an active safety concern as high risk on its own.
    """
    total = 0
    forces_high = False
    for key, points in _ITEM_POINTS.items():
        entry = risk_items.get(key) or {}
        if entry.get("checked"):
            total += points
            if key in _HIGH_FORCING_KEYS:
                forces_high = True

    if forces_high or total >= 10:
        level = "HIGH"
    elif total >= 5:
        level = "MODERATE"
    else:
        level = "LOW"
    return total, level
