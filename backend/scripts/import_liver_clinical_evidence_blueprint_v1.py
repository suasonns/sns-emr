# scripts/import_liver_clinical_evidence_blueprint_v1.py
"""
Liver Clinical Evidence Blueprint v1 -- Extension-Only Importer.

Reads backend/manifests/liver_clinical_evidence_blueprint_v1.json (the
sole authoritative source for this import) and EXTENDS the existing
"End Stage Liver Disease" AND "Chronic Liver Disease" diseases created
by the Liver Production Knowledge Manifest v1 (PR #41, merged). Unlike
the Renal Clinical Evidence Blueprint (which extends two genuinely
distinct diseases asymmetrically), this manifest applies every addition
IDENTICALLY to both liver diseases -- PR #41 built them with an
identical FINDING/COMPLICATION/HOSPICE_ELIGIBILITY_SUPPORT concept set,
so extending only one would create ontology drift between them. This
importer:

- NEVER creates a new OntologyBodySystem, OntologyDiseaseFamily, or
  OntologyDisease row. If either "End Stage Liver Disease",
  "Chronic Liver Disease", or "Functional Assessment Framework"
  (PR #49, merged) does not already exist, the import aborts before any
  writes.
- NEVER creates a new OntologyDiseaseVariant row.
- NEVER duplicates PR #41's or PR #49's PPS/KPS definitions, and NEVER
  duplicates a finding/complication/hospice-eligibility-support concept
  already present in PR #41 (see the manifest's
  already_present_verified.mapping). Instead it adds two
  OntologyRelationship edges per disease linking each disease's existing
  PPS Less Than 70 Percent / KPS Less Than 70 Percent concepts to the
  Functional Assessment Framework's existing PPS/KPS
  OntologyDiseaseFinding rows.
- Adds four genuinely missing atomic liver concepts (MELD Score,
  Elevated Serum Bilirubin, Hyponatremia, Recurrent Liver Disease
  Hospitalization), applied identically to both diseases, and 10 liver
  recertification-trend PROGNOSTIC_INDICATOR concepts per disease, every
  one carrying provenance metadata (content_source_type,
  content_review_status) encoded verbatim into the existing
  OntologyEvidenceRule.notes free-text field -- no schema, migration, or
  API changes.
- Idempotent: re-running inserts nothing new.
- Nothing is ever hard-deleted or deactivated.

Run with: .\\.venv\\Scripts\\python.exe scripts\\import_liver_clinical_evidence_blueprint_v1.py
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ontology.treatment_identity import concept_identity_key

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseVariant,
    OntologyConceptVariantApplicability,
    OntologyEvidenceRule,
    OntologyRelationship,
    OntologyDiseaseFinding,
    OntologyDiseaseComplication,
    OntologyDiseaseSymptom,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseasePrognosticIndicator,
)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "liver_clinical_evidence_blueprint_v1.json"
)
DEFAULT_ACCEPTANCE_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "liver_clinical_evidence_blueprint_acceptance_v1.json"
)

EXTENDS_DISEASE_NAMES = ["End Stage Liver Disease", "Chronic Liver Disease"]
# Kept singular for compatibility with the shared test-suite pattern used by
# every other Clinical Evidence Blueprint importer (CHF, Dementia).
EXTENDS_DISEASE_NAME = EXTENDS_DISEASE_NAMES[0]
FAF_DISEASE_NAME = "Functional Assessment Framework"

ALLOWED_CONCEPT_DOMAINS = {
    "SYMPTOM", "FINDING", "NUTRITIONAL_IMPACT", "COMPLICATION", "FUNCTIONAL_IMPACT",
    "HOSPICE_ELIGIBILITY_SUPPORT",
}
ALLOWED_APPLICABILITY_TYPES = {
    "APPLIES_TO", "EXPECTED_WITH", "STRONGLY_ASSOCIATED_WITH", "MAY_OCCUR_WITH",
    "SUPPORTS_DIFFERENTIATION", "CONTRAINDICATED_FOR", "TREATMENT_SPECIFIC_TO",
    "PROGNOSTIC_FOR", "END_STAGE_SUPPORT_FOR", "HOSPICE_SUPPORT_FOR",
}
ALLOWED_CONTENT_SOURCE_TYPES = {"USER_DICTATED", "CLINICAL_REFERENCE"}
ALLOWED_CONTENT_REVIEW_STATUSES = {"PENDING_MEDICAL_DIRECTOR_APPROVAL", "APPROVED", "REJECTED"}

FAF_LINKAGE_TARGET_DOMAIN = "FINDING"
RELATIONSHIP_TYPE = "REFERENCES_FUNCTIONAL_ASSESSMENT_SCALE"

CONCEPT_DOMAIN_MODEL_MAP = {
    "SYMPTOM": (OntologyDiseaseSymptom, "symptom_name"),
    "FINDING": (OntologyDiseaseFinding, "finding_name"),
    "NUTRITIONAL_IMPACT": (OntologyDiseaseNutritionalImpact, "impact_name"),
    "COMPLICATION": (OntologyDiseaseComplication, "complication_name"),
    "FUNCTIONAL_IMPACT": (OntologyDiseaseFunctionalImpact, "impact_name"),
    "HOSPICE_ELIGIBILITY_SUPPORT": (OntologyDiseaseHospiceEligibilitySupport, "indicator_name"),
}

# The generic concept_type -> (model, name_attr) map used ONLY to resolve
# already-existing Liver/FAF concepts referenced by name (never to create).
LOOKUP_DOMAIN_MODEL_MAP = dict(CONCEPT_DOMAIN_MODEL_MAP)

PROVENANCE_PATTERN = re.compile(
    r"content_source_type=(?P<cst>[A-Z_]+);\s*content_review_status=(?P<crs>[A-Z_]+)"
)

_FINDING_DESCRIPTION_ATTR = "finding_description"


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _provenance_text(content_source_type: str, content_review_status: str, extra: str = "") -> str:
    text = f"content_source_type={content_source_type}; content_review_status={content_review_status}."
    if extra:
        text = f"{text} {extra}"
    return text


def validate_manifest(manifest: dict) -> List[str]:
    """Structural + schema-vocabulary validation -- never a clinical
    judgment. Confirms every new concept, applicability edge, FAF
    linkage, and recertification trend indicator declares valid,
    present provenance metadata (ALL_CLINICAL_CONTENT_HAS_PROVENANCE),
    and that the manifest never declares a new disease/variant."""
    errors: List[str] = []

    scope = manifest.get("scope", {})
    if scope.get("extends_diseases") != EXTENDS_DISEASE_NAMES:
        errors.append(
            "manifest scope.extends_diseases must be "
            "['End Stage Liver Disease', 'Chronic Liver Disease']"
        )
    if scope.get("extends_functional_assessment_framework") != FAF_DISEASE_NAME:
        errors.append("manifest scope.extends_functional_assessment_framework must be 'Functional Assessment Framework'")

    if manifest.get("rules", {}).get("no_new_disease") is not True:
        errors.append("manifest rules.no_new_disease must be true")
    if manifest.get("rules", {}).get("no_duplicate_assessment_definitions") is not True:
        errors.append("manifest rules.no_duplicate_assessment_definitions must be true")

    seen_concepts = set()
    for c in manifest.get("new_concepts", []):
        domain = c.get("domain")
        name = c.get("name")
        cst = c.get("content_source_type")
        crs = c.get("content_review_status")
        if domain not in ALLOWED_CONCEPT_DOMAINS:
            errors.append(f"new_concepts entry has invalid domain: {domain!r}")
            continue
        if not name or not str(name).strip():
            errors.append("new_concepts entry missing name")
            continue
        if name.strip().isdigit():
            errors.append(f"new_concepts entry {name!r} is numeric-only -- not nurse-readable")
        key = (domain, name.strip().lower())
        if key in seen_concepts:
            errors.append(f"duplicate new_concepts identity in manifest: {domain}/{name}")
        seen_concepts.add(key)
        if cst not in ALLOWED_CONTENT_SOURCE_TYPES:
            errors.append(f"new_concepts entry {name!r} has invalid content_source_type: {cst!r}")
        if crs not in ALLOWED_CONTENT_REVIEW_STATUSES:
            errors.append(f"new_concepts entry {name!r} has invalid content_review_status: {crs!r}")
        if not c.get("description") or not str(c["description"]).strip():
            errors.append(f"new_concepts entry {name!r} missing human-readable description")

    for a in manifest.get("new_applicability", []):
        if a.get("concept_domain") not in ALLOWED_CONCEPT_DOMAINS:
            errors.append(f"new_applicability entry has invalid concept_domain: {a.get('concept_domain')!r}")
        if a.get("applicability_type") not in ALLOWED_APPLICABILITY_TYPES:
            errors.append(f"new_applicability entry has invalid applicability_type: {a.get('applicability_type')!r}")
        if not a.get("variant") or not a.get("concept"):
            errors.append("new_applicability entry missing variant or concept")
        if not a.get("variant_dimension"):
            errors.append("new_applicability entry missing variant_dimension (required -- liver variant "
                           "names are not unique across dimensions)")

    for link in manifest.get("functional_assessment_linkage", []):
        for field in ("chf_concept_domain", "chf_concept_name", "faf_concept_name", "relationship_type"):
            if not link.get(field):
                errors.append(f"functional_assessment_linkage entry missing {field}")
        cst = link.get("content_source_type")
        crs = link.get("content_review_status")
        if cst not in ALLOWED_CONTENT_SOURCE_TYPES:
            errors.append(f"functional_assessment_linkage entry has invalid content_source_type: {cst!r}")
        if crs not in ALLOWED_CONTENT_REVIEW_STATUSES:
            errors.append(f"functional_assessment_linkage entry has invalid content_review_status: {crs!r}")

    recert = manifest.get("recertification_evidence_model", {})
    if recert.get("diseases") != EXTENDS_DISEASE_NAMES:
        errors.append(
            "recertification_evidence_model.diseases must be "
            "['End Stage Liver Disease', 'Chronic Liver Disease']"
        )
    seen_trend = set()
    for t in recert.get("trend_indicators", []):
        name = t.get("name")
        if not name or not str(name).strip():
            errors.append("trend_indicators entry missing name")
            continue
        if name.strip().isdigit():
            errors.append(f"trend_indicators entry {name!r} is numeric-only -- not nurse-readable")
        normalized = name.strip().lower()
        if normalized in seen_trend:
            errors.append(f"duplicate trend_indicators identity in manifest: {name}")
        seen_trend.add(normalized)
        cst = t.get("content_source_type")
        crs = t.get("content_review_status")
        if cst not in ALLOWED_CONTENT_SOURCE_TYPES:
            errors.append(f"trend_indicators entry {name!r} has invalid content_source_type: {cst!r}")
        if crs not in ALLOWED_CONTENT_REVIEW_STATUSES:
            errors.append(f"trend_indicators entry {name!r} has invalid content_review_status: {crs!r}")
        if not t.get("description") or not str(t["description"]).strip():
            errors.append(f"trend_indicators entry {name!r} missing human-readable description")

    ai_layer = manifest.get("ai_layer", {})
    ai_may = set(ai_layer.get("ai_may", []))
    ai_may_not = set(ai_layer.get("ai_may_not", []))
    forbidden_engines = {"diagnosis_engine", "eligibility_engine", "terminal_status_engine", "prognosis_engine"}
    if not forbidden_engines.issubset(ai_may_not):
        errors.append("ai_layer.ai_may_not must include diagnosis_engine, eligibility_engine, "
                       "terminal_status_engine, and prognosis_engine")
    if ai_may & forbidden_engines:
        errors.append("ai_layer.ai_may must never include a forbidden engine term")

    return errors


def _resolve_disease(db: Session, name: str) -> OntologyDisease:
    disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
    if disease is None:
        raise RuntimeError(
            f"Liver Clinical Evidence Blueprint v1 requires the disease {name!r} to already exist. "
            "This manifest is extension-only and must never create a new disease foundation. "
            "Aborting without any writes."
        )
    return disease


def _resolve_variant(db: Session, disease_id, variant_name: str, variant_dimension: str | None = None) -> OntologyDiseaseVariant:
    """Resolves an existing variant by (disease_id, normalized_name), or by
    (disease_id, variant_dimension, normalized_name) when variant_dimension
    is provided. A dimension is REQUIRED whenever the liver disease has
    more than one variant sharing the same name across dimensions (e.g.
    'Child-Pugh Class C Cirrhosis' exists as a SEVERITY_CLASS variant on
    both diseases) -- omitting it in that case raises rather than
    silently picking one."""
    normalized = variant_name.strip().lower()
    query = db.query(OntologyDiseaseVariant).filter_by(disease_id=disease_id, normalized_name=normalized)
    if variant_dimension is not None:
        query = query.filter_by(variant_dimension=variant_dimension)
    matches = query.all()
    if len(matches) == 0:
        raise RuntimeError(
            f"Liver Clinical Evidence Blueprint v1 references variant {variant_name!r} "
            f"(dimension={variant_dimension!r}) which was not found on the existing liver disease. "
            "Aborting without any writes."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Liver Clinical Evidence Blueprint v1 references variant {variant_name!r} which is "
            "ambiguous (multiple dimensions share this name) -- a variant_dimension must be specified. "
            "Aborting without any writes."
        )
    return matches[0]


def _resolve_concept(db: Session, disease_id, domain: str, name: str):
    model_cls, name_attr = LOOKUP_DOMAIN_MODEL_MAP[domain]
    row = (
        db.query(model_cls)
        .filter_by(disease_id=disease_id)
        .filter(getattr(model_cls, name_attr).ilike(name.strip()))
        .one_or_none()
    )
    if row is None:
        raise RuntimeError(
            f"Liver Clinical Evidence Blueprint v1 references concept {name!r} (domain={domain}) which "
            "was not found on the expected disease. Aborting without any writes."
        )
    return row


def _ensure_evidence_rule(db: Session, concept_type: str, concept_id, content_source_type: str,
                           content_review_status: str, description: str) -> bool:
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
            evidence_source="liver_clinical_evidence_blueprint_v1",
            evidence_type="MANIFEST_ATOMIC_CONCEPT",
            confidence="HIGH",
            patient_fact_requires_evidence=True,
            notes=_provenance_text(
                content_source_type, content_review_status,
                f"Imported from the approved Liver Clinical Evidence Blueprint v1. {description}",
            ),
        )
    )
    return True


def _run_for_disease(db: Session, manifest: dict, disease: OntologyDisease, faf_disease: OntologyDisease) -> dict:
    """Applies the manifest's new_concepts / new_applicability /
    functional_assessment_linkage / recertification trend indicators to a
    single already-existing liver disease. Called once per disease in
    EXTENDS_DISEASE_NAMES so both mirrored diseases stay identical."""
    concepts_inserted_by_domain: Dict[str, int] = {}
    applicability_inserted = 0
    evidence_rules_inserted = 0
    relationships_inserted = 0
    trend_indicators_inserted = 0

    concept_by_key: Dict[Tuple[str, str], object] = {}
    for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
        for existing in db.query(model_cls).filter_by(disease_id=disease.id).all():
            concept_by_key[(domain, concept_identity_key(domain, getattr(existing, name_attr)))] = existing

    # --- new atomic concepts ---
    for c in manifest.get("new_concepts", []):
        domain = c["domain"]
        name = c["name"]
        normalized = concept_identity_key(domain, name)
        key = (domain, normalized)

        if key in concept_by_key:
            row = concept_by_key[key]
        else:
            model_cls, name_attr = CONCEPT_DOMAIN_MODEL_MAP[domain]
            description_attr = _FINDING_DESCRIPTION_ATTR if domain == "FINDING" else "description"
            row = model_cls(
                id=uuid.uuid4(),
                disease_id=disease.id,
                **{name_attr: name, description_attr: c["description"]},
            )
            db.add(row)
            db.flush()
            concept_by_key[key] = row
            concepts_inserted_by_domain[domain] = concepts_inserted_by_domain.get(domain, 0) + 1

        if _ensure_evidence_rule(
            db, domain, row.id, c["content_source_type"], c["content_review_status"], c["description"]
        ):
            evidence_rules_inserted += 1

    db.flush()

    # --- new applicability edges (new concept -> existing liver variant) ---
    for a in manifest.get("new_applicability", []):
        variant_name = a["variant"]
        concept_domain = a["concept_domain"]
        concept_name = a["concept"]
        applicability_type = a["applicability_type"]

        variant_row = _resolve_variant(db, disease.id, variant_name, a.get("variant_dimension"))
        concept_key = (concept_domain, concept_name.strip().lower())
        if concept_key not in concept_by_key:
            raise RuntimeError(
                f"Liver Clinical Evidence Blueprint v1 applicability mapping references a concept that "
                f"was not created: concept={concept_name!r} domain={concept_domain!r}. "
                "Aborting rather than skipping silently."
            )
        concept_row = concept_by_key[concept_key]

        existing_edge = (
            db.query(OntologyConceptVariantApplicability)
            .filter_by(
                concept_type=concept_domain,
                concept_id=concept_row.id,
                variant_id=variant_row.id,
                applicability_type=applicability_type,
            )
            .one_or_none()
        )
        if existing_edge is not None:
            continue

        db.add(
            OntologyConceptVariantApplicability(
                id=uuid.uuid4(),
                disease_id=disease.id,
                concept_type=concept_domain,
                concept_id=concept_row.id,
                variant_id=variant_row.id,
                applicability_type=applicability_type,
                description="Imported from the approved Liver Clinical Evidence Blueprint v1.",
                evidence_requirement=(
                    "Requires patient-record evidence before this applicability is ever treated as a "
                    "documented patient-specific fact."
                ),
            )
        )
        applicability_inserted += 1

    db.flush()

    # --- functional assessment framework linkage (OntologyRelationship, disease-agnostic) ---
    for link in manifest.get("functional_assessment_linkage", []):
        liver_concept = _resolve_concept(db, disease.id, link["chf_concept_domain"], link["chf_concept_name"])
        faf_concept = _resolve_concept(db, faf_disease.id, FAF_LINKAGE_TARGET_DOMAIN, link["faf_concept_name"])

        existing_rel = (
            db.query(OntologyRelationship)
            .filter_by(
                source_concept_type=link["chf_concept_domain"],
                source_concept_id=liver_concept.id,
                relationship_type=link["relationship_type"],
                target_concept_type=FAF_LINKAGE_TARGET_DOMAIN,
                target_concept_id=faf_concept.id,
            )
            .one_or_none()
        )
        if existing_rel is not None:
            continue

        db.add(
            OntologyRelationship(
                id=uuid.uuid4(),
                source_concept_type=link["chf_concept_domain"],
                source_concept_id=liver_concept.id,
                relationship_type=link["relationship_type"],
                target_concept_type=FAF_LINKAGE_TARGET_DOMAIN,
                target_concept_id=faf_concept.id,
                description=_provenance_text(
                    link["content_source_type"], link["content_review_status"], link.get("description", "")
                ),
                active=True,
            )
        )
        relationships_inserted += 1

    db.flush()

    # --- recertification trend indicators (PROGNOSTIC_INDICATOR, per-disease) ---
    existing_trend = {
        row.indicator_name.strip().lower(): row
        for row in db.query(OntologyDiseasePrognosticIndicator).filter_by(disease_id=disease.id).all()
    }
    recert = manifest.get("recertification_evidence_model", {})
    for t in recert.get("trend_indicators", []):
        name = t["name"]
        normalized = name.strip().lower()
        if normalized in existing_trend:
            row = existing_trend[normalized]
        else:
            row = OntologyDiseasePrognosticIndicator(
                id=uuid.uuid4(),
                disease_id=disease.id,
                indicator_name=name,
                description=t["description"],
            )
            db.add(row)
            db.flush()
            existing_trend[normalized] = row
            trend_indicators_inserted += 1

        if _ensure_evidence_rule(
            db, "PROGNOSTIC_INDICATOR", row.id, t["content_source_type"], t["content_review_status"],
            t["description"],
        ):
            evidence_rules_inserted += 1

    return {
        "concepts_inserted_by_domain": concepts_inserted_by_domain,
        "concepts_inserted_total": sum(concepts_inserted_by_domain.values()),
        "applicability_inserted": applicability_inserted,
        "relationships_inserted": relationships_inserted,
        "trend_indicators_inserted": trend_indicators_inserted,
        "evidence_rules_inserted": evidence_rules_inserted,
    }


def run(db: Session, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest()

    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"Liver Clinical Evidence Blueprint v1 failed structural/vocabulary validation: {errors}")

    faf_disease = _resolve_disease(db, FAF_DISEASE_NAME)
    diseases = [_resolve_disease(db, name) for name in EXTENDS_DISEASE_NAMES]
    db.flush()

    totals = {
        "concepts_inserted_by_domain": {},
        "concepts_inserted_total": 0,
        "applicability_inserted": 0,
        "relationships_inserted": 0,
        "trend_indicators_inserted": 0,
        "evidence_rules_inserted": 0,
    }
    for disease in diseases:
        result = _run_for_disease(db, manifest, disease, faf_disease)
        for domain, count in result["concepts_inserted_by_domain"].items():
            totals["concepts_inserted_by_domain"][domain] = totals["concepts_inserted_by_domain"].get(domain, 0) + count
        totals["concepts_inserted_total"] += result["concepts_inserted_total"]
        totals["applicability_inserted"] += result["applicability_inserted"]
        totals["relationships_inserted"] += result["relationships_inserted"]
        totals["trend_indicators_inserted"] += result["trend_indicators_inserted"]
        totals["evidence_rules_inserted"] += result["evidence_rules_inserted"]

    return totals


def build_acceptance_report(db: Session, manifest: dict, second_run_new_rows: int) -> dict:
    """Compare the manifest against the (already-imported) clean database
    and report expected vs. stored for new concepts, applicability, FAF
    relationships, and trend indicators -- summed across both extended
    diseases -- plus provenance coverage and the second-run new-row
    count. Never a clinical judgment -- purely a mechanical comparison."""
    faf_disease = _resolve_disease(db, FAF_DISEASE_NAME)
    diseases = [_resolve_disease(db, name) for name in EXTENDS_DISEASE_NAMES]

    expected_concept_keys = {
        (c["domain"], c["name"].strip().lower()) for c in manifest.get("new_concepts", [])
    }
    expected_trend_keys = {
        t["name"].strip().lower() for t in manifest.get("recertification_evidence_model", {}).get("trend_indicators", [])
    }
    expected_applicability = manifest.get("new_applicability", [])
    expected_linkages = manifest.get("functional_assessment_linkage", [])

    per_disease_reports = []
    total_concepts_stored = 0
    total_missing_concepts = []
    total_applicability_stored = 0
    total_relationships_stored = 0
    total_trend_stored = 0
    total_missing_trend = []
    provenance_checked = 0
    provenance_valid = 0
    pre_existing_concepts_all: List[Tuple[str, str, str]] = []

    for disease in diseases:
        stored_concept_keys = set()
        concept_id_by_key: Dict[Tuple[str, str], object] = {}
        for domain, (model_cls, name_attr) in CONCEPT_DOMAIN_MODEL_MAP.items():
            for row in db.query(model_cls).filter_by(disease_id=disease.id).all():
                key = (domain, getattr(row, name_attr).strip().lower())
                stored_concept_keys.add(key)
                concept_id_by_key[key] = row.id

        manifest_concept_keys = expected_concept_keys & stored_concept_keys
        missing_concepts = sorted(expected_concept_keys - stored_concept_keys)
        total_concepts_stored += len(manifest_concept_keys)
        total_missing_concepts.extend([(disease.disease_name, *k) for k in missing_concepts])

        pre_existing = sorted(
            k for k in (stored_concept_keys - expected_concept_keys) if k[0] in CONCEPT_DOMAIN_MODEL_MAP
        )
        pre_existing_concepts_all.extend((disease.disease_name, *k) for k in pre_existing)

        stored_trend_rows = db.query(OntologyDiseasePrognosticIndicator).filter_by(disease_id=disease.id).all()
        stored_trend_keys = {row.indicator_name.strip().lower() for row in stored_trend_rows}
        missing_trend = sorted(expected_trend_keys - stored_trend_keys)
        total_trend_stored += len(expected_trend_keys & stored_trend_keys)
        total_missing_trend.extend([(disease.disease_name, k) for k in missing_trend])

        for a in expected_applicability:
            variant = _resolve_variant(db, disease.id, a["variant"], a.get("variant_dimension"))
            key = (a["concept_domain"], a["concept"].strip().lower())
            if key not in concept_id_by_key:
                continue
            exists = (
                db.query(OntologyConceptVariantApplicability)
                .filter_by(
                    concept_type=a["concept_domain"],
                    concept_id=concept_id_by_key[key],
                    variant_id=variant.id,
                    applicability_type=a["applicability_type"],
                )
                .one_or_none()
            )
            if exists is not None:
                total_applicability_stored += 1

        for link in expected_linkages:
            liver_concept = _resolve_concept(db, disease.id, link["chf_concept_domain"], link["chf_concept_name"])
            faf_concept = _resolve_concept(db, faf_disease.id, FAF_LINKAGE_TARGET_DOMAIN, link["faf_concept_name"])
            exists = (
                db.query(OntologyRelationship)
                .filter_by(
                    source_concept_type=link["chf_concept_domain"],
                    source_concept_id=liver_concept.id,
                    relationship_type=link["relationship_type"],
                    target_concept_type=FAF_LINKAGE_TARGET_DOMAIN,
                    target_concept_id=faf_concept.id,
                )
                .one_or_none()
            )
            if exists is not None:
                total_relationships_stored += 1

        # provenance coverage across only this disease's manifest-owned concepts/trend indicators
        for (concept_type, _name), concept_id in concept_id_by_key.items():
            if (concept_type, _name) not in manifest_concept_keys:
                continue
            rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=concept_id)
                .one_or_none()
            )
            provenance_checked += 1
            if rule is not None:
                match = PROVENANCE_PATTERN.search(rule.notes or "")
                if match and match.group("cst") in ALLOWED_CONTENT_SOURCE_TYPES \
                        and match.group("crs") in ALLOWED_CONTENT_REVIEW_STATUSES:
                    provenance_valid += 1

        for row in stored_trend_rows:
            if row.indicator_name.strip().lower() not in expected_trend_keys:
                continue
            rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type="PROGNOSTIC_INDICATOR", concept_id=row.id)
                .one_or_none()
            )
            provenance_checked += 1
            if rule is not None:
                match = PROVENANCE_PATTERN.search(rule.notes or "")
                if match and match.group("cst") in ALLOWED_CONTENT_SOURCE_TYPES \
                        and match.group("crs") in ALLOWED_CONTENT_REVIEW_STATUSES:
                    provenance_valid += 1

    return {
        "manifest_version": manifest.get("manifest_version"),
        "extends_diseases": EXTENDS_DISEASE_NAMES,
        "extends_functional_assessment_framework": FAF_DISEASE_NAME,
        "concepts": {
            "expected": len(expected_concept_keys) * len(diseases),
            "stored": total_concepts_stored,
            "missing": total_missing_concepts,
            "pre_existing_pr41_concepts_in_shared_domains": pre_existing_concepts_all,
        },
        "applicability": {
            "expected": len(expected_applicability) * len(diseases),
            "stored": total_applicability_stored,
        },
        "functional_assessment_relationships": {
            "expected": len(expected_linkages) * len(diseases),
            "stored": total_relationships_stored,
        },
        "recertification_trend_indicators": {
            "expected": len(expected_trend_keys) * len(diseases),
            "stored": total_trend_stored,
            "missing": total_missing_trend,
        },
        "provenance_coverage": {
            "checked": provenance_checked,
            "valid": provenance_valid,
        },
        "second_run_new_rows": second_run_new_rows,
    }


def main() -> None:
    db = SessionLocal()
    try:
        manifest = load_manifest()
        result_first = run(db, manifest)
        db.commit()

        result_second = run(db, manifest)
        db.commit()
        second_run_new_rows = (
            result_second["concepts_inserted_total"]
            + result_second["applicability_inserted"]
            + result_second["relationships_inserted"]
            + result_second["trend_indicators_inserted"]
            + result_second["evidence_rules_inserted"]
        )

        report = build_acceptance_report(db, manifest, second_run_new_rows)
        DEFAULT_ACCEPTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_ACCEPTANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("First run:", result_first)
        print("Second run (should be all zero):", result_second)
        print("Acceptance report written to:", DEFAULT_ACCEPTANCE_PATH)
    finally:
        db.close()


if __name__ == "__main__":
    main()
