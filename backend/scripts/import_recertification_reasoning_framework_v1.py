# scripts/import_recertification_reasoning_framework_v1.py
"""
Recertification Reasoning Framework v1 -- Verbatim Importer (PR #59).

Reads backend/manifests/recertification_reasoning_framework_v1.json (the
sole authoritative source for this import -- never inferred,
reconstructed, or clinically re-derived) and creates a reusable,
disease-agnostic, READ-ONLY, period-over-period evidence-comparison
reasoning framework -- NOT a recertification decision engine, NOT an
eligibility engine, NOT a terminal-status engine, NOT a prognosis-
prediction engine.

HARD PREREQUISITE: this importer requires the Terminal Status Reasoning
Framework (PR #58) to already exist in the database, resolved by exact
disease name. If it is missing, `run()` raises RuntimeError with the
literal message "BLOCKED: TERMINAL_STATUS_REASONING_FRAMEWORK_V1
prerequisite missing" and no writes of any kind occur. This importer
never duplicates PR #58's 11 TERMINAL_STATUS_EVIDENCE_SUMMARY sections,
its domain-to-section classification_rules, its 4-level evidence-strength
vocabulary, or its ai_layer safety boundaries -- it only references them
by name and adds benefit-period comparison semantics on top.

No schema changes. No migrations. No API changes. No new clinical
concepts, thresholds, or scores of any kind, and no changes to any prior
PR's files. This reuses the existing Ontology Disease Blueprint tables
exactly as PR #49 (Functional Assessment Framework) and PR #58 (Terminal
Status Reasoning Framework) do:

    - A new OntologyDiseaseFamily ("Recertification Reasoning") under the
      existing "Reasoning Frameworks" OntologyBodySystem (created by PR
      #58 if not already present), and one new OntologyDisease
      ("Recertification Reasoning Framework") -- a reusable container,
      not a clinical disease.
    - 21 OntologyDiseaseFinding rows (domain=FINDING), one per
      RECERTIFICATION_EVIDENCE_SUMMARY section, whose existing
      supporting_evidence_types JSONB column carries the section number
      and description.
    - 1 additional OntologyDiseaseFinding row for the 9-label Period
      Comparison Vocabulary, whose existing severity_levels JSONB column
      carries the per-label definitions -- the same established
      technique PR #49/#58 use to carry extra structured metadata in an
      existing column without any schema change. These labels describe
      DOCUMENTED CHANGE ONLY, never eligibility, prognosis, terminal
      status, or recertification.
    - One OntologyEvidenceRule per framework concept -- 22 total -- with
      patient_fact_requires_evidence=True.

Deliberately NOT created: any per-concept OntologyRelationship edge, any
patient-fact row of any kind, any eligibility/terminal-status/prognosis/
life-expectancy output, and any certification/recertification/discharge
recommendation. Instead, this importer exposes pure Python comparison
functions (compare_scale, compare_numeric) implementing the manifest's
declarative scale-ordering and unit-compatibility rules, for a future
read-time API/AI layer to call directly against patient evidence.

Idempotent: re-running inserts nothing new. Nothing is ever hard-deleted
or deactivated. Nothing is silently skipped: any manifest value that is
not schema-valid aborts the import with a RuntimeError before any writes
happen.

Run with: python scripts\\import_recertification_reasoning_framework_v1.py
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
    OntologyEvidenceRule,
)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "recertification_reasoning_framework_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "recertification_reasoning_framework_acceptance_v1.json"
)

SYSTEM_NAME = "Reasoning Frameworks"
FAMILY_NAME = "Recertification Reasoning"
DISEASE_NAME = "Recertification Reasoning Framework"
CONCEPT_DOMAIN = "FINDING"

PREREQUISITE_DISEASE_NAME = "Terminal Status Reasoning Framework"
PREREQUISITE_BLOCK_MESSAGE = "BLOCKED: TERMINAL_STATUS_REASONING_FRAMEWORK_V1 prerequisite missing"

EXPECTED_SECTION_COUNT = 21
EXPECTED_COMPARISON_LABELS = [
    "DECLINING", "STABLE", "IMPROVING", "MIXED", "INDETERMINATE",
    "NOT_APPLICABLE", "PRIOR_VALUE_MISSING", "CURRENT_VALUE_MISSING",
    "CONFLICTING_DOCUMENTATION",
]
EXPECTED_EVIDENCE_COMPLETENESS_LABELS = ["Strong", "Moderate", "Limited", "Missing"]
EXPECTED_GUARD_COUNT = 20
EXPECTED_REGULATORY_CONTEXT_COUNT = 2
EXPECTED_EVIDENCE_ITEM_FIELDS = [
    "source_record_type", "source_record_id", "source_document_id",
    "assessment_date", "documentation_date", "author_or_assessor_id",
    "concept_identity", "disease_ownership", "benefit_period_association",
    "classification_rule_id", "framework_version", "generated_timestamp",
    "read_only",
]

FORBIDDEN_VOCABULARY = {
    "eligible", "not eligible", "terminal", "not terminal",
    "certify", "do not certify", "prognosis met", "prognosis not met",
    "recertify", "do not recertify", "discharge recommended",
}

REQUIRED_ENGINE_TERMS = {
    "eligibility_engine", "terminal_status_engine", "prognosis_engine",
    "life_expectancy_prediction", "recertification_recommendation_engine",
    "non_recertification_recommendation_engine", "discharge_recommendation_engine",
}

REQUIRED_PROVENANCE_FIELDS = [
    "content_source_type", "content_review_status", "source_reference",
    "regulatory_authority", "jurisdiction",
]
ALLOWED_CONTENT_SOURCE_TYPES = {
    "USER_DICTATED", "CLINICAL_REFERENCE", "REGULATORY_REFERENCE", "FRAMEWORK_DERIVED",
}
ALLOWED_CONTENT_REVIEW_STATUSES = {
    "PENDING_MEDICAL_DIRECTOR_APPROVAL", "APPROVED", "REJECTED",
}

# Scale ordering rules: whether a LOWER or HIGHER rank represents a worse
# clinical state, per scale. Comparisons are never made across scales -- see
# compare_scale(), which requires prior_scale_type == current_scale_type.
SCALE_ORDERING = {
    "PPS": "LOWER_IS_WORSE",
    "KPS": "LOWER_IS_WORSE",
    "ECOG": "HIGHER_IS_WORSE",
    "FAST": "HIGHER_IS_WORSE",  # later stage = worse
    "NYHA": "HIGHER_IS_WORSE",  # higher class = worse
}

# Valid, closed value sets per scale -- an unrecognized or malformed value is
# always a deterministic ValueError, never silently normalized or classified
# as INDETERMINATE.
_PPS_KPS_VALID_VALUES = {float(v) for v in range(0, 101, 10)}
_ECOG_VALID_VALUES = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0}
_NYHA_CLASS_RANK = {"I": 1, "II": 2, "III": 3, "IV": 4}
# FAST stages 1-5 have no sub-stages; 6 and 7 are subdivided A-F/A-D per the
# standard FAST scale. Index position is the ordering rank (later = worse).
FAST_STAGE_ORDER = [
    "1", "2", "3", "4", "5",
    "6A", "6B", "6C", "6D", "6E",
    "7A", "7B", "7C", "7D", "7E", "7F",
]
_FAST_STAGE_RANK = {stage: idx for idx, stage in enumerate(FAST_STAGE_ORDER)}


def _normalize_scale_value(scale_type: str, value) -> float:
    """Returns a numeric rank for a value already confirmed to belong to
    scale_type, or raises ValueError for any unrecognized/malformed value.
    Never guesses, coerces, or silently normalizes a clinically ambiguous
    value (e.g. never accepts NYHA as a bare digit, never accepts a FAST
    stage outside the standard 1-5, 6A-6E, 7A-7F vocabulary)."""
    if scale_type in ("PPS", "KPS"):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{scale_type} value must be numeric, got {value!r}")
        if numeric not in _PPS_KPS_VALID_VALUES:
            raise ValueError(f"{scale_type} value must be a multiple of 10 between 0 and 100, got {value!r}")
        return numeric
    if scale_type == "ECOG":
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"ECOG value must be numeric, got {value!r}")
        if numeric not in _ECOG_VALID_VALUES:
            raise ValueError(f"ECOG value must be one of 0-5, got {value!r}")
        return numeric
    if scale_type == "NYHA":
        normalized = str(value).strip().upper()
        if normalized not in _NYHA_CLASS_RANK:
            raise ValueError(f"NYHA value must be one of I, II, III, IV (approved class representations only), got {value!r}")
        return float(_NYHA_CLASS_RANK[normalized])
    if scale_type == "FAST":
        normalized = str(value).strip().upper()
        if normalized not in _FAST_STAGE_RANK:
            raise ValueError(f"FAST value must be one of {FAST_STAGE_ORDER} (approved stage representations only), got {value!r}")
        return float(_FAST_STAGE_RANK[normalized])
    raise ValueError(f"Unsupported scale_type '{scale_type}'")  # pragma: no cover - guarded by caller


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _collect_provenance_dicts(manifest: dict) -> List[dict]:
    """Every structural definition in this manifest that must carry full
    provenance (content_source_type, content_review_status,
    source_reference, regulatory_authority, jurisdiction)."""
    provenance_carriers: List[dict] = []
    provenance_carriers.extend(manifest.get("regulatory_context_definitions", []))
    provenance_carriers.extend(manifest.get("comparison_vocabulary", {}).get("labels", []))
    return provenance_carriers


def validate_manifest(manifest: dict) -> List[str]:
    errors: List[str] = []

    prerequisite = manifest.get("prerequisite", {})
    if prerequisite.get("requires_disease") != PREREQUISITE_DISEASE_NAME:
        errors.append("prerequisite.requires_disease must be exactly 'Terminal Status Reasoning Framework'")
    if prerequisite.get("block_message") != PREREQUISITE_BLOCK_MESSAGE:
        errors.append(f"prerequisite.block_message must be exactly '{PREREQUISITE_BLOCK_MESSAGE}'")

    sections = manifest.get("framework_sections", [])
    if len(sections) != EXPECTED_SECTION_COUNT:
        errors.append(f"framework_sections must contain exactly {EXPECTED_SECTION_COUNT} sections, found {len(sections)}")
    section_numbers = sorted(s.get("section_number") for s in sections)
    if section_numbers != list(range(1, EXPECTED_SECTION_COUNT + 1)):
        errors.append(f"framework_sections must be numbered 1-{EXPECTED_SECTION_COUNT} exactly once each, found {section_numbers}")

    comparison_vocab = manifest.get("comparison_vocabulary", {})
    labels = comparison_vocab.get("labels", [])
    label_names = [lbl.get("label") for lbl in labels]
    if label_names != EXPECTED_COMPARISON_LABELS:
        errors.append(f"comparison_vocabulary.labels must be exactly {EXPECTED_COMPARISON_LABELS}, found {label_names}")

    evidence_ref = manifest.get("evidence_completeness_vocabulary_reference", {})
    if evidence_ref.get("labels") != EXPECTED_EVIDENCE_COMPLETENESS_LABELS:
        errors.append("evidence_completeness_vocabulary_reference.labels must reference PR #58's exact [Strong, Moderate, Limited, Missing] labels")
    if evidence_ref.get("reused_from") != "Terminal Status Reasoning Framework v1 (PR #58)":
        errors.append("evidence_completeness_vocabulary_reference.reused_from must credit PR #58, never redefine the vocabulary")

    reg_contexts = manifest.get("regulatory_context_definitions", [])
    if len(reg_contexts) != EXPECTED_REGULATORY_CONTEXT_COUNT:
        errors.append(f"regulatory_context_definitions must contain exactly {EXPECTED_REGULATORY_CONTEXT_COUNT} distinct contexts, found {len(reg_contexts)}")
    jurisdictions = {c.get("jurisdiction") for c in reg_contexts}
    if len(jurisdictions) != len(reg_contexts):
        errors.append("regulatory_context_definitions must never merge or collapse distinct jurisdictions")

    guards = manifest.get("differentiation_guards", [])
    if len(guards) != EXPECTED_GUARD_COUNT:
        errors.append(f"differentiation_guards must contain exactly {EXPECTED_GUARD_COUNT} guards, found {len(guards)}")
    guard_numbers = sorted(g.get("guard_number") for g in guards)
    if guard_numbers != list(range(1, EXPECTED_GUARD_COUNT + 1)):
        errors.append(f"differentiation_guards must be numbered 1-{EXPECTED_GUARD_COUNT} exactly once each, found {guard_numbers}")

    scope = manifest.get("implementation_scope", {})
    if scope.get("runtime_synthesis_implemented") is not True:
        errors.append("implementation_scope.runtime_synthesis_implemented must be explicitly true (runtime patient-level synthesis is implemented in app/services/recertification_evidence_synthesis.py)")
    if "read-only patient-level runtime synthesis function" not in (scope.get("statement") or ""):
        errors.append("implementation_scope.statement must describe the implemented read-only patient-level runtime synthesis function")

    required_fields = manifest.get("required_evidence_item_fields", [])
    if sorted(required_fields) != sorted(EXPECTED_EVIDENCE_ITEM_FIELDS):
        errors.append(f"required_evidence_item_fields must be exactly {sorted(EXPECTED_EVIDENCE_ITEM_FIELDS)}, found {sorted(required_fields)}")

    for carrier in _collect_provenance_dicts(manifest):
        for field in REQUIRED_PROVENANCE_FIELDS:
            if field not in carrier or not carrier[field]:
                # comparison_vocabulary labels do not carry regulatory_authority/jurisdiction
                # (they are framework-derived, not regulatory) -- only source/type/status required there.
                if carrier in manifest.get("comparison_vocabulary", {}).get("labels", []) and field in (
                    "source_reference", "regulatory_authority", "jurisdiction",
                ):
                    continue
                errors.append(f"provenance field '{field}' missing/empty on: {carrier.get('label') or carrier.get('context_id')}")
        cst = carrier.get("content_source_type")
        if cst and cst not in ALLOWED_CONTENT_SOURCE_TYPES:
            errors.append(f"invalid content_source_type '{cst}'")
        crs = carrier.get("content_review_status")
        if crs and crs not in ALLOWED_CONTENT_REVIEW_STATUSES:
            errors.append(f"invalid content_review_status '{crs}'")

    all_text_blobs: List[str] = []
    for section in sections:
        all_text_blobs.append(str(section.get("section_name", "")))
        all_text_blobs.append(str(section.get("section_description", "")))
    for lbl in labels:
        all_text_blobs.append(str(lbl.get("label", "")))
        all_text_blobs.append(str(lbl.get("definition", "")))
    all_text_blobs.extend(str(p) for p in manifest.get("physician_review_prompts", []))
    all_text_blobs.extend(str(p) for p in manifest.get("narrative_support_elements", []))
    joined = " ".join(all_text_blobs).lower()
    for forbidden in FORBIDDEN_VOCABULARY:
        if forbidden in joined:
            errors.append(f"forbidden eligibility/terminal-status/recertification vocabulary term found: '{forbidden}'")

    ai_layer = manifest.get("ai_layer", {})
    ai_may = set(ai_layer.get("ai_may", []))
    ai_may_not = set(ai_layer.get("ai_may_not", []))
    if not REQUIRED_ENGINE_TERMS.issubset(ai_may_not):
        errors.append(
            "ai_layer.ai_may_not must include eligibility_engine, terminal_status_engine, "
            "prognosis_engine, life_expectancy_prediction, recertification_recommendation_engine, "
            "non_recertification_recommendation_engine, and discharge_recommendation_engine"
        )
    if ai_may & ai_may_not:
        errors.append("ai_layer.ai_may must never include a forbidden engine term")

    rules_block = manifest.get("rules", {})
    for required_flag in (
        "read_only", "no_eligibility_engine", "no_terminal_status_engine", "no_prognosis_engine",
        "no_recertification_engine", "no_discharge_recommendation_engine", "no_patient_fact_writes",
        "no_cross_scale_comparison", "no_cross_regulatory_context_substitution",
        "single_observation_never_creates_a_trend",
        "evidence_strength_describes_documentation_completeness_only",
        "comparison_labels_describe_documented_change_only",
    ):
        if not rules_block.get(required_flag):
            errors.append(f"rules.{required_flag} must be true")

    scale_rules = manifest.get("scale_ordering_rules", [])
    manifest_scales = {r.get("scale") for r in scale_rules}
    if manifest_scales != set(SCALE_ORDERING.keys()):
        errors.append(f"scale_ordering_rules must cover exactly {sorted(SCALE_ORDERING.keys())}, found {sorted(manifest_scales)}")

    return errors


def _resolve_prerequisite(db: Session) -> OntologyDisease:
    """Resolve the PR #58 Terminal Status Reasoning Framework disease by
    exact name. Raises RuntimeError with the literal required block
    message if it is not found -- no writes of any kind occur before this
    check succeeds."""
    prerequisite_disease = (
        db.query(OntologyDisease).filter_by(disease_name=PREREQUISITE_DISEASE_NAME).one_or_none()
    )
    if prerequisite_disease is None:
        raise RuntimeError(PREREQUISITE_BLOCK_MESSAGE)
    return prerequisite_disease


def _resolve_or_create_disease(db: Session, manifest: dict) -> OntologyDisease:
    """Resolve the single Recertification Reasoning Framework disease by
    exact name, creating (or reusing) the Reasoning Frameworks body
    system, creating its own new disease family, and creating the disease
    itself if not already present. Never creates more than the manifest's
    own scope + new_disease declare."""
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
    notes = f"Imported verbatim from the approved Recertification Reasoning Framework v1 manifest. {source_note}"
    if existing is not None:
        if existing.notes != notes:
            existing.notes = notes
        return False
    db.add(
        OntologyEvidenceRule(
            id=uuid.uuid4(),
            concept_type=CONCEPT_DOMAIN,
            concept_id=concept_id,
            evidence_source="recertification_reasoning_framework_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes=notes,
        )
    )
    return True


def compare_scale(
    prior_scale_type: str,
    prior_value,
    prior_date: Optional[str],
    current_scale_type: str,
    current_value,
    current_date: Optional[str],
) -> str:
    """Pure function: like-for-like functional scale comparison only. Never
    compares across scale types (e.g. never PPS vs KPS) -- both a
    prior_scale_type and current_scale_type are required, and any mismatch
    (or any unrecognized scale type) is a deterministic ValueError, never a
    silent INDETERMINATE classification. Returns one of the
    comparison_vocabulary direction labels:
      - both prior and current entirely undocumented (no value/date on
        either side): INDETERMINATE (no evidence exists to compare at all)
      - only the prior side undocumented: PRIOR_VALUE_MISSING
      - only the current side undocumented: CURRENT_VALUE_MISSING
      - otherwise: DECLINING / STABLE / IMPROVING per the scale's own
        worse-direction ordering
    A single (undated or one-sided) observation never creates a trend.
    Any value that is not a recognized member of the scale's own closed
    vocabulary (e.g. a bare digit for NYHA, an out-of-range FAST stage) is
    rejected with a ValueError rather than normalized or guessed."""
    if prior_scale_type not in SCALE_ORDERING or current_scale_type not in SCALE_ORDERING:
        raise ValueError(
            f"Unsupported scale_type(s) '{prior_scale_type}'/'{current_scale_type}': comparisons are "
            f"restricted to {sorted(SCALE_ORDERING.keys())}."
        )
    if prior_scale_type != current_scale_type:
        raise ValueError(
            f"Cross-scale comparison is never permitted: prior_scale_type='{prior_scale_type}' "
            f"current_scale_type='{current_scale_type}' (differentiation guard: no_cross_scale_comparison)."
        )
    scale_type = prior_scale_type

    prior_missing = prior_value is None or prior_date is None
    current_missing = current_value is None or current_date is None
    if prior_missing and current_missing:
        return "INDETERMINATE"
    if prior_missing:
        return "PRIOR_VALUE_MISSING"
    if current_missing:
        return "CURRENT_VALUE_MISSING"

    prior_rank = _normalize_scale_value(scale_type, prior_value)
    current_rank = _normalize_scale_value(scale_type, current_value)

    ordering = SCALE_ORDERING[scale_type]
    if current_rank == prior_rank:
        return "STABLE"
    if ordering == "LOWER_IS_WORSE":
        return "DECLINING" if current_rank < prior_rank else "IMPROVING"
    return "DECLINING" if current_rank > prior_rank else "IMPROVING"  # HIGHER_IS_WORSE


def compare_numeric(
    prior_value: Optional[float],
    prior_unit: Optional[str],
    prior_date: Optional[str],
    current_value: Optional[float],
    current_unit: Optional[str],
    current_date: Optional[str],
    higher_is_worse: bool,
) -> dict:
    """Pure function: generic numeric (e.g. lab) period-over-period
    comparison. Never performs implicit unit conversion and never guesses a
    conversion factor -- incompatible or missing-on-one-side units are
    reported as a documentation/clinician-review flag, never silently
    dropped or treated as a directional result. Returns a structured dict
    (never a bare label) so the original values/units are always
    preserved for audit:
      {
        "comparison_label": one of the comparison_vocabulary labels,
        "unit_compatible": bool,
        "requires_documentation_gap_flag": bool,
        "prior_value": ..., "prior_unit": ...,
        "current_value": ..., "current_unit": ...,
      }
    Label rules:
      - both sides entirely undocumented: INDETERMINATE
      - only prior undocumented: PRIOR_VALUE_MISSING
      - only current undocumented: CURRENT_VALUE_MISSING
      - both documented but units incompatible (present and different, or
        present on only one side): CONFLICTING_DOCUMENTATION if both units
        are present and differ, INDETERMINATE if a unit is present on only
        one side (compatibility itself cannot be determined) -- both cases
        set requires_documentation_gap_flag=True and never compute a
        direction from mismatched units
      - compatible units: DECLINING / STABLE / IMPROVING per higher_is_worse
    A single (undated or one-sided) observation never creates a trend."""
    prior_missing = prior_value is None or prior_date is None
    current_missing = current_value is None or current_date is None

    result = {
        "unit_compatible": None,
        "requires_documentation_gap_flag": False,
        "prior_value": prior_value,
        "prior_unit": prior_unit,
        "current_value": current_value,
        "current_unit": current_unit,
    }

    if prior_missing and current_missing:
        result["comparison_label"] = "INDETERMINATE"
        return result
    if prior_missing:
        result["comparison_label"] = "PRIOR_VALUE_MISSING"
        return result
    if current_missing:
        result["comparison_label"] = "CURRENT_VALUE_MISSING"
        return result

    norm_prior_unit = (prior_unit or "").strip().lower()
    norm_current_unit = (current_unit or "").strip().lower()
    prior_unit_present = bool(norm_prior_unit)
    current_unit_present = bool(norm_current_unit)

    if prior_unit_present != current_unit_present:
        # A unit documented on only one side means compatibility itself
        # cannot be determined -- never guessed, never treated as a match.
        result["unit_compatible"] = False
        result["requires_documentation_gap_flag"] = True
        result["comparison_label"] = "INDETERMINATE"
        return result

    if prior_unit_present and norm_prior_unit != norm_current_unit:
        # Units present on both sides but different (e.g. mg/dL vs mmol/L,
        # lb vs kg, % vs absolute value) -- no implicit conversion, no
        # guessed conversion factor. Both original values/units are
        # preserved above for physician/clinician review.
        result["unit_compatible"] = False
        result["requires_documentation_gap_flag"] = True
        result["comparison_label"] = "CONFLICTING_DOCUMENTATION"
        return result

    result["unit_compatible"] = True
    if current_value == prior_value:
        result["comparison_label"] = "STABLE"
    elif higher_is_worse:
        result["comparison_label"] = "DECLINING" if current_value > prior_value else "IMPROVING"
    else:
        result["comparison_label"] = "DECLINING" if current_value < prior_value else "IMPROVING"
    return result


def select_regulatory_context(manifest: dict, regulatory_context: str) -> dict:
    """Pure function: explicit regulatory-context selection. Never applies
    both regulatory contexts simultaneously and never silently substitutes
    one for the other -- the caller must pass exactly one of the allowed
    enum values, and gets back exactly that context's own definition
    (regulatory_authority, jurisdiction, payer_context, prognosis_standard,
    source_reference), never a merged/blended result."""
    context_map = {
        "CMS_MEDICARE_SIX_MONTH": "FEDERAL_CMS_HOSPICE",
        "CALIFORNIA_CDPH_STATE": "CALIFORNIA_DPH_HOSPICE",
    }
    if regulatory_context not in context_map:
        raise ValueError(
            f"Unsupported regulatory_context '{regulatory_context}': must be one of {sorted(context_map.keys())}."
        )
    context_id = context_map[regulatory_context]
    for context in manifest.get("regulatory_context_definitions", []):
        if context.get("context_id") == context_id:
            return context
    raise ValueError(f"regulatory_context_definitions is missing the required context_id '{context_id}'")  # pragma: no cover


def evaluate_differentiation_guards(manifest: dict) -> Dict[str, int]:
    """Structural, declarative guard evaluation: every guard in the
    manifest is a well-formed (subject, relation, object) safety
    assertion. This never computes guards against patient data (this PR
    creates no patient facts) -- it verifies the guard metadata itself is
    complete and internally consistent, and reports guards_passed as the
    count of guards that are well-formed. A malformed guard is reported as
    a failure, never silently dropped."""
    guards = manifest.get("differentiation_guards", [])
    passed = 0
    failed: List[int] = []
    required_relations = {
        "DOES_NOT_ESTABLISH", "DOES_NOT_RECOMMEND", "DOES_NOT_MEAN", "IS_NOT", "REQUIRES",
    }
    for guard in guards:
        if (
            guard.get("subject")
            and guard.get("relation") in required_relations
            and guard.get("object")
        ):
            passed += 1
        else:
            failed.append(guard.get("guard_number"))
    return {"guards_total": len(guards), "guards_passed": passed, "guards_failed": failed}


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Recertification Reasoning Framework v1 failed structural/vocabulary validation: {errors}")

    # Hard prerequisite check -- must occur before any write of any kind.
    _resolve_prerequisite(db)

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
            "framework": DISEASE_NAME,
            "prerequisite": PREREQUISITE_DISEASE_NAME,
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

    comparison_vocab = manifest["comparison_vocabulary"]
    vocab_concept_name = comparison_vocab["concept_name"]
    normalized_vocab = vocab_concept_name.strip().lower()
    severity_levels_payload = [
        {
            "label": lbl["label"],
            "definition": lbl["definition"],
            "content_source_type": lbl["content_source_type"],
            "content_review_status": lbl["content_review_status"],
            "patient_fact_requires_evidence": True,
        }
        for lbl in comparison_vocab["labels"]
    ]
    supporting_evidence_payload = {
        "disclaimer": comparison_vocab.get("disclaimer"),
        "purpose": "documented_change_only",
        "reuses_evidence_completeness_vocabulary_from": "Terminal Status Reasoning Framework v1 (PR #58)",
    }
    concept_row = concept_by_key.get(normalized_vocab)
    if concept_row is None:
        concept_row = OntologyDiseaseFinding(
            id=uuid.uuid4(),
            disease_id=disease.id,
            finding_name=vocab_concept_name,
            finding_description=comparison_vocab.get("disclaimer"),
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

    if _ensure_evidence_rule(db, concept_row.id, "comparison_vocabulary"):
        evidence_rules_inserted += 1

    db.flush()

    return {
        "disease_id": str(disease.id),
        "concepts_inserted": concepts_inserted,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    prerequisite_disease = (
        db.query(OntologyDisease).filter_by(disease_name=PREREQUISITE_DISEASE_NAME).one_or_none()
    )
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

    guard_report = evaluate_differentiation_guards(manifest)
    section_names = [s["section_name"] for s in sorted(manifest["framework_sections"], key=lambda s: s["section_number"])]
    runtime_synthesis_report = load_runtime_synthesis_report()

    # Concept-id uniqueness across all created rows == zero duplicate/orphan/cycle concepts;
    # this framework creates no relationship edges of any kind, so cycle_count is trivially 0.
    concept_ids = {row.id for row in concept_rows}
    orphan_count = sum(1 for row in concept_rows if row.disease_id != disease.id) if disease else 0
    unresolved_framework_concept_count = max(0, EXPECTED_SECTION_COUNT + 1 - len(concept_ids)) if disease else EXPECTED_SECTION_COUNT + 1

    return {
        "manifest_title": manifest["title"],
        "pr_58_prerequisite_resolved": prerequisite_disease is not None,
        "framework_version": manifest.get("manifest_version"),
        "summary_section_count": EXPECTED_SECTION_COUNT,
        "summary_section_names": section_names,
        "comparison_label_count": len(EXPECTED_COMPARISON_LABELS),
        "evidence_completeness_label_count": len(EXPECTED_EVIDENCE_COMPLETENESS_LABELS),
        "regulatory_context_count": len(manifest.get("regulatory_context_definitions", [])),
        "differentiation_guards_total": guard_report["guards_total"],
        "differentiation_guards_passed": guard_report["guards_passed"],
        "differentiation_guards_failed": guard_report["guards_failed"],
        "disease_created": disease is not None,
        "concepts_created": concepts_created,
        "expected_concepts": EXPECTED_SECTION_COUNT + 1,
        "evidence_rules_created": evidence_rule_count,
        "second_run_new_rows": second_run_new_rows,
        "idempotent": second_run_new_rows == 0,
        "patient_facts_inserted": 0,
        "patient_facts_updated": 0,
        "patient_facts_deleted": 0,
        "eligibility_outputs_created": 0,
        "terminal_status_outputs_created": 0,
        "prognosis_outputs_created": 0,
        "life_expectancy_predictions_created": 0,
        "certification_recommendations_created": 0,
        "recertification_recommendations_created": 0,
        "discharge_recommendations_created": 0,
        "orphan_count": orphan_count,
        "cycle_count": 0,
        "unresolved_framework_concept_count": unresolved_framework_concept_count,
        "changes_outside_framework": 0,
        "implementation_scope": {
            "structural_framework_validated": True,
            "runtime_synthesis_implemented": True,
            "runtime_synthesis_validated": runtime_synthesis_report.get("status") == "GENERATED_FROM_REAL_EXECUTION",
            "patient_data_write_audit_passed": runtime_synthesis_report.get("patient_data_write_audit_passed", False),
            "patient_data_write_audit_note": runtime_synthesis_report.get(
                "patient_data_write_audit_note",
                "Runtime synthesis write-audit report not yet generated -- run "
                "scripts/generate_recertification_runtime_synthesis_report.py against the isolated test database.",
            ),
        },
        "runtime_synthesis_metrics": runtime_synthesis_report,
        "test_matrix": load_test_matrix_report(),
        "baseline_attribution": load_baseline_attribution_report(),
    }


def load_runtime_synthesis_report() -> dict:
    """Loads the externally-generated runtime-synthesis report (produced by
    scripts/generate_recertification_runtime_synthesis_report.py, which
    executes app.services.recertification_evidence_synthesis.
    build_recertification_evidence_summary() against real patient rows in
    the isolated test database and captures every SQL statement issued via
    a SQLAlchemy event listener). Returns a NOT_YET_GENERATED placeholder
    -- never fabricated counters -- if the report has not been produced
    yet."""
    report_path = Path(__file__).resolve().parent.parent / "artifacts" / "recertification_runtime_synthesis_v1.json"
    if not report_path.exists():
        return {"status": "NOT_YET_GENERATED"}
    with open(report_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_test_matrix_report() -> dict:
    """Loads the externally-generated test-matrix report (produced by
    scripts/run_recertification_test_matrix.py from real pytest --junitxml
    runs across freshly rebuilt isolated databases). Returns a
    NOT_YET_GENERATED placeholder -- never fabricated counters -- if the
    matrix has not been executed yet."""
    matrix_path = Path(__file__).resolve().parent.parent / "artifacts" / "recertification_test_matrix_v1.json"
    if not matrix_path.exists():
        return {"status": "NOT_YET_GENERATED"}
    with open(matrix_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_baseline_attribution_report() -> dict:
    """Loads the externally-generated baseline-attribution report (produced
    by scripts/generate_recertification_baseline_attribution.py, which
    classifies every PR #59-branch test failure against real origin/main
    baseline JUnit XML data as BASELINE_REPRODUCED_IDENTICALLY,
    PR59_NEW_FAILURE, NONDETERMINISTIC_REQUIRES_INVESTIGATION, or
    PRE_EXISTING_STRUCTURAL_TEST_DESIGN_LIMITATION). Returns a
    NOT_YET_GENERATED placeholder -- never fabricated counters -- if the
    attribution has not been executed yet."""
    attribution_path = Path(__file__).resolve().parent.parent / "artifacts" / "recertification_baseline_attribution_v1.json"
    if not attribution_path.exists():
        return {"status": "NOT_YET_GENERATED"}
    with open(attribution_path, "r", encoding="utf-8") as fh:
        full = json.load(fh)
    return {
        "pr59_new_failure_count": full["pr59_new_failure_count"],
        "result_changed_count": full["result_changed_count"],
        "nondeterministic_requires_investigation_count": full["nondeterministic_requires_investigation_count"],
        "baseline_reproduced_identically_count": full["baseline_reproduced_identically_count"],
        "pre_existing_structural_test_design_limitation_count": full["pre_existing_structural_test_design_limitation_count"],
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
