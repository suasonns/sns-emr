# scripts/import_neurologic_production_source_manifest.py
"""
Neurologic Production Source Manifest v1 -- Verbatim Importer.

Reads backend/manifests/neurologic_production_source_manifest_v1.json (the
sole authoritative source for this import -- never inferred, reconstructed,
or clinically re-derived) and creates every Tier 4 variant, Tier 5 atomic
concept, and Tier 4<->Tier 5 applicability mapping it declares, for the six
already-existing Neurologic diseases:

    Stroke
    Hemiplegia
    Hemiparesis
    Contracture
    Dementia Due To Alzheimer's Disease
    Senile Degeneration of Brain

STRICT VERBATIM IMPORT RULES
-----------------------------
- No concept is renamed, substituted, combined, split, or omitted.
- No additional concept is invented beyond what the manifest declares.
- No variant dimension or applicability_type is changed or substituted for
  a "similar" existing value.
- A manifest identity match requires an EXACT match on every applicable
  identity field (disease + domain/dimension + normalized exact name) --
  a clinically similar existing term is never treated as satisfying a
  manifest requirement.
- Every concept created receives an OntologyEvidenceRule with
  patient_fact_requires_evidence = True.
- Nothing is ever hard-deleted or deactivated.
- Idempotent: re-running inserts nothing new.

SCHEMA-CONSTRAINT BLOCKING (no schema change, no substitution allowed)
------------------------------------------------------------------------
This importer must not modify the schema, models, or migrations. Two
categories of manifest content cannot be written under the CURRENT schema
without either a schema change (prohibited) or an invented/substituted
value (prohibited):

1. Tier 4 variants whose `dimension` is not one of the values already
   permitted by the `ck_ontology_disease_variant_dimension` CHECK
   constraint on `ontology_disease_variant` (defined in
   ontology_disease_blueprint.py). The manifest uses two dimension values
   that are not in that allowed set: SUBTYPE and SEVERITY_PHENOTYPE.
2. Tier 5 concepts whose domain is TREATMENT or TREATMENT_LIMITATION.
   Both `OntologyDiseaseTreatment.treatment_category` and
   `OntologyDiseaseTreatmentLimitation.limitation_category` are NOT NULL
   columns constrained to a fixed enum of values
   (DISEASE_DIRECTED/SUPPORTIVE/HOSPICE and
   OPTIMALLY_TREATED/TREATMENT_FAILED/.../COMFORT_FOCUSED respectively).
   The manifest does not supply a category for any TREATMENT or
   TREATMENT_LIMITATION concept, and inventing one would be a clinical
   judgment not authorized by the manifest.

Every individual variant/concept/applicability row affected by one of
these two conditions is skipped (not created, not substituted) and
reported as a BLOCKED item with the exact reason -- never silently
dropped and never worked around by choosing an existing "similar enough"
dimension, category, or concept. All other, unaffected manifest content
is imported normally in the same run.

Run with: .\\.venv\\Scripts\\python.exe scripts\\import_neurologic_production_source_manifest.py
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
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
    OntologyDiseasePsychosocialConcern,
    OntologyDiseaseSpiritualConcern,
)

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "manifests" / "neurologic_production_source_manifest_v1.json"
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "neurologic_production_manifest_acceptance_v1.json"
)

# --- Tier 4 variant dimensions currently permitted by the DB CHECK
# constraint (ck_ontology_disease_variant_dimension). Any manifest variant
# whose dimension is NOT in this set is blocked, never substituted. ---
ALLOWED_VARIANT_DIMENSIONS = {
    "MECHANISM", "PATHOLOGICAL_SUBTYPE", "HISTOLOGY", "MOLECULAR_SUBTYPE",
    "ANATOMICAL_LOCATION", "PRIMARY_SITE", "VASCULAR_TERRITORY", "HEMISPHERE",
    "DOMINANCE", "LATERALITY", "CORTICAL_LOCATION", "SUBCORTICAL_LOCATION",
    "DEEP_STRUCTURE", "BRAINSTEM_LEVEL", "CEREBELLAR_LOCATION", "CARDIAC_SIDE",
    "CARDIAC_CHAMBER", "PHYSIOLOGICAL_PHENOTYPE", "SEVERITY_CLASS", "STAGE",
    "GRADE", "DISEASE_PHASE", "RECURRENCE_STATE", "METASTATIC_STATE",
    "METASTATIC_DESTINATION", "TREATMENT_STATE", "RESIDUAL_DEFICIT_STATE",
}

# --- Tier 5 domains that CANNOT be written without inventing a required,
# non-nullable, enum-constrained field the manifest does not supply.
# Blocked entirely -- never substituted with a guessed category. ---
BLOCKED_CONCEPT_DOMAINS = {"TREATMENT", "TREATMENT_LIMITATION"}

# concept_domain -> (ORM model class, unique-name column)
CONCEPT_DOMAIN_MODEL_MAP = {
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

APPLICABILITY_TYPES = {
    "APPLIES_TO", "EXPECTED_WITH", "STRONGLY_ASSOCIATED_WITH", "MAY_OCCUR_WITH",
    "SUPPORTS_DIFFERENTIATION", "CONTRAINDICATED_FOR", "TREATMENT_SPECIFIC_TO",
    "PROGNOSTIC_FOR", "END_STAGE_SUPPORT_FOR", "HOSPICE_SUPPORT_FOR",
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    """Structural validation only -- never a clinical judgment. Returns a
    list of validation errors (empty means the manifest is well-formed).
    Duplicate EXACT identities inside the manifest are rejected."""
    errors: List[str] = []
    diseases = manifest.get("diseases")
    if not isinstance(diseases, list) or not diseases:
        errors.append("manifest.diseases must be a non-empty list")
        return errors

    for disease_entry in diseases:
        disease_name = disease_entry.get("disease")
        if not disease_name:
            errors.append("a disease entry is missing 'disease' name")
            continue

        seen_variants = set()
        for v in disease_entry.get("variants", []):
            key = (disease_name, v.get("dimension"), (v.get("name") or "").strip().lower())
            if key in seen_variants:
                errors.append(f"duplicate variant identity in manifest: {key}")
            seen_variants.add(key)

        seen_concepts = set()
        for c in disease_entry.get("concepts", []):
            key = (disease_name, c.get("domain"), (c.get("name") or "").strip().lower())
            if key in seen_concepts:
                errors.append(f"duplicate concept identity in manifest: {key}")
            seen_concepts.add(key)

        seen_applic = set()
        for a in disease_entry.get("applicability", []):
            key = (
                disease_name, a.get("variant"), a.get("concept"),
                a.get("concept_domain"), a.get("applicability_type"),
            )
            if key in seen_applic:
                errors.append(f"duplicate applicability identity in manifest: {key}")
            seen_applic.add(key)

    return errors


def _resolve_diseases(db: Session, manifest: dict) -> Dict[str, OntologyDisease]:
    resolved: Dict[str, OntologyDisease] = {}
    missing: List[str] = []
    for disease_entry in manifest["diseases"]:
        name = disease_entry["disease"]
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            missing.append(name)
        else:
            resolved[name] = disease
    if missing:
        raise RuntimeError(
            f"Neurologic Production Manifest v1 import requires these diseases to already exist: {missing}. "
            "Aborting without any writes."
        )
    return resolved


def _ensure_evidence_rule(db: Session, concept_type: str, concept_id) -> bool:
    """Create or preserve an OntologyEvidenceRule for a concept, always
    with patient_fact_requires_evidence=True. Returns True if a new row
    was inserted."""
    existing = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type=concept_type, concept_id=concept_id)
        .one_or_none()
    )
    if existing is not None:
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=concept_type,
            concept_id=concept_id,
            evidence_source="neurologic_production_source_manifest_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes="Imported verbatim from the approved Neurologic Production Source Manifest v1.",
        )
    )
    return True


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Neurologic Production Manifest v1 failed structural validation: {errors}")

    diseases = _resolve_diseases(db, manifest)

    variants_inserted = 0
    variants_blocked: List[dict] = []
    concepts_inserted_by_domain: Dict[str, int] = {}
    concepts_blocked: List[dict] = []
    applicability_inserted = 0
    applicability_blocked: List[dict] = []
    evidence_rules_inserted = 0

    # variant_by_key keyed on (disease_name, dimension, normalized_name) so
    # concept_domain-scoped applicability lookups can resolve the exact
    # manifest-specified variant.
    variant_by_key: Dict[Tuple[str, str, str], OntologyDiseaseVariant] = {}
    # pre-load any already-existing variants for this disease so the
    # importer is idempotent across runs.
    for disease_name, disease in diseases.items():
        for existing in db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all():
            variant_by_key[(disease_name, existing.variant_dimension, existing.normalized_name)] = existing

    concept_by_key: Dict[Tuple[str, str, str], object] = {}
    for concept_type, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for disease_name, disease in diseases.items():
            for existing in db.query(model_cls).filter_by(disease_id=disease.id).all():
                key = (disease_name, concept_type, getattr(existing, name_attr).strip().lower())
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

            if dimension not in ALLOWED_VARIANT_DIMENSIONS:
                variants_blocked.append({
                    "disease": disease_name,
                    "dimension": dimension,
                    "name": name,
                    "reason": (
                        f"variant_dimension '{dimension}' is not permitted by the current "
                        "ck_ontology_disease_variant_dimension CHECK constraint; creating it would "
                        "require a schema/migration change, which is prohibited for this import, and "
                        "substituting an existing 'similar' dimension is prohibited by the no-substitution rule."
                    ),
                })
                continue

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
                    "Requires patient-record evidence (imaging, exam, or documented clinical course) "
                    "before this variant/context is ever treated as a confirmed patient-specific fact."
                ),
                source_reference="neurologic_production_source_manifest_v1",
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
            normalized = name.strip().lower()
            key = (disease_name, domain, normalized)

            if domain in BLOCKED_CONCEPT_DOMAINS:
                concepts_blocked.append({
                    "disease": disease_name,
                    "domain": domain,
                    "name": name,
                    "reason": (
                        f"concept domain '{domain}' requires a non-nullable, enum-constrained category "
                        "column (treatment_category / limitation_category) that the manifest does not "
                        "supply a value for; inventing a category value would be an unauthorized clinical "
                        "judgment, and no schema change is permitted for this import."
                    ),
                })
                continue

            if domain not in CONCEPT_DOMAIN_MODEL_MAP:
                concepts_blocked.append({
                    "disease": disease_name,
                    "domain": domain,
                    "name": name,
                    "reason": f"concept domain '{domain}' has no corresponding Tier 5 table in the current schema.",
                })
                continue

            if key in concept_by_key:
                # already present -- ensure its evidence rule exists (idempotent) and continue
                existing_row = concept_by_key[key]
                if _ensure_evidence_rule(db, domain, existing_row.id):
                    evidence_rules_inserted += 1
                continue

            model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
            row = model_cls(id=uuid.uuid4(), disease_id=disease.id, **{name_attr: name})
            db.add(row)
            db.flush()
            concept_by_key[key] = row
            concepts_inserted_by_domain[domain] = concepts_inserted_by_domain.get(domain, 0) + 1

            if _ensure_evidence_rule(db, domain, row.id):
                evidence_rules_inserted += 1

    db.flush()

    # --- Tier 4 <-> Tier 5 applicability ---
    for disease_entry in manifest["diseases"]:
        disease_name = disease_entry["disease"]
        disease = diseases[disease_name]
        for a in disease_entry.get("applicability", []):
            variant_name = a["variant"]
            concept_name = a["concept"]
            concept_domain = a["concept_domain"]
            applicability_type = a["applicability_type"]

            if applicability_type not in APPLICABILITY_TYPES:
                applicability_blocked.append({
                    "disease": disease_name, "variant": variant_name, "concept": concept_name,
                    "concept_domain": concept_domain, "applicability_type": applicability_type,
                    "reason": f"applicability_type '{applicability_type}' is not permitted by the current CHECK constraint.",
                })
                continue

            variant_key_found = None
            for (d_name, dimension, normalized), variant_row in variant_by_key.items():
                if d_name == disease_name and variant_row.variant_name == variant_name:
                    variant_key_found = variant_row
                    break
            concept_key_found = None
            for (d_name, domain, normalized), concept_row in concept_by_key.items():
                if d_name == disease_name and domain == concept_domain and normalized == concept_name.strip().lower():
                    concept_key_found = concept_row
                    break

            if variant_key_found is None or concept_key_found is None:
                applicability_blocked.append({
                    "disease": disease_name, "variant": variant_name, "concept": concept_name,
                    "concept_domain": concept_domain, "applicability_type": applicability_type,
                    "reason": (
                        "referenced variant or concept was itself blocked (schema-constrained) and does not exist"
                        if (variant_key_found is None or concept_key_found is None) else "unknown"
                    ),
                })
                continue

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
                description="Imported verbatim from the approved Neurologic Production Source Manifest v1.",
                evidence_requirement=(
                    "Requires patient-record evidence before this applicability is ever treated as a "
                    "documented patient-specific fact."
                ),
            )
            db.add(edge)
            applicability_inserted += 1

    return {
        "variants_inserted": variants_inserted,
        "variants_blocked": variants_blocked,
        "concepts_inserted_by_domain": concepts_inserted_by_domain,
        "concepts_inserted_total": sum(concepts_inserted_by_domain.values()),
        "concepts_blocked": concepts_blocked,
        "applicability_inserted": applicability_inserted,
        "applicability_blocked": applicability_blocked,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


def main() -> None:
    db = SessionLocal()
    try:
        counts = run(db)
        db.commit()
        for label, value in counts.items():
            if isinstance(value, list):
                print(f"{label}: {len(value)}")
                for item in value:
                    print(f"    {item}")
            else:
                print(f"{label}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
