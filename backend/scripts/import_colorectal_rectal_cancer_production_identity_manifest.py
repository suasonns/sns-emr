# scripts/import_colorectal_rectal_cancer_production_identity_manifest.py
"""
Colorectal and Rectal Cancer Production Identity Manifest v1 -- Verbatim
Importer (PR #48).

A disease-specific Oncology manifest spanning TWO canonical diseases.
Reads
backend/manifests/colorectal_rectal_cancer_production_identity_manifest_v1.json
(the sole authoritative source for this import -- never inferred,
reconstructed, or clinically re-derived) and:

    - Resolves (never re-creates) the Oncology body system, the Solid
      Malignancies family, and the existing "Colorectal Cancer" canonical
      disease created by the Oncology Foundation import (PR #45). Raises a
      RuntimeError before any writes if it does not already exist, or if
      more than one row with that name exists (duplicate canonical
      disease).
    - Creates (or resolves, if already present from a prior run) exactly
      ONE new canonical disease: "Rectal Cancer", under the same Oncology /
      Solid Malignancies scope. Raises a RuntimeError if more than one
      "Rectal Cancer" row would ever exist.
    - Resolves (never re-creates) the four Tier 4 variants the foundation
      already created for Colorectal Cancer (Colorectal Primary Site,
      Localized Disease, Metastatic Disease, Recurrent Disease).
    - Creates exactly FOUR new Tier 4 variants for Rectal Cancer (Rectal
      Primary Site, Localized Disease, Metastatic Disease, Recurrent
      Disease) -- Rectal Cancer's own variant rows, never copied from or
      shared with Colorectal Cancer's variant rows.
    - Creates exactly NINE Tier 5 FINDING identity concepts across both
      diseases (5 for Colorectal Cancer, 4 for Rectal Cancer).
    - Creates exactly SEVEN explicit, individually-declared Tier4<->Tier5
      applicability mappings (APPLIES_TO). NO Cartesian or nested-loop
      mapping generation, and NO mapping from any Rectal Cancer concept to
      a Colorectal Cancer variant (or vice versa).

This PR does NOT create a "Colon Cancer" canonical disease, does NOT treat
Rectal Cancer as interchangeable with Colorectal Cancer, does NOT infer
that every Colorectal Cancer is Rectal Cancer, and does NOT create stage,
grade, molecular subtype, anatomical-subdivision, or metastatic-destination
knowledge for either disease -- none of that is supported by the approved
source (Cancer-Types-NCI-08.22.2021.pdf) for this PR.

Reuses the exact verbatim-import pattern proven in
scripts/import_lung_cancer_production_identity_manifest.py (PR #47) and
every prior production-manifest importer (PR #37-#47), generalized to span
two diseases in one manifest:

- No concept is renamed, substituted, combined, split, or omitted.
- No additional concept is invented beyond what the manifest declares.
- A manifest identity match requires an EXACT match on every applicable
    identity field (disease + domain/dimension + normalized exact name).
- Every concept created receives an OntologyEvidenceRule with
    patient_fact_requires_evidence = True.
- Nothing is ever hard-deleted or deactivated in this importer.
- Idempotent: re-running inserts nothing new.
- Nothing is silently skipped: any manifest value that is not
    schema-valid, or any required pre-existing row that is missing, aborts
    the import with a RuntimeError before any writes happen.

The Oncology Foundation import (PR #45) itself reuses two shared
PROGNOSTIC_INDICATOR concepts (Progressive Disease, Worsening Clinical
Status) for every cancer disease it creates -- including Colorectal Cancer.
This importer creates ZERO new PROGNOSTIC_INDICATOR concepts or
applicability edges of its own for either disease (Rectal Cancer is new
and therefore starts with zero foundation-shared prognosis concepts, which
is expected and correct -- this importer never adds any).

Run with: python scripts\\import_colorectal_rectal_cancer_production_identity_manifest.py
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDiseaseFamily,
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyDiseaseFinding,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests"
    / "colorectal_rectal_cancer_production_identity_manifest_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts"
    / "colorectal_rectal_cancer_production_identity_acceptance_v1.json"
)

SYSTEM_NAME = "Oncology"
FAMILY_NAME = "Solid Malignancies"
EXISTING_DISEASE_NAME = "Colorectal Cancer"
NEW_DISEASE_NAME = "Rectal Cancer"
ALL_DISEASE_NAMES = (EXISTING_DISEASE_NAME, NEW_DISEASE_NAME)

# Colorectal Cancer already carries these Tier 5 FINDING concepts, this one
# applicability edge, and these two Oncology-Foundation-shared
# PROGNOSTIC_INDICATOR concepts from the Oncology Foundation import (PR
# #45) -- pre-existing, approved, source-faithful rows this PR never
# touches, renames, or re-declares. Rectal Cancer is a brand-new disease
# created by THIS PR, so it has no foundation-inherited rows at all.
PRE_EXISTING_FOUNDATION_CONCEPT_KEYS = {
    (EXISTING_DISEASE_NAME, "FINDING", "metastatic disease"),
    (EXISTING_DISEASE_NAME, "FINDING", "regional spread"),
    (EXISTING_DISEASE_NAME, "FINDING", "distant metastatic disease"),
    (EXISTING_DISEASE_NAME, "PROGNOSTIC_INDICATOR", "progressive disease"),
    (EXISTING_DISEASE_NAME, "PROGNOSTIC_INDICATOR", "worsening clinical status"),
}
PRE_EXISTING_FOUNDATION_APPLICABILITY_KEYS = {
    (EXISTING_DISEASE_NAME, "METASTATIC_STATE", "Metastatic Disease", "FINDING", "Metastatic Disease", "MAY_OCCUR_WITH"),
}
# The Foundation-shared PROGNOSTIC_INDICATOR baseline this importer must
# never grow, per disease. Rectal Cancer's baseline is empty because the
# Foundation import never created it (it is a new disease under THIS PR),
# and this importer itself creates zero PROGNOSTIC_INDICATOR rows.
PROGNOSTIC_INDICATOR_BASELINE = {
    EXISTING_DISEASE_NAME: {"progressive disease", "worsening clinical status"},
    NEW_DISEASE_NAME: set(),
}

ALLOWED_VARIANT_DIMENSIONS = {
    "MECHANISM", "PATHOLOGICAL_SUBTYPE", "HISTOLOGY", "MOLECULAR_SUBTYPE",
    "ANATOMICAL_LOCATION", "PRIMARY_SITE", "VASCULAR_TERRITORY", "HEMISPHERE",
    "DOMINANCE", "LATERALITY", "CORTICAL_LOCATION", "SUBCORTICAL_LOCATION",
    "DEEP_STRUCTURE", "BRAINSTEM_LEVEL", "CEREBELLAR_LOCATION", "CARDIAC_SIDE",
    "CARDIAC_CHAMBER", "PHYSIOLOGICAL_PHENOTYPE", "SEVERITY_CLASS", "STAGE",
    "GRADE", "DISEASE_PHASE", "RECURRENCE_STATE", "METASTATIC_STATE",
    "METASTATIC_DESTINATION", "TREATMENT_STATE", "RESIDUAL_DEFICIT_STATE",
}

ALLOWED_TREATMENT_CATEGORIES = {"DISEASE_DIRECTED", "SUPPORTIVE", "HOSPICE"}
ALLOWED_LIMITATION_CATEGORIES = {
    "OPTIMALLY_TREATED", "TREATMENT_FAILED", "TREATMENT_INTOLERANT", "NOT_A_CANDIDATE",
    "TREATMENT_DECLINED", "TREATMENT_DISCONTINUED", "TREATMENT_CONTRAINDICATED", "COMFORT_FOCUSED",
    "NOT_CANDIDATE", "CONTRAINDICATED", "DECLINED", "NOT_TOLERATED",
    "OUTSIDE_WINDOW", "GOALS_OF_CARE", "DISCONTINUED", "NOT_BENEFICIAL",
}

APPLICABILITY_TYPES = {
    "APPLIES_TO", "EXPECTED_WITH", "STRONGLY_ASSOCIATED_WITH", "MAY_OCCUR_WITH",
    "SUPPORTS_DIFFERENTIATION", "CONTRAINDICATED_FOR", "TREATMENT_SPECIFIC_TO",
    "PROGNOSTIC_FOR", "END_STAGE_SUPPORT_FOR", "HOSPICE_SUPPORT_FOR",
}

# This manifest only ever creates FINDING-domain Tier 5 concepts (the same
# domain the Oncology Foundation used for its own reusable concepts).
# TREATMENT / TREATMENT_LIMITATION / HOSPICE_ELIGIBILITY_SUPPORT /
# PROGNOSTIC_INDICATOR are listed here only so differentiation guards can
# assert their absence (or, for PROGNOSTIC_INDICATOR, their unchanged
# Foundation baseline).
CONCEPT_DOMAIN_MODEL_MAP = {
    "FINDING": (OntologyDiseaseFinding, "finding_name"),
    "TREATMENT": (OntologyDiseaseTreatment, "treatment_name"),
    "TREATMENT_LIMITATION": (OntologyDiseaseTreatmentLimitation, "limitation_name"),
    "HOSPICE_ELIGIBILITY_SUPPORT": (OntologyDiseaseHospiceEligibilitySupport, "indicator_name"),
    "PROGNOSTIC_INDICATOR": (OntologyDiseasePrognosticIndicator, "indicator_name"),
}

DESCRIPTION_ATTR_BY_DOMAIN = {
    "FINDING": "finding_description",
}

# Source-classification vocabulary -- carried in the concept's own
# OntologyEvidenceRule.notes (per the reviewer-approved PR #40/#45-#47
# pattern), never via a new migration. NCI_CANCER_CATALOG classifies
# disease *identity* knowledge only; ONCOLOGY_FOUNDATION classifies this
# disease's application of the reusable oncology-foundation
# Localized/Metastatic/Recurrent states.
ALLOWED_SOURCE_CLASSIFICATIONS = {"NCI_CANCER_CATALOG", "ONCOLOGY_FOUNDATION"}

# --- Differentiation-guard assertion vocabulary. Every guard is a list of
# ANDed structural assertions (never a clinically-false relationship edge).
# Every assertion that targets a single disease's data now carries an
# explicit "disease" key (required whenever more than one disease is in
# scope) resolved against ctx.diseases. See _evaluate_guard_assertion for
# the mechanical semantics of each. ---
ASSERTION_TYPES = {
    "disease_exists", "disease_absent", "diseases_distinct",
    "variant_exists", "no_variants_in_dimension",
    "concept_exists", "concept_absent", "concept_requires_evidence",
    "concept_has_no_applicability", "concepts_not_collapsed",
    "no_concept_in_domain", "no_applicability_of_type_for_disease",
    "no_new_prognostic_concepts_for_disease", "no_prognostic_applicability_for_disease",
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    """Structural + schema-vocabulary validation -- never a clinical
    judgment. Returns a list of validation errors (empty means the
    manifest is well-formed and every value is schema-valid)."""
    errors: List[str] = []

    scope = manifest.get("scope") or {}
    if scope.get("body_system") != SYSTEM_NAME:
        errors.append(f"manifest.scope.body_system must be {SYSTEM_NAME!r}")
    if scope.get("family") != FAMILY_NAME:
        errors.append(f"manifest.scope.family must be {FAMILY_NAME!r}")
    if set(scope.get("diseases") or []) != set(ALL_DISEASE_NAMES):
        errors.append(f"manifest.scope.diseases must be exactly {sorted(ALL_DISEASE_NAMES)}")

    existing = manifest.get("existing_disease") or {}
    if existing.get("name") != EXISTING_DISEASE_NAME:
        errors.append(f"manifest.existing_disease.name must be {EXISTING_DISEASE_NAME!r}")

    new_disease = manifest.get("new_disease") or {}
    if new_disease.get("name") != NEW_DISEASE_NAME:
        errors.append(f"manifest.new_disease.name must be {NEW_DISEASE_NAME!r}")

    required_variants = manifest.get("required_existing_variants") or {}
    seen_required_variants = set()
    for disease_name, variants in required_variants.items():
        if disease_name not in ALL_DISEASE_NAMES:
            errors.append(f"required_existing_variants references unknown disease {disease_name!r}")
        for v in variants:
            key = (disease_name, v.get("dimension"), (v.get("name") or "").strip().lower())
            if key in seen_required_variants:
                errors.append(f"duplicate required_existing_variants entry: {key}")
            seen_required_variants.add(key)
            if v.get("dimension") not in ALLOWED_VARIANT_DIMENSIONS:
                errors.append(f"unsupported required_existing_variants dimension for {key}")

    new_variants = manifest.get("new_variants") or {}
    seen_new_variants = set()
    for disease_name, variants in new_variants.items():
        if disease_name not in ALL_DISEASE_NAMES:
            errors.append(f"new_variants references unknown disease {disease_name!r}")
        for v in variants:
            key = (disease_name, v.get("dimension"), (v.get("name") or "").strip().lower())
            if key in seen_new_variants:
                errors.append(f"duplicate new_variants entry: {key}")
            seen_new_variants.add(key)
            if v.get("dimension") not in ALLOWED_VARIANT_DIMENSIONS:
                errors.append(f"unsupported new_variants dimension for {key}")
            if v.get("source_classification") not in ALLOWED_SOURCE_CLASSIFICATIONS:
                errors.append(f"unsupported or missing source_classification for new variant {key}")
            if not v.get("source_reference"):
                errors.append(f"missing source_reference for new variant {key}")

    seen_concepts = set()
    concept_lookup: Dict[Tuple[str, str, str], dict] = {}
    for c in manifest.get("concepts", []):
        disease_name = c.get("disease")
        key = (disease_name, c.get("domain"), (c.get("name") or "").strip().lower())
        if disease_name not in ALL_DISEASE_NAMES:
            errors.append(f"concept references unknown disease {disease_name!r} for {key}")
        if key in seen_concepts:
            errors.append(f"duplicate concept identity in manifest: {key}")
        seen_concepts.add(key)
        concept_lookup[key] = c
        if c.get("domain") not in CONCEPT_DOMAIN_MODEL_MAP:
            errors.append(f"unsupported concept domain '{c.get('domain')}' for {key}")
        if c.get("source_classification") not in ALLOWED_SOURCE_CLASSIFICATIONS:
            errors.append(f"unsupported or missing source_classification for {key}")
        if not c.get("source_reference"):
            errors.append(f"missing source_reference for {key}")
        if c.get("patient_fact_requires_evidence") is not True:
            errors.append(f"patient_fact_requires_evidence must be true for {key}")

    seen_applic = set()
    for a in manifest.get("applicability", []):
        disease_name = a.get("disease")
        key = (
            disease_name, a.get("variant_dimension"), a.get("variant"),
            a.get("concept_domain"), a.get("concept"), a.get("applicability_type"),
        )
        if disease_name not in ALL_DISEASE_NAMES:
            errors.append(f"applicability references unknown disease {disease_name!r} for {key}")
        if key in seen_applic:
            errors.append(f"duplicate applicability identity in manifest: {key}")
        seen_applic.add(key)
        if a.get("variant_dimension") not in ALLOWED_VARIANT_DIMENSIONS:
            errors.append(f"unsupported applicability variant_dimension for {key}")
        if a.get("applicability_type") not in APPLICABILITY_TYPES:
            errors.append(f"unsupported applicability_type for {key}")
        referenced = concept_lookup.get(
            (disease_name, a.get("concept_domain"), (a.get("concept") or "").strip().lower())
        )
        if referenced is None:
            errors.append(f"applicability references undeclared concept for {key}")

    for guard in manifest.get("differentiation_guards", []):
        for assertion in guard.get("assertions", []):
            assert_type = assertion.get("assert")
            if assert_type not in ASSERTION_TYPES:
                errors.append(f"unsupported differentiation_guard assertion '{assert_type}' in guard {guard.get('guard_name')!r}")

    return errors


def _resolve_body_system_and_family(db: Session) -> Tuple[OntologyBodySystem, OntologyDiseaseFamily]:
    system = db.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 requires the {SYSTEM_NAME!r} "
            f"body system to already exist (created by the Oncology Foundation import, PR #45). "
            f"Aborting without any writes."
        )
    family = (
        db.query(OntologyDiseaseFamily)
        .filter_by(family_name=FAMILY_NAME, body_system_id=system.id)
        .one_or_none()
    )
    if family is None:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 requires the {FAMILY_NAME!r} "
            f"family to already exist under {SYSTEM_NAME!r} (created by the Oncology Foundation import, "
            f"PR #45). Aborting without any writes."
        )
    return system, family


def _resolve_existing_disease(db: Session, family: OntologyDiseaseFamily) -> OntologyDisease:
    """Resolve (never create) the existing Colorectal Cancer canonical
    disease. Aborts before any writes if it is missing, or if more than one
    row with that name exists (duplicate canonical disease)."""
    matches = db.query(OntologyDisease).filter_by(disease_name=EXISTING_DISEASE_NAME).all()
    if len(matches) == 0:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 requires the canonical "
            f"{EXISTING_DISEASE_NAME!r} disease to already exist (created by the Oncology Foundation "
            f"import, PR #45). Run that import first. Aborting without any writes."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 found {len(matches)} duplicate "
            f"{EXISTING_DISEASE_NAME!r} disease rows. This importer never imports against an ambiguous "
            f"existing state. Aborting without any writes."
        )
    disease = matches[0]
    if disease.disease_family_id != family.id:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 found the existing "
            f"{EXISTING_DISEASE_NAME!r} disease attached to a different family than {FAMILY_NAME!r}. "
            f"Aborting without any writes."
        )
    return disease


def _resolve_or_create_new_disease(db: Session, manifest: dict, family: OntologyDiseaseFamily) -> OntologyDisease:
    """Resolve the Rectal Cancer canonical disease if a prior run of this
    importer already created it, or create exactly one new row. Aborts
    before any writes if more than one row with that name would ever
    exist (duplicate canonical disease) -- this importer never creates a
    second Rectal Cancer disease, and never creates a 'Colon Cancer' or
    'Colon and Rectal Cancer' canonical disease at all."""
    matches = db.query(OntologyDisease).filter_by(disease_name=NEW_DISEASE_NAME).all()
    if len(matches) > 1:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 found {len(matches)} duplicate "
            f"{NEW_DISEASE_NAME!r} disease rows. This importer never creates a duplicate canonical disease "
            f"and refuses to import against an ambiguous existing state. Aborting without any writes."
        )
    if len(matches) == 1:
        disease = matches[0]
        if disease.disease_family_id != family.id:
            raise RuntimeError(
                f"Colorectal and Rectal Cancer Production Identity Manifest v1 found the existing "
                f"{NEW_DISEASE_NAME!r} disease attached to a different family than {FAMILY_NAME!r}. "
                f"Aborting without any writes."
            )
        return disease

    entry = manifest.get("new_disease") or {}
    disease = OntologyDisease(
        id=uuid.uuid4(),
        disease_name=NEW_DISEASE_NAME,
        disease_family_id=family.id,
        disease_category=entry.get("disease_category"),
        primary_organ=entry.get("primary_organ"),
        disease_type=entry.get("disease_type"),
        disease_description=entry.get("disease_description"),
        clinical_purpose=entry.get("clinical_purpose"),
        hospice_relevance=entry.get("hospice_relevance"),
    )
    db.add(disease)
    db.flush()
    return disease


def _resolve_required_variants(
    db: Session, manifest: dict, diseases: Dict[str, OntologyDisease]
) -> Dict[Tuple[str, str, str], OntologyDiseaseVariant]:
    """Resolve (never create) every Tier 4 variant this manifest depends on
    from the Oncology Foundation import. Aborts before any writes if any
    required variant is missing."""
    resolved: Dict[Tuple[str, str, str], OntologyDiseaseVariant] = {}
    for disease_name, variants in (manifest.get("required_existing_variants") or {}).items():
        disease = diseases[disease_name]
        for v in variants:
            dimension = v["dimension"]
            normalized = v["name"].strip().lower()
            variant = (
                db.query(OntologyDiseaseVariant)
                .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=normalized)
                .one_or_none()
            )
            if variant is None:
                raise RuntimeError(
                    f"Colorectal and Rectal Cancer Production Identity Manifest v1 requires the existing "
                    f"{dimension} variant {v['name']!r} to already exist for {disease_name!r} (created by "
                    f"the Oncology Foundation import, PR #45). Aborting without any writes."
                )
            resolved[(disease_name, dimension, normalized)] = variant
    return resolved


def _evidence_notes(concept_entry: dict) -> str:
    parts = [
        "Imported verbatim from the approved Colorectal and Rectal Cancer Production Identity Manifest v1.",
        f"source_classification={concept_entry.get('source_classification')}",
        f"source_reference={concept_entry.get('source_reference')}",
    ]
    reqs = concept_entry.get("evidence_requirements") or []
    if reqs:
        parts.append("evidence_requirements=" + ",".join(reqs))
    return " | ".join(parts)


def _ensure_evidence_rule(db: Session, concept_type: str, concept_id, concept_entry: dict) -> bool:
    existing = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type=concept_type, concept_id=concept_id)
        .one_or_none()
    )
    notes = _evidence_notes(concept_entry)
    if existing is not None:
        if existing.notes != notes:
            existing.notes = notes
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=concept_type,
            concept_id=concept_id,
            evidence_source="colorectal_rectal_cancer_production_identity_manifest_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes=notes,
        )
    )
    return True


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(
            f"Colorectal and Rectal Cancer Production Identity Manifest v1 failed validation: {errors}"
        )

    system, family = _resolve_body_system_and_family(db)
    existing_disease = _resolve_existing_disease(db, family)
    new_disease = _resolve_or_create_new_disease(db, manifest, family)
    diseases = {EXISTING_DISEASE_NAME: existing_disease, NEW_DISEASE_NAME: new_disease}
    disease_created = new_disease.disease_family_id == family.id  # always true; kept for clarity

    required_variants = _resolve_required_variants(db, manifest, diseases)
    db.flush()

    variant_by_key: Dict[Tuple[str, str, str], OntologyDiseaseVariant] = dict(required_variants)
    for disease_name, disease in diseases.items():
        for existing in db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all():
            variant_by_key.setdefault((disease_name, existing.variant_dimension, existing.normalized_name), existing)

    concept_by_key: Dict[Tuple[str, str, str], object] = {}
    for concept_type, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for disease_name, disease in diseases.items():
            for existing in db.query(model_cls).filter_by(disease_id=disease.id).all():
                key = (disease_name, concept_type, getattr(existing, name_attr).strip().lower())
                concept_by_key[key] = existing

    variants_inserted = 0
    concepts_inserted_by_domain: Dict[str, int] = {}
    applicability_inserted = 0
    evidence_rules_inserted = 0

    # --- new Tier 4 variants (Rectal Cancer only) ---
    for disease_name, variants in (manifest.get("new_variants") or {}).items():
        disease = diseases[disease_name]
        for v in variants:
            dimension = v["dimension"]
            name = v["name"]
            normalized = name.strip().lower()
            key = (disease_name, dimension, normalized)
            if key in variant_by_key:
                continue
            variant = OntologyDiseaseVariant(
                id=uuid.uuid4(),
                disease_id=disease.id,
                parent_variant_id=None,
                variant_name=name,
                normalized_name=normalized,
                variant_dimension=dimension,
                description=None,
                evidence_requirement=(
                    f"Requires patient-record evidence (pathology, imaging, or documented clinician "
                    f"assessment) before this {dimension} variant is ever treated as a confirmed "
                    f"patient-specific fact. Diagnosis alone never establishes this variant, and this "
                    f"variant alone never establishes hospice eligibility or prognosis."
                ),
                source_reference=v.get("source_reference"),
            )
            db.add(variant)
            db.flush()
            variant_by_key[key] = variant
            variants_inserted += 1

    # --- Tier 5 atomic concepts (both diseases) ---
    for c in manifest.get("concepts", []):
        disease_name = c["disease"]
        domain = c["domain"]
        name = c["name"]
        normalized = name.strip().lower()
        key = (disease_name, domain, normalized)

        if key in concept_by_key:
            existing_row = concept_by_key[key]
            if _ensure_evidence_rule(db, domain, existing_row.id, c):
                evidence_rules_inserted += 1
            continue

        disease = diseases[disease_name]
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
        row = model_cls(id=uuid.uuid4(), disease_id=disease.id, **{name_attr: name})
        description_attr = DESCRIPTION_ATTR_BY_DOMAIN.get(domain)
        if description_attr is not None and c.get("description"):
            setattr(row, description_attr, c["description"])
        db.add(row)
        db.flush()
        concept_by_key[key] = row
        concepts_inserted_by_domain[domain] = concepts_inserted_by_domain.get(domain, 0) + 1

        if _ensure_evidence_rule(db, domain, row.id, c):
            evidence_rules_inserted += 1

    db.flush()

    # --- Tier 4 <-> Tier 5 applicability: exactly the manifest's own
    # explicit, individually-declared mappings, per disease -- never a
    # nested loop or Cartesian product, and never a cross-disease mapping. ---
    for a in manifest.get("applicability", []):
        disease_name = a["disease"]
        disease = diseases[disease_name]
        variant_name = a["variant"]
        variant_dimension = a["variant_dimension"]
        concept_name = a["concept"]
        concept_domain = a["concept_domain"]
        applicability_type = a["applicability_type"]

        variant_found = variant_by_key.get((disease_name, variant_dimension, variant_name.strip().lower()))
        concept_found = concept_by_key.get((disease_name, concept_domain, concept_name.strip().lower()))

        if variant_found is None or concept_found is None:
            raise RuntimeError(
                f"Colorectal and Rectal Cancer Production Identity Manifest v1 applicability mapping "
                f"references a variant/concept that was not resolved for {disease_name!r}: "
                f"variant={variant_name!r} dimension={variant_dimension!r} concept={concept_name!r} "
                f"domain={concept_domain!r}. Aborting rather than skipping silently."
            )

        existing_edge = (
            db.query(OntologyConceptVariantApplicability)
            .filter_by(
                concept_type=concept_domain,
                concept_id=concept_found.id,
                variant_id=variant_found.id,
                applicability_type=applicability_type,
            )
            .one_or_none()
        )
        if existing_edge is not None:
            continue

        edge = OntologyConceptVariantApplicability(
            id=uuid.uuid4(),
            disease_id=disease.id,
            concept_type=concept_domain,
            concept_id=concept_found.id,
            variant_id=variant_found.id,
            applicability_type=applicability_type,
            description=(
                "Imported verbatim from the approved Colorectal and Rectal Cancer Production Identity "
                "Manifest v1."
            ),
            evidence_requirement=(
                "Requires patient-record evidence before this applicability is ever treated as a "
                "documented patient-specific fact."
            ),
        )
        db.add(edge)
        applicability_inserted += 1

    return {
        "variants_inserted": variants_inserted,
        "concepts_inserted_by_domain": concepts_inserted_by_domain,
        "concepts_inserted_total": sum(concepts_inserted_by_domain.values()),
        "applicability_inserted": applicability_inserted,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


class _GuardContext:
    """Read-only mechanical lookup context for evaluating a differentiation
    guard assertion, generalized across the two diseases this manifest
    spans. Every assertion is a structural database check -- never a
    clinically-false relationship edge."""

    def __init__(self, db: Session, manifest: dict, diseases: Dict[str, OntologyDisease]):
        self.db = db
        self.manifest = manifest
        self.diseases = diseases

    def disease_exists(self, name: str) -> bool:
        return self.db.query(OntologyDisease).filter_by(disease_name=name).one_or_none() is not None

    def _disease(self, assertion: dict) -> OntologyDisease:
        name = assertion["disease"]
        if name not in self.diseases:
            raise RuntimeError(f"guard assertion references unknown disease {name!r}")
        return self.diseases[name]

    def _variant(self, disease: OntologyDisease, dimension: str, name: str):
        return (
            self.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=name.strip().lower())
            .one_or_none()
        )

    def _concept(self, disease: OntologyDisease, domain: str, name: str):
        if domain not in CONCEPT_DOMAIN_MODEL_MAP:
            return None
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
        return (
            self.db.query(model_cls)
            .filter(model_cls.disease_id == disease.id)
            .filter(func.lower(func.trim(getattr(model_cls, name_attr))) == name.strip().lower())
            .one_or_none()
        )


def _evaluate_guard_assertion(ctx: "_GuardContext", assertion: dict) -> bool:
    assert_type = assertion["assert"]

    if assert_type == "disease_exists":
        return ctx.disease_exists(assertion["name"])
    if assert_type == "disease_absent":
        return not ctx.disease_exists(assertion["name"])
    if assert_type == "diseases_distinct":
        disease_a = ctx.diseases.get(assertion["disease_a"]) or ctx.db.query(OntologyDisease).filter_by(
            disease_name=assertion["disease_a"]
        ).one_or_none()
        disease_b = ctx.diseases.get(assertion["disease_b"]) or ctx.db.query(OntologyDisease).filter_by(
            disease_name=assertion["disease_b"]
        ).one_or_none()
        if disease_a is None or disease_b is None:
            return False
        return disease_a.id != disease_b.id

    if assert_type == "variant_exists":
        disease = ctx._disease(assertion)
        return ctx._variant(disease, assertion["dimension"], assertion["name"]) is not None

    if assert_type == "no_variants_in_dimension":
        disease = ctx._disease(assertion)
        count = (
            ctx.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=disease.id, variant_dimension=assertion["dimension"])
            .count()
        )
        return count == 0

    if assert_type == "concept_exists":
        disease = ctx._disease(assertion)
        return ctx._concept(disease, assertion["domain"], assertion["name"]) is not None

    if assert_type == "concept_absent":
        disease = ctx._disease(assertion)
        return ctx._concept(disease, assertion["domain"], assertion["name"]) is None

    if assert_type == "concept_requires_evidence":
        disease = ctx._disease(assertion)
        concept = ctx._concept(disease, assertion["domain"], assertion["name"])
        if concept is None:
            return False
        rule = (
            ctx.db.query(OntologyEvidenceRule)
            .filter_by(concept_type=assertion["domain"], concept_id=concept.id)
            .one_or_none()
        )
        return rule is not None and rule.patient_fact_requires_evidence is True

    if assert_type == "concept_has_no_applicability":
        disease = ctx._disease(assertion)
        concept = ctx._concept(disease, assertion["domain"], assertion["name"])
        if concept is None:
            return False
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(concept_type=assertion["domain"], concept_id=concept.id)
            .count()
        )
        return count == 0

    if assert_type == "concepts_not_collapsed":
        disease = ctx._disease(assertion)
        domain_a = assertion.get("domain_a", assertion.get("domain"))
        domain_b = assertion.get("domain_b", assertion.get("domain"))
        c_a = ctx._concept(disease, domain_a, assertion["name_a"])
        c_b = ctx._concept(disease, domain_b, assertion["name_b"])
        if c_a is None or c_b is None:
            return False
        return c_a.id != c_b.id

    if assert_type == "no_concept_in_domain":
        disease = ctx._disease(assertion)
        if assertion["domain"] not in CONCEPT_DOMAIN_MODEL_MAP:
            return True
        model_cls, _name_attr = CONCEPT_DOMAIN_MODEL_MAP[assertion["domain"]]
        count = ctx.db.query(model_cls).filter_by(disease_id=disease.id).count()
        return count == 0

    if assert_type == "no_applicability_of_type_for_disease":
        disease = ctx._disease(assertion)
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(disease_id=disease.id, applicability_type=assertion["applicability_type"])
            .count()
        )
        return count == 0

    if assert_type == "no_new_prognostic_concepts_for_disease":
        disease_name = assertion["disease"]
        disease = ctx.diseases[disease_name]
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP["PROGNOSTIC_INDICATOR"]
        stored = {
            getattr(row, name_attr).strip().lower()
            for row in ctx.db.query(model_cls).filter_by(disease_id=disease.id).all()
        }
        baseline = PROGNOSTIC_INDICATOR_BASELINE.get(disease_name, set())
        # Passes only if this importer added no PROGNOSTIC_INDICATOR
        # concept beyond the pre-existing Oncology Foundation baseline
        # (empty for a brand-new disease like Rectal Cancer).
        return stored == baseline

    if assert_type == "no_prognostic_applicability_for_disease":
        disease = ctx._disease(assertion)
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(disease_id=disease.id, concept_type="PROGNOSTIC_INDICATOR")
            .count()
        )
        return count == 0

    return False


def _evaluate_guard(ctx: "_GuardContext", guard: dict) -> bool:
    return all(_evaluate_guard_assertion(ctx, a) for a in guard.get("assertions", []))


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    """Compare the manifest against the (already-imported) database and
    report expected vs. stored vs. missing vs. unexpected, plus coverage,
    guard results, orphan/cycle/unresolved counts, and the second-run
    new-row count. Never a clinical judgment -- purely a mechanical
    comparison. Counts are derived from the committed manifest, never
    computed dynamically from arbitrary DB state."""
    system, family = _resolve_body_system_and_family(db)
    existing_disease = _resolve_existing_disease(db, family)
    new_disease = _resolve_or_create_new_disease(db, manifest, family)
    diseases = {EXISTING_DISEASE_NAME: existing_disease, NEW_DISEASE_NAME: new_disease}

    expected_variant_keys = {
        (disease_name, v["dimension"], v["name"].strip().lower())
        for disease_name, variants in (manifest.get("new_variants") or {}).items()
        for v in variants
    }
    required_variant_keys = {
        (disease_name, v["dimension"], v["name"].strip().lower())
        for disease_name, variants in (manifest.get("required_existing_variants") or {}).items()
        for v in variants
    }

    stored_variants_by_disease: Dict[str, list] = {}
    stored_variant_keys_all = set()
    for disease_name, disease in diseases.items():
        rows = db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
        stored_variants_by_disease[disease_name] = rows
        for v in rows:
            stored_variant_keys_all.add((disease_name, v.variant_dimension, v.normalized_name))

    stored_new_variant_keys = stored_variant_keys_all & expected_variant_keys
    missing_variants = sorted(expected_variant_keys - stored_new_variant_keys)
    unsupported_variants = sorted(
        k for k in stored_variant_keys_all if k not in expected_variant_keys and k not in required_variant_keys
    )

    expected_concept_keys = {
        (c["disease"], c["domain"], c["name"].strip().lower()) for c in manifest.get("concepts", [])
    }
    stored_concept_keys = set()
    concept_id_by_key: Dict[Tuple[str, str, str], object] = {}
    concepts_by_domain: Dict[str, int] = {}
    for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for disease_name, disease in diseases.items():
            rows = db.query(model_cls).filter_by(disease_id=disease.id).all()
            if domain == "FINDING":
                concepts_by_domain[domain] = concepts_by_domain.get(domain, 0) + len(rows)
            for row in rows:
                key = (disease_name, domain, getattr(row, name_attr).strip().lower())
                stored_concept_keys.add(key)
                concept_id_by_key[key] = row.id
    missing_concepts = sorted(expected_concept_keys - stored_concept_keys)
    unexpected_concepts = sorted(
        stored_concept_keys - expected_concept_keys - PRE_EXISTING_FOUNDATION_CONCEPT_KEYS
    )
    pre_existing_foundation_concepts_found = sorted(
        stored_concept_keys & PRE_EXISTING_FOUNDATION_CONCEPT_KEYS
    )

    expected_applicability = {
        (a["disease"], a["variant_dimension"], a["variant"], a["concept_domain"], a["concept"], a["applicability_type"])
        for a in manifest.get("applicability", [])
    }
    stored_applicability_keys = set()
    applicability_by_type: Dict[str, int] = {}
    for disease_name, disease in diseases.items():
        stored_edges = db.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
        variant_id_to_key = {
            v.id: (v.variant_dimension, v.variant_name) for v in stored_variants_by_disease[disease_name]
        }
        for edge in stored_edges:
            applicability_by_type[edge.applicability_type] = applicability_by_type.get(edge.applicability_type, 0) + 1
            dimension, variant_name = variant_id_to_key.get(edge.variant_id, (None, None))
            model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
            concept_row = db.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
            concept_name = getattr(concept_row, name_attr) if concept_row is not None else None
            stored_applicability_keys.add(
                (disease_name, dimension, variant_name, edge.concept_type, concept_name, edge.applicability_type)
            )
    missing_applicability = sorted(k for k in expected_applicability if k not in stored_applicability_keys)
    undeclared_applicability = sorted(
        k for k in stored_applicability_keys
        if k not in expected_applicability and k not in PRE_EXISTING_FOUNDATION_APPLICABILITY_KEYS
    )
    pre_existing_foundation_applicability_found = sorted(
        k for k in stored_applicability_keys if k in PRE_EXISTING_FOUNDATION_APPLICABILITY_KEYS
    )

    # Evidence-rule / provenance / classification coverage scoped to this
    # manifest's own expected concepts.
    evidence_covered = 0
    evidence_missing = []
    provenance_covered = 0
    classification_covered = 0
    for key in expected_concept_keys:
        concept_id = concept_id_by_key.get(key)
        if concept_id is None:
            evidence_missing.append(key)
            continue
        rule = db.query(OntologyEvidenceRule).filter_by(concept_type=key[1], concept_id=concept_id).one_or_none()
        if rule is not None and rule.patient_fact_requires_evidence is True:
            evidence_covered += 1
            if rule.notes and "source_reference=" in rule.notes:
                provenance_covered += 1
            if rule.notes and "source_classification=" in rule.notes:
                classification_covered += 1
        else:
            evidence_missing.append(key)

    # Orphans: applicability edges whose concept_id/variant_id no longer
    # resolves to a live row.
    orphan_count = 0
    all_stored_variants = [v for rows in stored_variants_by_disease.values() for v in rows]
    for disease_name, disease in diseases.items():
        for edge in db.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all():
            model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
            if db.query(model_cls).filter_by(id=edge.concept_id).one_or_none() is None:
                orphan_count += 1
            if db.query(OntologyDiseaseVariant).filter_by(id=edge.variant_id).one_or_none() is None:
                orphan_count += 1

    # Cycle check: no variant's parent_variant_id chain loops back on itself.
    cycle_count = 0
    by_id = {v.id: v for v in all_stored_variants}
    for v in all_stored_variants:
        seen = set()
        current = v
        while current is not None and current.parent_variant_id is not None:
            if current.id in seen:
                cycle_count += 1
                break
            seen.add(current.id)
            current = by_id.get(current.parent_variant_id)

    # Unresolved concepts: manifest concepts referencing a domain with no
    # matching model (should never happen given validate_manifest, kept as
    # a defensive, always-zero mechanical check).
    unresolved_concept_count = sum(
        1 for c in manifest.get("concepts", []) if c["domain"] not in CONCEPT_DOMAIN_MODEL_MAP
    )

    ctx = _GuardContext(db, manifest, diseases)
    guard_results = [
        {
            "guard_name": guard["guard_name"],
            "passed": _evaluate_guard(ctx, guard),
        }
        for guard in manifest.get("differentiation_guards", [])
    ]

    return {
        "manifest_id": "colorectal_rectal_cancer_production_identity_manifest_v1",
        "colorectal_cancer_canonical_disease_count": len(
            db.query(OntologyDisease).filter_by(disease_name=EXISTING_DISEASE_NAME).all()
        ),
        "rectal_cancer_canonical_disease_count": len(
            db.query(OntologyDisease).filter_by(disease_name=NEW_DISEASE_NAME).all()
        ),
        "colon_cancer_canonical_disease_count": len(
            db.query(OntologyDisease).filter_by(disease_name="Colon Cancer").all()
        ),
        "duplicate_canonical_disease_count": max(
            0,
            len(db.query(OntologyDisease).filter_by(disease_name=EXISTING_DISEASE_NAME).all()) - 1,
        ) + max(
            0,
            len(db.query(OntologyDisease).filter_by(disease_name=NEW_DISEASE_NAME).all()) - 1,
        ),
        "variants_by_dimension": {
            dim: len([v for v in all_stored_variants if v.variant_dimension == dim])
            for dim in sorted({v.variant_dimension for v in all_stored_variants})
        },
        "concepts_by_domain": concepts_by_domain,
        "applicability_by_type": applicability_by_type,
        "expected_new_variants_count": len(expected_variant_keys),
        "stored_new_variants_count": len(stored_new_variant_keys),
        "missing_variants": [list(k) for k in missing_variants],
        "unsupported_variants": [list(k) for k in unsupported_variants],
        "unsupported_variant_count": len(unsupported_variants),
        "expected_concepts_count": len(expected_concept_keys),
        "stored_concepts_count": len(stored_concept_keys),
        "missing_concepts": [list(k) for k in missing_concepts],
        "unexpected_concepts": [list(k) for k in unexpected_concepts],
        "foundation_inherited_concepts": [list(k) for k in pre_existing_foundation_concepts_found],
        "expected_applicability_count": len(expected_applicability),
        "stored_applicability_count": len(stored_applicability_keys),
        "missing_applicability": [list(k) for k in missing_applicability],
        "undeclared_applicability": [list(k) for k in undeclared_applicability],
        "undeclared_applicability_count": len(undeclared_applicability),
        "foundation_inherited_applicability": [list(k) for k in pre_existing_foundation_applicability_found],
        "evidence_rule_coverage": {
            "covered": evidence_covered,
            "expected": len(expected_concept_keys),
            "missing": [list(k) for k in evidence_missing],
        },
        "source_provenance_coverage": {"covered": provenance_covered, "expected": len(expected_concept_keys)},
        "source_classification_coverage": {"covered": classification_covered, "expected": len(expected_concept_keys)},
        "differentiation_guard_results": guard_results,
        "orphan_count": orphan_count,
        "cycle_count": cycle_count,
        "unresolved_concept_count": unresolved_concept_count,
        "second_run_new_rows": second_run_new_rows,
        "changes_outside_oncology": [],
    }


def main() -> None:
    manifest = load_manifest()
    db = SessionLocal()
    try:
        result = run(db, manifest=manifest)
        db.commit()
        print("First run result:", json.dumps(result, indent=2))

        db2_result = run(db, manifest=manifest)
        db.commit()
        second_run_new_rows = (
            db2_result["variants_inserted"]
            + db2_result["concepts_inserted_total"]
            + db2_result["applicability_inserted"]
        )
        print("Second run new rows:", second_run_new_rows)

        report = build_acceptance_report(db, manifest, second_run_new_rows)
        DEFAULT_ACCEPTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_ACCEPTANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Wrote acceptance report to {DEFAULT_ACCEPTANCE_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
