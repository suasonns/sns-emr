from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# =========================================================
# RESULT MODEL
# =========================================================

@dataclass
class MedComparisonResult:
    match_type: str
    matched: bool
    requires_review: bool
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

    if not text:
        return None

    return text


def _norm(value: Optional[Any]) -> Optional[str]:
    cleaned = _clean(value)

    if cleaned is None:
        return None

    return " ".join(
        cleaned.lower().split()
    )


def _same(
    a: Optional[Any],
    b: Optional[Any],
) -> bool:
    return _norm(a) == _norm(b)


def _name_matches(
    imported_name: Optional[str],
    existing_medication: Dict[str, Any],
) -> bool:
    imported = _norm(imported_name)

    if imported is None:
        return False

    existing_canonical = _norm(
        existing_medication.get("canonical_name")
    )

    existing_med_name = _norm(
        existing_medication.get("medication_name")
    )

    return imported in {
        existing_canonical,
        existing_med_name,
    }


def _field_match_score(
    imported_item: Dict[str, Any],
    existing_medication: Dict[str, Any],
) -> int:
    score = 0

    if _same(
        imported_item.get("dose_normalized"),
        existing_medication.get("dose_normalized"),
    ):
        score += 1

    if _same(
        imported_item.get("route_normalized"),
        existing_medication.get("route_normalized"),
    ):
        score += 1

    if _same(
        imported_item.get("frequency_normalized"),
        existing_medication.get("frequency_normalized"),
    ):
        score += 1

    return score


def _discrepancy_flags(
    imported_item: Dict[str, Any],
    existing_medication: Dict[str, Any],
) -> List[str]:
    flags: List[str] = []

    if not _same(
        imported_item.get("dose_normalized"),
        existing_medication.get("dose_normalized"),
    ):
        flags.append("DOSE_MISMATCH")

    if not _same(
        imported_item.get("route_normalized"),
        existing_medication.get("route_normalized"),
    ):
        flags.append("ROUTE_MISMATCH")

    if not _same(
        imported_item.get("frequency_normalized"),
        existing_medication.get("frequency_normalized"),
    ):
        flags.append("FREQUENCY_MISMATCH")

    return flags


def _review_reason_from_flags(
    flags: List[str],
) -> Optional[str]:
    if not flags:
        return None

    if flags == ["DOSE_MISMATCH"]:
        return (
            "Imported medication name matches active list, "
            "but dose differs"
        )

    if flags == ["ROUTE_MISMATCH"]:
        return (
            "Imported medication name matches active list, "
            "but route differs"
        )

    if flags == ["FREQUENCY_MISMATCH"]:
        return (
            "Imported medication name matches active list, "
            "but frequency differs"
        )

    return (
        "Imported medication partially matches active list, "
        "but structured fields differ"
    )


def _imported_name(
    imported_item: Dict[str, Any],
) -> Optional[str]:
    return (
        imported_item.get("med_name_normalized")
        or imported_item.get("med_name_raw")
    )


# =========================================================
# SINGLE MEDICATION COMPARISON
# =========================================================

def compare_imported_medication_to_existing(
    *,
    imported_item: Dict[str, Any],
    existing_medication: Dict[str, Any],
) -> MedComparisonResult:
    """
    Compare one imported medication row against one existing medication.

    Backward-compatible public function expected by legacy tests.

    Match behavior:
    - Exact name + dose + route + frequency match:
        EXACT_NORMALIZED_MATCH
    - Name match but dose/route/frequency discrepancy:
        PARTIAL_MATCH_WITH_DISCREPANCY
    - Name does not match:
        NO_MATCH_IN_ACTIVE_MED_LIST
    """

    imported_name = _imported_name(
        imported_item
    )

    imported_dose_normalized = imported_item.get(
        "dose_normalized"
    )

    imported_route_normalized = imported_item.get(
        "route_normalized"
    )

    imported_frequency_normalized = imported_item.get(
        "frequency_normalized"
    )

    if not _name_matches(
        imported_name,
        existing_medication,
    ):
        return MedComparisonResult(
            match_type="NO_MATCH_IN_ACTIVE_MED_LIST",
            matched=False,
            requires_review=True,
            discrepancy_flags=[
                "MISSING_FROM_ACTIVE_MED_LIST"
            ],
            existing_medication_id=None,
            review_reason=(
                "Imported medication not found "
                "in active medication list"
            ),
            imported_dose_normalized=imported_dose_normalized,
            imported_route_normalized=imported_route_normalized,
            imported_frequency_normalized=imported_frequency_normalized,
        )

    flags = _discrepancy_flags(
        imported_item,
        existing_medication,
    )

    if not flags:
        return MedComparisonResult(
            match_type="EXACT_NORMALIZED_MATCH",
            matched=True,
            requires_review=False,
            discrepancy_flags=[],
            existing_medication_id=existing_medication.get("id"),
            review_reason=None,
            imported_dose_normalized=imported_dose_normalized,
            imported_route_normalized=imported_route_normalized,
            imported_frequency_normalized=imported_frequency_normalized,
        )

    return MedComparisonResult(
        match_type="PARTIAL_MATCH_WITH_DISCREPANCY",
        matched=True,
        requires_review=True,
        discrepancy_flags=flags,
        existing_medication_id=existing_medication.get("id"),
        review_reason=_review_reason_from_flags(
            flags
        ),
        imported_dose_normalized=imported_dose_normalized,
        imported_route_normalized=imported_route_normalized,
        imported_frequency_normalized=imported_frequency_normalized,
    )


# =========================================================
# ACTIVE MEDICATION LIST COMPARISON
# =========================================================

def compare_imported_item_against_med_list(
    *,
    imported_item: Dict[str, Any],
    existing_medications: List[Dict[str, Any]],
) -> MedComparisonResult:
    """
    Compare one imported medication reconciliation row against active medications.

    Comparison priorities:
    1. Match by normalized medication identity first.
    2. Prefer exact structured dose/route/frequency match.
    3. If no exact structured match exists, return the best partial match.
    4. If no name match exists, return NO_MATCH_IN_ACTIVE_MED_LIST.
    """

    imported_name = _imported_name(
        imported_item
    )

    imported_dose_normalized = imported_item.get(
        "dose_normalized"
    )

    imported_route_normalized = imported_item.get(
        "route_normalized"
    )

    imported_frequency_normalized = imported_item.get(
        "frequency_normalized"
    )

    name_candidates = [
        medication
        for medication in existing_medications
        if _name_matches(
            imported_name,
            medication,
        )
    ]

    if not name_candidates:
        return MedComparisonResult(
            match_type="NO_MATCH_IN_ACTIVE_MED_LIST",
            matched=False,
            requires_review=True,
            discrepancy_flags=[
                "MISSING_FROM_ACTIVE_MED_LIST"
            ],
            existing_medication_id=None,
            review_reason=(
                "Imported medication not found "
                "in active medication list"
            ),
            imported_dose_normalized=imported_dose_normalized,
            imported_route_normalized=imported_route_normalized,
            imported_frequency_normalized=imported_frequency_normalized,
        )

    for medication in name_candidates:
        result = compare_imported_medication_to_existing(
            imported_item=imported_item,
            existing_medication=medication,
        )

        if result.match_type == "EXACT_NORMALIZED_MATCH":
            return result

    best_candidate = max(
        name_candidates,
        key=lambda medication: _field_match_score(
            imported_item,
            medication,
        ),
    )

    return compare_imported_medication_to_existing(
        imported_item=imported_item,
        existing_medication=best_candidate,
    )