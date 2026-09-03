# app/services/recertification_evidence_synthesis.py
"""
Recertification Evidence Summary -- READ-ONLY runtime patient-level
synthesis (PR #59 production-grade extension).

This module adds exactly one public entry point:

    build_recertification_evidence_summary(...)

It reads existing patient records ONLY (SELECT statements via SQLAlchemy
`Query`/`session.execute(select(...))`) and produces a
RECERTIFICATION_EVIDENCE_SUMMARY containing all 21 committed sections
defined by scripts/import_recertification_reasoning_framework_v1.py's
manifest. It reuses that module's `compare_scale`, `compare_numeric`, and
`select_regulatory_context` pure functions verbatim -- it does not
reimplement or fork any comparison logic.

HARD BOUNDARIES (enforced by construction, not by convention):
  - This module NEVER calls db.add(...), db.flush(), db.commit(),
    Session.merge(...), or any ORM mutation method. Every access is a
    read (`db.query(...)` / `.filter(...)` / `.all()` / `.one_or_none()`
    / `.first()`). Grep this file: there is no `.add(`, no `.flush(`, no
    `.commit(`, no `.delete(`, no `.merge(` anywhere below this docstring.
  - This module creates NO patient-fact rows, NO eligibility output, NO
    terminal-status output, NO prognosis output, NO life-expectancy
    prediction, NO certification/recertification/discharge recommendation
    of any kind. It returns a plain Python dict; nothing is persisted.
  - It never infers a value that isn't documented. Missing evidence is
    always reported as one of the required missing/indeterminate labels,
    never silently defaulted or guessed.
  - It never merges CMS_MEDICARE_SIX_MONTH and CALIFORNIA_CDPH_STATE
    regulatory contexts -- select_regulatory_context() is called exactly
    once per invocation with the caller's single explicit choice.

DATA SOURCES (grounded in the real, already-migrated schema -- verified
directly against app/models/*.py, not assumed):
  - app.models.benefit_period.BenefitPeriod: current/prior period metadata
    (period_number, start_date, end_date, election_date).
  - app.models.patient_diagnosis.PatientDiagnosis: primary/secondary/
    comorbidity diagnoses, windowed by effective_benefit_period_number /
    resolved_benefit_period_number.
  - app.models.f2f_encounter.F2FEncounter: the richest per-benefit-period
    structured functional/nutritional/utilization snapshot in this schema
    (pps_score_previous/current, kps_score, ecog_score_previous/current,
    fast_score, nyha_class, adl_dependency_level/count, weight_loss_lbs,
    oral_intake_decline, dysphagia, hospitalizations_30d,
    oxygen_lpm_previous/current, clinical_decline_summary).
  - app.models.rn_recert_assessment.RNRecertAssessment: a second,
    independent structured source for the same benefit period (pps_score,
    kps_score, fast_stage, nyha_class, adl_level, adl_dependency_count) --
    used to detect same-date cross-source conflicts (Blocker: Conflicting
    Evidence, Scenario 6).
  - app.models.certification.Certification: physician_narrative /
    clinical_decline_indicators text for the benefit period, referenced
    (never rewritten) as a documentation source.

NO DEDICATED TABLE EXISTS in this schema version for: discrete symptom
tracking, discrete laboratory results, discrete complication/infection
tracking, or ED-visit tracking (only F2FEncounter.hospitalizations_30d,
an aggregate count, exists for utilization). Per the review's own
instruction ("if evidence is unavailable, return the applicable missing
or indeterminate label"), sections 8 (Symptoms and Clinical Signs), 9
(Laboratory and Objective-Finding), and 10 (Complications and Infections)
are honestly reported as structurally EMPTY with
missing_evidence_code="NO_STRUCTURED_SOURCE_AVAILABLE_IN_SCHEMA" rather
than fabricated from free-text notes.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.f2f_encounter import F2FEncounter
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.rn_recert_assessment import RNRecertAssessment

from scripts.import_recertification_reasoning_framework_v1 import (
    compare_numeric,
    compare_scale,
    select_regulatory_context,
)

FRAMEWORK_VERSION = 1

ALLOWED_REGULATORY_CONTEXTS = {"CMS_MEDICARE_SIX_MONTH", "CALIFORNIA_CDPH_STATE"}

REQUIRED_SECTION_TITLES = [
    "Review Context", "Prior Benefit-Period Baseline", "Current Benefit-Period Evidence",
    "Functional Assessment Comparison", "ADL and Care-Dependence Comparison",
    "Nutritional and Hydration Comparison", "Disease-Specific Evidence Comparison",
    "Symptoms and Clinical Signs Comparison", "Laboratory and Objective-Finding Comparison",
    "Complications and Infections Comparison", "Hospitalization and Utilization Comparison",
    "Treatment and Intervention Context", "Co-Morbidity Contribution",
    "Stability or Improvement Review", "Potentially Reversible Factors",
    "Conflicting Evidence", "Missing Evidence", "Documentation Gaps",
    "Physician Review Questions", "Suggested Individualized Narrative Elements",
    "Source and Audit Trace",
]

# A small, fixed, deterministic vocabulary of documented reversible-factor
# phrases. This is a literal substring match against clinician-authored
# text -- never an AI clinical judgment, never a guess -- and always
# quotes the exact matched source text back to the reviewer.
_REVERSIBLE_FACTOR_PHRASES = [
    "diuresis", "medication side effect", "dehydration", "constipation",
    "urinary tract infection treated", "infection treated", "depression",
    "medication adjustment", "overmedication", "polypharmacy",
]


class RecertificationSynthesisError(ValueError):
    """Raised for caller input errors (unknown regulatory_context, benefit
    period not found for this patient, etc.). Never raised for missing
    clinical evidence -- that is always reported as a label, not an
    exception."""


def _utc_date(dt: Optional[datetime]) -> Optional[date]:
    """Extracts the calendar date from a (possibly timezone-aware)
    datetime, normalized to UTC first. Calling `.date()` directly on a
    tz-aware datetime is server/session-timezone-dependent (a UTC midnight
    timestamp can render as the previous calendar day in a non-UTC
    session/connection timezone) and would make same-date conflict
    detection silently miss real conflicts depending on the DB connection's
    timezone setting. Always normalize to UTC first for determinism."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.date()


