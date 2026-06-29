from __future__ import annotations

import re
from typing import Dict, Optional

from app.utils.drug_alias import normalize_drug_name
from app.utils.med_normalization import normalize_dose as base_normalize_dose
from app.utils.med_normalization import normalize_text


# =========================================================
# CANONICAL NORMALIZATION MAPS
# =========================================================

ROUTE_MAP = {
    "PO": "PO",
    "P.O.": "PO",
    "ORAL": "PO",
    "BY MOUTH": "PO",

    "IV": "IV",
    "I.V.": "IV",
    "INTRAVENOUS": "IV",

    "IM": "IM",
    "I.M.": "IM",
    "INTRAMUSCULAR": "IM",

    "SQ": "SQ",
    "SC": "SQ",
    "SUBQ": "SQ",
    "SUBCUT": "SQ",
    "SUBCUTANEOUS": "SQ",

    "SL": "SL",
    "SUBLINGUAL": "SL",

    "PR": "PR",
    "RECTAL": "PR",

    "TOPICAL": "TOPICAL",
    "TD": "TOPICAL",
    "TRANSDERMAL": "TOPICAL",

    "INHALATION": "INHALATION",
    "INH": "INHALATION",
    "NEB": "INHALATION",
    "NEBULIZED": "INHALATION",

    "GTUBE": "GTUBE",
    "G-TUBE": "GTUBE",
    "PEG": "GTUBE",
    "PEG TUBE": "GTUBE",

    "JTUBE": "JTUBE",
    "J-TUBE": "JTUBE",

    "BUCCAL": "BUCCAL",
    "VAGINAL": "VAGINAL",
}


FREQUENCY_DIRECT_MAP = {
    "DAILY": "DAILY",
    "QD": "DAILY",
    "QDAY": "DAILY",
    "EVERY DAY": "DAILY",

    "BID": "BID",
    "TWICE DAILY": "BID",

    "TID": "TID",
    "THREE TIMES DAILY": "TID",

    "QID": "QID",
    "FOUR TIMES DAILY": "QID",

    "HS": "HS",
    "QHS": "QHS",
    "AT BEDTIME": "QHS",
    "BEDTIME": "QHS",

    "PRN": "PRN",
    "AS NEEDED": "PRN",
}


# =========================================================
# BASE CLEANERS
# =========================================================

def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fallback_med_name_normalized(value: Optional[str]) -> Optional[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None

    normalized = cleaned.lower()
    normalized = normalized.replace(",", " ")
    normalized = normalized.replace("(", " ")
    normalized = normalized.replace(")", " ")
    normalized = normalized.replace("/", " / ")
    normalized = _compact_spaces(normalized)
    return normalized


# =========================================================
# MED NAME NORMALIZATION
# =========================================================

def _normalize_med_name(value: Optional[str]) -> Optional[str]:
    """
    Use existing alias-aware drug normalization first.
    Fall back to deterministic lowercase cleanup if alias utility
    returns nothing.
    """
    cleaned = _clean_text(value)
    if not cleaned:
        return None

    alias_normalized = normalize_drug_name(cleaned)
    if alias_normalized:
        return _compact_spaces(str(alias_normalized).lower())

    return _fallback_med_name_normalized(cleaned)


# =========================================================
# DOSE NORMALIZATION
# =========================================================

def _normalize_dose(dose: Optional[str], med_name_raw: Optional[str]) -> Optional[str]:
    """
    Normalize dose into compact canonical form such as:
      5mg
      10mg
      0.5mg
      1ml
      2tab
      15mcg

    Strategy:
    1) Use existing normalize_dose utility if it returns a value
    2) If missing, attempt extraction from med_name_raw
    """
    cleaned_dose = _clean_text(dose)

    if cleaned_dose:
        normalized = base_normalize_dose(cleaned_dose)
        if normalized:
            return _compact_spaces(str(normalized).lower())

    candidate = _clean_text(med_name_raw)
    if not candidate:
        return None

    text_value = candidate.lower().strip()

    dose_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|tabs?|tablets?|caps?|capsules?|drops?)\b",
        text_value,
    )
    if dose_match:
        value = dose_match.group(1)
        unit = dose_match.group(2)

        unit_map = {
            "tablet": "tab",
            "tablets": "tab",
            "tabs": "tab",
            "tab": "tab",
            "caps": "cap",
            "capsule": "cap",
            "capsules": "cap",
            "cap": "cap",
            "unit": "unit",
            "units": "unit",
            "drops": "drop",
            "drop": "drop",
        }

        unit = unit_map.get(unit, unit)
        return f"{value}{unit}"

    return None


