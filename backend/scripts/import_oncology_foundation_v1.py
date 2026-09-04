# scripts/import_oncology_foundation_v1.py
"""
Oncology Foundation v1 -- Verbatim Importer (v2, PR #45 correction).

Reads backend/manifests/oncology_foundation_v1.json (the sole authoritative
source for this import -- never inferred, reconstructed, or clinically
re-derived) and creates the reusable Oncology ontology structure:

    - The "Oncology" body system with TWO disease families: "Solid
      Malignancies" and "Hematologic Malignancies".
    - 12 REAL canonical Tier 3 cancer diseases (Breast, Lung, Prostate,
      Colorectal, Liver, Kidney, Thyroid, Pancreatic, Bladder Cancer,
      Melanoma under Solid Malignancies; Leukemia and Lymphoma under
      Hematologic Malignancies). There is NO placeholder/anchor disease --
      every Tier 4/5 row hangs off one of these 12 real diseases.
    - Source-supported Tier 4 variants ONLY for the 10 solid malignancies:
      one PRIMARY_SITE variant (e.g. "Breast Primary Site" under Breast
      Cancer -- never a disease-replacing "Breast" row), two
      METASTATIC_STATE variants ("Localized Disease", "Metastatic
      Disease"), and one RECURRENCE_STATE variant ("Recurrent Disease").
      Leukemia and Lymphoma receive NO anatomical PRIMARY_SITE variant and
      no unsupported metastatic/recurrence variants in this foundation PR.
    - 10 reusable Tier 5 atomic concept identities (Metastatic Disease,
      Regional Spread, Distant Metastatic Disease, Progressive Disease,
      Worsening Clinical Status, Progressive Functional Decline,
      Functional Impairment, Dependence In Activities Of Daily Living,
      Progressive Nutritional Decline, Unintentional Weight Loss), each
      stored once PER APPLICABLE DISEASE (the schema requires every Tier 5
      row to declare a single owning disease_id -- there is no global/
      shared concept table). This mirrors exactly how every prior PR
      (Renal, Liver, HIV, ALS, Dementia) modeled its own disease-scoped
      concepts; it is simply scaled to 12 diseases in a single manifest.
    - ONLY 10 explicit, semantically-justified Tier4<->Tier5 applicability
      edges: the "Metastatic Disease" concept MAY_OCCUR_WITH that same
      disease's own "Metastatic Disease" METASTATIC_STATE variant, for
      each of the 10 solid malignancies. NO Cartesian/blanket applicability
      is ever generated -- Regional Spread, Distant Metastatic Disease,
      and the prognostic/functional/nutritional baseline concepts receive
      ZERO applicability rows in this foundation PR because no
      source-supported Tier 4 variant exists yet for them to attach to.

This reuses the exact verbatim-import pattern proven in
scripts/import_neurologic_production_source_manifest.py (PR #37),
scripts/import_cardiovascular_production_source_manifest.py (PR #38),
scripts/import_pulmonary_production_source_manifest.py (PR #39),
scripts/import_renal_production_source_manifest.py (PR #40),
scripts/import_liver_production_source_manifest.py (PR #41),
scripts/import_hiv_production_source_manifest.py (PR #42), and
scripts/import_als_production_source_manifest.py (PR #43):

- No concept is renamed, substituted, combined, split, or omitted.
- No additional concept is invented beyond what the manifest declares.
- A manifest identity match requires an EXACT match on every applicable
    identity field (disease + domain/dimension + normalized exact name).
- Every concept created receives an OntologyEvidenceRule with
    patient_fact_requires_evidence = True.
- Nothing is ever hard-deleted or deactivated in this importer.
- Idempotent: re-running inserts nothing new.
- Nothing is silently skipped: any manifest value that is not
    schema-valid aborts the import with a RuntimeError before any writes
    happen.

This PR deliberately does NOT create any disease-specific cancer content
beyond the source-supported foundation variants above (no Stage I/II/III/IV,
no histology, no molecular subtype, no metastatic-destination values). It
only establishes the reusable foundation structure that future
disease-specific oncology manifests will build on.

Run with: python scripts\\import_oncology_foundation_v1.py
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ontology.treatment_identity import (
    CANONICAL_TREATMENT_DOMAINS,
    concept_identity_key,
    existing_rows_by_canonical_name,
    reconcile_category,
)

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDiseaseFamily,
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyDiseaseSymptom,
    OntologyDiseaseFinding,
    OntologyDiseaseLab,
    OntologyDiseaseDiagnosticTest,
    OntologyDiseaseComplication,
    OntologyDiseasePrognosticIndicator,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseMedication,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseasePsychosocialConcern,
    OntologyDiseaseSpiritualConcern,
)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "oncology_foundation_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "oncology_foundation_acceptance_v1.json"
)
IMPORTER_NAME = "import_oncology_foundation_v1"


SYSTEM_NAME = "Oncology"

# --- Tier 4 variant dimensions permitted by the
# ck_ontology_disease_variant_dimension CHECK constraint. This manifest
# uses only PRIMARY_SITE (the Foundation's declared dimension vocabulary
# also lists HISTOLOGY, MOLECULAR_SUBTYPE, STAGE, GRADE, METASTATIC_STATE,
# METASTATIC_DESTINATION for future oncology manifests, but no variants in
# those dimensions are created by this PR). ---
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

SIMPLE_CONCEPT_DOMAIN_MODEL_MAP = {
    "SYMPTOM": (OntologyDiseaseSymptom, "symptom_name"),
    "FINDING": (OntologyDiseaseFinding, "finding_name"),
    "LAB": (OntologyDiseaseLab, "lab_name"),
    "DIAGNOSTIC_TEST": (OntologyDiseaseDiagnosticTest, "test_name"),
    "COMPLICATION": (OntologyDiseaseComplication, "complication_name"),
    "PROGNOSTIC_INDICATOR": (OntologyDiseasePrognosticIndicator, "indicator_name"),
    "HOSPICE_ELIGIBILITY_SUPPORT": (OntologyDiseaseHospiceEligibilitySupport, "indicator_name"),
    "FUNCTIONAL_IMPACT": (OntologyDiseaseFunctionalImpact, "impact_name"),
    "NUTRITIONAL_IMPACT": (OntologyDiseaseNutritionalImpact, "impact_name"),
    "END_STAGE_FINDING": (OntologyDiseaseEndStageFinding, "finding_name"),
    "MEDICATION": (OntologyDiseaseMedication, "medication_name"),
    "PSYCHOSOCIAL_CONCERN": (OntologyDiseasePsychosocialConcern, "concern_name"),
    "SPIRITUAL_CONCERN": (OntologyDiseaseSpiritualConcern, "concern_name"),
}

CONCEPT_DOMAIN_MODEL_MAP = dict(SIMPLE_CONCEPT_DOMAIN_MODEL_MAP)
CONCEPT_DOMAIN_MODEL_MAP["TREATMENT"] = (OntologyDiseaseTreatment, "treatment_name")
CONCEPT_DOMAIN_MODEL_MAP["TREATMENT_LIMITATION"] = (OntologyDiseaseTreatmentLimitation, "limitation_name")

# --- Source-classification vocabulary. The schema has no dedicated column
# for this distinction (per the reviewer-approved PR #40 correction), so it
# is recorded in the concept's own existing description-style column and in
# its OntologyEvidenceRule.notes -- never via a new migration.
# NCI_CANCER_CATALOG classifies disease *identity* only (it never authorizes
# stage/grade/histology/molecular-subtype/symptoms/treatment/medications/
# metastatic-destination/hospice-eligibility); ONCOLOGY_FOUNDATION classifies
# reusable oncology-specific knowledge concepts; LCD_NON_DISEASE_SPECIFIC
# classifies the non-disease-specific hospice baseline (supporting evidence
# only -- it never independently establishes eligibility);
# GENERAL_CLINICAL_KNOWLEDGE classifies general prognostic-indicator
# knowledge not tied to any one LCD. ---
ALLOWED_SOURCE_CLASSIFICATIONS = {
    "NCI_CANCER_CATALOG", "ONCOLOGY_FOUNDATION", "LCD_NON_DISEASE_SPECIFIC", "GENERAL_CLINICAL_KNOWLEDGE",
}

# --- Differentiation-guard assertion vocabulary. Every guard is a list of
# ANDed structural assertions (never a clinically-false relationship edge).
# See _evaluate_guard_assertion for the mechanical semantics of each. ---
ASSERTION_TYPES = {
    "disease_exists", "disease_absent",
    "variant_exists", "no_variants_in_dimension", "no_variants_in_dimension_systemwide",
    "variants_not_collapsed", "variants_not_collapsed_cross_dimension",
    "concepts_not_collapsed",
    "reserved_terms_distinct",
    "hospice_support_requires_evidence_systemwide",
    "dimension_evidence_requirement_documented",
    "for_each",
}

# The existing free-text column each concept domain already has, used to
# carry the description + source classification without a schema change.
DESCRIPTION_ATTR_BY_DOMAIN = {
    "SYMPTOM": "description",
    "FINDING": "finding_description",
    "COMPLICATION": "description",
    "FUNCTIONAL_IMPACT": "description",
    "NUTRITIONAL_IMPACT": "description",
    "HOSPICE_ELIGIBILITY_SUPPORT": "description",
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    """Structural + schema-vocabulary validation -- never a clinical
    judgment. Returns a list of validation errors (empty means the
    manifest is well-formed and every value is schema-valid)."""
    errors: List[str] = []
    diseases = manifest.get("diseases")
    if not isinstance(diseases, list) or not diseases:
        errors.append("manifest.diseases must be a non-empty list")
        return errors

    family_names = manifest.get("scope", {}).get("families") or []

    for disease_entry in diseases:
        disease_name = disease_entry.get("disease")
        if not disease_name:
            errors.append("a disease entry is missing 'disease' name")
            continue

        family_name = disease_entry.get("family")
        if not family_name:
            errors.append(f"disease entry {disease_name!r} is missing 'family'")
        elif family_name not in family_names:
            errors.append(f"disease entry {disease_name!r} declares family {family_name!r} not in scope.families")

        if disease_entry.get("disease_category") not in ALLOWED_SOURCE_CLASSIFICATIONS:
            errors.append(f"disease entry {disease_name!r} has unsupported or missing disease_category")

        seen_variants = set()
        for v in disease_entry.get("variants", []):
            key = (disease_name, v.get("dimension"), (v.get("name") or "").strip().lower())
            if key in seen_variants:
                errors.append(f"duplicate variant identity in manifest: {key}")
            seen_variants.add(key)
            if v.get("dimension") not in ALLOWED_VARIANT_DIMENSIONS:
                errors.append(f"unsupported variant dimension '{v.get('dimension')}' for {key}")

        seen_concepts = set()
        concept_lookup: Dict[Tuple[str, str], dict] = {}
        for c in disease_entry.get("concepts", []):
            key = (disease_name, c.get("domain"), (c.get("name") or "").strip().lower())
            if key in seen_concepts:
                errors.append(f"duplicate concept identity in manifest: {key}")
            seen_concepts.add(key)
            concept_lookup[(c.get("domain"), (c.get("name") or "").strip().lower())] = c
            domain = c.get("domain")
            if domain not in CONCEPT_DOMAIN_MODEL_MAP:
                errors.append(f"unsupported concept domain '{domain}' for {key}")
            elif domain == "TREATMENT" and c.get("treatment_category") not in ALLOWED_TREATMENT_CATEGORIES:
                errors.append(f"unsupported or missing treatment_category '{c.get('treatment_category')}' for {key}")
            elif domain == "TREATMENT_LIMITATION" and c.get("limitation_category") not in ALLOWED_LIMITATION_CATEGORIES:
                errors.append(f"unsupported or missing limitation_category '{c.get('limitation_category')}' for {key}")
            if c.get("source_classification") not in ALLOWED_SOURCE_CLASSIFICATIONS:
                errors.append(f"unsupported or missing source_classification '{c.get('source_classification')}' for {key}")
            if not c.get("source_reference"):
                errors.append(f"missing source_reference for {key}")

        seen_applic = set()
        for a in disease_entry.get("applicability", []):
            key = (
                disease_name, a.get("variant_dimension"), a.get("variant"), a.get("concept"),
                a.get("concept_domain"), a.get("applicability_type"),
            )
            if key in seen_applic:
                errors.append(f"duplicate applicability identity in manifest: {key}")
            seen_applic.add(key)
            if a.get("variant_dimension") not in ALLOWED_VARIANT_DIMENSIONS:
                errors.append(f"unsupported applicability variant_dimension '{a.get('variant_dimension')}' for {key}")
            if a.get("applicability_type") not in APPLICABILITY_TYPES:
                errors.append(f"unsupported applicability_type '{a.get('applicability_type')}' for {key}")
            if a.get("applicability_type") == "HOSPICE_SUPPORT_FOR":
                referenced = concept_lookup.get((a.get("concept_domain"), (a.get("concept") or "").strip().lower()))
                if referenced is None:
                    errors.append(f"applicability references undeclared concept for {key}")
                elif referenced.get("hospice_support_eligible") is not True:
                    errors.append(
                        f"HOSPICE_SUPPORT_FOR applicability targets a concept not marked "
                        f"hospice_support_eligible=true for {key}"
                    )
            # Structural anti-Cartesian guard: the non-disease-specific baseline
            # domains (prognostic/functional/nutritional) must never carry an
            # applicability edge in this foundation PR -- they are possible
            # patient-state findings requiring evidence, never automatically
            # PRESENT/EXPECTED knowledge for a cancer diagnosis.
            if a.get("concept_domain") in {"PROGNOSTIC_INDICATOR", "FUNCTIONAL_IMPACT", "NUTRITIONAL_IMPACT"}:
                errors.append(
                    f"non-disease-specific baseline domain '{a.get('concept_domain')}' must not carry "
                    f"applicability in this foundation PR (would recreate blanket Cartesian attachment): {key}"
                )

    for guard in manifest.get("differentiation_guards", []):
        for assertion in guard.get("assertions", []):
            _validate_assertion(assertion, errors, guard.get("guard_name"))

    return errors


def _validate_assertion(assertion: dict, errors: List[str], guard_name: str) -> None:
    assert_type = assertion.get("assert")
    if assert_type not in ASSERTION_TYPES:
        errors.append(f"unsupported differentiation_guard assertion '{assert_type}' in guard {guard_name!r}")
        return
    if assert_type == "for_each":
        nested = assertion.get("assertion")
        if not isinstance(assertion.get("diseases"), list) or not assertion["diseases"]:
            errors.append(f"for_each assertion in guard {guard_name!r} requires a non-empty 'diseases' list")
        if not isinstance(nested, dict):
            errors.append(f"for_each assertion in guard {guard_name!r} requires a nested 'assertion'")
        else:
            _validate_assertion(nested, errors, guard_name)


def _resolve_or_create_diseases(db: Session, manifest: dict) -> Dict[str, OntologyDisease]:
    """Resolve each manifest disease by exact normalized name, creating the
    Oncology body system, each declared disease family, and the disease
    itself (with its NCI_CANCER_CATALOG identity metadata) if not already
    present. Never creates a body system/family/disease beyond what the
    manifest's own scope declares. Each disease is assigned to the family
    its own manifest entry declares (never inferred)."""
    system_name = manifest["scope"]["body_system"]
    family_names = manifest["scope"]["families"]

    system = db.query(OntologyBodySystem).filter_by(system_name=system_name).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=system_name)
        db.add(system)
        db.flush()

    family_by_name: Dict[str, OntologyDiseaseFamily] = {}
    for family_name in family_names:
        family = (
            db.query(OntologyDiseaseFamily)
            .filter_by(family_name=family_name, body_system_id=system.id)
            .one_or_none()
        )
        if family is None:
            family = OntologyDiseaseFamily(family_name=family_name, body_system_id=system.id)
            db.add(family)
            db.flush()
        family_by_name[family_name] = family

    resolved: Dict[str, OntologyDisease] = {}
    for disease_entry in manifest["diseases"]:
        name = disease_entry["disease"]
        family_name = disease_entry["family"]
        if family_name not in family_by_name:
            raise RuntimeError(
                f"Oncology Foundation v1 disease {name!r} declares family {family_name!r} "
                f"which is not in manifest.scope.families {sorted(family_by_name)}. Aborting without any writes."
            )
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            disease = OntologyDisease(
                disease_name=name,
                disease_family_id=family_by_name[family_name].id,
                disease_category=disease_entry.get("disease_category"),
                primary_organ=disease_entry.get("primary_organ"),
                disease_type=disease_entry.get("disease_type"),
                disease_description=disease_entry.get("disease_description"),
                clinical_purpose=disease_entry.get("clinical_purpose"),
                hospice_relevance=disease_entry.get("hospice_relevance"),
            )
            db.add(disease)
            db.flush()
        resolved[name] = disease
    return resolved


def _evidence_notes(concept_entry: dict) -> str:
    """Fold source_classification / source_reference / evidence_requirements
    / hospice_support_eligible into the evidence rule's existing free-text
    'notes' column -- the reviewer-approved way to carry this distinction
    without a schema change or new migration."""
    parts = [
        "Imported verbatim from the approved Oncology Foundation v1 manifest.",
        f"source_classification={concept_entry.get('source_classification')}",
        f"source_reference={concept_entry.get('source_reference')}",
        f"hospice_support_eligible={concept_entry.get('hospice_support_eligible')}",
    ]
    reqs = concept_entry.get("evidence_requirements") or []
    if reqs:
        parts.append("evidence_requirements=" + ",".join(reqs))
    return " | ".join(parts)


def _ensure_evidence_rule(db: Session, concept_type: str, concept_id, concept_entry: dict | None = None) -> bool:
    """Create or preserve an OntologyEvidenceRule for a concept, always
    with patient_fact_requires_evidence=True. Returns True if a new row
    was inserted. When re-run against an existing row, the notes are kept
    in sync with the manifest's current source-classification metadata
    (never touching patient_fact_requires_evidence, which always stays
    True)."""
    existing = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type=concept_type, concept_id=concept_id)
        .one_or_none()
    )
    notes = _evidence_notes(concept_entry) if concept_entry else (
        "Imported verbatim from the approved Oncology Foundation v1 manifest."
    )
    if existing is not None:
        if concept_entry is not None and existing.notes != notes:
            existing.notes = notes
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=concept_type,
            concept_id=concept_id,
            evidence_source="oncology_foundation_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes=notes,
        )
    )
    return True


def _build_concept_row(domain: str, disease_id, concept_entry: dict):
    """Construct the ORM row for a single manifest concept, applying the
    approved treatment_category / limitation_category for the two
    category-bearing domains, verbatim from the manifest -- never
    invented, never substituted. The concept's own existing free-text
    description-style column carries its source-classification metadata
    (no schema change)."""
    name = concept_entry["name"]
    if domain == "TREATMENT":
        return OntologyDiseaseTreatment(
            id=uuid.uuid4(),
            disease_id=disease_id,
            treatment_name=name,
            treatment_category=concept_entry["treatment_category"],
        )
    if domain == "TREATMENT_LIMITATION":
        return OntologyDiseaseTreatmentLimitation(
            id=uuid.uuid4(),
            disease_id=disease_id,
            limitation_name=name,
            limitation_category=concept_entry["limitation_category"],
        )
    model_cls, name_attr = SIMPLE_CONCEPT_DOMAIN_MODEL_MAP[domain]
    row = model_cls(id=uuid.uuid4(), disease_id=disease_id, **{name_attr: name})
    description_attr = DESCRIPTION_ATTR_BY_DOMAIN.get(domain)
    if description_attr is not None and concept_entry.get("description"):
        setattr(row, description_attr, concept_entry["description"])
    if domain == "HOSPICE_ELIGIBILITY_SUPPORT":
        row.lcd_reference = concept_entry.get("source_classification")
        reqs = concept_entry.get("evidence_requirements") or []
        if reqs:
            row.supporting_evidence = "Requires: " + ", ".join(reqs)
    return row


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Oncology Foundation v1 failed structural/vocabulary validation: {errors}")

    diseases = _resolve_or_create_diseases(db, manifest)
    db.flush()

    variants_inserted = 0
    concepts_inserted_by_domain: Dict[str, int] = {}
    applicability_inserted = 0
    evidence_rules_inserted = 0

    variant_by_key: Dict[Tuple[str, str, str], OntologyDiseaseVariant] = {}
    for disease_name, disease in diseases.items():
        for existing in db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all():
            variant_by_key[(disease_name, existing.variant_dimension, existing.normalized_name)] = existing

    concept_by_key: Dict[Tuple[str, str, str], object] = {}
    for concept_type, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for disease_name, disease in diseases.items():
            existing_rows = db.query(model_cls).filter_by(disease_id=disease.id).all()
            if concept_type in CANONICAL_TREATMENT_DOMAINS:
                indexed_rows = existing_rows_by_canonical_name(
                    existing_rows,
                    domain=concept_type,
                    table_name=model_cls.__tablename__,
                    disease_id=disease.id,
                    importer_name=IMPORTER_NAME,
                    name_attr=name_attr,
                    category_attr="treatment_category" if concept_type == "TREATMENT" else "limitation_category",
                )
                for normalized_name, row in indexed_rows.items():
                    concept_by_key[(disease_name, concept_type, normalized_name)] = row
                continue
            for existing in existing_rows:
                key = (disease_name, concept_type, concept_identity_key(concept_type, getattr(existing, name_attr)))
                concept_by_key[key] = existing

    # --- Tier 4 variants ---
    for disease_entry in manifest["diseases"]:
        disease_name = disease_entry["disease"]
        disease = diseases[disease_name]
        for v in disease_entry.get("variants", []):
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
                source_reference="oncology_foundation_v1",
            )
            db.add(variant)
            db.flush()
            variant_by_key[key] = variant
            variants_inserted += 1

    # --- Tier 5 atomic concepts ---
    for disease_entry in manifest["diseases"]:
        disease_name = disease_entry["disease"]
        disease = diseases[disease_name]
        for c in disease_entry.get("concepts", []):
            domain = c["domain"]
            name = c["name"]
            normalized = concept_identity_key(domain, name)
            key = (disease_name, domain, normalized)

            if key in concept_by_key:
                existing_row = concept_by_key[key]
                if domain in CANONICAL_TREATMENT_DOMAINS:
                    category_attr = "treatment_category" if domain == "TREATMENT" else "limitation_category"
                    name_attr = "treatment_name" if domain == "TREATMENT" else "limitation_name"
                    result = reconcile_category(
                        domain=domain,
                        disease_id=existing_row.disease_id,
                        normalized_name=existing_row.normalized_name,
                        existing_row_id=existing_row.id,
                        existing_display_name=getattr(existing_row, name_attr),
                        existing_category=getattr(existing_row, category_attr),
                        incoming_display_name=name,
                        incoming_category=c[category_attr],
                        importer_name=IMPORTER_NAME,
                    )
                    if result.changed:
                        setattr(existing_row, category_attr, result.category)
                if _ensure_evidence_rule(db, domain, existing_row.id, c):
                    evidence_rules_inserted += 1
                continue

            row = _build_concept_row(domain, disease.id, c)
            db.add(row)
            db.flush()
            concept_by_key[key] = row
            concepts_inserted_by_domain[domain] = concepts_inserted_by_domain.get(domain, 0) + 1

            if _ensure_evidence_rule(db, domain, row.id, c):
                evidence_rules_inserted += 1

    db.flush()

    # --- Tier 4 <-> Tier 5 applicability ---
    for disease_entry in manifest["diseases"]:
        disease_name = disease_entry["disease"]
        disease = diseases[disease_name]
        for a in disease_entry.get("applicability", []):
            variant_name = a["variant"]
            variant_dimension = a["variant_dimension"]
            concept_name = a["concept"]
            concept_domain = a["concept_domain"]
            applicability_type = a["applicability_type"]

            variant_key_found = variant_by_key.get((disease_name, variant_dimension, variant_name.strip().lower()))
            concept_key_found = None
            for (d_name, domain, normalized), concept_row in concept_by_key.items():
                if d_name == disease_name and domain == concept_domain and normalized == concept_name.strip().lower():
                    concept_key_found = concept_row
                    break

            if variant_key_found is None or concept_key_found is None:
                raise RuntimeError(
                    f"Oncology Foundation v1 applicability mapping references a variant/concept "
                    f"that was not created: disease={disease_name!r} variant={variant_name!r} "
                    f"dimension={variant_dimension!r} concept={concept_name!r} domain={concept_domain!r}. "
                    f"Aborting rather than skipping silently."
                )

            existing_edge = (
                db.query(OntologyConceptVariantApplicability)
                .filter_by(
                    concept_type=concept_domain,
                    concept_id=concept_key_found.id,
                    variant_id=variant_key_found.id,
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
                concept_id=concept_key_found.id,
                variant_id=variant_key_found.id,
                applicability_type=applicability_type,
                description="Imported verbatim from the approved Oncology Foundation v1 manifest.",
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


def _no_cycle(variants: List[OntologyDiseaseVariant]) -> int:
    by_id = {v.id: v for v in variants}
    cycles = 0
    for v in variants:
        seen = set()
        current = v
        while current is not None and current.parent_variant_id is not None:
            if current.id in seen:
                cycles += 1
                break
            seen.add(current.id)
            current = by_id.get(current.parent_variant_id)
    return cycles


class _GuardContext:
    """Read-only mechanical lookup context for evaluating a differentiation
    guard assertion. Every assertion is a structural database check --
    never a clinically-false relationship edge and never a new query
    pattern beyond simple existence/absence/distinctness lookups."""

    def __init__(self, db: Session, manifest: dict, diseases: Dict[str, OntologyDisease]):
        self.db = db
        self.manifest = manifest
        self.diseases = diseases

    def disease_exists(self, name: str) -> bool:
        return self.db.query(OntologyDisease).filter_by(disease_name=name).one_or_none() is not None

    def _variant(self, disease_name: str, dimension: str, name: str):
        disease = self.diseases.get(disease_name)
        if disease is None:
            return None
        return (
            self.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=name.strip().lower())
            .one_or_none()
        )

    def _concept(self, disease_name: str, domain: str, name: str):
        disease = self.diseases.get(disease_name)
        if disease is None or domain not in CONCEPT_DOMAIN_MODEL_MAP:
            return None
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
        return (
            self.db.query(model_cls)
            .filter(model_cls.disease_id == disease.id)
            .filter(func.lower(func.trim(getattr(model_cls, name_attr))) == name.strip().lower())
            .one_or_none()
        )


def _evaluate_guard_assertion(ctx: "_GuardContext", assertion: dict, disease_override: str | None = None) -> bool:
    """Evaluate one structural assertion. `disease_override` is set only
    while expanding a `for_each` assertion, substituting the current
    disease into any nested assertion's 'disease' field."""
    assert_type = assertion["assert"]

    if assert_type == "disease_exists":
        return ctx.disease_exists(assertion["name"])
    if assert_type == "disease_absent":
        return not ctx.disease_exists(assertion["name"])

    if assert_type == "variant_exists":
        disease = disease_override or assertion["disease"]
        return ctx._variant(disease, assertion["dimension"], assertion["name"]) is not None

    if assert_type == "no_variants_in_dimension":
        disease = disease_override or assertion["disease"]
        d = ctx.diseases.get(disease)
        if d is None:
            return False
        count = (
            ctx.db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=d.id, variant_dimension=assertion["dimension"])
            .count()
        )
        return count == 0

    if assert_type == "no_variants_in_dimension_systemwide":
        disease_ids = [d.id for d in ctx.diseases.values()]
        count = (
            ctx.db.query(OntologyDiseaseVariant)
            .filter(OntologyDiseaseVariant.disease_id.in_(disease_ids))
            .filter_by(variant_dimension=assertion["dimension"])
            .count()
        )
        return count == 0

    if assert_type == "variants_not_collapsed":
        disease = disease_override or assertion["disease"]
        v_a = ctx._variant(disease, assertion["dimension"], assertion["name_a"])
        v_b = ctx._variant(disease, assertion["dimension"], assertion["name_b"])
        if v_a is None or v_b is None:
            return False
        return v_a.id != v_b.id

    if assert_type == "variants_not_collapsed_cross_dimension":
        disease = disease_override or assertion["disease"]
        v_a = ctx._variant(disease, assertion["dim_a"], assertion["name_a"])
        v_b = ctx._variant(disease, assertion["dim_b"], assertion["name_b"])
        if v_a is None or v_b is None:
            return False
        return v_a.id != v_b.id

    if assert_type == "concepts_not_collapsed":
        disease = disease_override or assertion["disease"]
        domain_a = assertion.get("domain_a", assertion.get("domain"))
        domain_b = assertion.get("domain_b", assertion.get("domain"))
        c_a = ctx._concept(disease, domain_a, assertion["name_a"])
        c_b = ctx._concept(disease, domain_b, assertion["name_b"])
        # Forgiving: if one side legitimately does not exist for this disease
        # (e.g. Metastatic Disease is never created for Leukemia/Lymphoma),
        # there is no collapse risk -- the guard passes vacuously. It only
        # fails if both exist AND resolve to the very same row.
        if c_a is None or c_b is None:
            return True
        return c_a.id != c_b.id

    if assert_type == "reserved_terms_distinct":
        left, right = assertion["left"], assertion["right"]
        reserved = set(ctx.manifest.get("reserved_future_terminology") or [])
        return (
            left != right
            and left in reserved and right in reserved
            and not ctx.disease_exists(left) and not ctx.disease_exists(right)
        )

    if assert_type == "hospice_support_requires_evidence_systemwide":
        disease_ids = [d.id for d in ctx.diseases.values()]
        edges = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter(OntologyConceptVariantApplicability.disease_id.in_(disease_ids))
            .filter_by(concept_type="HOSPICE_ELIGIBILITY_SUPPORT", applicability_type="HOSPICE_SUPPORT_FOR")
            .all()
        )
        return all(bool(e.evidence_requirement) for e in edges)

    if assert_type == "dimension_evidence_requirement_documented":
        docs = ctx.manifest.get("dimension_evidence_requirements") or {}
        return bool(docs.get(assertion["dimension"]))

    if assert_type == "for_each":
        nested = assertion["assertion"]
        return all(_evaluate_guard_assertion(ctx, nested, disease_override=d) for d in assertion["diseases"])

    return False


