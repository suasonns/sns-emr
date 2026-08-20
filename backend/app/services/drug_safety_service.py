# app/services/drug_safety_service.py

"""
Medication safety engine: allergy cross-checking + drug-drug interaction detection.

Architecture:
- Reference data (drug -> class, class/drug interaction rules, allergen -> class)
  lives in JSON config under app/config/. This keeps the engine deterministic,
  auditable, and easy to swap for a licensed feed (First Databank / Medi-Span)
  later — only the loader functions below would change, not the callers.
- This is a curated/open dataset, NOT a substitute for a licensed clinical drug
  database. It covers the most clinically significant, commonly-encountered
  interactions/allergy classes relevant to hospice care.

Compliance notes:
- NEVER blocks medication entry.
- Only flags + returns structured warnings for clinician review.
- Deterministic and auditable (JSON-driven, no ML/heuristic guessing).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.patient_allergy import PatientAllergy
from app.utils.med_normalization import normalize_text
from app.services.medication_alias_service import resolve_canonical_medication_name

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

# Common pharmaceutical salt/ester/hydrate qualifiers. When a medication name
# is entered with one of these (e.g. "Morphine Sulfate", "Metoprolol
# Tartrate"), the base drug_classes.json lookup key is the bare generic name
# ("morphine", "metoprolol"). We strip trailing qualifier words before giving
# up on a class lookup so real-world medication names still resolve.
_SALT_SUFFIXES = (
    "sulfate", "hydrochloride", "hcl", "tartrate", "succinate", "besylate",
    "maleate", "mesylate", "citrate", "phosphate", "bitartrate", "acetate",
    "fumarate", "sodium", "potassium", "calcium", "magnesium", "dihydrate",
    "monohydrate", "hemihydrate", "anhydrous", "extended-release", "extended",
    "release", "er", "xr", "sr", "cr", "odt", "hbr", "besilate",
)


def _strip_salt_suffixes(name: str) -> str:
    """Strip trailing salt/form qualifier words one at a time (e.g.
    "morphine sulfate" -> "morphine") until a match is found or no more
    qualifier words remain."""
    words = name.split(" ")
    while len(words) > 1 and words[-1] in _SALT_SUFFIXES:
        words = words[:-1]
    return " ".join(words)


@lru_cache(maxsize=1)
def _load_drug_classes() -> dict[str, list[str]]:
    path = CONFIG_DIR / "drug_classes.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


@lru_cache(maxsize=1)
def _load_interaction_rules() -> dict:
    path = CONFIG_DIR / "drug_interactions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_allergy_class_map() -> dict:
    path = CONFIG_DIR / "allergy_class_map.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("classes", {})


@lru_cache(maxsize=1)
def _load_class_groups() -> dict[str, list[str]]:
    path = CONFIG_DIR / "drug_class_groups.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def get_drug_classes(canonical_name: str) -> set[str]:
    """Return the set of class keys a canonical (generic, lowercase) drug name belongs to.

    Tries an exact match first, then falls back to stripping trailing
    salt/form qualifier words (e.g. "morphine sulfate" -> "morphine") so
    real-world medication names (which usually include a salt form) still
    resolve against the bare-generic-name keys in drug_classes.json.
    """
    if not canonical_name:
        return set()
    key = normalize_text(canonical_name) or ""
    classes_map = _load_drug_classes()
    if key in classes_map:
        return set(classes_map[key])

    stripped = _strip_salt_suffixes(key)
    if stripped != key and stripped in classes_map:
        return set(classes_map[stripped])

    return set()


def get_class_group(group_or_class: str) -> set[str]:
    """
    Resolve a class-group name (e.g. "ANTIBIOTICS") to its member class keys,
    or fall back to treating the input as a single class key directly
    (e.g. "OPIOIDS") if it isn't a known group.
    """
    if not group_or_class:
        return set()

    key = group_or_class.strip().upper()
    groups = _load_class_groups()
    if key in groups:
        return set(groups[key])

    return {key}


def resolve_allergen(allergen_text: str) -> tuple[Optional[str], list[str]]:
    """
    Resolve a free-text allergen phrase to (drug_class_key, [exact_generic_drug_names]).
    Returns (None, []) if the allergen has no known drug-class mapping (e.g. food/environmental).
    """
    if not allergen_text:
        return None, []

    key = normalize_text(allergen_text) or ""
    entry = _load_allergy_class_map().get(key)
    if not entry:
        return None, []

    return entry.get("drug_class"), entry.get("also_flag_drugs", [])


def _severity_rank(severity: str) -> int:
    order = {"CONTRAINDICATED": 4, "MAJOR": 3, "MODERATE": 2, "MINOR": 1}
    return order.get((severity or "").upper(), 0)


def check_interactions(new_canonical: str, new_classes: set[str], existing_canonical: str, existing_classes: set[str]) -> Optional[dict]:
    """
    Check a single (new drug, existing drug) pair against the class-pair and
    exact drug-pair interaction rule sets. Returns the highest-severity match, or None.
    """
    rules = _load_interaction_rules()
    best: Optional[dict] = None

    # Exact drug-pair rules (most specific)
    for rule in rules.get("drug_pairs", []):
        pair = {normalize_text(d) for d in rule.get("drugs", [])}
        if pair == {new_canonical, existing_canonical} and new_canonical != existing_canonical:
            candidate = {
                "severity": rule["severity"],
                "effect": rule["effect"],
                "management": rule["management"],
                "matched_on": "drug_pair",
            }
            if best is None or _severity_rank(candidate["severity"]) > _severity_rank(best["severity"]):
                best = candidate

    # Class-pair rules
    for rule in rules.get("class_pairs", []):
        class_a, class_b = rule["classes"][0], rule["classes"][1]
        match = (
            (class_a in new_classes and class_b in existing_classes)
            or (class_b in new_classes and class_a in existing_classes)
        )
        if not match:
            continue

        # Same-class self-pairs (e.g. QT_PROLONGING + QT_PROLONGING) should only
        # fire between two DIFFERENT drugs, never a drug against itself.
        if class_a == class_b and new_canonical == existing_canonical:
            continue

        candidate = {
            "severity": rule["severity"],
            "effect": rule["effect"],
            "management": rule["management"],
            "matched_on": f"{class_a} + {class_b}",
        }
        if best is None or _severity_rank(candidate["severity"]) > _severity_rank(best["severity"]):
            best = candidate

    return best


def check_new_medication_safety(
    db: Session,
    patient_id,
    drug_name_raw: str,
) -> dict:
    """
    Real-time safety check for a medication name being entered for a patient.

    Returns:
        {
          "canonical_name": str,
          "allergy_alerts": [ { "allergen": str, "severity": str, "reaction": str|None, "matched_on": str } ],
          "interaction_alerts": [ { "with_medication": str, "severity": str, "effect": str, "management": str } ],
        }
    """
    canonical = normalize_text(resolve_canonical_medication_name(db, drug_name_raw)) or ""
    new_classes = get_drug_classes(canonical)

    result: dict = {
        "canonical_name": canonical,
        "allergy_alerts": [],
        "interaction_alerts": [],
    }

    if not canonical:
        return result

    # ---- Allergy cross-check ----
    allergies = (
        db.query(PatientAllergy)
        .filter(
            PatientAllergy.patient_id == patient_id,
            PatientAllergy.active.is_(True),
            PatientAllergy.allergen_type == "DRUG",
        )
        .all()
    )

    for allergy in allergies:
        allergen_class, exact_drugs = resolve_allergen(allergy.allergen_text)
        stored_class = allergy.drug_class or allergen_class

        exact_match = canonical in {normalize_text(d) for d in exact_drugs}
        class_match = bool(stored_class) and stored_class in new_classes

        if exact_match or class_match:
            result["allergy_alerts"].append(
                {
                    "allergen": allergy.allergen_text,
                    "severity": allergy.severity or "UNKNOWN",
                    "reaction": allergy.reaction_description,
                    "matched_on": "exact_drug" if exact_match else f"drug_class:{stored_class}",
                }
            )

    # ---- Interaction cross-check against active medications ----
    active_meds = (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient_id,
            Medication.end_date.is_(None),
        )
        .all()
    )

    seen_existing = set()
    for med in active_meds:
        existing_canonical = normalize_text(med.canonical_name) or normalize_text(med.medication_name) or ""
        if not existing_canonical or existing_canonical in seen_existing:
            continue
        seen_existing.add(existing_canonical)

        if existing_canonical == canonical:
            continue  # duplicate therapy is handled separately (DUPLICATE_ACTIVE_MED)

        existing_classes = get_drug_classes(existing_canonical)
        match = check_interactions(canonical, new_classes, existing_canonical, existing_classes)
        if match:
            result["interaction_alerts"].append(
                {
                    "with_medication": med.medication_name,
                    "severity": match["severity"],
                    "effect": match["effect"],
                    "management": match["management"],
                    "matched_on": match["matched_on"],
                }
            )

    return result
