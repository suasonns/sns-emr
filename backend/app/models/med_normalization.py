from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_WS_RE = re.compile(r"\s+")

_DOSE_RE = re.compile(
    r"^\s*(\d+(\.\d+)?)\s*(mcg|μg|ug|mg|g|gm|grams?|milligrams?)\s*$",
    re.IGNORECASE,
)

# Anything we NEVER normalize (clinical safety)
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


def normalize_text(val: str | None) -> str:
    """
    Normalize spacing only.
    DO NOT force lowercase globally (clinical abbreviations matter).
    """
    if val is None:
        return ""
    return _WS_RE.sub(" ", str(val).strip())


def normalize_dose(dose: str | None) -> str:
    """
    Normalize mass units ONLY (mg/g/mcg).
    Preserve all complex or structured medication instructions.

    Safety rules:
    - Do NOT normalize volume (mL), compound doses, or route-dependent formats
    - Do NOT alter PRN / BID / Q4H structures
    - Fail-safe: return original if unsure
    """
    if not dose:
        return ""

    d = normalize_text(dose).lower()

    # ---------------------------------------------------------
    # HARD STOP: DO NOT TOUCH COMPLEX EXPRESSIONS
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

    unit = m.group(3).lower()

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

    # ---------------------------------------------------------
    # SAFE STRING FORMAT (NO SCIENTIFIC NOTATION)
    # ---------------------------------------------------------
    mg_str = format(mg.normalize(), "f")

    return f"{mg_str}mg"
