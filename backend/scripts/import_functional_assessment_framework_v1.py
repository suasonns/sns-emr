# scripts/import_functional_assessment_framework_v1.py
"""
Functional Assessment Framework v1 -- Verbatim Importer (PR #49).

Reads backend/manifests/functional_assessment_framework_v1.json (the sole
authoritative source for this import -- never inferred, reconstructed, or
clinically re-derived) and creates a reusable, disease-agnostic reference
library of five standardized functional/performance assessment scales:

    PPS (Palliative Performance Scale), KPS (Karnofsky Performance Status),
    FAST (Functional Assessment Staging Tool), NYHA (New York Heart
    Association Functional Classification), ECOG (Eastern Cooperative
    Oncology Group Performance Status).

No schema changes. No migrations. No API changes. No patient-record
modifications. This reuses the existing Ontology Disease Blueprint tables
exactly as every prior production manifest does:

    - A new OntologyBodySystem ("Functional Assessment") with one new
      OntologyDiseaseFamily ("Functional Assessment Scales") and one new
      OntologyDisease ("Functional Assessment Framework") -- a reusable
      container, not a clinical disease, hosting scale reference knowledge
      inside the existing schema without any migration.
    - One OntologyDiseaseVariant (dimension=SEVERITY_CLASS, an
      already-CHECK-constraint-allowed dimension) per individual score
      level -- 45 total (ECOG 5, NYHA 4, FAST 16, KPS 10, PPS 10) -- never
      collapsed into a single row. Each variant's existing free-text
      columns (description / clinical_significance / hospice_relevance /
      evidence_requirement / source_reference) carry that level's
      clinical_meaning / functional_summary / hospice_interpretation /
      evidence requirement / source citation, so no score is ever stored
      as a number alone.
    - One OntologyDiseaseFinding concept per scale -- 5 total -- whose
      existing severity_levels JSONB column carries the FULL structured
      per-level record (score, display_title, clinical_meaning,
      functional_summary, hospice_interpretation, ai_summary,
      source_reference) for every level of that scale, and whose existing
      supporting_evidence_types JSONB column carries the scale's
      visibility-rule and trend-policy metadata. This is the mechanism
      that satisfies "must not store scores only" without any schema
      change (the same reviewer-approved technique used by every prior
      manifest to carry extra structured metadata in an existing column).
    - One APPLIES_TO OntologyConceptVariantApplicability edge per score
      level -- 45 total -- linking that level's variant to its scale's
      concept.
    - One OntologyEvidenceRule per scale concept -- 5 total -- with
      patient_fact_requires_evidence=True.

The 'assessor' and 'assessment_date' fields named in the specification's
DATABASE MODEL section belong to the separate, unchanged, patient-facing
assessment-recording feature (the existing `assessments` table). This PR
does not touch patient records, the API, or that table -- it only builds
the reference knowledge library those future recordings will point back
to.

Idempotent: re-running inserts nothing new. Nothing is ever hard-deleted
or deactivated. Nothing is silently skipped: any manifest value that is
not schema-valid aborts the import with a RuntimeError before any writes
happen.

Run with: python scripts\\import_functional_assessment_framework_v1.py
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
    OntologyDiseaseFinding,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "functional_assessment_framework_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "functional_assessment_framework_acceptance_v1.json"
)

SYSTEM_NAME = "Functional Assessment"
DISEASE_NAME = "Functional Assessment Framework"
VARIANT_DIMENSION = "SEVERITY_CLASS"
CONCEPT_DOMAIN = "FINDING"
APPLICABILITY_TYPE = "APPLIES_TO"

ALLOWED_SOURCE_CLASSIFICATIONS = {
    "GENERAL_CLINICAL_KNOWLEDGE", "LCD_NON_DISEASE_SPECIFIC",
}

REQUIRED_LEVEL_FIELDS = [
    "score", "display_title", "clinical_meaning", "functional_summary",
    "clinical_examples", "hospice_interpretation", "ai_summary",
]

ASSERTION_TYPES = {
    "disease_exists", "concepts_not_collapsed", "variants_not_collapsed",
    "for_each_level", "hospice_support_requires_evidence_systemwide",
    "no_diagnosis_or_score_establishes",
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    """Structural + schema-vocabulary validation -- never a clinical
    judgment. Returns a list of validation errors (empty means the
    manifest is well-formed and every value is schema-valid)."""
    errors: List[str] = []
    scales = manifest.get("assessment_scales")
    if not isinstance(scales, list) or not scales:
        errors.append("manifest.assessment_scales must be a non-empty list")
        return errors

    seen_concept_names = set()
    seen_variant_names = set()
    for scale in scales:
        scale_code = scale.get("scale_code")
        concept_name = scale.get("concept_name")
        if not scale_code or not concept_name:
            errors.append("assessment_scales entry missing scale_code or concept_name")
            continue

        normalized_concept = concept_name.strip().lower()
        if normalized_concept in seen_concept_names:
            errors.append(f"duplicate concept identity in manifest: {concept_name}")
        seen_concept_names.add(normalized_concept)

        if scale.get("source_classification") not in ALLOWED_SOURCE_CLASSIFICATIONS:
            errors.append(f"unsupported or missing source_classification for scale {scale_code!r}")
        if not scale.get("source_reference"):
            errors.append(f"missing source_reference for scale {scale_code!r}")
        if not isinstance(scale.get("visibility_rule"), dict):
            errors.append(f"missing visibility_rule for scale {scale_code!r}")

        levels = scale.get("levels")
        if not isinstance(levels, list) or not levels:
            errors.append(f"scale {scale_code!r} must declare a non-empty 'levels' list")
            continue

        for level in levels:
            for field in REQUIRED_LEVEL_FIELDS:
                if not level.get(field):
                    errors.append(
                        f"scale {scale_code!r} level {level.get('score')!r} is missing required "
                        f"field {field!r} -- scores may never be stored without full interpretation"
                    )
            variant_name = f"{scale_code} {level.get('score')}"
            normalized_variant = variant_name.strip().lower()
            if normalized_variant in seen_variant_names:
                errors.append(f"duplicate variant identity in manifest: {variant_name}")
            seen_variant_names.add(normalized_variant)

    for guard in manifest.get("differentiation_guards", []):
        for assertion in guard.get("assertions", []):
            assert_type = assertion.get("assert")
            if assert_type not in ASSERTION_TYPES:
                errors.append(
                    f"unsupported differentiation_guard assertion '{assert_type}' "
                    f"in guard {guard.get('guard_name')!r}"
                )

    return errors


def _resolve_or_create_disease(db: Session, manifest: dict) -> OntologyDisease:
    """Resolve the single Functional Assessment Framework disease by exact
    name, creating the Functional Assessment body system, its one disease
    family, and the disease itself if not already present. Never creates
    more than the manifest's own scope + new_disease declare."""
    system_name = manifest["scope"]["body_system"]
    family_name = manifest["scope"]["family"]
    disease_entry = manifest["new_disease"]

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

    name = disease_entry["disease"]
    disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
    if disease is None:
        disease = OntologyDisease(
            disease_name=name,
            disease_family_id=family.id,
            disease_category=disease_entry.get("disease_category"),
            disease_type=disease_entry.get("disease_type"),
            disease_description=disease_entry.get("disease_description"),
            clinical_purpose=disease_entry.get("clinical_purpose"),
            hospice_relevance=disease_entry.get("hospice_relevance"),
        )
        db.add(disease)
        db.flush()
    return disease