def _evidence_item(
    *,
    patient_id: UUID,
    hospice_episode_id: UUID,
    benefit_period_id: Optional[UUID],
    period_role: str,
    disease_id: Optional[str],
    disease_name: Optional[str],
    concept_domain: str,
    concept_name: str,
    value: Any,
    unit: Optional[str],
    assessment_date: Optional[date],
    documentation_date: Optional[datetime],
    source_record_type: str,
    source_record_id: Optional[UUID],
    author_or_assessor_id: Optional[UUID],
    classification_rule_id: str,
    generated_at: datetime,
) -> Dict[str, Any]:
    """Builds one Source and Audit Trace evidence item with every field
    required by the review's Source Traceability section. source_document_id
    is always None in this schema version (no document-linkage column
    exists on the source tables read here) -- reported honestly, not
    fabricated."""
    return {
        "evidence_id": f"{source_record_type}:{source_record_id}:{concept_name}",
        "patient_id": str(patient_id),
        "hospice_episode_id": str(hospice_episode_id),
        "benefit_period_id": str(benefit_period_id) if benefit_period_id else None,
        "period_role": period_role,
        "disease_id": disease_id,
        "disease_name": disease_name,
        "concept_domain": concept_domain,
        "concept_name": concept_name,
        "exact_documented_value": value,
        "unit": unit,
        "assessment_date": assessment_date.isoformat() if assessment_date else None,
        "documentation_date": documentation_date.isoformat() if documentation_date else None,
        "source_record_type": source_record_type,
        "source_record_id": str(source_record_id) if source_record_id else None,
        "source_document_id": None,
        "author_or_assessor_id": str(author_or_assessor_id) if author_or_assessor_id else None,
        "classification_rule_id": classification_rule_id,
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at.isoformat(),
        "read_only": True,
    }


def _get_benefit_period(db: Session, patient_id: UUID, benefit_period_id: Optional[UUID]) -> Optional[BenefitPeriod]:
    if benefit_period_id is None:
        return None
    bp = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.id == benefit_period_id, BenefitPeriod.patient_id == patient_id)
        .one_or_none()
    )
    if bp is None:
        raise RecertificationSynthesisError(
            f"benefit_period_id {benefit_period_id} does not exist for patient_id {patient_id}."
        )
    return bp


def _get_f2f(db: Session, patient_id: UUID, bp: Optional[BenefitPeriod]) -> Optional[F2FEncounter]:
    if bp is None:
        return None
    return (
        db.query(F2FEncounter)
        .filter(F2FEncounter.patient_id == patient_id, F2FEncounter.benefit_period_id == bp.id)
        .order_by(F2FEncounter.encounter_date.desc())
        .first()
    )


def _get_rn_recert(db: Session, patient_id: UUID, bp: Optional[BenefitPeriod]) -> Optional[RNRecertAssessment]:
    if bp is None:
        return None
    return (
        db.query(RNRecertAssessment)
        .filter(RNRecertAssessment.patient_id == patient_id, RNRecertAssessment.benefit_period_id == bp.id)
        .order_by(RNRecertAssessment.finalized_at.desc().nullslast(), RNRecertAssessment.created_at.desc())
        .first()
    )


def _active_diagnoses(db: Session, patient_id: UUID, bp: Optional[BenefitPeriod], diagnosis_types: List[str]) -> List[PatientDiagnosis]:
    if bp is None or bp.period_number is None:
        return []
    return (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.diagnosis_type.in_(diagnosis_types),
        )
        .filter(
            (PatientDiagnosis.effective_benefit_period_number.is_(None))
            | (PatientDiagnosis.effective_benefit_period_number <= bp.period_number)
        )
        .filter(
            (PatientDiagnosis.resolved_benefit_period_number.is_(None))
            | (PatientDiagnosis.resolved_benefit_period_number >= bp.period_number)
        )
        .order_by(PatientDiagnosis.diagnosis_type.asc())
        .all()
    )


