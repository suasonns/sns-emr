from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

_WS_RE = re.compile(r"\s+")


def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text safely for matching (non-destructive).
    """
    if text is None:
        return ""

    return _WS_RE.sub(" ", text.strip().lower())


# ---------------------------------------------------------
# DOSE NORMALIZATION (ENTERPRISE SAFE)
# ---------------------------------------------------------

_DOSE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(mcg|μg|ug|mg|g|gm|grams?|milligrams?)\s*$",
    re.IGNORECASE,
)

# Complex forms we should NEVER transform (clinical safety)
_COMPLEX_MARKERS = (
    "/",
    "ml",
    "patch",
    "%",
    "unit",
    "tab",
    "caps",
    "supp",
)


def normalize_dose(dose: Optional[str]) -> str:
    """
    Normalize mass-based medication doses to mg.

    Safety rules:
    - Do NOT normalize volume (ml), compound, or route-dependent doses
    - Preserve expressions like '5 mg/ml', '1 patch daily'
    - Fail-safe: return original if unsure
    """

    if not dose:
        return ""

    d = normalize_text(dose)

    # ---------------------------------------------------------
    # HARD STOP: preserve complex clinical expressions
    # ---------------------------------------------------------
    if any(marker in d for marker in _COMPLEX_MARKERS):
        return d

    m = _DOSE_RE.match(d)
    if not m:
        return d

    try:
        value = Decimal(m.group(1))
    except InvalidOperation:
        return d

    unit = m.group(2).lower()

    # ---------------------------------------------------------
    # UNIT NORMALIZATION → mg
    # ---------------------------------------------------------
    if unit in ("mg", "milligram", "milligrams"):
        mg = value
    elif unit in ("g", "gm", "gram", "grams"):
        mg = value * Decimal("1000")
    elif unit in ("mcg", "ug", "μg"):
        mg = value / Decimal("1000")
    else:
        return d

    # prevent scientific notation
    mg_str = format(mg.normalize(), "f")

    return f"{mg_str}mg"