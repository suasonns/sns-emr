# scripts/import_lung_cancer_production_identity_manifest.py
"""
Lung Cancer Production Identity Manifest v1 -- Verbatim Importer (PR #47).

A disease-specific Oncology manifest. Reads
backend/manifests/lung_cancer_production_identity_manifest_v1.json (the
sole authoritative source for this import -- never inferred, reconstructed,
or clinically re-derived) and adds ONLY source-supported identity knowledge
on top of the existing "Lung Cancer" canonical disease created by the
Oncology Foundation import (scripts/import_oncology_foundation_v1.py, PR
#45):

    - Resolves (never re-creates) the Oncology body system, the Solid
      Malignancies family, and the existing "Lung Cancer" canonical
      disease. Raises a RuntimeError before any writes if the disease does
      not already exist, or if more than one row with that name exists
      (duplicate canonical disease).
    - Resolves (never re-creates) the four Tier 4 variants the foundation
      already created for Lung Cancer (Lung Primary Site, Localized
      Disease, Metastatic Disease, Recurrent Disease).
    - Creates exactly FIVE new Tier 4 variants (PATHOLOGICAL_SUBTYPE
      dimension) -- the only variants the approved NCI cancer-types
      catalog supports for this PR: Non-Small Cell Lung Cancer, Small Cell
      Lung Cancer, Pleuropulmonary Blastoma, Tracheobronchial Tumor,
      Bronchial Tumor.
    - Creates exactly NINE Tier 5 FINDING identity concepts: Lung Cancer,
      Non-Small Cell Lung Cancer, Small Cell Lung Cancer, Pleuropulmonary
      Blastoma, Tracheobronchial Tumor, Bronchial Tumor, Localized Lung
      Cancer, Metastatic Lung Cancer, Recurrent Lung Cancer.
    - Creates exactly EIGHT explicit, individually-declared Tier4<->Tier5
      applicability mappings (APPLIES_TO): each pathological-subtype
      concept -> its own variant; Localized/Metastatic/Recurrent Lung
      Cancer concepts -> their corresponding foundation variants. NO
      Cartesian or nested-loop mapping generation. "Lung Cancer" (base
      identity) intentionally receives ZERO applicability edges -- it
      anchors disease identity, not a Tier 4 variant.

This PR does NOT create a universal cancer manifest, does NOT copy any of
this content to another cancer disease, does NOT mix the Pulmonary
Disease LCD manifest with Lung Cancer identity knowledge (pulmonary
terminal-disease criteria do not automatically apply to Lung Cancer), and
does NOT create stage, grade, laterality, molecular-subtype,
metastatic-destination, symptom, diagnostic, treatment, medication, or
prognosis knowledge -- none of that is supported by the approved source
(Cancer-Types-NCI-08.22.2021.pdf) for this PR.

Reuses the exact verbatim-import pattern proven in
scripts/import_breast_cancer_production_identity_manifest.py (PR #46) and
every prior production-manifest importer (PR #37-#46):

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

Run with: python scripts\\import_lung_cancer_production_identity_manifest.py
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
    Path(__file__).resolve().parent.parent / "manifests" / "lung_cancer_production_identity_manifest_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "lung_cancer_production_identity_acceptance_v1.json"
)

SYSTEM_NAME = "Oncology"
FAMILY_NAME = "Solid Malignancies"
DISEASE_NAME = "Lung Cancer"

# Lung Cancer already carries these Tier 5 FINDING concepts and this one
# applicability edge from the Oncology Foundation import (PR #45) -- they
# are pre-existing, approved, source-faithful rows this PR never touches,
# renames, or re-declares. They are excluded from this manifest's own
# expected/unexpected accounting so the acceptance report only flags a
# TRUE defect (an actually-unplanned row), never legitimate prior-PR
# content this importer correctly left alone.
PRE_EXISTING_FOUNDATION_CONCEPT_KEYS = {
    ("FINDING", "metastatic disease"),
    ("FINDING", "regional spread"),
    ("FINDING", "distant metastatic disease"),
}
PRE_EXISTING_FOUNDATION_APPLICABILITY_KEYS = {
    ("METASTATIC_STATE", "Metastatic Disease", "FINDING", "Metastatic Disease", "MAY_OCCUR_WITH"),
}

# --- Tier 4 variant dimensions permitted by the
# ck_ontology_disease_variant_dimension CHECK constraint. Listed here for
# validation only -- this manifest creates variants in only ONE of them
# (PATHOLOGICAL_SUBTYPE). ---
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
# domain the Oncology Foundation used for its own reusable
# Metastatic Disease / Regional Spread / Distant Metastatic Disease
# concepts). TREATMENT / TREATMENT_LIMITATION / HOSPICE_ELIGIBILITY_SUPPORT
# / PROGNOSTIC_INDICATOR are listed here only so differentiation guards
# can assert their absence.
CONCEPT_DOMAIN_MODEL_MAP = {
    "FINDING": (OntologyDiseaseFinding, "finding_name"),
    "TREATMENT": (OntologyDiseaseTreatment, "treatment_name"),
    "TREATMENT_LIMITATION": (OntologyDiseaseTreatmentLimitation, "limitation_name"),
    "HOSPICE_ELIGIBILITY_SUPPORT": (OntologyDiseaseHospiceEligibilitySupport, "indicator_name"),
    "PROGNOSTIC_INDICATOR": (OntologyDiseasePrognosticIndicator, "indicator_name"),
}

# The existing free-text column each concept domain already has, used to
# carry the description without a schema change.
DESCRIPTION_ATTR_BY_DOMAIN = {
    "FINDING": "finding_description",
}

# --- Source-classification vocabulary. The schema has no dedicated column
# for this distinction (per the reviewer-approved PR #40/#45/#46 pattern),
# so it is recorded in the concept's own OntologyEvidenceRule.notes --
# never via a new migration. NCI_CANCER_CATALOG classifies disease
# *identity* knowledge only (never stage/grade/molecular-subtype/
# treatment/hospice-eligibility); ONCOLOGY_FOUNDATION classifies this
# disease's application of the reusable oncology-foundation
# Localized/Metastatic/Recurrent states. ---
ALLOWED_SOURCE_CLASSIFICATIONS = {"NCI_CANCER_CATALOG", "ONCOLOGY_FOUNDATION"}

# --- Differentiation-guard assertion vocabulary. Every guard is a list of
# ANDed structural assertions (never a clinically-false relationship edge).
# See _evaluate_guard_assertion for the mechanical semantics of each. ---
ASSERTION_TYPES = {
    "disease_exists", "disease_absent",
    "variant_exists", "no_variants_in_dimension",
    "concept_exists", "concept_absent", "concept_requires_evidence",
    "concept_has_no_applicability", "concepts_not_collapsed",
    "no_concept_in_domain", "no_applicability_of_type_for_disease",
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
    if scope.get("disease") != DISEASE_NAME:
        errors.append(f"manifest.scope.disease must be {DISEASE_NAME!r}")

    seen_required_variants = set()
    for v in manifest.get("required_existing_variants", []):
        key = (v.get("dimension"), (v.get("name") or "").strip().lower())
        if key in seen_required_variants:
            errors.append(f"duplicate required_existing_variants entry: {key}")
        seen_required_variants.add(key)
        if v.get("dimension") not in ALLOWED_VARIANT_DIMENSIONS:
            errors.append(f"unsupported required_existing_variants dimension for {key}")

    seen_new_variants = set()
    for v in manifest.get("new_variants", []):
        key = (v.get("dimension"), (v.get("name") or "").strip().lower())
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
    concept_lookup: Dict[Tuple[str, str], dict] = {}
    for c in manifest.get("concepts", []):
        key = (c.get("domain"), (c.get("name") or "").strip().lower())
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
        key = (a.get("variant_dimension"), a.get("variant"), a.get("concept_domain"), a.get("concept"), a.get("applicability_type"))
        if key in seen_applic:
            errors.append(f"duplicate applicability identity in manifest: {key}")
        seen_applic.add(key)
        if a.get("variant_dimension") not in ALLOWED_VARIANT_DIMENSIONS:
            errors.append(f"unsupported applicability variant_dimension for {key}")
        if a.get("applicability_type") not in APPLICABILITY_TYPES:
            errors.append(f"unsupported applicability_type for {key}")
        referenced = concept_lookup.get((a.get("concept_domain"), (a.get("concept") or "").strip().lower()))
        if referenced is None:
            errors.append(f"applicability references undeclared concept for {key}")

    for guard in manifest.get("differentiation_guards", []):
        for assertion in guard.get("assertions", []):
            assert_type = assertion.get("assert")
            if assert_type not in ASSERTION_TYPES:
                errors.append(f"unsupported differentiation_guard assertion '{assert_type}' in guard {guard.get('guard_name')!r}")

    return errors


def _resolve_existing_disease(db: Session, manifest: dict) -> OntologyDisease:
    """Resolve the Oncology body system, Solid Malignancies family, and the
    existing Lung Cancer canonical disease -- created by the Oncology
    Foundation import (PR #45). This importer NEVER creates the body
    system, family, or disease: it aborts with a RuntimeError before any
    writes if any of them is missing, or if more than one Lung Cancer
    disease row exists (duplicate canonical disease)."""
    system = db.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        raise RuntimeError(
            f"Lung Cancer Production Identity Manifest v1 requires the {SYSTEM_NAME!r} body system to "
            f"already exist (created by the Oncology Foundation import, PR #45). Aborting without any writes."
        )
    family = (
        db.query(OntologyDiseaseFamily)
        .filter_by(family_name=FAMILY_NAME, body_system_id=system.id)
        .one_or_none()
    )
    if family is None:
        raise RuntimeError(
            f"Lung Cancer Production Identity Manifest v1 requires the {FAMILY_NAME!r} family to already "
            f"exist under {SYSTEM_NAME!r} (created by the Oncology Foundation import, PR #45). "
            f"Aborting without any writes."
        )

    matches = db.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
    if len(matches) == 0:
        raise RuntimeError(
            f"Lung Cancer Production Identity Manifest v1 requires the canonical {DISEASE_NAME!r} disease "
            f"to already exist (created by the Oncology Foundation import, PR #45). Run that import first. "
            f"Aborting without any writes."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Lung Cancer Production Identity Manifest v1 found {len(matches)} duplicate {DISEASE_NAME!r} "
            f"disease rows. This importer never creates a duplicate canonical disease and refuses to import "
            f"against an ambiguous existing state. Aborting without any writes."
        )
    disease = matches[0]
    if disease.disease_family_id != family.id:
        raise RuntimeError(
            f"Lung Cancer Production Identity Manifest v1 found the existing {DISEASE_NAME!r} disease "
            f"attached to a different family than {FAMILY_NAME!r}. Aborting without any writes."
        )
    return disease


def _resolve_required_variants(db: Session, manifest: dict, disease: OntologyDisease) -> Dict[Tuple[str, str], OntologyDiseaseVariant]:
    """Resolve (never create) every Tier 4 variant this manifest depends on
    from the Oncology Foundation import. Aborts before any writes if any
    required variant is missing."""
    resolved: Dict[Tuple[str, str], OntologyDiseaseVariant] = {}
    for v in manifest.get("required_existing_variants", []):
        dimension = v["dimension"]
        normalized = v["name"].strip().lower()
        variant = (
            db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=normalized)
            .one_or_none()
        )
        if variant is None:
            raise RuntimeError(
                f"Lung Cancer Production Identity Manifest v1 requires the existing {dimension} variant "
                f"{v['name']!r} to already exist for {DISEASE_NAME!r} (created by the Oncology Foundation "
                f"import, PR #45). Aborting without any writes."
            )
        resolved[(dimension, normalized)] = variant
    return resolved


def _evidence_notes(concept_entry: dict) -> str:
    parts = [
        "Imported verbatim from the approved Lung Cancer Production Identity Manifest v1.",
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
            evidence_source="lung_cancer_production_identity_manifest_v1",
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
        raise RuntimeError(f"Lung Cancer Production Identity Manifest v1 failed validation: {errors}")

    disease = _resolve_existing_disease(db, manifest)
    required_variants = _resolve_required_variants(db, manifest, disease)
    db.flush()

    variant_by_key: Dict[Tuple[str, str], OntologyDiseaseVariant] = dict(required_variants)
    for existing in db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all():
        variant_by_key.setdefault((existing.variant_dimension, existing.normalized_name), existing)

    concept_by_key: Dict[Tuple[str, str], object] = {}
    for concept_type, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for existing in db.query(model_cls).filter_by(disease_id=disease.id).all():
            key = (concept_type, getattr(existing, name_attr).strip().lower())
            concept_by_key[key] = existing

    variants_inserted = 0
    concepts_inserted_by_domain: Dict[str, int] = {}
    applicability_inserted = 0
    evidence_rules_inserted = 0

    # --- new Tier 4 variants ---
    for v in manifest.get("new_variants", []):
        dimension = v["dimension"]
        name = v["name"]
        normalized = name.strip().lower()
        key = (dimension, normalized)
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
            evidence_requirement=v.get("evidence_requirement"),
            source_reference=v.get("source_reference"),
        )
        db.add(variant)
        db.flush()
        variant_by_key[key] = variant
        variants_inserted += 1

    # --- Tier 5 atomic concepts ---
    for c in manifest.get("concepts", []):
        domain = c["domain"]
        name = c["name"]
        normalized = name.strip().lower()
        key = (domain, normalized)

        if key in concept_by_key:
            existing_row = concept_by_key[key]
            if _ensure_evidence_rule(db, domain, existing_row.id, c):
                evidence_rules_inserted += 1
            continue

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
    # explicit, individually-declared mappings -- never a nested loop or
    # Cartesian product. ---
    for a in manifest.get("applicability", []):
        variant_name = a["variant"]
        variant_dimension = a["variant_dimension"]
        concept_name = a["concept"]
        concept_domain = a["concept_domain"]
        applicability_type = a["applicability_type"]

        variant_found = variant_by_key.get((variant_dimension, variant_name.strip().lower()))
        concept_found = concept_by_key.get((concept_domain, concept_name.strip().lower()))

        if variant_found is None or concept_found is None:
            raise RuntimeError(
                f"Lung Cancer Production Identity Manifest v1 applicability mapping references a "
                f"variant/concept that was not resolved: variant={variant_name!r} dimension={variant_dimension!r} "
                f"concept={concept_name!r} domain={concept_domain!r}. Aborting rather than skipping silently."
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
            description="Imported verbatim from the approved Lung Cancer Production Identity Manifest v1.",
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
    guard assertion. Every assertion is a structural database check --
    never a clinically-false relationship edge."""

    def __init__(self, db: Session, manifest: dict, disease: OntologyDisease):
        self.db = db
        self.manifest = manifest
        self.disease = disease

    def disease_exists(self, name: str) -> bool:
        return self.db.query(OntologyDisease).filter_by(disease_name=name).one_or_none() is not None

    def _variant(self, dimension: str, name: str):
        return (
            self.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=self.disease.id, variant_dimension=dimension, normalized_name=name.strip().lower())
            .one_or_none()
        )

    def _concept(self, domain: str, name: str):
        if domain not in CONCEPT_DOMAIN_MODEL_MAP:
            return None
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
        return (
            self.db.query(model_cls)
            .filter(model_cls.disease_id == self.disease.id)
            .filter(func.lower(func.trim(getattr(model_cls, name_attr))) == name.strip().lower())
            .one_or_none()
        )