def _format_diagnosis(dx: PatientDiagnosis) -> Dict[str, Any]:
    return {
        "id": str(dx.id),
        "icd10_code": dx.icd10_code,
        "display_name": dx.display_name,
        "diagnosis_type": str(dx.diagnosis_type.value if hasattr(dx.diagnosis_type, "value") else dx.diagnosis_type),
        "is_terminal": dx.is_terminal,
    }


def _diagnosis_pool_text(diagnoses: List[PatientDiagnosis]) -> str:
    return " ".join(f"{d.icd10_code} {d.display_name} {d.diagnosis_description}" for d in diagnoses).lower()


def _scale_applicability(diagnosis_text: str) -> Dict[str, bool]:
    """Deterministic, substring-based (never AI-inferred) applicability
    rule for disease-restricted functional scales. ECOG applies only when
    an active diagnosis documents malignancy; FAST only when an active
    diagnosis documents dementia; NYHA only when an active diagnosis
    documents CHF. PPS and KPS are always applicable."""
    return {
        "ECOG": bool(re.search(r"\bcancer\b|\bmalignan|\bneoplasm\b|\bc[0-9]{2}\b", diagnosis_text)),
        "FAST": bool(re.search(r"\bdementia\b|\balzheimer|\bg30\b|\bf03\b", diagnosis_text)),
        "NYHA": bool(re.search(r"\bheart failure\b|\bchf\b|\bi50\b", diagnosis_text)),
    }


def _classify_functional_scale(
    scale_type: str,
    prior_value: Any,
    prior_date: Optional[date],
    current_value: Any,
    current_date: Optional[date],
) -> str:
    return compare_scale(
        scale_type, prior_value, prior_date.isoformat() if prior_date else None,
        scale_type, current_value, current_date.isoformat() if current_date else None,
    )


