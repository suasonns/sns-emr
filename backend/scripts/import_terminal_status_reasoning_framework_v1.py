# scripts/import_terminal_status_reasoning_framework_v1.py
"""
Terminal Status Reasoning Framework v1 -- Verbatim Importer (PR #58).

Reads backend/manifests/terminal_status_reasoning_framework_v1.json (the
sole authoritative source for this import -- never inferred, reconstructed,
or clinically re-derived) and creates a reusable, disease-agnostic, READ-ONLY
cross-disease evidence-synthesis reasoning framework -- NOT a decision
engine. It never establishes diagnosis, prognosis, hospice eligibility,
terminal status, or a recertification recommendation.

This is the first PR in the series that reads across all 8 previously
merged Clinical Evidence Blueprint PRs (12 diseases total: Amyotrophic
Lateral Sclerosis, Congestive Heart Failure, Dementia Due To Alzheimer's
Disease, Advanced HIV Disease, AIDS, End Stage Liver Disease, Chronic Liver
Disease, Chronic Obstructive Pulmonary Disease, End Stage Pulmonary
Disease, Acute Renal Failure, Chronic Renal Failure, Stroke) instead of
extending a single disease.

No schema changes. No migrations. No API changes. No new clinical concepts,
thresholds, or scores of any kind. This reuses the existing Ontology
Disease Blueprint tables exactly as PR #49 (Functional Assessment
Framework) does:

    - A new OntologyBodySystem ("Reasoning Frameworks") with one new
      OntologyDiseaseFamily ("Terminal Status Reasoning") and one new
      OntologyDisease ("Terminal Status Reasoning Framework") -- a reusable
      container, not a clinical disease.
    - 11 OntologyDiseaseFinding rows (domain=FINDING), one per
      TERMINAL_STATUS_EVIDENCE_SUMMARY section, whose existing
      supporting_evidence_types JSONB column carries the section's source
      domains and description.
    - 1 additional OntologyDiseaseFinding row for the 4-level Evidence
      Strength Vocabulary (Strong/Moderate/Limited/Missing), whose existing
      severity_levels JSONB column carries the per-level definitions --
      the same established technique PR #49 uses to carry extra structured
      metadata in an existing column without any schema change. These
      labels describe DOCUMENTATION COMPLETENESS ONLY, never eligibility,
      prognosis, or terminal status.
    - One OntologyEvidenceRule per framework concept -- 12 total -- with
      patient_fact_requires_evidence=True.

Deliberately NOT created: any per-concept OntologyRelationship edge linking
every existing disease concept (across 12 diseases) to a section. That
would be hundreds of fragile, high-maintenance rows and would exceed a
read-only reasoning framework's scope. Instead, this importer exposes a
pure Python classify_concept(domain, name) function implementing the
manifest's declarative, ordered classification_rules, for a future
read-time API/AI layer to call directly against the concepts already
persisted by the 8 merged Clinical Evidence Blueprint PRs.

Idempotent: re-running inserts nothing new. Nothing is ever hard-deleted or
deactivated. Nothing is silently skipped: any manifest value that is not
schema-valid aborts the import with a RuntimeError before any writes
happen.

Run with: python scripts\\import_terminal_status_reasoning_framework_v1.py
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDiseaseFamily,
    OntologyDisease,
    OntologyDiseaseFinding,
    OntologyDiseaseSymptom,
    OntologyDiseaseComplication,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
    OntologyDiseaseEndStageFinding,
    OntologyEvidenceRule,
)

try:
    from app.models.ontology_disease_blueprint import OntologyDiseaseLab
except ImportError:  # pragma: no cover - defensive, matches _dump_domains.py
    OntologyDiseaseLab = None

try:
    from app.models.ontology_disease_blueprint import OntologyDiseaseDiagnosticTest
except ImportError:  # pragma: no cover - defensive, matches _dump_domains.py
    OntologyDiseaseDiagnosticTest = None

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "terminal_status_reasoning_framework_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "terminal_status_reasoning_framework_acceptance_v1.json"
)

SYSTEM_NAME = "Reasoning Frameworks"
FAMILY_NAME = "Terminal Status Reasoning"
DISEASE_NAME = "Terminal Status Reasoning Framework"
CONCEPT_DOMAIN = "FINDING"

FORBIDDEN_VOCABULARY = {
    "eligible", "not eligible", "terminal", "not terminal",
    "certify", "do not certify", "prognosis met", "prognosis not met",
}

REQUIRED_ENGINE_TERMS = {
    "diagnosis_engine", "eligibility_engine", "terminal_status_engine", "prognosis_engine",
}

# Domain name -> (model class, name attribute) used for both classification
# grounding (see _dump_domains.py, a scratch tool not part of this PR) and
# for the acceptance report's coverage check below.
DOMAIN_MODELS = {
    "SYMPTOM": (OntologyDiseaseSymptom, "symptom_name"),
    "FINDING": (OntologyDiseaseFinding, "finding_name"),
    "COMPLICATION": (OntologyDiseaseComplication, "complication_name"),
    "FUNCTIONAL_IMPACT": (OntologyDiseaseFunctionalImpact, "impact_name"),
    "NUTRITIONAL_IMPACT": (OntologyDiseaseNutritionalImpact, "impact_name"),
    "HOSPICE_ELIGIBILITY_SUPPORT": (OntologyDiseaseHospiceEligibilitySupport, "indicator_name"),
    "PROGNOSTIC_INDICATOR": (OntologyDiseasePrognosticIndicator, "indicator_name"),
    "END_STAGE_FINDING": (OntologyDiseaseEndStageFinding, "finding_name"),
}
if OntologyDiseaseLab is not None:
    for _attr in ("lab_name", "test_name", "name"):
        if hasattr(OntologyDiseaseLab, _attr):
            DOMAIN_MODELS["LAB"] = (OntologyDiseaseLab, _attr)
            break
if OntologyDiseaseDiagnosticTest is not None:
    for _attr in ("test_name", "name"):
        if hasattr(OntologyDiseaseDiagnosticTest, _attr):
            DOMAIN_MODELS["DIAGNOSTIC_TEST"] = (OntologyDiseaseDiagnosticTest, _attr)
            break

TARGET_DISEASES = [
    "Amyotrophic Lateral Sclerosis",
    "Congestive Heart Failure",
    "Dementia Due To Alzheimer's Disease",
    "Advanced HIV Disease",
    "AIDS",
    "End Stage Liver Disease",
    "Chronic Liver Disease",
    "Chronic Obstructive Pulmonary Disease",
    "End Stage Pulmonary Disease",
    "Acute Renal Failure",
    "Chronic Renal Failure",
    "Stroke",
]

SECTIONS_WITH_STORED_EVIDENCE = {1, 2, 3, 4, 5, 6, 7}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> List[str]:
    errors: List[str] = []

    sections = manifest.get("framework_sections", [])
    if len(sections) != 11:
        errors.append(f"framework_sections must contain exactly 11 sections, found {len(sections)}")
    section_numbers = sorted(s.get("section_number") for s in sections)
    if section_numbers != list(range(1, 12)):
        errors.append(f"framework_sections must be numbered 1-11 exactly once each, found {section_numbers}")

    vocab = manifest.get("evidence_strength_vocabulary", {})
    levels = vocab.get("levels", [])
    level_names = [lvl.get("level") for lvl in levels]
    if level_names != ["Strong", "Moderate", "Limited", "Missing"]:
        errors.append(f"evidence_strength_vocabulary.levels must be exactly [Strong, Moderate, Limited, Missing], found {level_names}")

    all_text_blobs = []
    for section in sections:
        all_text_blobs.append(str(section.get("section_name", "")))
        all_text_blobs.append(str(section.get("section_description", "")))
    for lvl in levels:
        all_text_blobs.append(str(lvl.get("level", "")))
        all_text_blobs.append(str(lvl.get("definition", "")))
    all_text_blobs.extend(str(p) for p in manifest.get("physician_review_prompts", []))
    all_text_blobs.extend(str(p) for p in manifest.get("narrative_support_elements", []))
    joined = " ".join(all_text_blobs).lower()
    for forbidden in FORBIDDEN_VOCABULARY:
        if forbidden in joined:
            errors.append(f"forbidden eligibility/terminal-status vocabulary term found: '{forbidden}'")

    rules = manifest.get("classification_rules", [])
    if not rules:
        errors.append("classification_rules must not be empty")
    seen_orders = set()
    for rule in rules:
        order = rule.get("order")
        if order in seen_orders:
            errors.append(f"classification_rules has duplicate order {order}")
        seen_orders.add(order)
        section_num = rule.get("section_number")
        if section_num not in range(1, 12):
            errors.append(f"classification_rules order {order} has invalid section_number {section_num}")

    ai_layer = manifest.get("ai_layer", {})
    ai_may = set(ai_layer.get("ai_may", []))
    ai_may_not = set(ai_layer.get("ai_may_not", []))
    if not REQUIRED_ENGINE_TERMS.issubset(ai_may_not):
        errors.append(
            "ai_layer.ai_may_not must include diagnosis_engine, eligibility_engine, "
            "terminal_status_engine, and prognosis_engine"
        )
    if ai_may & ai_may_not:
        errors.append("ai_layer.ai_may must never include a forbidden engine term")

    rules_block = manifest.get("rules", {})
    if not rules_block.get("read_only"):
        errors.append("rules.read_only must be true")
    if not rules_block.get("evidence_strength_describes_documentation_completeness_only"):
        errors.append("rules.evidence_strength_describes_documentation_completeness_only must be true")

    return errors


def _resolve_or_create_disease(db: Session, manifest: dict) -> OntologyDisease:
    """Resolve the single Terminal Status Reasoning Framework disease by
    exact name, creating the Reasoning Frameworks body system, its one
    disease family, and the disease itself if not already present. Never
    creates more than the manifest's own scope + new_disease declare."""
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