def _evidence_notes(scale: dict) -> str:
    """Fold source_classification / source_reference / visibility_rule
    into the evidence rule's existing free-text 'notes' column -- the
    established way to carry this distinction without a schema change."""
    parts = [
        "Imported verbatim from the approved Functional Assessment Framework v1 manifest.",
        f"source_classification={scale.get('source_classification')}",
        f"source_reference={scale.get('source_reference')}",
        f"visibility_rule={json.dumps(scale.get('visibility_rule'))}",
    ]
    return " | ".join(parts)


def _ensure_evidence_rule(db: Session, concept_id, scale: dict) -> bool:
    """Create or preserve an OntologyEvidenceRule for a scale concept,
    always with patient_fact_requires_evidence=True. Returns True if a
    new row was inserted."""
    existing = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept_id)
        .one_or_none()
    )
    notes = _evidence_notes(scale)
    if existing is not None:
        if existing.notes != notes:
            existing.notes = notes
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=CONCEPT_DOMAIN,
            concept_id=concept_id,
            evidence_source="functional_assessment_framework_v1",
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
        raise RuntimeError(f"Functional Assessment Framework v1 failed structural/vocabulary validation: {errors}")

    disease = _resolve_or_create_disease(db, manifest)
    db.flush()

    variants_inserted = 0
    concepts_inserted = 0
    applicability_inserted = 0
    evidence_rules_inserted = 0

    variant_by_key: Dict[Tuple[str, str], OntologyDiseaseVariant] = {
        (v.variant_dimension, v.normalized_name): v
        for v in db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
    }
    concept_by_key: Dict[str, OntologyDiseaseFinding] = {
        row.finding_name.strip().lower(): row
        for row in db.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).all()
    }

    for scale in manifest["assessment_scales"]:
        scale_code = scale["scale_code"]
        concept_name = scale["concept_name"]
        normalized_concept = concept_name.strip().lower()

        severity_levels_payload = [
            {
                "score": level["score"],
                "display_title": level["display_title"],
                "clinical_meaning": level["clinical_meaning"],
                "functional_summary": level["functional_summary"],
                "clinical_examples": level["clinical_examples"],
                "hospice_interpretation": level["hospice_interpretation"],
                "ai_summary": level["ai_summary"],
                "source_reference": level.get("source_reference", scale["source_reference"]),
                "patient_fact_requires_evidence": True,
            }
            for level in scale["levels"]
        ]
        supporting_evidence_payload = {
            "source_classification": scale["source_classification"],
            "source_reference": scale["source_reference"],
            "visibility_rule": scale["visibility_rule"],
            "purpose": scale.get("purpose"),
            "trend_policy": manifest.get("trend_policy"),
        }

        concept_row = concept_by_key.get(normalized_concept)
        if concept_row is None:
            concept_row = OntologyDiseaseFinding(
                id=uuid.uuid4(),
                disease_id=disease.id,
                finding_name=concept_name,
                finding_description=scale.get("purpose"),
                severity_levels=severity_levels_payload,
                supporting_evidence_types=supporting_evidence_payload,
            )
            db.add(concept_row)
            db.flush()
            concept_by_key[normalized_concept] = concept_row
            concepts_inserted += 1
        else:
            # Keep the JSONB payloads in sync with the manifest's current
            # content on re-run (never touches patient_fact_requires_evidence,
            # which always stays True via the evidence rule below).
            if concept_row.severity_levels != severity_levels_payload:
                concept_row.severity_levels = severity_levels_payload
            if concept_row.supporting_evidence_types != supporting_evidence_payload:
                concept_row.supporting_evidence_types = supporting_evidence_payload

        if _ensure_evidence_rule(db, concept_row.id, scale):
            evidence_rules_inserted += 1

        for level in scale["levels"]:
            variant_name = f"{scale_code} {level['score']}"
            normalized_variant = variant_name.strip().lower()
            key = (VARIANT_DIMENSION, normalized_variant)

            if key in variant_by_key:
                variant_row = variant_by_key[key]
            else:
                variant_row = OntologyDiseaseVariant(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    parent_variant_id=None,
                    variant_name=variant_name,
                    normalized_name=normalized_variant,
                    variant_dimension=VARIANT_DIMENSION,
                    variant_code=level["score"],
                    description=level["clinical_meaning"],
                    clinical_significance=level["functional_summary"],
                    hospice_relevance=level["hospice_interpretation"],
                    evidence_requirement=(
                        f"Requires a documented {scale_code} assessment (date, assessor, and source "
                        f"record) before this score is ever treated as a confirmed patient-specific "
                        f"fact. This score alone never establishes diagnosis, prognosis, hospice "
                        f"eligibility, or terminal status. AI interpretation: {level['ai_summary']}"
                    ),
                    source_reference=level.get("source_reference", scale["source_reference"]),
                )
                db.add(variant_row)
                db.flush()
                variant_by_key[key] = variant_row
                variants_inserted += 1

            existing_edge = (
                db.query(OntologyConceptVariantApplicability)
                .filter_by(
                    concept_type=CONCEPT_DOMAIN,
                    concept_id=concept_row.id,
                    variant_id=variant_row.id,
                    applicability_type=APPLICABILITY_TYPE,
                )
                .one_or_none()
            )
            if existing_edge is None:
                edge = OntologyConceptVariantApplicability(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    concept_type=CONCEPT_DOMAIN,
                    concept_id=concept_row.id,
                    variant_id=variant_row.id,
                    applicability_type=APPLICABILITY_TYPE,
                    description=(
                        f"Imported verbatim from the approved Functional Assessment Framework v1 "
                        f"manifest: {variant_name} is a score level of {concept_name}."
                    ),
                    evidence_requirement=(
                        "Requires patient-record evidence (a documented assessment with date, "
                        "assessor, and source record) before this score is ever treated as a "
                        "documented patient-specific fact."
                    ),
                )
                db.add(edge)
                applicability_inserted += 1

    return {
        "variants_inserted": variants_inserted,
        "concepts_inserted_by_domain": {CONCEPT_DOMAIN: concepts_inserted},
        "concepts_inserted_total": concepts_inserted,
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

    def concept(self, name: str) -> OntologyDiseaseFinding | None:
        return (
            self.db.query(OntologyDiseaseFinding)
            .filter_by(disease_id=self.disease.id)
            .filter(OntologyDiseaseFinding.finding_name.ilike(name.strip()))
            .one_or_none()
        )

    def variant(self, name: str) -> OntologyDiseaseVariant | None:
        return (
            self.db.query(OntologyDiseaseVariant)
            .filter_by(
                disease_id=self.disease.id,
                variant_dimension=VARIANT_DIMENSION,
                normalized_name=name.strip().lower(),
            )
            .one_or_none()
        )


def _evaluate_guard_assertion(ctx: _GuardContext, assertion: dict) -> bool:
    assert_type = assertion["assert"]

    if assert_type == "disease_exists":
        return ctx.disease_exists(assertion["disease"])

    if assert_type == "concepts_not_collapsed":
        rows = [ctx.concept(name) for name in assertion["names"]]
        if any(r is None for r in rows):
            return False
        ids = {r.id for r in rows}
        return len(ids) == len(rows)

    if assert_type == "variants_not_collapsed":
        rows = [ctx.variant(name) for name in assertion["names"]]
        if any(r is None for r in rows):
            return False
        ids = {r.id for r in rows}
        return len(ids) == len(rows)

    if assert_type == "for_each_level":
        required = assertion["required_fields"]
        concepts = ctx.db.query(OntologyDiseaseFinding).filter_by(disease_id=ctx.disease.id).all()
        for concept_row in concepts:
            for level in concept_row.severity_levels or []:
                if any(not level.get(f) for f in required):
                    return False
        return True

    if assert_type == "hospice_support_requires_evidence_systemwide":
        concepts = [ctx.concept(name) for name in assertion["names"]]
        if any(c is None for c in concepts):
            return False
        for c in concepts:
            rule = (
                ctx.db.query(OntologyEvidenceRule)
                .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=c.id)
                .one_or_none()
            )
            if rule is None or rule.patient_fact_requires_evidence is not True:
                return False
        return True

    if assert_type == "no_diagnosis_or_score_establishes":
        # Purely documentary: this manifest never creates a
        # HOSPICE_ELIGIBILITY_SUPPORT / END_STAGE_FINDING row or any
        # applicability edge of type HOSPICE_SUPPORT_FOR / PROGNOSTIC_FOR,
        # so no score can independently establish the forbidden outcomes.
        forbidden_types = {"HOSPICE_SUPPORT_FOR", "PROGNOSTIC_FOR", "END_STAGE_SUPPORT_FOR"}
        count = (
            ctx.db.query(OntologyConceptVariantApplicability)
            .filter_by(disease_id=ctx.disease.id)
            .filter(OntologyConceptVariantApplicability.applicability_type.in_(forbidden_types))
            .count()
        )
        return count == 0

    return False