# =========================================================
# ROUTE NORMALIZATION
# =========================================================

def _normalize_route(route: Optional[str]) -> Optional[str]:
    """
    Normalize route to canonical route codes:
      PO, IV, IM, SQ, SL, PR, TOPICAL, INHALATION, GTUBE, JTUBE, ...
    """
    cleaned = _clean_text(route)
    if not cleaned:
        return None

    normalized_input = normalize_text(cleaned) or cleaned
    upper_value = _compact_spaces(str(normalized_input).upper())

    # exact direct map first
    if upper_value in ROUTE_MAP:
        return ROUTE_MAP[upper_value]

    # fuzzy contains fallback
    for raw_key, normalized in ROUTE_MAP.items():
        if raw_key in upper_value:
            return normalized

    return upper_value


# =========================================================
# FREQUENCY NORMALIZATION
# =========================================================

def _normalize_frequency(frequency: Optional[str]) -> Optional[str]:
    """
    Normalize frequency to canonical values such as:
      DAILY, BID, TID, QID, QHS, PRN, Q4H, Q6H, Q8H, Q12H, Q2H PRN, etc.
    """
    cleaned = _clean_text(frequency)
    if not cleaned:
        return None

    normalized_input = normalize_text(cleaned) or cleaned
    upper_value = _compact_spaces(str(normalized_input).upper())

    # direct map
    if upper_value in FREQUENCY_DIRECT_MAP:
        return FREQUENCY_DIRECT_MAP[upper_value]

    # qxh patterns such as q4h, q6h, q8h, q12h
    qh_match = re.search(r"\bQ\s*(\d{1,2})\s*H\b", upper_value)
    if qh_match:
        normalized = f"Q{qh_match.group(1)}H"
        if "PRN" in upper_value or "AS NEEDED" in upper_value:
            return f"{normalized} PRN"
        return normalized

    # every x hours
    every_hours_match = re.search(r"\bEVERY\s+(\d{1,2})\s+HOURS?\b", upper_value)
    if every_hours_match:
        normalized = f"Q{every_hours_match.group(1)}H"
        if "PRN" in upper_value or "AS NEEDED" in upper_value:
            return f"{normalized} PRN"
        return normalized

    # every x days
    every_days_match = re.search(r"\bEVERY\s+(\d{1,2})\s+DAYS?\b", upper_value)
    if every_days_match:
        normalized = f"Q{every_days_match.group(1)}D"
        if "PRN" in upper_value or "AS NEEDED" in upper_value:
            return f"{normalized} PRN"
        return normalized

    # preserve PRN wording if present in otherwise unknown pattern
    if "PRN" in upper_value and upper_value != "PRN":
        return upper_value.replace("AS NEEDED", "PRN")

    return upper_value


# =========================================================
# PUBLIC ENTRYPOINT
# =========================================================

def normalize_med_reconciliation_item(
    *,
    med_name_raw: Optional[str],
    dose: Optional[str],
    route: Optional[str],
    frequency: Optional[str],
) -> Dict[str, Optional[str]]:
    """
    Deterministic normalization for imported medication reconciliation rows.

    Rules:
    - Preserve raw source data separately
    - Do not infer route/frequency if not supplied
    - Normalize fields for safe comparison / dedup / storage
    - Return normalized fields for DB signature-based matching
    """
    med_name_normalized = _normalize_med_name(med_name_raw)
    dose_normalized = _normalize_dose(dose, med_name_raw)
    route_normalized = _normalize_route(route)
    frequency_normalized = _normalize_frequency(frequency)

    return {
        "med_name_normalized": med_name_normalized,
        "dose_normalized": dose_normalized,
        "route_normalized": route_normalized,
        "frequency_normalized": frequency_normalized,
    }