from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# =========================================================
# RESULT MODEL
# =========================================================

@dataclass
class MedComparisonResult:
    match_type: str
    discrepancy_flags: List[str]
    existing_medication_id: Optional[Any]
    review_reason: Optional[str]
    imported_dose_normalized: Optional[str]
    imported_route_normalized: Optional[str]
    imported_frequency_normalized: Optional[str]


# =========================================================
# HELPERS
# =========================================================

def _clean(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm(value: Optional[Any]) -> Optional[str]:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    return " ".join(cleaned.lower().split())


def _same(a: Optional[Any], b: Optional[Any]) -> bool:
    """
    Compare two values after normalization.
    """
    return _norm(a) == _norm(b)


def _is_present(value: Optional[Any]) -> bool:
    return _clean(value) is not None


def _best_name_value(existing_med: Dict[str, Any]) -> Optional[str]:
    """
    Prefer canonical_name, then medication_name.
    """
    return (
        existing_med.get("canonical_name")
        or existing_med.get("medication_name")
    )


def _name_matches(imported_name: Optional[str], existing_med: Dict[str, Any]) -> bool:
    imported = _norm(imported_name)
    if imported is None:
        return False

    existing_canonical = _norm(existing_med.get("canonical_name"))
    existing_med_name = _norm(existing_med.get("medication_name"))

    return imported in {existing_canonical, existing_med_name}


def _field_match_score(imported_item: Dict[str, Any], existing_med: Dict[str, Any]) -> int:
    """
    Count how many structured normalized fields match.
    """
    score = 0

    if _same(imported_item.get("dose_normalized"), existing_med.get("dose_normalized")):
        score += 1
    if _same(imported_item.get("route_normalized"), existing_med.get("route_normalized")):
        score += 1
    if _same(imported_item.get("frequency_normalized"), existing_med.get("frequency_normalized")):
        score += 1

    return score


def _discrepancy_flags(imported_item: Dict[str, Any], existing_med: Dict[str, Any]) -> List[str]:
    flags: List[str] = []

    if not _same(imported_item.get("dose_normalized"), existing_med.get("dose_normalized")):
        flags.append("DOSE_MISMATCH")

    if not _same(imported_item.get("route_normalized"), existing_med.get("route_normalized")):
        flags.append("ROUTE_MISMATCH")

    if not _same(imported_item.get("frequency_normalized"), existing_med.get("frequency_normalized")):
        flags.append("FREQUENCY_MISMATCH")

    return flags


def _review_reason_from_flags(flags: List[str]) -> Optional[str]:
    if not flags:
        return None

    if flags == ["DOSE_MISMATCH"]:
        return "Imported medication name matches active list, but dose differs"
    if flags == ["ROUTE_MISMATCH"]:
        return "Imported medication name matches active list, but route differs"
    if flags == ["FREQUENCY_MISMATCH"]:
        return "Imported medication name matches active list, but frequency differs"

    return "Imported medication partially matches active list, but structured fields differ"


# =========================================================
# MAIN COMPARISON
# =========================================================

def compare_imported_item_against_med_list(
    *,
    imported_item: Dict[str, Any],
    existing_medications: List[Dict[str, Any]],
) -> MedComparisonResult:
    """
    Compare one imported medication reconciliation row against active medications.

    Comparison priorities:
    1) Match by normalized medication identity first
    2) Then prioritize structured normalized fields:
       - dose_normalized
       - route_normalized
       - frequency_normalized
    3) Return explicit discrepancy flags instead of generic med-name-only matches

    Expected imported_item keys:
      - med_name_raw
      - med_name_normalized
      - dose
      - dose_normalized
      - route_normalized
      - frequency_normalized

    Expected existing_medications keys (where available):
      - id
      - medication_name
      - canonical_name
      - dose_normalized
      - route_normalized
      - frequency_normalized
    """

    imported_name = imported_item.get("med_name_normalized") or imported_item.get("med_name_raw")
    imported_dose_normalized = imported_item.get("dose_normalized")
    imported_route_normalized = imported_item.get("route_normalized")
    imported_frequency_normalized = imported_item.get("frequency_normalized")

    # ---------------------------------------------------------
    # 1) Find name-matching candidates
    # ---------------------------------------------------------
    name_candidates = [
        med for med in existing_medications
        if _name_matches(imported_name, med)
    ]

    if not name_candidates:
        return MedComparisonResult(
            match_type="NO_MATCH",
            discrepancy_flags=[],
            existing_medication_id=None,
            review_reason="Imported medication not found in active medication list",
            imported_dose_normalized=imported_dose_normalized,
            imported_route_normalized=imported_route_normalized,
            imported_frequency_normalized=imported_frequency_normalized,
        )

    # ---------------------------------------------------------
    # 2) Look for exact structured match
    # ---------------------------------------------------------
    for med in name_candidates:
        dose_match = _same(imported_dose_normalized, med.get("dose_normalized"))
        route_match = _same(imported_route_normalized, med.get("route_normalized"))
        frequency_match = _same(imported_frequency_normalized, med.get("frequency_normalized"))

        if dose_match and route_match and frequency_match:
            return MedComparisonResult(
                match_type="EXACT_NORMALIZED_MATCH",
                discrepancy_flags=[],
                existing_medication_id=med.get("id"),
                review_reason=None,
                imported_dose_normalized=imported_dose_normalized,
                imported_route_normalized=imported_route_normalized,
                imported_frequency_normalized=imported_frequency_normalized,
            )

    # ---------------------------------------------------------
    # 3) Choose best partial candidate by structured field score
    # ---------------------------------------------------------
    best_candidate = max(
        name_candidates,
        key=lambda med: _field_match_score(imported_item, med),
    )

    flags = _discrepancy_flags(imported_item, best_candidate)
    score = _field_match_score(imported_item, best_candidate)

    if score == 0:
        match_type = "NAME_ONLY_MATCH"
    else:
        match_type = "PARTIAL_MATCH"

    return MedComparisonResult(
        match_type=match_type,
        discrepancy_flags=flags,
        existing_medication_id=best_candidate.get("id"),
        review_reason=_review_reason_from_flags(flags),
        imported_dose_normalized=imported_dose_normalized,
        imported_route_normalized=imported_route_normalized,
        imported_frequency_normalized=imported_frequency_normalized,
    )