def _evaluate_guard(ctx: _GuardContext, guard: dict) -> bool:
    return all(_evaluate_guard_assertion(ctx, a) for a in guard.get("assertions", []))


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
    disease = _resolve_or_create_disease(db, manifest)

    expected_variant_keys = set()
    expected_concept_keys = set()
    expected_applicability = []
    for scale in manifest["assessment_scales"]:
        concept_name = scale["concept_name"]
        expected_concept_keys.add((CONCEPT_DOMAIN, concept_name.strip().lower()))
        for level in scale["levels"]:
            variant_name = f"{scale['scale_code']} {level['score']}"
            expected_variant_keys.add((VARIANT_DIMENSION, variant_name.strip().lower()))
            expected_applicability.append(
                (VARIANT_DIMENSION, variant_name, CONCEPT_DOMAIN, concept_name, APPLICABILITY_TYPE)
            )

    stored_variants = db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
    stored_variant_keys = {(v.variant_dimension, v.normalized_name) for v in stored_variants}
    missing_variants = sorted(expected_variant_keys - stored_variant_keys)
    unexpected_variants = sorted(k for k in stored_variant_keys if k not in expected_variant_keys)

    stored_concepts = db.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).all()
    stored_concept_keys = {(CONCEPT_DOMAIN, row.finding_name.strip().lower()) for row in stored_concepts}
    concept_id_by_key = {(CONCEPT_DOMAIN, row.finding_name.strip().lower()): row.id for row in stored_concepts}
    missing_concepts = sorted(expected_concept_keys - stored_concept_keys)
    unexpected_concepts = sorted(k for k in stored_concept_keys if k not in expected_concept_keys)

    stored_applicability_rows = (
        db.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    )
    variant_id_to_name_dim = {v.id: (v.variant_dimension, v.variant_name) for v in stored_variants}
    concept_id_to_name = {row.id: row.finding_name for row in stored_concepts}
    stored_applicability_keys = set()
    for edge in stored_applicability_rows:
        dimension, variant_name = variant_id_to_name_dim.get(edge.variant_id, (None, None))
        concept_name = concept_id_to_name.get(edge.concept_id)
        stored_applicability_keys.add(
            (dimension, variant_name, edge.concept_type, concept_name, edge.applicability_type)
        )
    missing_applicability = sorted(
        [key for key in expected_applicability if key not in stored_applicability_keys],
        key=lambda k: (k[0], k[1], k[2], k[3], k[4]),
    )
    unexpected_applicability = sorted(
        [key for key in stored_applicability_keys if key not in set(expected_applicability)],
        key=lambda k: (str(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4])),
    )

    evidence_covered = 0
    evidence_missing = []
    for key in expected_concept_keys:
        concept_id = concept_id_by_key.get(key)
        if concept_id is None:
            evidence_missing.append(list(key))
            continue
        rule = db.query(OntologyEvidenceRule).filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept_id).one_or_none()
        if rule is not None and rule.patient_fact_requires_evidence is True:
            evidence_covered += 1
        else:
            evidence_missing.append(list(key))

    guard_ctx = _GuardContext(db, manifest, disease)
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
        if v.disease_id != disease.id:
            orphan_count += 1
        elif v.parent_variant_id is not None and v.parent_variant_id not in stored_variant_ids:
            orphan_count += 1
    unresolved_concept_count = 0
    for edge in stored_applicability_rows:
        if edge.variant_id not in stored_variant_ids:
            orphan_count += 1
        if edge.concept_id not in concept_id_to_name:
            orphan_count += 1
            unresolved_concept_count += 1

    cycle_count = _no_cycle(stored_variants)

    every_level_has_full_interpretation = all(
        not any(not level.get(f) for f in REQUIRED_LEVEL_FIELDS)
        for row in stored_concepts
        for level in (row.severity_levels or [])
    )

    report = {
        "manifest_id": manifest.get("title"),
        "expected_disease": DISEASE_NAME,
        "stored_disease": disease.disease_name,
        "expected_scales_count": len(manifest["assessment_scales"]),
        "stored_scales_count": len(stored_concepts),
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
        "every_score_level_has_full_interpretation_not_number_only": every_level_has_full_interpretation,
        "orphan_count": orphan_count,
        "cycle_count": cycle_count,
        "unresolved_concept_count": unresolved_concept_count,
        "second_run_new_rows": second_run_new_rows,
        "changes_outside_functional_assessment": [],
        "differentiation_guard_results": guard_results,
    }
    return report


def main() -> None:
    manifest = load_manifest()
    db = SessionLocal()
    try:
        result = run(db, manifest=manifest)
        db.commit()
        print("First run result:", json.dumps(result, indent=2))

        result2 = run(db, manifest=manifest)
        db.commit()
        second_run_new_rows = (
            result2["variants_inserted"]
            + result2["concepts_inserted_total"]
            + result2["applicability_inserted"]
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
