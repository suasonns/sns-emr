from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Optional

from app.services.med_reconciliation_normalizer import (
    normalize_med_reconciliation_item,
)
from app.utils.drug_alias import normalize_drug_name
from app.utils.med_normalization import normalize_dose, normalize_text


# ---------------------------------------------------------
# RESULT MODELS
# ---------------------------------------------------------

@dataclass
class MedicationSnapshot:
    medication_id: Optional[str]
    med_name_raw: Optional[str]
    med_name_normalized: str
    dose_raw: Optional[str]
    dose_normalized: str
    route_raw: Optional[str]
    route_normalized: str
    frequency_raw: Optional[str]
    frequency_normalized: str
    is_active: bool


@dataclass
class ReconciliationComparisonResult:
    comparison_type: str
    severity: str
    med_name_normalized: str
    imported_med_name_raw: Optional[str]
    imported_dose_raw: Optional[str]
    imported_dose_normalized: str
    existing_med_name_raw: Optional[str]
    existing_dose_raw: Optional[str]
    existing_dose_normalized: str
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------
# SNAPSHOT HELPERS
# ---------------------------------------------------------

def build_import_snapshot(item: Any) -> MedicationSnapshot:
    """
    Convert MedReconciliationItem ORM row (or dict-like object) into
    normalized comparison snapshot.
    """
    med_name_raw = getattr(item, "med_name_raw", None)
    dose_raw = getattr(item, "dose", None)
    route_raw = getattr(item, "route", None)
    frequency_raw = getattr(item, "frequency", None)

    normalized = normalize_med_reconciliation_item(
        med_name_raw=med_name_raw,
        dose=dose_raw,
        route=route_raw,
        frequency=frequency_raw,
    )

    return MedicationSnapshot(
        medication_id=str(getattr(item, "id", "")) or None,
        med_name_raw=med_name_raw,
        med_name_normalized=normalized["med_name_normalized"] or "",
        dose_raw=dose_raw,
        dose_normalized=normalized["dose_normalized"] or "",
        route_raw=route_raw,
        route_normalized=normalized["route_normalized"] or "",
        frequency_raw=frequency_raw,
        frequency_normalized=normalized["frequency_normalized"] or "",
        is_active=True,
    )


def build_existing_med_snapshot(med: Any) -> MedicationSnapshot:
    """
    Convert Medication ORM row into normalized comparison snapshot.
    """
    med_name_raw = getattr(med, "medication_name", None)
    dose_raw = getattr(med, "dosage", None)
    route_raw = getattr(med, "route", None)
    frequency_raw = getattr(med, "frequency", None)

    return MedicationSnapshot(
        medication_id=str(getattr(med, "id", "")) or None,
        med_name_raw=med_name_raw,
        med_name_normalized=normalize_drug_name(med_name_raw),
        dose_raw=dose_raw,
        dose_normalized=normalize_dose(dose_raw),
        route_raw=route_raw,
        route_normalized=normalize_text(route_raw),
        frequency_raw=frequency_raw,
        frequency_normalized=normalize_text(frequency_raw),
        is_active=bool(getattr(med, "is_active", True)),
    )


# ---------------------------------------------------------
# MATCH RULES
# ---------------------------------------------------------

def _same_medication_name(a: MedicationSnapshot, b: MedicationSnapshot) -> bool:
    return a.med_name_normalized == b.med_name_normalized


def _same_dose(a: MedicationSnapshot, b: MedicationSnapshot) -> bool:
    return a.dose_normalized == b.dose_normalized


def _same_route