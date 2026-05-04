import re
from decimal import Decimal, InvalidOperation

_WS_RE = re.compile(r"\s+")

_DOSE_RE = re.compile(
    r"^\s*(\d+(\.\d+)?)\s*(mcg|μg|ug|mg|g|gm)\s*$",
    re.IGNORECASE,
)

def normalize_text(val: str) -> str:
    return _WS_RE.sub(" ", (val or "").strip().lower())

def normalize_dose(dose: str) -> str:
    """
    Normalize mass units ONLY (mg/g/mcg).
    mL, patches, mg/mL, etc are left untouched
    to protect hospice comfort‑kit ladders.
    """
    d = normalize_text(dose)
    if not d:
        return ""

    # Do NOT normalize volume-based or compound doses
    if "/" in d or "ml" in d or "patch" in d:
        return d

    m = _DOSE_RE.match(d)
    if not m:
        return d

    try:
        value = Decimal(m.group(1))
    except InvalidOperation:
        return d

    unit = m.group(3).lower()
    if unit == "mg":
        mg = value
    elif unit in ("g", "gm"):
        mg = value * Decimal("1000")
    elif unit in ("mcg", "ug", "μg"):
        mg = value / Decimal("1000")
    else:
        return d

    return f"{mg.normalize()}mg"