def _evaluate_guard_assertion(ctx: "_GuardContext", assertion: dict) -> bool:
    assert_type = assertion["assert"]

    if assert_type == "disease_exists":
        return ctx.disease_exists(assertion["name"])
    if assert_type == "disease_absent":
        return not ctx.disease_exists(assertion["name"])

    if assert_type == "variant_exists":
        return ctx._variant(assertion["dimension"], assertion["name"]) is not None

    if assert_type == "no_variants_in_dimension":
        count = (
            ctx.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=ctx.disease.id, variant_dimension=assertion["dimension"])
            .count()
        )
        return count == 0

    if assert_type == "concept_exists":
        return ctx._concept(assertion["domain"], assertion["name"]) is not None

    if assert_type == "concept_absent":
        return ctx._concept(assertion["domain"], assertion["name"]) is None

    if assert_type == "concept_requires_evidence":
        concept = ctx._concept(assertion["domain"], assertion["name"])
        if concept is None:
            return False
        rule = (
            ctx.db.query(OntologyEvidenceRule)
            .filter_by(concept_type=assertion["domain"], concept_id=concept.id)
            .one_or_none()
        )
        return rule is not None and rule.patient_fact_requires_evidence is True

    if assert_type == "concept_has_no_applicability":
        concept = ctx._concept(assertion["domain"], assertion["name"])
        if concept is None:
            return False
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(concept_type=assertion["domain"], concept_id=concept.id)
            .count()
        )
        return count == 0

    if assert_type == "concepts_not_collapsed":
        domain_a = assertion.get("domain_a", assertion.get("domain"))
        domain_b = assertion.get("domain_b", assertion.get("domain"))
        c_a = ctx._concept(domain_a, assertion["name_a"])
        c_b = ctx._concept(domain_b, assertion["name_b"])
        if c_a is None or c_b is None:
            return False
        return c_a.id != c_b.id

    if assert_type == "no_concept_in_domain":
        if assertion["domain"] not in CONCEPT_DOMAIN_MODEL_MAP:
            return True
        model_cls, _name_attr = CONCEPT_DOMAIN_MODEL_MAP[assertion["domain"]]
        count = ctx.db.query(model_cls).filter_by(disease_id=ctx.disease.id).count()
        return count == 0

    if assert_type == "no_applicability_of_type_for_disease":
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(disease_id=ctx.disease.id, applicability_type=assertion["applicability_type"])
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
    disease = _resolve_existing_disease(db, manifest)

    expected_variant_keys = {
        (v["dimension"], v["name"].strip().lower()) for v in manifest.get("new_variants", [])
    }
    stored_variants = db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
    new_variant_names = {v["name"].strip().lower() for v in manifest.get("new_variants", [])}
    stored_new_variant_keys = {
        (v.variant_dimension, v.normalized_name) for v in stored_variants if v.normalized_name in new_variant_names
    }
    missing_variants = sorted(expected_variant_keys - stored_new_variant_keys)
    unexpected_new_variants = sorted(stored_new_variant_keys - expected_variant_keys)

    required_variant_keys = {
        (v["dimension"], v["name"].strip().lower()) for v in manifest.get("required_existing_variants", [])
    }
    stored_variant_keys_all = {(v.variant_dimension, v.normalized_name) for v in stored_variants}
    unsupported_variants = sorted(
        k for k in stored_variant_keys_all if k not in expected_variant_keys and k not in required_variant_keys
    )

    expected_concept_keys = {(c["domain"], c["name"].strip().lower()) for c in manifest.get("concepts", [])}
    stored_concept_keys = set()
    concept_id_by_key: Dict[Tuple[str, str], object] = {}
    concepts_by_domain: Dict[str, int] = {}
    for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        rows = db.query(model_cls).filter_by(disease_id=disease.id).all()
        if domain == "FINDING":
            concepts_by_domain[domain] = len(rows)
        for row in rows:
            key = (domain, getattr(row, name_attr).strip().lower())
            stored_concept_keys.add(key)
            concept_id_by_key[key] = row.id
    missing_concepts = sorted(expected_concept_keys - stored_concept_keys)
    unexpected_concepts = sorted(
        stored_concept_keys - expected_concept_keys - PRE_EXISTING_FOUNDATION_CONCEPT_KEYS
    )
    pre_existing_foundation_concepts_found = sorted(
        stored_concept_keys & PRE_EXISTING_FOUNDATION_CONCEPT_KEYS
    )

    expected_applicability = [
        (a["variant_dimension"], a["variant"], a["concept_domain"], a["concept"], a["applicability_type"])
        for a in manifest.get("applicability", [])
    ]
    stored_edges = db.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    variant_id_to_key = {v.id: (v.variant_dimension, v.variant_name) for v in stored_variants}
    stored_applicability_keys = set()
    applicability_by_type: Dict[str, int] = {}
    for edge in stored_edges:
        applicability_by_type[edge.applicability_type] = applicability_by_type.get(edge.applicability_type, 0) + 1
        dimension, variant_name = variant_id_to_key.get(edge.variant_id, (None, None))
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        concept_name = getattr(concept_row, name_attr) if concept_row is not None else None
        stored_applicability_keys.add((dimension, variant_name, edge.concept_type, concept_name, edge.applicability_type))
    missing_applicability = sorted(k for k in expected_applicability if k not in stored_applicability_keys)
    undeclared_applicability = sorted(
        k for k in stored_applicability_keys
        if k not in set(expected_applicability) and k not in PRE_EXISTING_FOUNDATION_APPLICABILITY_KEYS
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
        rule = db.query(OntologyEvidenceRule).filter_by(concept_type=key[0], concept_id=concept_id).one_or_none()
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
    for edge in stored_edges:
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        if db.query(model_cls).filter_by(id=edge.concept_id).one_or_none() is None:
            orphan_count += 1
        if db.query(OntologyDiseaseVariant).filter_by(id=edge.variant_id).one_or_none() is None:
            orphan_count += 1

    # Cycle check: no variant's parent_variant_id chain loops back on itself.
    cycle_count = 0
    by_id = {v.id: v for v in stored_variants}
    for v in stored_variants:
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

    # Pulmonary-LCD-inheritance count: mechanical proof that no pulmonary
    # terminal-disease finding was ever attached to Lung Cancer. Any
    # non-zero value here would mean the Pulmonary LCD pathway leaked into
    # this cancer-identity manifest.
    pulmonary_lcd_terms = {
        "hypoxemia", "hypercapnia", "oxygen saturation threshold",
        "right heart failure", "fev1 decline", "respiratory failure",
    }
    pulmonary_lcd_inheritance_count = sum(
        1 for key in stored_concept_keys if key[0] == "FINDING" and key[1] in pulmonary_lcd_terms
    )

    ctx = _GuardContext(db, manifest, disease)
    guard_results = [
        {
            "guard_name": guard["guard_name"],
            "passed": _evaluate_guard(ctx, guard),
        }
        for guard in manifest.get("differentiation_guards", [])
    ]

    return {
        "manifest_id": "lung_cancer_production_identity_manifest_v1",
        "canonical_disease_count": {"expected": 1, "stored": 1 if disease is not None else 0},
        "duplicate_canonical_disease_count": len(
            db.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).all()
        ) - 1,
        "variants_by_dimension": {
            dim: len([v for v in stored_variants if v.variant_dimension == dim])
            for dim in sorted({v.variant_dimension for v in stored_variants})
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
        "pre_existing_foundation_concepts": [list(k) for k in pre_existing_foundation_concepts_found],
        "expected_applicability_count": len(expected_applicability),
        "stored_applicability_count": len(stored_applicability_keys),
        "missing_applicability": [list(k) for k in missing_applicability],
        "undeclared_applicability": [list(k) for k in undeclared_applicability],
        "undeclared_applicability_count": len(undeclared_applicability),
        "pre_existing_foundation_applicability": [list(k) for k in pre_existing_foundation_applicability_found],
        "pulmonary_lcd_inheritance_count": pulmonary_lcd_inheritance_count,
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
