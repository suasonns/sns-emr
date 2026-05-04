# app/utils/med_normalization.py

"""
Medication normalization utilities.

Compliance notes:
- Deterministic formatting only
- No clinical inference (no route/frequency assumptions)
- No database access
- Safe for MAR/POC/IDG reconciliation matching
"""

from __future__ import annotations
import re
from typing import Optional, Tuple


_whitespace_re = re.compile(r"\s+")
# Matches common dose formats: 5 mg, 0.5mg, 10 mcg, 1 g, 650mg, etc.
_dose_re = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>mcg|ug|mg|g|ml|mL|units|unit|iu|IU)\b",
    flags=re.IGNORECASE,
)

def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Normalize free-text medication strings for matching:
    - strip
    - lowercase
    - collapse whitespace
    - keep punctuation (do not alter clinical meaning)
    """
    if text is None:
        return None
    cleaned = text.strip().lower()
    cleaned = _whitespace_re.sub(" ", cleaned)
    return cleaned


def normalize_dose(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract a normalized (value, unit) dose from a med string.

    Returns:
        (value, unit) where:
        - value is a string number like "5" or "0.5"
        - unit is normalized to lowercase: "mg", "mcg", "g", "ml", "units", "iu"
    If no dose found, returns (None, None)

    This is extraction-only; it does NOT convert units (e.g., mcg->mg).
    """
    if not text:
        return (None, None)

    m = _dose_re.search(text)
    if not m:
        return (None, None)

    value = m.group("value")
    unit = m.group("unit").lower()

    # Normalize some equivalent unit spellings
    if unit == "ug":
        unit = "mcg"
    if unit == "unit":
        unit = "units"

    return (value, unit)