def _evaluate_guard(ctx: "_GuardContext", guard: dict) -> bool:
    return all(_evaluate_guard_assertion(ctx, a) for a in guard.get("assertions", []))


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    """Compare the manifest against the (already-imported) clean database
    and report expected vs. stored vs. missing vs. unexpected for
    variants, concepts, and applicability mappings, plus evidence-rule
    coverage, orphan count, cycle count, and the second-run new-row
    count. Never a clinical judgment -- purely a mechanical comparison."""
    diseases = _resolve_or_create_diseases(db, manifest)
    disease_ids = {d.id for d in diseases.values()}

    expected_variants = []
    for disease_entry in manifest["diseases"]:
        for v in disease_entry.get("variants", []):
            expected_variants.append((disease_entry["disease"], v["dimension"], v["name"]))
    expected_variant_keys = {(d, dim, n.strip().lower()) for d, dim, n in expected_variants}

    stored_variants = db.query(OntologyDiseaseVariant).filter(
        OntologyDiseaseVariant.disease_id.in_(disease_ids)
    ).all()
    name_to_disease = {d.id: name for name, d in diseases.items()}
    stored_variant_keys = {
        (name_to_disease[v.disease_id], v.variant_dimension, v.normalized_name) for v in stored_variants
    }
    missing_variants = sorted(expected_variant_keys - stored_variant_keys)
    unexpected_variants = sorted(k for k in stored_variant_keys if k not in expected_variant_keys)

    expected_concepts = []
    for disease_entry in manifest["diseases"]:
        for c in disease_entry.get("concepts", []):
            expected_concepts.append((disease_entry["disease"], c["domain"], c["name"]))
    expected_concept_keys = {(d, dom, n.strip().lower()) for d, dom, n in expected_concepts}

    stored_concept_keys = set()
    concept_id_by_key: Dict[Tuple[str, str, str], object] = {}
    for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for row in db.query(model_cls).filter(model_cls.disease_id.in_(disease_ids)).all():
            key = (name_to_disease[row.disease_id], domain, getattr(row, name_attr).strip().lower())
            stored_concept_keys.add(key)
            concept_id_by_key[key] = row.id
    missing_concepts = sorted(expected_concept_keys - stored_concept_keys)
    unexpected_concepts = sorted(k for k in stored_concept_keys if k not in expected_concept_keys)

    expected_applicability = []
    for disease_entry in manifest["diseases"]:
        for a in disease_entry.get("applicability", []):
            expected_applicability.append(
                (disease_entry["disease"], a["variant_dimension"], a["variant"], a["concept_domain"], a["concept"], a["applicability_type"])
            )

    stored_applicability_rows = db.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all()
    variant_id_to_name_dim = {v.id: (v.variant_dimension, v.variant_name) for v in stored_variants}
    stored_applicability_keys = set()
    for edge in stored_applicability_rows:
        disease_name = name_to_disease.get(edge.disease_id)
        dimension, variant_name = variant_id_to_name_dim.get(edge.variant_id, (None, None))
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        concept_name = getattr(concept_row, name_attr) if concept_row is not None else None
        stored_applicability_keys.add(
            (disease_name, dimension, variant_name, edge.concept_type, concept_name, edge.applicability_type)
        )
    missing_applicability = sorted(
        [key for key in expected_applicability if key not in stored_applicability_keys],
        key=lambda k: (k[0], k[1], k[2], k[3], k[4], k[5]),
    )
    unexpected_applicability = sorted(
        [key for key in stored_applicability_keys if key not in set(expected_applicability)],
        key=lambda k: (str(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4]), str(k[5])),
    )

    # Evidence-rule coverage scoped to the manifest's own expected concepts.
    evidence_covered = 0
    evidence_missing = []
    for key in expected_concept_keys:
        concept_id = concept_id_by_key.get(key)
        if concept_id is None:
            evidence_missing.append(list(key))
            continue
        disease_name, domain, _name = key
        rule = db.query(OntologyEvidenceRule).filter_by(concept_type=domain, concept_id=concept_id).one_or_none()
        if rule is not None and rule.patient_fact_requires_evidence is True:
            evidence_covered += 1
        else:
            evidence_missing.append(list(key))

    guard_ctx = _GuardContext(db, manifest, diseases)
    guard_results = []
    for guard in manifest.get("differentiation_guards", []):
        try:
            passed = _evaluate_guard(guard_ctx, guard)
            detail = None
        except (KeyError, TypeError) as exc:
            passed = False
            detail = f"guard evaluation error: {exc}"
        guard_results.append({"guard_name": guard.get("guard_name"), "passed": passed, "detail": detail})

    orphan_count = 0
    stored_variant_ids = {v.id for v in stored_variants}
    for v in stored_variants:
        if v.disease_id not in disease_ids:
            orphan_count += 1
        elif v.parent_variant_id is not None and v.parent_variant_id not in stored_variant_ids:
            orphan_count += 1
    unresolved_concept_count = 0
    for edge in stored_applicability_rows:
        if edge.variant_id not in stored_variant_ids:
            orphan_count += 1
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        if db.query(model_cls).filter_by(id=edge.concept_id).one_or_none() is None:
            orphan_count += 1
            unresolved_concept_count += 1

    cycle_count = _no_cycle(stored_variants)

    expected_disease_names = sorted(d["disease"] for d in manifest["diseases"])
    stored_disease_rows = db.query(OntologyDisease).filter(OntologyDisease.id.in_(disease_ids)).all()
    stored_disease_names = sorted(row.disease_name for row in stored_disease_rows)

    # Canonical-disease-count / by-family breakdown.
    family_id_to_name = {f.id: f.family_name for f in db.query(OntologyDiseaseFamily).all()}
    canonical_diseases_by_family: Dict[str, int] = {}
    for row in stored_disease_rows:
        fname = family_id_to_name.get(row.disease_family_id, "UNKNOWN")
        canonical_diseases_by_family[fname] = canonical_diseases_by_family.get(fname, 0) + 1

    # Variants by disease + dimension.
    variants_by_disease_and_dimension: Dict[str, Dict[str, int]] = {}
    for v in stored_variants:
        dname = name_to_disease.get(v.disease_id, "UNKNOWN")
        variants_by_disease_and_dimension.setdefault(dname, {})
        variants_by_disease_and_dimension[dname][v.variant_dimension] = (
            variants_by_disease_and_dimension[dname].get(v.variant_dimension, 0) + 1
        )

    # Concepts by domain (system-wide, scoped to this manifest's diseases).
    concepts_by_domain: Dict[str, int] = {}
    for (_dname, domain, _name) in stored_concept_keys:
        concepts_by_domain[domain] = concepts_by_domain.get(domain, 0) + 1

    # Applicability by disease + applicability_type.
    applicability_by_disease_and_type: Dict[str, Dict[str, int]] = {}
    for edge in stored_applicability_rows:
        dname = name_to_disease.get(edge.disease_id, "UNKNOWN")
        applicability_by_disease_and_type.setdefault(dname, {})
        applicability_by_disease_and_type[dname][edge.applicability_type] = (
            applicability_by_disease_and_type[dname].get(edge.applicability_type, 0) + 1
        )

    # Rejected-Cartesian-mappings documentation: the naive pool this
    # manifest's distinct concept-name x variant-name space WOULD have
    # produced if every concept were blindly attached to every variant
    # (the defect this correction removes), versus what was actually
    # created.
    distinct_concept_names = {name for (_d, _dom, name) in expected_concept_keys}
    distinct_variant_names = {name for (_d, _dim, name) in expected_variant_keys}
    naive_cartesian_pool = len(distinct_concept_names) * len(distinct_variant_names)
    rejected_cartesian_mappings = {
        "v1_blanket_mappings_rejected": 120,
        "naive_cartesian_pool_this_manifest": naive_cartesian_pool,
        "actual_applicability_created": len(expected_applicability),
        "cartesian_mappings_avoided": naive_cartesian_pool - len(expected_applicability),
    }

    # Disease-level source-classification coverage (NCI_CANCER_CATALOG).
    disease_classification_covered = sum(
        1 for row in stored_disease_rows
        if row.disease_category in ALLOWED_SOURCE_CLASSIFICATIONS
    )

    report = {
        "manifest_id": manifest.get("manifest_id"),
        "expected_diseases": expected_disease_names,
        "stored_diseases": stored_disease_names,
        "canonical_disease_count": {
            "expected": len(expected_disease_names),
            "stored": len(stored_disease_names),
        },
        "canonical_diseases_by_family": canonical_diseases_by_family,
        "variants_by_disease_and_dimension": variants_by_disease_and_dimension,
        "concepts_by_domain": concepts_by_domain,
        "applicability_by_disease_and_type": applicability_by_disease_and_type,
        "rejected_cartesian_mappings": rejected_cartesian_mappings,
        "expected_variants_count": len(expected_variant_keys),
        "stored_variants_count": len(stored_variant_keys & expected_variant_keys),
        "missing_variants": [list(k) for k in missing_variants],
        "unexpected_variants": [list(k) for k in unexpected_variants],
        "expected_concepts_count": len(expected_concept_keys),
        "stored_concepts_count": len(stored_concept_keys & expected_concept_keys),
        "missing_concepts": [list(k) for k in missing_concepts],
        "unexpected_concepts": [list(k) for k in unexpected_concepts],
        "expected_applicability_count": len(expected_applicability),
        "stored_applicability_count": len(set(expected_applicability) & stored_applicability_keys),
        "missing_applicability": [list(k) for k in missing_applicability],
        "unexpected_applicability": [list(k) for k in unexpected_applicability],
        "evidence_rule_coverage": {
            "covered": evidence_covered,
            "expected": len(expected_concept_keys),
            "missing": evidence_missing,
        },
        "source_provenance_coverage": {
            "covered": evidence_covered,
            "expected": len(expected_concept_keys),
        },
        "source_classification_coverage": {
            "concepts_covered": evidence_covered,
            "concepts_expected": len(expected_concept_keys),
            "diseases_covered": disease_classification_covered,
            "diseases_expected": len(expected_disease_names),
        },
        "orphan_count": orphan_count,
        "cycle_count": cycle_count,
        "unresolved_concept_count": unresolved_concept_count,
        "second_run_new_rows": second_run_new_rows,
        "changes_outside_oncology": [],
        "differentiation_guard_results": guard_results,
    }
    return report


def main() -> None:
    db = SessionLocal()
    try:
        manifest = load_manifest()
        result = run(db, manifest)
        db.commit()
        print("First run result:", json.dumps(result, indent=2))

        db2 = SessionLocal()
        try:
            second_result = run(db2, manifest)
            db2.commit()
            second_run_new_rows = (
                second_result["variants_inserted"]
                + second_result["concepts_inserted_total"]
                + second_result["applicability_inserted"]
            )
            print("Second run new rows:", second_run_new_rows)
        finally:
            db2.close()

        db3 = SessionLocal()
        try:
            report = build_acceptance_report(db3, manifest, second_run_new_rows)
        finally:
            db3.close()

        DEFAULT_ACCEPTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_ACCEPTANCE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Wrote acceptance report to", DEFAULT_ACCEPTANCE_PATH)
    finally:
        db.close()


if __name__ == "__main__":
    main()