def _ensure_evidence_rule(db: Session, concept_id, source_note: str) -> bool:
    """Create or preserve an OntologyEvidenceRule for a framework concept,
    always with patient_fact_requires_evidence=True. Returns True if a new
    row was inserted."""
    existing = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type=CONCEPT_DOMAIN, concept_id=concept_id)
        .one_or_none()
    )
    notes = f"Imported verbatim from the approved Terminal Status Reasoning Framework v1 manifest. {source_note}"
    if existing is not None:
        if existing.notes != notes:
            existing.notes = notes
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=CONCEPT_DOMAIN,
            concept_id=concept_id,
            evidence_source="terminal_status_reasoning_framework_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes=notes,
        )
    )
    return True


def classify_concept(domain: str, name: str, classification_rules: List[dict]) -> Optional[int]:
    """Pure function implementing the manifest's declarative, ordered
    classification_rules: given a concept's domain and name, return the
    TERMINAL_STATUS_EVIDENCE_SUMMARY section_number (1-11) it belongs to,
    or None if no rule matches. Never mutates the database and never
    materializes a relationship edge -- intended to be called at read time
    by a future API/AI layer against concepts already persisted by the 8
    merged Clinical Evidence Blueprint PRs."""
    name_lower = (name or "").lower()
    for rule in sorted(classification_rules, key=lambda r: r.get("order", 0)):
        if rule.get("concept_domain") != domain:
            continue
        keywords = rule.get("name_keywords")
        if not keywords:
            return rule["section_number"]
        if any(kw.lower() in name_lower for kw in keywords):
            return rule["section_number"]
    return None


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Terminal Status Reasoning Framework v1 failed structural/vocabulary validation: {errors}")

    disease = _resolve_or_create_disease(db, manifest)
    db.flush()

    concepts_inserted = 0
    evidence_rules_inserted = 0

    concept_by_key: Dict[str, OntologyDiseaseFinding] = {
        row.finding_name.strip().lower(): row
        for row in db.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).all()
    }

    for section in manifest["framework_sections"]:
        concept_name = f"Section {section['section_number']}: {section['section_name']}"
        normalized = concept_name.strip().lower()
        supporting_evidence_payload = {
            "section_number": section["section_number"],
            "source_domains": section.get("source_domains"),
        }

        concept_row = concept_by_key.get(normalized)
        if concept_row is None:
            concept_row = OntologyDiseaseFinding(
                id=uuid.uuid4(),
                disease_id=disease.id,
                finding_name=concept_name,
                finding_description=section.get("section_description"),
                severity_levels=None,
                supporting_evidence_types=supporting_evidence_payload,
            )
            db.add(concept_row)
            db.flush()
            concept_by_key[normalized] = concept_row
            concepts_inserted += 1
        else:
            if concept_row.supporting_evidence_types != supporting_evidence_payload:
                concept_row.supporting_evidence_types = supporting_evidence_payload

        if _ensure_evidence_rule(db, concept_row.id, f"section_number={section['section_number']}"):
            evidence_rules_inserted += 1

    vocab = manifest["evidence_strength_vocabulary"]
    vocab_concept_name = vocab["concept_name"]
    normalized_vocab = vocab_concept_name.strip().lower()
    severity_levels_payload = [
        {
            "level": lvl["level"],
            "definition": lvl["definition"],
            "content_source_type": lvl["content_source_type"],
            "content_review_status": lvl["content_review_status"],
            "patient_fact_requires_evidence": True,
        }
        for lvl in vocab["levels"]
    ]
    supporting_evidence_payload = {
        "disclaimer": vocab.get("disclaimer"),
        "purpose": "documentation_completeness_only",
    }
    concept_row = concept_by_key.get(normalized_vocab)
    if concept_row is None:
        concept_row = OntologyDiseaseFinding(
            id=uuid.uuid4(),
            disease_id=disease.id,
            finding_name=vocab_concept_name,
            finding_description=vocab.get("disclaimer"),
            severity_levels=severity_levels_payload,
            supporting_evidence_types=supporting_evidence_payload,
        )
        db.add(concept_row)
        db.flush()
        concept_by_key[normalized_vocab] = concept_row
        concepts_inserted += 1
    else:
        if concept_row.severity_levels != severity_levels_payload:
            concept_row.severity_levels = severity_levels_payload
        if concept_row.supporting_evidence_types != supporting_evidence_payload:
            concept_row.supporting_evidence_types = supporting_evidence_payload

    if _ensure_evidence_rule(db, concept_row.id, "evidence_strength_vocabulary"):
        evidence_rules_inserted += 1

    db.flush()

    return {
        "disease_id": str(disease.id),
        "concepts_inserted": concepts_inserted,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    """Mechanically verifies, by applying classify_concept() against every
    concept already persisted in the live DB for each of the 12 target
    diseases, that Sections 1-7 have at least one classified concept per
    disease. This is informational coverage evidence only -- it is never a
    clinical judgment and a zero-match disease/section combination is
    reported (as 'missing evidence'), never treated as a validation
    failure, since some diseases may legitimately lack certain evidence
    types."""
    disease = db.query(OntologyDisease).filter_by(disease_name=DISEASE_NAME).one_or_none()
    concept_rows = (
        db.query(OntologyDiseaseFinding).filter_by(disease_id=disease.id).all() if disease else []
    )
    concepts_created = len(concept_rows)

    evidence_rule_count = (
        db.query(OntologyEvidenceRule)
        .filter(OntologyEvidenceRule.concept_type == CONCEPT_DOMAIN)
        .filter(OntologyEvidenceRule.concept_id.in_([row.id for row in concept_rows]))
        .count()
        if concept_rows else 0
    )

    classification_rules = manifest["classification_rules"]
    coverage: Dict[str, Dict[str, int]] = {}
    missing_evidence: List[dict] = []

    for disease_name in TARGET_DISEASES:
        target = db.query(OntologyDisease).filter_by(disease_name=disease_name).one_or_none()
        section_hits: Dict[int, int] = {n: 0 for n in SECTIONS_WITH_STORED_EVIDENCE}
        if target is not None:
            for domain, (model_cls, name_attr) in DOMAIN_MODELS.items():
                rows = db.query(model_cls).filter_by(disease_id=target.id).all()
                for row in rows:
                    name_value = getattr(row, name_attr, None)
                    section_num = classify_concept(domain, name_value, classification_rules)
                    if section_num in section_hits:
                        section_hits[section_num] += 1
        coverage[disease_name] = section_hits
        for section_num in sorted(SECTIONS_WITH_STORED_EVIDENCE):
            if section_hits[section_num] == 0:
                missing_evidence.append({"disease": disease_name, "section_number": section_num})

    return {
        "manifest_title": manifest["title"],
        "disease_created": disease is not None,
        "concepts_created": concepts_created,
        "expected_concepts": 12,
        "evidence_rules_created": evidence_rule_count,
        "second_run_new_rows": second_run_new_rows,
        "idempotent": second_run_new_rows == 0,
        "section_coverage_by_disease": coverage,
        "missing_evidence_informational": missing_evidence,
        "target_diseases_checked": TARGET_DISEASES,
    }


def main() -> None:
    manifest = load_manifest()
    db = SessionLocal()
    try:
        result_first = run(db, manifest)
        db.commit()

        result_second = run(db, manifest)
        db.commit()
        second_run_new_rows = result_second["concepts_inserted"] + result_second["evidence_rules_inserted"]

        report = build_acceptance_report(db, manifest, second_run_new_rows)
        DEFAULT_ACCEPTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_ACCEPTANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"First run: {result_first}")
        print(f"Second run (should be idempotent): {result_second}")
        print(f"Acceptance report written to {DEFAULT_ACCEPTANCE_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
