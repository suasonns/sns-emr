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
- Nothing is silently skipped: any manifest value that is not schema-valid
  (an unsupported variant_dimension, concept_domain, applicability_type,
  treatment_category, or limitation_category) aborts the import with a
  RuntimeError before any writes happen, rather than being dropped quietly.

SCHEMA-COMPATIBLE VOCABULARY (approved corrections)
------------------------------------------------------
The manifest's variant dimensions and TREATMENT / TREATMENT_LIMITATION
category assignments were corrected, at the manifest level, to the
approved schema vocabulary (SUBTYPE -> PATHOLOGICAL_SUBTYPE,
SEVERITY_PHENOTYPE -> SEVERITY_CLASS, plus an explicit
treatment_category / limitation_category on every TREATMENT /
TREATMENT_LIMITATION concept). This is a vocabulary correction only -- no
concept name, evidence requirement, or applicability mapping was changed,
renamed, or omitted. All 123 variants, 557 concepts, and 84 applicability
mappings declared by the manifest are imported.

Run with: .\\.venv\\Scripts\\python.exe scripts\\import_neurologic_production_source_manifest.py
"""
from __future__ import annotations

import json
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
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseasePsychosocialConcern,
    OntologyDiseaseSpiritualConcern,
)

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "manifests" / "neurologic_production_source_manifest_v1.json"
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "neurologic_production_manifest_acceptance_v1.json"
)

# --- Tier 4 variant dimensions permitted by the
# ck_ontology_disease_variant_dimension CHECK constraint. ---
ALLOWED_VARIANT_DIMENSIONS = {
    "MECHANISM", "PATHOLOGICAL_SUBTYPE", "HISTOLOGY", "MOLECULAR_SUBTYPE",
    "ANATOMICAL_LOCATION", "PRIMARY_SITE", "VASCULAR_TERRITORY", "HEMISPHERE",
    "DOMINANCE", "LATERALITY", "CORTICAL_LOCATION", "SUBCORTICAL_LOCATION",
    "DEEP_STRUCTURE", "BRAINSTEM_LEVEL", "CEREBELLAR_LOCATION", "CARDIAC_SIDE",
    "CARDIAC_CHAMBER", "PHYSIOLOGICAL_PHENOTYPE", "SEVERITY_CLASS", "STAGE",
    "GRADE", "DISEASE_PHASE", "RECURRENCE_STATE", "METASTATIC_STATE",
    "METASTATIC_DESTINATION", "TREATMENT_STATE", "RESIDUAL_DEFICIT_STATE",
}

# --- ck_ontology_disease_treatment_category CHECK constraint values. ---
ALLOWED_TREATMENT_CATEGORIES = {"DISEASE_DIRECTED", "SUPPORTIVE", "HOSPICE"}

# --- ck_ontology_disease_treatment_limitation_category CHECK constraint
# values, after the additive widening migration
# (c3f7a1e9b0d2_widen_ontology_disease_treatment_limitation_category). ---
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

# concept_domain -> (ORM model class, unique-name column) for the "simple"
# domains that only require a name plus disease_id.
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

# Full domain -> (model class, name column) map, including the two
# category-bearing domains, used for read/lookup purposes (applicability
# resolution, orphan checks, etc.).
CONCEPT_DOMAIN_MODEL_MAP = dict(SIMPLE_CONCEPT_DOMAIN_MODEL_MAP)
CONCEPT_DOMAIN_MODEL_MAP["TREATMENT"] = (OntologyDiseaseTreatment, "treatment_name")
CONCEPT_DOMAIN_MODEL_MAP["TREATMENT_LIMITATION"] = (OntologyDiseaseTreatmentLimitation, "limitation_name")


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    """Structural + schema-vocabulary validation -- never a clinical
    judgment. Returns a list of validation errors (empty means the
    manifest is well-formed and every value is schema-valid). Duplicate
    EXACT identities inside the manifest are rejected. Any unsupported
    dimension / domain / applicability_type / category value is reported
    as an error and aborts the import -- nothing is silently skipped."""
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
            if v.get("dimension") not in ALLOWED_VARIANT_DIMENSIONS:
                errors.append(f"unsupported variant dimension '{v.get('dimension')}' for {key}")

        seen_concepts = set()
        for c in disease_entry.get("concepts", []):
            key = (disease_name, c.get("domain"), (c.get("name") or "").strip().lower())
            if key in seen_concepts:
                errors.append(f"duplicate concept identity in manifest: {key}")
            seen_concepts.add(key)
            domain = c.get("domain")
            if domain not in CONCEPT_DOMAIN_MODEL_MAP:
                errors.append(f"unsupported concept domain '{domain}' for {key}")
            elif domain == "TREATMENT" and c.get("treatment_category") not in ALLOWED_TREATMENT_CATEGORIES:
                errors.append(f"unsupported or missing treatment_category '{c.get('treatment_category')}' for {key}")
            elif domain == "TREATMENT_LIMITATION" and c.get("limitation_category") not in ALLOWED_LIMITATION_CATEGORIES:
                errors.append(f"unsupported or missing limitation_category '{c.get('limitation_category')}' for {key}")

        seen_applic = set()
        for a in disease_entry.get("applicability", []):
            key = (
                disease_name, a.get("variant"), a.get("concept"),
                a.get("concept_domain"), a.get("applicability_type"),
            )
            if key in seen_applic:
                errors.append(f"duplicate applicability identity in manifest: {key}")
            seen_applic.add(key)
            if a.get("applicability_type") not in APPLICABILITY_TYPES:
                errors.append(f"unsupported applicability_type '{a.get('applicability_type')}' for {key}")

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


def _build_concept_row(domain: str, disease_id, concept_entry: dict):
    """Construct the ORM row for a single manifest concept, applying the
    approved treatment_category / limitation_category for the two
    category-bearing domains, verbatim from the manifest -- never
    invented, never substituted."""
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
    return model_cls(id=uuid.uuid4(), disease_id=disease_id, **{name_attr: name})


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Neurologic Production Manifest v1 failed structural/vocabulary validation: {errors}")

    diseases = _resolve_diseases(db, manifest)

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

            if key in concept_by_key:
                existing_row = concept_by_key[key]
                # The manifest is authoritative over any pre-existing category
                # value on an identity-matched concept (e.g. one created
                # earlier by a different committed population script) --
                # this reconciles the stored category to the approved
                # manifest value verbatim; it never renames, substitutes,
                # or deletes the concept itself.
                if domain == "TREATMENT" and existing_row.treatment_category != c["treatment_category"]:
                    existing_row.treatment_category = c["treatment_category"]
                elif domain == "TREATMENT_LIMITATION" and existing_row.limitation_category != c["limitation_category"]:
                    existing_row.limitation_category = c["limitation_category"]
                if _ensure_evidence_rule(db, domain, existing_row.id):
                    evidence_rules_inserted += 1
                continue

            row = _build_concept_row(domain, disease.id, c)
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
                raise RuntimeError(
                    f"Neurologic Production Manifest v1 applicability mapping references a variant/concept "
                    f"that was not created: disease={disease_name!r} variant={variant_name!r} "
                    f"concept={concept_name!r} domain={concept_domain!r}. Aborting rather than skipping silently."
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
        "concepts_inserted_by_domain": concepts_inserted_by_domain,
        "concepts_inserted_total": sum(concepts_inserted_by_domain.values()),
        "applicability_inserted": applicability_inserted,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


def _no_cycle(variants: List[OntologyDiseaseVariant]) -> int:
    """Count hierarchy cycles among the given variants (parent_variant_id
    chains). Returns the number of variants at which a cycle is detected."""
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


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    """Compare the manifest against the (already-imported) clean database
    and report expected vs. stored vs. missing vs. unexpected for
    variants, concepts, and applicability mappings, plus evidence-rule
    coverage, differentiation-guard results, orphan count, cycle count,
    and the second-run new-row count. Never a clinical judgment -- purely
    a mechanical comparison of the committed manifest against what is
    actually stored."""
    diseases = _resolve_diseases(db, manifest)
    disease_ids = {d.id for d in diseases.values()}

    # --- variants ---
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

    # --- concepts ---
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

    # --- applicability ---
    expected_applicability = []
    for disease_entry in manifest["diseases"]:
        for a in disease_entry.get("applicability", []):
            expected_applicability.append(
                (disease_entry["disease"], a["variant"], a["concept_domain"], a["concept"], a["applicability_type"])
            )

    variant_id_by_name: Dict[Tuple[str, str], object] = {}
    for v in stored_variants:
        variant_id_by_name[(name_to_disease[v.disease_id], v.variant_name)] = v.id

    stored_applicability_rows = db.query(OntologyConceptVariantApplicability).filter(
        OntologyConceptVariantApplicability.disease_id.in_(disease_ids)
    ).all()
    variant_id_to_name = {v.id: v.variant_name for v in stored_variants}
    stored_applicability_keys = set()
    for edge in stored_applicability_rows:
        disease_name = name_to_disease.get(edge.disease_id)
        variant_name = variant_id_to_name.get(edge.variant_id)
        model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        concept_row = db.query(model_cls).filter_by(id=edge.concept_id).one_or_none()
        concept_name = getattr(concept_row, name_attr) if concept_row is not None else None
        stored_applicability_keys.add(
            (disease_name, variant_name, edge.concept_type, concept_name, edge.applicability_type)
        )
    missing_applicability = sorted(
        [key for key in expected_applicability if key not in stored_applicability_keys],
        key=lambda k: (k[0], k[1], k[2], k[3], k[4]),
    )
    unexpected_applicability = sorted(
        [key for key in stored_applicability_keys if key not in set(expected_applicability)],
        key=lambda k: (str(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4])),
    )

    # --- evidence rule coverage (scoped to the manifest's own 557 expected
    # concepts only -- not every concept in the database, which also holds
    # concepts from other committed population scripts). ---
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

    # --- differentiation guards (mechanical check per the guard's own
    # declared rule -- reuses the same logic the test suite asserts). ---
    guard_results = []
    for guard in manifest.get("differentiation_guards", []):
        rule = guard["rule"]
        left, right = guard["left"], guard["right"]
        passed = None
        detail = None
        if rule in ("NOT_AUTOMATICALLY_EQUIVALENT",):
            left_d, right_d = diseases.get(left), diseases.get(right)
            passed = left_d is not None and right_d is not None and left_d.id != right_d.id
        elif rule == "NOT_INTERCHANGEABLE":
            left_ids = {v.id for v in stored_variants if v.variant_name == left}
            right_ids = {v.id for v in stored_variants if v.variant_name == right}
            if left_ids or right_ids:
                passed = left_ids.isdisjoint(right_ids)
            else:
                # Not variant names for this manifest -- fall back to
                # disease-level distinctness (e.g. Hemiplegia/Hemiparesis).
                left_d, right_d = diseases.get(left), diseases.get(right)
                passed = left_d is not None and right_d is not None and left_d.id != right_d.id
        elif rule == "CONTRAINDICATED_APPLICABILITY":
            variant_id = variant_id_by_name.get(("Stroke", left))
            passed = variant_id is not None and not any(
                e.variant_id == variant_id and e.applicability_type == "TREATMENT_SPECIFIC_TO"
                for e in stored_applicability_rows
            )
        elif rule == "DO_NOT_INFER_CURRENT_STATE":
            variant_id = variant_id_by_name.get(("Stroke", left))
            passed = variant_id is not None and not any(
                e.variant_id == variant_id and e.applicability_type == "APPLIES_TO"
                for e in stored_applicability_rows
            )
        else:
            detail = f"unrecognized guard rule: {rule}"
        guard_results.append({"left": left, "right": right, "rule": rule, "passed": passed, "detail": detail})

    orphan_count = 0
    for v in stored_variants:
        if v.disease_id not in disease_ids:
            orphan_count += 1
        elif v.parent_variant_id is not None and v.parent_variant_id not in {vv.id for vv in stored_variants}:
            orphan_count += 1
    for edge in stored_applicability_rows:
        if edge.variant_id not in {v.id for v in stored_variants}:
            orphan_count += 1
        model_cls, _ = CONCEPT_DOMAIN_MODEL_MAP[edge.concept_type]
        if db.query(model_cls).filter_by(id=edge.concept_id).one_or_none() is None:
            orphan_count += 1

    cycle_count = _no_cycle(stored_variants)

    return {
        "manifest_path": str(DEFAULT_MANIFEST_PATH),
        "expected_variants": len(expected_variant_keys),
        "stored_variants": len(stored_variant_keys & expected_variant_keys),
        "missing_variants": [list(k) for k in missing_variants],
        "unexpected_variants": [list(k) for k in unexpected_variants],
        "expected_concepts": len(expected_concept_keys),
        "stored_concepts": len(stored_concept_keys & expected_concept_keys),
        "missing_concepts": [list(k) for k in missing_concepts],
        "unexpected_concepts": [list(k) for k in unexpected_concepts],
        "expected_applicability_mappings": len(expected_applicability),
        "stored_applicability_mappings": len(set(expected_applicability) & stored_applicability_keys),
        "missing_applicability_mappings": [list(k) for k in missing_applicability],
        "unexpected_applicability_mappings": [list(k) for k in unexpected_applicability],
        "evidence_rule_coverage": {
            "expected": len(expected_concept_keys),
            "covered": evidence_covered,
            "missing": evidence_missing,
        },
        "differentiation_guard_results": guard_results,
        "orphan_count": orphan_count,
        "cycle_count": cycle_count,
        "second_run_new_rows": second_run_new_rows,
    }


def main() -> None:
    db = SessionLocal()
    try:
        manifest = load_manifest()
        counts = run(db, manifest=manifest)
        db.commit()
        for label, value in counts.items():
            print(f"{label}: {value}")

        second_counts = run(db, manifest=manifest)
        db.commit()
        second_run_new_rows = (
            second_counts["variants_inserted"]
            + second_counts["concepts_inserted_total"]
            + second_counts["applicability_inserted"]
        )

        report = build_acceptance_report(db, manifest, second_run_new_rows)
        DEFAULT_ACCEPTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_ACCEPTANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"acceptance_export: {DEFAULT_ACCEPTANCE_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
