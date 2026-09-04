# scripts/populate_ontology_ak_neuro_cardio.py
"""
Idempotent population script for A-K domains E (Treatment Limitations),
H (End-Stage Findings), J (Evidence Architecture), and K (Validation) for
the nine approved Neurologic + Cardiovascular diseases:

    Stroke, Hemiplegia, Hemiparesis, Contracture,
    Dementia Due To Alzheimer's Disease,
    Chronic Systolic Heart Failure, Coronary Artery Disease,
    Prior Myocardial Infarction, Atrial Fibrillation

Every disease and concept is resolved by stable name (never by hardcoded
UUID), through the existing System -> Family -> Disease hierarchy already
populated in the ontology_* tables. Re-running this script is always safe:

    - missing records are inserted
    - matching records (by existing unique constraints) are left unchanged
    - no records are ever deleted
    - no other body system, disease, or patient/staff table is touched

Run with: .\\.venv\\Scripts\\python.exe scripts\\populate_ontology_ak_neuro_cardio.py
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ontology.treatment_identity import (
    concept_identity_key,
    existing_rows_by_canonical_name,
    reconcile_category,
)

# Importing the full model package pre-registers most ORM classes, but
# app.models.poc (POCProblem etc.) is not re-exported from app/models/__init__.py,
# which otherwise leaves SQLAlchemy's lazy mapper configuration unable to
# resolve a cross-module relationship the first time any query touches the
# registry. Import it explicitly here (read-only import, no file changes)
# so this script can safely issue queries without depending on an unrelated
# fix to app/models/__init__.py.
import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseComplication,
    OntologyDiseaseDiagnosticTest,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFinding,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseLab,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseaseSymptom,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
)

APPROVED_DISEASE_NAMES = [
    "Stroke",
    "Hemiplegia",
    "Hemiparesis",
    "Contracture",
    "Dementia Due To Alzheimer's Disease",
    "Chronic Systolic Heart Failure",
    "Coronary Artery Disease",
    "Prior Myocardial Infarction",
    "Atrial Fibrillation",
]
IMPORTER_NAME = "populate_ontology_ak_neuro_cardio"

# Disease-level evidence source label, keyed by stable disease name (matches
# the disease-level ontology_evidence_rule.evidence_source values already
# on record for these nine diseases).
EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    "Stroke": "LCD Stroke and Coma; UpToDate stroke prognosis",
    "Hemiplegia": "General neurologic hospice decline guidance",
    "Hemiparesis": "General neurologic hospice decline guidance",
    "Contracture": "General neurologic hospice decline guidance",
    "Dementia Due To Alzheimer's Disease": "LCD Dementia (FAST staging criteria)",
    "Chronic Systolic Heart Failure": "LCD Heart Disease",
    "Coronary Artery Disease": "LCD Heart Disease",
    "Prior Myocardial Infarction": "LCD Heart Disease",
    "Atrial Fibrillation": "LCD Heart Disease",
}

IMAGING_TEST_NAMES = {"echocardiogram", "chest x-ray", "ct", "mri", "ct scan", "mri brain", "ct head"}

# ---------------------------------------------------------------------------
# E: TREATMENT LIMITATIONS
# (limitation_name, limitation_category, description, evidence_requirement, hospice_relevance)
# ---------------------------------------------------------------------------
TREATMENT_LIMITATIONS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    "Stroke": [
        ("Not a Candidate for Thrombectomy/tPA", "NOT_A_CANDIDATE",
         "Beyond treatment window or contraindicated for thrombolysis/thrombectomy.",
         "Documented time-of-onset and contraindication assessment.",
         "Supports non-reversible neurologic decline."),
        ("Declined Further Rehabilitation", "TREATMENT_DECLINED",
         "Patient/family declined continued intensive rehabilitation.",
         "Documentation of goals-of-care discussion.",
         "Reflects shift toward comfort-focused care."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort rather than restorative rehabilitation.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
    "Hemiplegia": [
        ("Not a Candidate for Further Rehabilitation", "NOT_A_CANDIDATE",
         "Plateaued functional status; no further gains expected from therapy.",
         "Therapy discharge summary/functional assessment.",
         "Supports irreversible functional decline."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort and contracture prevention only.",
         "Care plan/goals-of-care documentation.",
         "Reflects advanced functional decline."),
    ],
    "Hemiparesis": [
        ("Plateaued With Physical Therapy", "TREATMENT_FAILED",
         "No further functional improvement despite ongoing PT/OT.",
         "Serial functional assessments.",
         "Supports declining function trajectory."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort and maintenance only.",
         "Care plan/goals-of-care documentation.",
         "Reflects advanced functional decline."),
    ],
    "Contracture": [
        ("Not a Candidate for Surgical Release", "NOT_A_CANDIDATE",
         "Not a surgical candidate given overall functional/medical status.",
         "Physician/surgical consultation notes.",
         "Reflects advanced, irreversible disease."),
        ("Splinting/Range-of-Motion Therapy Discontinued", "TREATMENT_DISCONTINUED",
         "Active splinting/ROM therapy discontinued as goals shifted to comfort.",
         "Care plan documentation.",
         "Supports comfort-focused transition."),
    ],
    "Dementia Due To Alzheimer's Disease": [
        ("Not a Candidate for Disease-Modifying Therapy", "NOT_A_CANDIDATE",
         "Advanced stage precludes disease-modifying pharmacotherapy.",
         "Physician assessment/staging documentation.",
         "Supports advanced dementia staging."),
        ("Declined Artificial Nutrition/Hydration", "TREATMENT_DECLINED",
         "Patient/surrogate declined feeding tube or IV hydration.",
         "Advance directive/goals-of-care documentation.",
         "Recognized hospice eligibility support factor."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused dementia care.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
    "Chronic Systolic Heart Failure": [
        ("Optimally Treated on Diuretics/ACE/Beta-Blocker", "OPTIMALLY_TREATED",
         "Maximized guideline-directed medical therapy without symptom control.",
         "Medication administration record/physician documentation.",
         "LCD Heart Disease supporting factor."),
        ("Not a Candidate for Advanced Therapy (Transplant/LVAD)", "NOT_A_CANDIDATE",
         "Not a candidate for cardiac transplantation or mechanical circulatory support.",
         "Cardiology consultation notes.",
         "LCD Heart Disease supporting factor."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused heart failure management.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
    "Coronary Artery Disease": [
        ("Not a Candidate for Revascularization", "NOT_A_CANDIDATE",
         "Not a candidate for PCI or CABG.",
         "Cardiology consultation notes.",
         "LCD Heart Disease supporting factor."),
        ("Declined Cardiac Catheterization", "TREATMENT_DECLINED",
         "Patient declined further invasive cardiac workup.",
         "Documentation of goals-of-care discussion.",
         "Supports comfort-focused transition."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused management of ischemic symptoms.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
    "Prior Myocardial Infarction": [
        ("Not a Candidate for Further Cardiac Intervention", "NOT_A_CANDIDATE",
         "Not a candidate for further revascularization or device therapy.",
         "Cardiology consultation notes.",
         "LCD Heart Disease supporting factor."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused management.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
    "Atrial Fibrillation": [
        ("Not a Candidate for Ablation", "NOT_A_CANDIDATE",
         "Not a candidate for catheter/surgical ablation.",
         "Cardiology consultation notes.",
         "Reflects advanced overall cardiac status."),
        ("Anticoagulation Discontinued (Bleeding/Fall Risk)", "TREATMENT_DISCONTINUED",
         "Anticoagulation discontinued due to bleeding or fall risk in advanced disease.",
         "Physician documentation of risk/benefit reassessment.",
         "Common comfort-focused reassessment in advanced illness."),
        ("Comfort-Focused Care", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused rhythm/symptom management.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
}

# ---------------------------------------------------------------------------
# H: END-STAGE FINDINGS
# (finding_name, description, evidence_requirement, clinical_significance, hospice_relevance)
# ---------------------------------------------------------------------------
END_STAGE_FINDINGS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    "Stroke": [
        ("Persistent Vegetative State",
         "No purposeful response to stimuli following stroke.",
         "Serial neurologic assessment.",
         "Represents maximal neurologic devastation.",
         "Strong hospice eligibility support factor."),
        ("Recurrent Stroke Despite Secondary Prevention",
         "New stroke event despite optimal antiplatelet/anticoagulant/risk-factor management.",
         "Imaging + clinical assessment of new deficit.",
         "Reflects treatment-refractory cerebrovascular disease.",
         "Supports disease progression."),
    ],
    "Hemiplegia": [
        ("Complete Immobility",
         "Total loss of voluntary movement on the affected side with no functional use.",
         "PT/OT functional assessment.",
         "Represents maximal motor deficit.",
         "Supports profound functional decline."),
        ("Global Contracture Development",
         "Multi-joint contractures developing despite positioning/ROM interventions.",
         "Physical exam/ROM measurement.",
         "Reflects irreversible musculoskeletal decline.",
         "Supports advanced immobility."),
    ],
    "Hemiparesis": [
        ("Progression to Complete Hemiplegia",
         "Partial weakness progresses to total paralysis of the affected side.",
         "Serial motor strength assessment.",
         "Represents disease progression.",
         "Supports declining neurologic function."),
    ],
    "Contracture": [
        ("Multi-Joint Fixed Contractures",
         "Fixed, non-reducible contractures across multiple joints unresponsive to therapy.",
         "Physical exam/goniometric measurement.",
         "Represents irreversible end-stage musculoskeletal change.",
         "Supports profound functional decline and skin breakdown risk."),
    ],
    "Dementia Due To Alzheimer's Disease": [
        ("FAST Stage 7 (Severe Dementia)",
         "Functional Assessment Staging Tool stage 7 -- inability to ambulate, sit up, smile, or hold head up.",
         "FAST staging assessment.",
         "Standard hospice-eligibility-supportive dementia staging marker.",
         "Directly referenced in dementia hospice guidance."),
        ("Loss of Purposeful Speech",
         "Vocabulary limited to a few intelligible words or no intelligible speech.",
         "Speech/language assessment.",
         "Reflects advanced cortical decline.",
         "Supports FAST 7 staging."),
        ("Total Functional Dependence",
         "Complete dependence for all ADLs including feeding, toileting, and mobility.",
         "ADL/functional assessment.",
         "Represents end-stage functional status.",
         "Core hospice eligibility support factor."),
    ],
    "Chronic Systolic Heart Failure": [
        ("Refractory NYHA Class IV Symptoms at Rest",
         "Dyspnea/fatigue at rest despite maximal guideline-directed medical therapy.",
         "Clinical assessment + medication record.",
         "Defines end-stage heart failure per LCD Heart Disease.",
         "Primary hospice eligibility support marker."),
        ("Cardiorenal Syndrome With Diuretic Resistance",
         "Worsening renal function limiting diuretic titration despite persistent congestion.",
         "Serial creatinine/BUN + diuretic response.",
         "Reflects end-stage cardiorenal decline.",
         "Supports refractory disease state."),
    ],
    "Coronary Artery Disease": [
        ("Refractory Angina Despite Maximal Anti-Ischemic Therapy",
         "Persistent angina despite maximal medical therapy and non-candidacy for revascularization.",
         "Clinical assessment + medication record.",
         "Defines end-stage ischemic heart disease.",
         "LCD Heart Disease supporting factor."),
    ],
    "Prior Myocardial Infarction": [
        ("Progressive Ischemic Cardiomyopathy With Severely Reduced EF",
         "Serial decline in EF to severely reduced range post-infarct.",
         "Serial echocardiograms.",
         "Represents end-stage post-infarct ventricular dysfunction.",
         "Supports cardiac hospice eligibility."),
    ],
    "Atrial Fibrillation": [
        ("Refractory Arrhythmia With Hemodynamic Compromise",
         "Persistent rapid/irregular rhythm causing hemodynamic instability despite optimal rate/rhythm control.",
         "Clinical assessment + EKG/vitals.",
         "Reflects end-stage arrhythmia burden.",
         "Supports overall cardiac decline."),
    ],
}

# Domain tables/models included in J (per-concept evidence rule) coverage,
# and in K's EVIDENCE_COVERAGE / SOURCE_PROVENANCE / DOMAIN_COMPLETENESS checks.
# (model_class, concept_type label, name attribute, required-nonempty-for-completeness)
CONCEPT_DOMAINS = [
    (OntologyDiseaseSymptom, "SYMPTOM", "symptom_name", True),
    (OntologyDiseaseFinding, "FINDING", "finding_name", False),
    (OntologyDiseaseLab, "LAB", "lab_name", False),
    (OntologyDiseaseDiagnosticTest, "DIAGNOSTIC_TEST", "test_name", False),
    (OntologyDiseaseComplication, "COMPLICATION", "complication_name", True),
    (OntologyDiseaseFunctionalImpact, "FUNCTIONAL_IMPACT", "impact_name", True),
    (OntologyDiseaseNutritionalImpact, "NUTRITIONAL_IMPACT", "impact_name", True),
    (OntologyDiseaseHospiceEligibilitySupport, "HOSPICE_ELIGIBILITY_SUPPORT", "indicator_name", True),
    (OntologyDiseaseTreatmentLimitation, "TREATMENT_LIMITATION", "limitation_name", True),
    (OntologyDiseaseEndStageFinding, "END_STAGE_FINDING", "finding_name", True),
]

REQUIRED_VALIDATION_TYPES = [
    "DUPLICATE",
    "ORPHAN",
    "HIERARCHY",
    "DOMAIN_COMPLETENESS",
    "EVIDENCE_COVERAGE",
    "RELATIONSHIP_INTEGRITY",
    "SOURCE_PROVENANCE",
]


def _active_rows(db: Session, model_cls, disease_id) -> List:
    """Return rows for this disease, filtered to active=True only when the
    model actually has an `active` column (several of the original A-K
    concept tables -- symptom, finding, lab, diagnostic_test, complication,
    functional_impact, nutritional_impact, hospice_eligibility_support --
    predate the active-status convention and have no such column, so every
    row on those tables is implicitly active)."""
    query = db.query(model_cls).filter_by(disease_id=disease_id)
    if hasattr(model_cls, "active"):
        query = query.filter(model_cls.active.is_(True))
    return query.all()


def _resolve_diseases(db: Session, names: List[str]) -> Dict[str, OntologyDisease]:
    diseases = (
        db.query(OntologyDisease)
        .filter(OntologyDisease.disease_name.in_(names))
        .all()
    )
    by_name = {d.disease_name: d for d in diseases}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise RuntimeError(
            f"Cannot populate A-K domains: disease(s) not found by name: {missing}. "
            "Ontology base content for these diseases must already exist."
        )
    return by_name


def populate_treatment_limitations(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    inserted = 0
    for disease_name, rows in TREATMENT_LIMITATIONS.items():
        disease = diseases[disease_name]
        existing_rows = existing_rows_by_canonical_name(
            db.query(OntologyDiseaseTreatmentLimitation).filter_by(disease_id=disease.id).all(),
            domain="TREATMENT_LIMITATION",
            table_name=OntologyDiseaseTreatmentLimitation.__tablename__,
            disease_id=disease.id,
            importer_name=IMPORTER_NAME,
            name_attr="limitation_name",
            category_attr="limitation_category",
        )
        for name, category, desc, evidence_req, hospice_rel in rows:
            normalized_name = concept_identity_key("TREATMENT_LIMITATION", name)
            existing = existing_rows.get(normalized_name)
            if existing is not None:
                result = reconcile_category(
                    domain="TREATMENT_LIMITATION",
                    disease_id=existing.disease_id,
                    normalized_name=existing.normalized_name,
                    existing_row_id=existing.id,
                    existing_display_name=existing.limitation_name,
                    existing_category=existing.limitation_category,
                    incoming_display_name=name,
                    incoming_category=category,
                    importer_name=IMPORTER_NAME,
                )
                if result.changed:
                    existing.limitation_category = result.category
                continue
            row = OntologyDiseaseTreatmentLimitation(
                id=uuid.uuid4(),
                disease_id=disease.id,
                limitation_name=name,
                normalized_name=normalized_name,
                limitation_category=category,
                description=desc,
                evidence_requirement=evidence_req,
                hospice_relevance=hospice_rel,
            )
            db.add(row)
            db.flush()
            existing_rows[normalized_name] = row
            inserted += 1
    db.flush()
    return inserted


def populate_end_stage_findings(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    inserted = 0
    for disease_name, rows in END_STAGE_FINDINGS.items():
        disease = diseases[disease_name]
        for name, desc, evidence_req, clinical_sig, hospice_rel in rows:
            existing = (
                db.query(OntologyDiseaseEndStageFinding)
                .filter_by(disease_id=disease.id, finding_name=name)
                .one_or_none()
            )
            if existing is not None:
                continue
            db.add(
                OntologyDiseaseEndStageFinding(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    finding_name=name,
                    description=desc,
                    evidence_requirement=evidence_req,
                    clinical_significance=clinical_sig,
                    hospice_relevance=hospice_rel,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_evidence_rules(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    """J: one active evidence rule per active concept row, for every concept
    domain in CONCEPT_DOMAINS, for the nine approved diseases only."""
    inserted = 0
    disease_ids = {d.id for d in diseases.values()}
    for model_cls, concept_type, name_attr, _required in CONCEPT_DOMAINS:
        rows = (
            db.query(model_cls)
            .filter(model_cls.disease_id.in_(disease_ids))
        )
        if hasattr(model_cls, "active"):
            rows = rows.filter(model_cls.active.is_(True))
        rows = rows.all()
        for row in rows:
            existing = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if existing is not None:
                continue
            disease_name = next(
                (name for name, d in diseases.items() if d.id == row.disease_id), None
            )
            source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(
                disease_name, "General hospice decline guidance"
            )
            evidence_type = concept_type
            if concept_type == "DIAGNOSTIC_TEST":
                concept_name = (getattr(row, name_attr) or "").strip().lower()
                evidence_type = "IMAGING" if concept_name in IMAGING_TEST_NAMES else "DIAGNOSTIC_TEST"
            concept_name_display = getattr(row, name_attr)
            db.add(
                OntologyEvidenceRule(
                    id=uuid.uuid4(),
                    concept_type=concept_type,
                    concept_id=row.id,
                    evidence_source=source_label,
                    evidence_type=evidence_type,
                    confidence="moderate",
                    review_trigger="RN_REVIEW",
                    patient_fact_requires_evidence=True,
                    notes=(
                        f"Evidence rule for {concept_type} concept '{concept_name_display}'; "
                        "requires patient-record evidence before treated as documented."
                    ),
                )
            )
            inserted += 1
    db.flush()
    return inserted


def _run_validation_checks(db: Session, disease: OntologyDisease) -> List[Tuple[str, str, str, int, int]]:
    """Compute the seven K validation checks for one disease. Returns
    (validation_type, status, details, error_count, warning_count) tuples."""
    checks: List[Tuple[str, str, str, int, int]] = []
    disease_id = disease.id

    # 1. DUPLICATE
    dup_errors = 0
    dup_detail: List[str] = []
    for model_cls, _ct, name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        seen: Dict[str, int] = {}
        for row in rows:
            key = (getattr(row, name_attr) or "").strip().lower()
            seen[key] = seen.get(key, 0) + 1
        dups = {k: v for k, v in seen.items() if v > 1}
        if dups:
            dup_errors += len(dups)
            dup_detail.append(f"{model_cls.__tablename__}: {dups}")
    status = "FAIL" if dup_errors else "PASS"
    checks.append((
        "DUPLICATE", status,
        "; ".join(dup_detail) or "No duplicate concept names found in any domain table for this disease.",
        dup_errors, 0,
    ))

    # 2. ORPHAN
    orphan_errors = 0
    orphan_detail: List[str] = []
    if disease.disease_family is None or disease.disease_family.body_system is None:
        orphan_errors += 1
        orphan_detail.append("Disease has no resolvable disease_family/body_system chain.")
    for model_cls, _ct, _name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        for row in rows:
            if row.disease is None:
                orphan_errors += 1
                orphan_detail.append(f"{model_cls.__tablename__}: orphaned row {row.id}")
    status = "FAIL" if orphan_errors else "PASS"
    checks.append((
        "ORPHAN", status,
        "; ".join(orphan_detail) or "No orphaned domain rows; disease resolves to family and body system.",
        orphan_errors, 0,
    ))

    # 3. HIERARCHY
    hier_errors = 0
    hier_detail: List[str] = []
    family = disease.disease_family
    system = family.body_system if family else None
    if not (disease.disease_name and family and family.family_name and system and system.system_name):
        hier_errors += 1
        hier_detail.append("Hierarchy row incomplete.")
    elif not (disease.active and family.active and system.active):
        hier_errors += 1
        hier_detail.append("Hierarchy row inactive at some level.")
    status = "FAIL" if hier_errors else "PASS"
    detail = "; ".join(hier_detail) or (
        f"3-tier hierarchy intact: {disease.disease_name} -> {family.family_name} -> "
        f"{system.system_name} (all active)."
    )
    checks.append(("HIERARCHY", status, detail, hier_errors, 0))

    # 4. DOMAIN_COMPLETENESS
    completeness_warnings = 0
    completeness_detail: List[str] = []
    for model_cls, _ct, _name_attr, required in CONCEPT_DOMAINS:
        if not required:
            continue
        cnt = db.query(model_cls).filter_by(disease_id=disease_id).count()
        if cnt == 0:
            completeness_warnings += 1
            completeness_detail.append(f"{model_cls.__tablename__}: 0 rows")
    status = "WARNING" if completeness_warnings else "PASS"
    checks.append((
        "DOMAIN_COMPLETENESS", status,
        "; ".join(completeness_detail) or "All required A-K domains have at least one row for this disease.",
        0, completeness_warnings,
    ))

    # 5. EVIDENCE_COVERAGE
    total_concepts = 0
    covered = 0
    for model_cls, concept_type, _name_attr, _req in CONCEPT_DOMAINS:
        rows = _active_rows(db, model_cls, disease_id)
        total_concepts += len(rows)
        for row in rows:
            has_rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if has_rule is not None:
                covered += 1
    uncovered = total_concepts - covered
    pct = (covered / total_concepts * 100.0) if total_concepts else 0.0
    status = "PASS" if uncovered == 0 else "WARNING"
    checks.append((
        "EVIDENCE_COVERAGE", status,
        f"{covered}/{total_concepts} concept rows have a disease-specific evidence rule ({pct:.1f}%).",
        0, uncovered,
    ))

    # 6. RELATIONSHIP_INTEGRITY
    from app.models.ontology_disease_blueprint import OntologyRelationship

    rel_rows = (
        db.query(OntologyRelationship)
        .filter(
            (OntologyRelationship.source_concept_id == disease_id)
            | (OntologyRelationship.target_concept_id == disease_id)
        )
        .all()
    )
    rel_errors = 0
    rel_detail: List[str] = []
    for rr in rel_rows:
        if rr.source_concept_type == "DISEASE":
            if db.query(OntologyDisease).filter_by(id=rr.source_concept_id).one_or_none() is None:
                rel_errors += 1
                rel_detail.append(f"dangling source {rr.source_concept_id}")
        if rr.target_concept_type == "DISEASE":
            if db.query(OntologyDisease).filter_by(id=rr.target_concept_id).one_or_none() is None:
                rel_errors += 1
                rel_detail.append(f"dangling target {rr.target_concept_id}")
    status = "FAIL" if rel_errors else "PASS"
    checks.append((
        "RELATIONSHIP_INTEGRITY", status,
        "; ".join(rel_detail) or f"{len(rel_rows)} relationship row(s) touching this disease resolve correctly.",
        rel_errors, 0,
    ))

    # 7. SOURCE_PROVENANCE
    prov_missing = 0
    for model_cls, concept_type, _name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        for row in rows:
            rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if rule is not None and not rule.evidence_source:
                prov_missing += 1
    disease_rule = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type="DISEASE", concept_id=disease_id)
        .one_or_none()
    )
    if disease_rule is not None and not disease_rule.evidence_source:
        prov_missing += 1
    status = "FAIL" if prov_missing else "PASS"
    checks.append((
        "SOURCE_PROVENANCE", status,
        "All evidence rules for this disease carry a non-null evidence_source."
        if not prov_missing else f"{prov_missing} evidence rule(s) missing evidence_source.",
        prov_missing, 0,
    ))

    return checks


def populate_validation_results(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    inserted = 0
    for disease in diseases.values():
        checks = _run_validation_checks(db, disease)
        for validation_type, status, details, error_count, warning_count in checks:
            existing = (
                db.query(OntologyDiseaseValidationResult)
                .filter_by(disease_id=disease.id, validation_type=validation_type)
                .one_or_none()
            )
            if existing is not None:
                existing.validation_status = status
                existing.details = details
                existing.error_count = error_count
                existing.warning_count = warning_count
                existing.validator_version = "v1"
                continue
            db.add(
                OntologyDiseaseValidationResult(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    validation_type=validation_type,
                    validation_status=status,
                    details=details,
                    error_count=error_count,
                    warning_count=warning_count,
                    validator_version="v1",
                )
            )
            inserted += 1
    db.flush()
    return inserted


def run(db: Session) -> Dict[str, int]:
    """Run the full E/H/J/K population against the given session. Does not
    commit -- the caller controls the transaction boundary. Safe to call
    repeatedly; returns the count of NEW rows inserted in this call for
    each domain (0 on a fully-idempotent re-run)."""
    diseases = _resolve_diseases(db, APPROVED_DISEASE_NAMES)
    e_count = populate_treatment_limitations(db, diseases)
    h_count = populate_end_stage_findings(db, diseases)
    j_count = populate_evidence_rules(db, diseases)
    k_count = populate_validation_results(db, diseases)
    return {
        "treatment_limitations_inserted": e_count,
        "end_stage_findings_inserted": h_count,
        "evidence_rules_inserted": j_count,
        "validation_results_inserted": k_count,
    }


def main() -> None:
    db = SessionLocal()
    try:
        counts = run(db)
        db.commit()
        for label, count in counts.items():
            print(f"{label}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
