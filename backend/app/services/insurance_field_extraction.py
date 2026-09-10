"""Generic insurance-field candidate extraction from raw document text.

This is a harvesting mechanism only -- per docs/architecture/
InsuranceMappingReconciliation.md and docs/workflows/SourceOfTruthMatrix.md,
OCR/extraction owns nothing. It produces CANDIDATE values only; a human
must accept them (via app/api/field_suggestions.py) before they ever
reach PatientFaceSheet, the sole source of truth for insurance data.

Deliberately NOT named/scoped as "HNP OCR" -- this operates on raw
extracted text from any document processing pathway (currently wired
into the H&P ingestion path in app/api/patients.py, since that is
presently the only pipeline stage that has raw extracted text available;
any future document-processing stage can call this same function with
its own extracted text without introducing a second extraction/queue
implementation).

Extraction here is intentionally permissive/heuristic (regex-based
pattern matching) since every result is routed through staff review
before it can affect any record -- false positives are an acceptable
review-queue cost; false silent writes are not possible because there is
no auto-write path (WARN-mode auto_applied behavior is opt-in per tenant,
same policy as demographic fields, and staff can always reject or fix
the suggestion).
"""

from __future__ import annotations

import re

# CMS Medicare Beneficiary Identifier (MBI) format: 11 characters,
# positions 1/4/7/10 are digits 1-9, positions 2/3/5/6/8/9 are letters
# (excluding easily-confused B/I/L/O/S/Z) or digits, position 11 is a
# digit 0-9. This is a heuristic candidate matcher, not a validator --
# see module docstring.
_MBI_PATTERN = re.compile(
    r"\b([1-9][AC-HJ-KM-NP-RT-Y][AC-HJ-KM-NP-RT-Y0-9][0-9]"
    r"[AC-HJ-KM-NP-RT-Y][AC-HJ-KM-NP-RT-Y0-9][0-9]"
    r"[AC-HJ-KM-NP-RT-Y][AC-HJ-KM-NP-RT-Y][0-9]{2})\b"
)

_POLICY_NUMBER_PATTERN = re.compile(
    r"(?:policy\s*(?:number|#|no\.?)|member\s*id)\s*[:#]?\s*([A-Za-z0-9-]{5,20})",
    re.IGNORECASE,
)

# A small, extensible set of common payer names to match against free
# text. Not exhaustive -- staff review handles anything this misses; this
# is a candidate signal, not an authoritative payer directory.
_KNOWN_PAYER_NAMES = [
    "Medicare",
    "Medicaid",
    "Aetna",
    "Cigna",
    "Humana",
    "UnitedHealthcare",
    "United Healthcare",
    "Anthem",
    "Blue Cross",
    "Blue Shield",
    "Kaiser Permanente",
    "Molina Healthcare",
    "WellCare",
    "Tricare",
]


def extract_insurance_candidates(text: str) -> dict[str, str]:
    """Return a dict of candidate insurance field values found in `text`.

    Keys, when present, are a subset of: mbi_number, primary_policy_number,
    primary_payer. Returns an empty dict if nothing is found. Never
    raises on unparseable/empty text.
    """
    if not text:
        return {}

    candidates: dict[str, str] = {}

    mbi_match = _MBI_PATTERN.search(text)
    if mbi_match:
        candidates["mbi_number"] = mbi_match.group(1)

    policy_match = _POLICY_NUMBER_PATTERN.search(text)
    if policy_match:
        candidates["primary_policy_number"] = policy_match.group(1)

    for payer_name in _KNOWN_PAYER_NAMES:
        if re.search(re.escape(payer_name), text, re.IGNORECASE):
            candidates["primary_payer"] = payer_name
            break

    return candidates
