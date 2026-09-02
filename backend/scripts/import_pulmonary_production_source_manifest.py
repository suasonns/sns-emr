# scripts/import_pulmonary_production_source_manifest.py
"""
Pulmonary Production Source Manifest v1 -- Verbatim Importer.

Reads backend/manifests/pulmonary_production_source_manifest_v1.json
(the sole authoritative source for this import -- never inferred,
reconstructed, or clinically re-derived) and creates the Pulmonary
System body system / family, the two canonical diseases, every Tier 4
variant, Tier 5 atomic concept, and Tier 4<->Tier 5 applicability mapping
it declares:

    End Stage Pulmonary Disease
    Chronic Obstructive Pulmonary Disease

This reuses the exact verbatim-import pattern proven in
scripts/import_neurologic_production_source_manifest.py (PR #37) and
scripts/import_cardiovascular_production_source_manifest.py (PR #38):

- No concept is renamed, substituted, combined, split, or omitted.
- No additional concept is invented beyond what the manifest declares.
- A manifest identity match requires an EXACT match on every applicable
  identity field (disease + domain/dimension + normalized exact name).
- Every concept created receives an OntologyEvidenceRule with
  patient_fact_requires_evidence = True.
- Nothing is ever hard-deleted or deactivated.
- Idempotent: re-running inserts nothing new.
- Nothing is silently skipped: any manifest value that is not
  schema-valid aborts the import with a RuntimeError before any writes
  happen.

Approved vocabulary correction: the requested RESPIRATORY_PHYSIOLOGY
variant dimension does not exist in ck_ontology_disease_variant_dimension.
Per explicit user approval, the three respiratory-failure phenotype
variants (Hypoxemic / Hypercapnic / Combined Hypoxemic Hypercapnic
Respiratory Failure) are stored under the existing PHYSIOLOGICAL_PHENOTYPE
dimension instead -- no new dimension, no migration, no schema change.

Run with: .\\.venv\\Scripts\\python.exe scripts\\import_pulmonary_production_source_manifest.py
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
    Path(__file__).resolve().parent.parent / "manifests" / "pulmonary_production_source_manifest_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "pulmonary_production_manifest_acceptance_v1.json"
)

SYSTEM_NAME = "Pulmonary System"

# --- Tier 4 variant dimensions permitted by the
# ck_ontology_disease_variant_dimension CHECK constraint. This manifest
# uses only a subset (SEVERITY_CLASS, DISEASE_PHASE, TREATMENT_STATE,
# RECURRENCE_STATE, PHYSIOLOGICAL_PHENOTYPE); RESPIRATORY_PHYSIOLOGY was
# never created (approved vocabulary correction: mapped to the existing
# PHYSIOLOGICAL_PHENOTYPE dimension instead). ---
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

    return errors


def _resolve_or_create_diseases(db: Session, manifest: dict) -> Dict[str, OntologyDisease]:
    """Resolve each manifest disease by exact normalized name, creating the
    Pulmonary System body system, the declared family, and the disease
    itself if not already present. Never creates a new body
    system/family/disease beyond what the manifest's own scope declares."""
    system_name = manifest["scope"]["body_system"]
    family_names = manifest["scope"]["families"]
    if len(family_names) != 1:
        raise RuntimeError(
            f"Pulmonary Production Manifest v1 declares {len(family_names)} families; "
            "this importer expects exactly one shared family. Aborting without any writes."
        )
    family_name = family_names[0]

    system = db.query(OntologyBodySystem).filter_by(system_name=system_name).one_or_none()
    if system is None:
        system = OntologyBodySystem(system_name=system_name)
        db.add(system)
        db.flush()

    family = (
        db.query(OntologyDiseaseFamily)
        .filter_by(family_name=family_name, body_system_id=system.id)
        .one_or_none()
    )
    if family is None:
        family = OntologyDiseaseFamily(family_name=family_name, body_system_id=system.id)
        db.add(family)
        db.flush()

    resolved: Dict[str, OntologyDisease] = {}
    for disease_entry in manifest["diseases"]:
        name = disease_entry["disease"]
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            disease = OntologyDisease(disease_name=name, disease_family_id=family.id)
            db.add(disease)
            db.flush()
        resolved[name] = disease
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
            evidence_source="pulmonary_production_source_manifest_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes="Imported verbatim from the approved Pulmonary Production Source Manifest v1.",
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
        raise RuntimeError(f"Pulmonary Production Manifest v1 failed structural/vocabulary validation: {errors}")

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
                source_reference="pulmonary_production_source_manifest_v1",
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
                    f"Pulmonary Production Manifest v1 applicability mapping references a variant/concept "
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
                description="Imported verbatim from the approved Pulmonary Production Source Manifest v1.",
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

    variant_id_by_name: Dict[Tuple[str, str, str], object] = {}
    for v in stored_variants:
        variant_id_by_name[(name_to_disease[v.disease_id], v.variant_dimension, v.variant_name)] = v.id

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

    guard_results = []
    for guard in manifest.get("differentiation_guards", []):
        rule = guard["rule"]
        left, right = guard["left"], guard["right"]
        passed = None
        detail = None
        if rule == "NOT_AUTOMATICALLY_EQUIVALENT":
            left_d, right_d = diseases.get(left), diseases.get(right)
            passed = left_d is not None and right_d is not None and left_d.id != right_d.id
        else:
            detail = f"unrecognized guard rule: {rule}"
        guard_results.append({"left": left, "right": right, "rule": rule, "passed": passed, "detail": detail})

    orphan_count = 0
    stored_variant_ids = {v.id for v in stored_variants}
    for v in stored_variants:
        if v.disease_id not in disease_ids:
            orphan_count += 1
        elif v.parent_variant_id is not None and v.parent_variant_id not in stored_variant_ids:
            orphan_count += 1
    for edge in stored_applicability_rows:
        if edge.variant_id not in stored_variant_ids:
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