def build_recertification_evidence_summary(
    db: Session,
    *,
    patient_id: UUID,
    hospice_episode_id: UUID,
    current_benefit_period_id: UUID,
    prior_benefit_period_id: Optional[UUID],
    regulatory_context: str,
    generated_at: datetime,
) -> Dict[str, Any]:
    """READ-ONLY runtime synthesis. Raises RecertificationSynthesisError
    for caller input errors (unknown regulatory_context, a benefit_period_id
    that does not belong to patient_id). Never raises for missing clinical
    evidence -- every section is always present, and empty sections carry
    a status/reason/missing_evidence_code per the review's own
    accommodation for undocumented evidence."""
    if regulatory_context not in ALLOWED_REGULATORY_CONTEXTS:
        raise RecertificationSynthesisError(
            f"regulatory_context must be one of {sorted(ALLOWED_REGULATORY_CONTEXTS)}, got {regulatory_context!r}."
        )

    from scripts.import_recertification_reasoning_framework_v1 import load_manifest
    manifest = load_manifest()
    regulatory_context_definition = select_regulatory_context(manifest, regulatory_context)

    current_bp = _get_benefit_period(db, patient_id, current_benefit_period_id)
    if current_bp is None:
        raise RecertificationSynthesisError("current_benefit_period_id is required and must exist for this patient.")
    prior_bp = _get_benefit_period(db, patient_id, prior_benefit_period_id) if prior_benefit_period_id else None

    current_f2f = _get_f2f(db, patient_id, current_bp)
    prior_f2f = _get_f2f(db, patient_id, prior_bp)
    current_rn = _get_rn_recert(db, patient_id, current_bp)
    prior_rn = _get_rn_recert(db, patient_id, prior_bp)

    current_dx_primary_secondary = _active_diagnoses(db, patient_id, current_bp, ["PRIMARY", "SECONDARY"])
    prior_dx_primary_secondary = _active_diagnoses(db, patient_id, prior_bp, ["PRIMARY", "SECONDARY"])
    current_comorbidities = _active_diagnoses(db, patient_id, current_bp, ["COMORBIDITY"])

    scale_applicability = _scale_applicability(_diagnosis_pool_text(current_dx_primary_secondary + current_comorbidities))

    evidence_items: List[Dict[str, Any]] = []
    missing_evidence: List[Dict[str, Any]] = []
    documentation_gaps: List[Dict[str, Any]] = []
    physician_review_questions: List[str] = []
    conflicts: List[Dict[str, Any]] = []

    def _record_evidence(**kwargs) -> Dict[str, Any]:
        item = _evidence_item(
            patient_id=patient_id, hospice_episode_id=hospice_episode_id, generated_at=generated_at, **kwargs
        )
        evidence_items.append(item)
        return item

    # -----------------------------------------------------------------
    # Section 1: Review Context
    # -----------------------------------------------------------------
    section_1 = {
        "section_number": 1, "section_title": "Review Context", "status": "POPULATED", "reason": None,
        "missing_evidence_code": None,
        "content": {
            "patient_id": str(patient_id),
            "hospice_episode_id": str(hospice_episode_id),
            "current_benefit_period_id": str(current_benefit_period_id),
            "prior_benefit_period_id": str(prior_benefit_period_id) if prior_benefit_period_id else None,
            "regulatory_context": regulatory_context,
            "regulatory_context_definition": regulatory_context_definition,
            "framework_version": FRAMEWORK_VERSION,
            "generated_at": generated_at.isoformat(),
        },
    }

    def _period_snapshot(bp: Optional[BenefitPeriod], f2f: Optional[F2FEncounter], rn: Optional[RNRecertAssessment], role: str) -> Dict[str, Any]:
        if bp is None:
            return {"status": "EMPTY", "reason": "No benefit period supplied.", "missing_evidence_code": "PRIOR_BENEFIT_PERIOD_NOT_APPLICABLE"}
        pps = f2f.pps_score_current if role == "CURRENT_BENEFIT_PERIOD" and f2f else (f2f.pps_score_previous if f2f else None)
        pps_date = f2f.encounter_date if f2f else None
        kps = f2f.kps_score if f2f else (rn.kps_score if rn else None)
        content = {
            "benefit_period_id": str(bp.id),
            "period_number": bp.period_number,
            "benefit_type": str(bp.benefit_type),
            "start_date": bp.start_date.isoformat() if bp.start_date else None,
            "end_date": bp.end_date.isoformat() if bp.end_date else None,
            "pps_score": pps if pps is not None else (rn.pps_score if rn else None),
            "kps_score": kps,
            "assessment_date": pps_date.isoformat() if pps_date else (_utc_date(rn.finalized_at).isoformat() if rn and rn.finalized_at else None),
            "diagnoses": [_format_diagnosis(d) for d in (current_dx_primary_secondary if role == "CURRENT_BENEFIT_PERIOD" else prior_dx_primary_secondary)],
        }
        if f2f is not None:
            _record_evidence(
                benefit_period_id=bp.id, period_role=role, disease_id=None, disease_name=None,
                concept_domain="FUNCTIONAL_SCALE", concept_name="PPS",
                value=content["pps_score"], unit=None, assessment_date=f2f.encounter_date,
                documentation_date=f2f.finalized_at, source_record_type="F2FEncounter", source_record_id=f2f.id,
                author_or_assessor_id=f2f.performed_by_user_id, classification_rule_id="PERIOD_SNAPSHOT_V1",
            )
        return {"status": "POPULATED", "reason": None, "missing_evidence_code": None, "content": content}

    section_2 = {
        "section_number": 2, "section_title": "Prior Benefit-Period Baseline",
        **_period_snapshot(prior_bp, prior_f2f, prior_rn, "PRIOR_BENEFIT_PERIOD"),
    }
    if prior_bp is None:
        missing_evidence.append({"section": 2, "code": "PRIOR_BENEFIT_PERIOD_NOT_APPLICABLE", "detail": "No immediately preceding benefit period exists for this patient."})

    section_3 = {
        "section_number": 3, "section_title": "Current Benefit-Period Evidence",
        **_period_snapshot(current_bp, current_f2f, current_rn, "CURRENT_BENEFIT_PERIOD"),
    }

    # -----------------------------------------------------------------
    # Section 4: Functional Assessment Comparison (PPS/KPS always;
    # ECOG/FAST/NYHA only when disease-applicable)
    # -----------------------------------------------------------------
    def _scale_pair(scale_type: str) -> Optional[Dict[str, Any]]:
        if scale_type == "PPS":
            prior_val = prior_f2f.pps_score_current if prior_f2f else (prior_rn.pps_score if prior_rn else None)
            current_val = current_f2f.pps_score_current if current_f2f else (current_rn.pps_score if current_rn else None)
        elif scale_type == "KPS":
            prior_val = prior_f2f.kps_score if prior_f2f else (prior_rn.kps_score if prior_rn else None)
            current_val = current_f2f.kps_score if current_f2f else (current_rn.kps_score if current_rn else None)
        elif scale_type == "ECOG":
            if not scale_applicability["ECOG"]:
                return {"scale_type": "ECOG", "comparison_label": "NOT_APPLICABLE", "reason": "No active malignancy diagnosis documented."}
            prior_val = prior_f2f.ecog_score_previous if prior_f2f else None
            current_val = current_f2f.ecog_score_current if current_f2f else None
        elif scale_type == "FAST":
            if not scale_applicability["FAST"]:
                return {"scale_type": "FAST", "comparison_label": "NOT_APPLICABLE", "reason": "No active dementia diagnosis documented."}
            prior_val = prior_f2f.fast_score if prior_f2f else (prior_rn.fast_stage if prior_rn else None)
            current_val = current_f2f.fast_score if current_f2f else (current_rn.fast_stage if current_rn else None)
        elif scale_type == "NYHA":
            if not scale_applicability["NYHA"]:
                return {"scale_type": "NYHA", "comparison_label": "NOT_APPLICABLE", "reason": "No active CHF diagnosis documented."}
            prior_val = prior_f2f.nyha_class if prior_f2f else (prior_rn.nyha_class if prior_rn else None)
            current_val = current_f2f.nyha_class if current_f2f else (current_rn.nyha_class if current_rn else None)
        else:
            raise RecertificationSynthesisError(f"Unsupported scale_type {scale_type!r}")  # pragma: no cover

        prior_date = prior_f2f.encounter_date if prior_f2f else (_utc_date(prior_rn.finalized_at) if prior_rn and prior_rn.finalized_at else None)
        current_date = current_f2f.encounter_date if current_f2f else (_utc_date(current_rn.finalized_at) if current_rn and current_rn.finalized_at else None)

        # Same-benefit-period, same-date, cross-source conflict detection
        # (Scenario 6): F2FEncounter vs RNRecertAssessment disagreeing on
        # the same date for the same scale, in the same benefit period.
        if scale_type in ("PPS", "KPS") and current_f2f and current_rn:
            f2f_val = current_f2f.pps_score_current if scale_type == "PPS" else current_f2f.kps_score
            rn_val = current_rn.pps_score if scale_type == "PPS" else current_rn.kps_score
            f2f_date = current_f2f.encounter_date
            rn_date = _utc_date(current_rn.finalized_at) if current_rn.finalized_at else None
            if f2f_val is not None and rn_val is not None and f2f_date == rn_date and f2f_val != rn_val:
                conflicts.append({
                    "conflict_type": f"CONFLICTING_{scale_type}_SAME_DATE",
                    "conflicting_values": [f2f_val, rn_val],
                    "dates": [f2f_date.isoformat() if f2f_date else None],
                    "source_record_identifiers": [str(current_f2f.id), str(current_rn.id)],
                    "authors_or_assessors": [
                        str(current_f2f.performed_by_user_id) if current_f2f.performed_by_user_id else None,
                        str(current_rn.created_by_user_id) if current_rn.created_by_user_id else None,
                    ],
                    "resolution_status": "UNRESOLVED",
                    "physician_review_question": f"{scale_type} was documented as {f2f_val} (F2F encounter) and {rn_val} (RN recertification assessment) on the same date ({f2f_date.isoformat() if f2f_date else 'unknown'}). Please clarify which value reflects the patient's actual status.",
                })
                return {"scale_type": scale_type, "comparison_label": "CONFLICTING_DOCUMENTATION", "prior_value": prior_val, "current_value": current_val}

        label = _classify_functional_scale(scale_type, prior_val, prior_date, current_val, current_date)
        result = {
            "scale_type": scale_type, "comparison_label": label,
            "prior_value": prior_val, "prior_date": prior_date.isoformat() if prior_date else None,
            "current_value": current_val, "current_date": current_date.isoformat() if current_date else None,
        }
        if label in ("PRIOR_VALUE_MISSING", "CURRENT_VALUE_MISSING", "INDETERMINATE"):
            missing_evidence.append({"section": 4, "concept": scale_type, "label": label})
        return result

    functional_results = {s: _scale_pair(s) for s in ("PPS", "KPS", "ECOG", "FAST", "NYHA")}
    section_4 = {
        "section_number": 4, "section_title": "Functional Assessment Comparison", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None, "content": functional_results,
    }

    # -----------------------------------------------------------------
    # Section 5: ADL and Care-Dependence Comparison
    # -----------------------------------------------------------------
    prior_adl_count = prior_f2f.adl_dependency_count if prior_f2f else (prior_rn.adl_dependency_count if prior_rn else None)
    current_adl_count = current_f2f.adl_dependency_count if current_f2f else (current_rn.adl_dependency_count if current_rn else None)
    prior_adl_date = prior_f2f.encounter_date.isoformat() if prior_f2f else None
    current_adl_date = current_f2f.encounter_date.isoformat() if current_f2f else None
    adl_count_comparison = compare_numeric(
        prior_adl_count, None, prior_adl_date, current_adl_count, None, current_adl_date, higher_is_worse=True,
    )
    prior_adl_level = prior_f2f.adl_dependency_level if prior_f2f else (prior_rn.adl_level if prior_rn else None)
    current_adl_level = current_f2f.adl_dependency_level if current_f2f else (current_rn.adl_level if current_rn else None)
    if prior_adl_level is None and current_adl_level is None:
        adl_level_label = "INDETERMINATE"
    elif prior_adl_level is None:
        adl_level_label = "PRIOR_VALUE_MISSING"
    elif current_adl_level is None:
        adl_level_label = "CURRENT_VALUE_MISSING"
    elif prior_adl_level == current_adl_level:
        adl_level_label = "STABLE"
    else:
        # A free-text ADL-dependency-level category is not an ordered
        # numeric scale in this schema -- a change is reported as MIXED
        # (documented change, direction not computable) rather than
        # guessed as decline or improvement.
        adl_level_label = "MIXED"
    section_5 = {
        "section_number": 5, "section_title": "ADL and Care-Dependence Comparison", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None,
        "content": {
            "adl_dependency_count_comparison": adl_count_comparison,
            "adl_dependency_level_comparison": {
                "comparison_label": adl_level_label, "prior_value": prior_adl_level, "current_value": current_adl_level,
            },
        },
    }
    if adl_count_comparison["comparison_label"] in ("PRIOR_VALUE_MISSING", "CURRENT_VALUE_MISSING", "INDETERMINATE"):
        missing_evidence.append({"section": 5, "concept": "ADL_DEPENDENCY_COUNT", "label": adl_count_comparison["comparison_label"]})

    # -----------------------------------------------------------------
    # Section 6: Nutritional and Hydration Comparison
    # -----------------------------------------------------------------
    prior_weight_loss = float(prior_f2f.weight_loss_lbs) if prior_f2f and prior_f2f.weight_loss_lbs is not None else None
    current_weight_loss = float(current_f2f.weight_loss_lbs) if current_f2f and current_f2f.weight_loss_lbs is not None else None
    weight_comparison = compare_numeric(
        prior_weight_loss, "lbs" if prior_weight_loss is not None else None, prior_adl_date,
        current_weight_loss, "lbs" if current_weight_loss is not None else None, current_adl_date,
        higher_is_worse=True,
    )
    section_6 = {
        "section_number": 6, "section_title": "Nutritional and Hydration Comparison", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None,
        "content": {
            "weight_loss_comparison": weight_comparison,
            "oral_intake_decline": {
                "prior": prior_f2f.oral_intake_decline if prior_f2f else None,
                "current": current_f2f.oral_intake_decline if current_f2f else None,
            },
            "dysphagia": {
                "prior": prior_f2f.dysphagia if prior_f2f else None,
                "current": current_f2f.dysphagia if current_f2f else None,
            },
            "hydration_evidence": {
                "status": "EMPTY", "missing_evidence_code": "NO_STRUCTURED_SOURCE_AVAILABLE_IN_SCHEMA",
                "reason": "No dedicated hydration-tracking field exists in this schema version.",
            },
        },
    }
    documentation_gaps.append({"section": 6, "code": "NO_STRUCTURED_HYDRATION_SOURCE", "detail": "Hydration evidence is not structurally tracked."})
    if weight_comparison["comparison_label"] in ("PRIOR_VALUE_MISSING", "CURRENT_VALUE_MISSING", "INDETERMINATE"):
        missing_evidence.append({"section": 6, "concept": "WEIGHT_LOSS", "label": weight_comparison["comparison_label"]})

    # -----------------------------------------------------------------
    # Section 7: Disease-Specific Evidence Comparison
    # -----------------------------------------------------------------
    current_codes = {d.icd10_code for d in current_dx_primary_secondary}
    prior_codes = {d.icd10_code for d in prior_dx_primary_secondary}
    section_7 = {
        "section_number": 7, "section_title": "Disease-Specific Evidence Comparison", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None,
        "content": {
            "current_diagnoses": [_format_diagnosis(d) for d in current_dx_primary_secondary],
            "prior_diagnoses": [_format_diagnosis(d) for d in prior_dx_primary_secondary],
            "added_since_prior_period": sorted(current_codes - prior_codes),
            "resolved_since_prior_period": sorted(prior_codes - current_codes),
        },
    }
    for d in current_dx_primary_secondary:
        _record_evidence(
            benefit_period_id=current_bp.id, period_role="CURRENT_BENEFIT_PERIOD", disease_id=str(d.id),
            disease_name=d.display_name, concept_domain="DIAGNOSIS", concept_name=d.diagnosis_type,
            value=d.icd10_code, unit=None, assessment_date=d.effective_date, documentation_date=d.created_at,
            source_record_type="PatientDiagnosis", source_record_id=d.id, author_or_assessor_id=d.created_by,
            classification_rule_id="DIAGNOSIS_WINDOW_V1",
        )

    # -----------------------------------------------------------------
    # Sections 8/9/10: no structured source in this schema version
    # -----------------------------------------------------------------
    def _no_source_section(number: int, title: str) -> Dict[str, Any]:
        code = "NO_STRUCTURED_SOURCE_AVAILABLE_IN_SCHEMA"
        reason = f"No dedicated structured table exists for '{title}' evidence in this schema version."
        missing_evidence.append({"section": number, "code": code, "detail": reason})
        documentation_gaps.append({"section": number, "code": code, "detail": reason})
        return {"section_number": number, "section_title": title, "status": "EMPTY", "reason": reason, "missing_evidence_code": code, "content": None}

    section_8 = _no_source_section(8, "Symptoms and Clinical Signs Comparison")
    section_9 = _no_source_section(9, "Laboratory and Objective-Finding Comparison")
    section_10 = _no_source_section(10, "Complications and Infections Comparison")

    # -----------------------------------------------------------------
    # Section 11: Hospitalization and Utilization Comparison
    # -----------------------------------------------------------------
    prior_hosp = prior_f2f.hospitalizations_30d if prior_f2f else None
    current_hosp = current_f2f.hospitalizations_30d if current_f2f else None
    hosp_comparison = compare_numeric(prior_hosp, None, prior_adl_date, current_hosp, None, current_adl_date, higher_is_worse=True)
    section_11 = {
        "section_number": 11, "section_title": "Hospitalization and Utilization Comparison", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None, "content": {"hospitalizations_30d_comparison": hosp_comparison},
    }
    if hosp_comparison["comparison_label"] in ("PRIOR_VALUE_MISSING", "CURRENT_VALUE_MISSING", "INDETERMINATE"):
        missing_evidence.append({"section": 11, "concept": "HOSPITALIZATIONS_30D", "label": hosp_comparison["comparison_label"]})

    # -----------------------------------------------------------------
    # Section 12: Treatment and Intervention Context
    # -----------------------------------------------------------------
    prior_o2 = float(prior_f2f.oxygen_lpm_previous) if prior_f2f and prior_f2f.oxygen_lpm_previous is not None else None
    current_o2 = float(current_f2f.oxygen_lpm_current) if current_f2f and current_f2f.oxygen_lpm_current is not None else None
    o2_comparison = compare_numeric(
        prior_o2, "LPM" if prior_o2 is not None else None, prior_adl_date,
        current_o2, "LPM" if current_o2 is not None else None, current_adl_date, higher_is_worse=True,
    )
    section_12 = {
        "section_number": 12, "section_title": "Treatment and Intervention Context", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None,
        "content": {
            "oxygen_lpm_comparison": o2_comparison,
            "clinical_decline_summary": {
                "content_origin": "SOURCE_CLINICAL_RECORD",
                "text": current_f2f.clinical_decline_summary if current_f2f else None,
            },
        },
    }

    # -----------------------------------------------------------------
    # Section 13: Co-Morbidity Contribution
    # -----------------------------------------------------------------
    section_13 = {
        "section_number": 13, "section_title": "Co-Morbidity Contribution",
        "status": "POPULATED" if current_comorbidities else "EMPTY",
        "reason": None if current_comorbidities else "No active comorbidity-type diagnoses documented for the current benefit period.",
        "missing_evidence_code": None if current_comorbidities else "NO_COMORBIDITY_DIAGNOSES_DOCUMENTED",
        "content": [_format_diagnosis(d) for d in current_comorbidities] if current_comorbidities else None,
    }

    # -----------------------------------------------------------------
    # Section 14: Stability or Improvement Review
    # -----------------------------------------------------------------
    directional_labels = [
        r["comparison_label"] for r in functional_results.values()
        if r["comparison_label"] in ("DECLINING", "STABLE", "IMPROVING")
    ]
    directional_labels += [
        lbl for lbl in (adl_count_comparison["comparison_label"], weight_comparison["comparison_label"], hosp_comparison["comparison_label"])
        if lbl in ("DECLINING", "STABLE", "IMPROVING")
    ]
    has_decline = "DECLINING" in directional_labels
    has_stable = "STABLE" in directional_labels
    has_improve = "IMPROVING" in directional_labels
    review_question_for_stability_or_improvement = False
    if not directional_labels:
        overall_classification = "INDETERMINATE"
    elif has_decline and (has_stable or has_improve):
        overall_classification = "MIXED_CLINICAL_COURSE"
        review_question_for_stability_or_improvement = True
    elif has_decline:
        overall_classification = "DECLINE_DOCUMENTED_NO_STABILITY_OR_IMPROVEMENT"
    elif has_stable and has_improve:
        overall_classification = "MIXED_CLINICAL_COURSE"
        review_question_for_stability_or_improvement = True
    elif has_improve:
        overall_classification = "IMPROVED_WITH_CONTINUED_BURDEN"
        review_question_for_stability_or_improvement = True
    else:
        overall_classification = "STABLE_WITH_CONTINUED_BURDEN"
        review_question_for_stability_or_improvement = True

    section_14 = {
        "section_number": 14, "section_title": "Stability or Improvement Review", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None,
        "content": {"overall_classification": overall_classification, "directional_labels_considered": directional_labels},
    }
    if review_question_for_stability_or_improvement:
        physician_review_questions.append(
            f"Documented stability/improvement ({overall_classification}) was found. Please confirm whether this "
            "affects continued eligibility for the hospice benefit and, if so, document the clinical basis."
        )

    # -----------------------------------------------------------------
    # Section 15: Potentially Reversible Factors
    # -----------------------------------------------------------------
    note_text = (current_f2f.clinical_decline_summary or "") if current_f2f else ""
    matched_phrases = [p for p in _REVERSIBLE_FACTOR_PHRASES if p in note_text.lower()]
    if matched_phrases:
        physician_review_questions.append(
            f"Documentation references potentially reversible factor(s) ({', '.join(matched_phrases)}). "
            "Please clarify whether observed decline is attributable to a reversible cause."
        )
        section_15 = {
            "section_number": 15, "section_title": "Potentially Reversible Factors", "status": "POPULATED",
            "reason": None, "missing_evidence_code": None,
            "content": {"matched_phrases": matched_phrases, "source_text": note_text},
        }
    else:
        section_15 = {
            "section_number": 15, "section_title": "Potentially Reversible Factors", "status": "EMPTY",
            "reason": "No documented reversible-factor language found in the current benefit period's clinical decline summary.",
            "missing_evidence_code": "NO_REVERSIBLE_FACTOR_LANGUAGE_DOCUMENTED", "content": None,
        }

    # -----------------------------------------------------------------
    # Section 16: Conflicting Evidence
    # -----------------------------------------------------------------
    section_16 = {
        "section_number": 16, "section_title": "Conflicting Evidence",
        "status": "POPULATED" if conflicts else "EMPTY",
        "reason": None if conflicts else "No same-date cross-source conflicts detected for the compared benefit periods.",
        "missing_evidence_code": None if conflicts else "NO_CONFLICTS_DETECTED",
        "content": conflicts if conflicts else None,
    }
    for c in conflicts:
        physician_review_questions.append(c["physician_review_question"])

    # -----------------------------------------------------------------
    # Sections 17/18: Missing Evidence / Documentation Gaps (aggregated)
    # -----------------------------------------------------------------
    section_17 = {
        "section_number": 17, "section_title": "Missing Evidence",
        "status": "POPULATED" if missing_evidence else "EMPTY",
        "reason": None if missing_evidence else "No missing-evidence issues were identified.",
        "missing_evidence_code": None, "content": missing_evidence if missing_evidence else None,
    }
    section_18 = {
        "section_number": 18, "section_title": "Documentation Gaps",
        "status": "POPULATED" if documentation_gaps else "EMPTY",
        "reason": None if documentation_gaps else "No documentation gaps were identified.",
        "missing_evidence_code": None, "content": documentation_gaps if documentation_gaps else None,
    }

    # -----------------------------------------------------------------
    # Section 19: Physician Review Questions
    # -----------------------------------------------------------------
    section_19 = {
        "section_number": 19, "section_title": "Physician Review Questions",
        "status": "POPULATED" if physician_review_questions else "EMPTY",
        "reason": None if physician_review_questions else "No physician-review questions were generated.",
        "missing_evidence_code": None, "content": physician_review_questions if physician_review_questions else None,
    }

    # -----------------------------------------------------------------
    # Section 20: Suggested Individualized Narrative Elements
    # (AI_GENERATED_DRAFT_SUPPORT -- never clinician-authored, never a
    # certification, attestation, or eligibility/terminal-status/
    # life-expectancy/recert/discharge conclusion)
    # -----------------------------------------------------------------
    narrative_elements: List[Dict[str, Any]] = []
    for scale_type, result in functional_results.items():
        if result["comparison_label"] in ("DECLINING", "IMPROVING"):
            verb = "declined" if result["comparison_label"] == "DECLINING" else "improved"
            narrative_elements.append({
                "content_origin": "AI_GENERATED_DRAFT_SUPPORT",
                "text": f"{scale_type} {verb} from {result['prior_value']} to {result['current_value']} between the prior and current benefit periods.",
            })
    section_20 = {
        "section_number": 20, "section_title": "Suggested Individualized Narrative Elements",
        "status": "POPULATED" if narrative_elements else "EMPTY",
        "reason": None if narrative_elements else "No directional functional changes were documented to draft narrative support from.",
        "missing_evidence_code": None, "content": narrative_elements if narrative_elements else None,
    }

    # -----------------------------------------------------------------
    # Section 21: Source and Audit Trace
    # -----------------------------------------------------------------
    section_21 = {
        "section_number": 21, "section_title": "Source and Audit Trace", "status": "POPULATED",
        "reason": None, "missing_evidence_code": None, "content": evidence_items,
    }

    sections = [
        section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8, section_9,
        section_10, section_11, section_12, section_13, section_14, section_15, section_16, section_17,
        section_18, section_19, section_20, section_21,
    ]
    assert len(sections) == 21
    assert [s["section_title"] for s in sections] == REQUIRED_SECTION_TITLES

    return {
        "summary_type": "RECERTIFICATION_EVIDENCE_SUMMARY",
        "framework_version": FRAMEWORK_VERSION,
        "patient_id": str(patient_id),
        "hospice_episode_id": str(hospice_episode_id),
        "generated_at": generated_at.isoformat(),
        "regulatory_context": regulatory_context,
        "sections": sections,
        "read_only": True,
    }
