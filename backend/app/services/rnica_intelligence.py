from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


from dataclasses import dataclass, field as _dataclass_field


@dataclass
class _EligibilitySecondaryDx:
    """Adapts a patient_diagnoses row into the shape the eligibility
    engine expects for `patient.secondary_diagnoses` entries (`.icd10`,
    `.description`, `.is_related`)."""

    icd10: str | None
    description: str | None
    is_related: bool


@dataclass
class _EligibilityPatientAdapter:
    """Read-only adapter supplying the attribute names
    app.services.eligibility.engine actually reads (see
    _build_eligibility_sections docstring for why this is required)."""

    id: Any
    tenant_id: Any
    primary_diagnosis_description: str | None
    primary_diagnosis_code: str | None
    admission_date: Any
    secondary_diagnoses: list = _dataclass_field(default_factory=list)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str, ensure_ascii=False)
    return str(value)


def _flatten_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(_flatten_value(item))
        return parts
    if isinstance(value, (list, tuple, set)):
        collected: list[str] = []
        for item in value:
            item_text = _as_text(item).strip()
            if item_text:
                collected.append(item_text)
        return collected
    text = _as_text(value).strip()
    return [text] if text else []


def _section_text(form_data: dict[str, Any], section_key: str) -> str:
    section = form_data.get(section_key) or {}
    texts: list[str] = []
    for item in _flatten_value(section):
        if item:
            texts.append(item)
    return " ".join(texts)


def _int_to_level(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).replace("%", "")))
    except (TypeError, ValueError):
        return None


def _collect_findings(form_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    recommendations: list[str] = []
    evidence: list[dict[str, Any]] = []
    missing: list[str] = []

    primary_dx = (form_data.get("diagnoses") or {}).get("primaryDiagnosis") or {}
    primary_text = " ".join(
        part for part in [
            primary_dx.get("description"),
            primary_dx.get("icd10"),
            (form_data.get("diagnoses") or {}).get("diseaseTrajectory"),
        ] if part
    )
    if not primary_text:
        missing.append("Primary diagnosis not documented")

    pain = form_data.get("pain") or {}
    pain_score = _int_to_level(pain.get("painIntensity", {}).get("current"))
    if pain_score is not None and pain_score >= 7:
        findings.append({
            "category": "pain_management",
            "title": "High pain burden",
            "details": f"Current pain intensity is {pain_score}/10 and should be reviewed against the current care plan.",
            "severity": "high",
        })
        recommendations.append("Review pain treatment plan and reassess symptom control within the next visit.")
    elif pain_score is not None and pain_score >= 4:
        findings.append({
            "category": "pain_management",
            "title": "Moderate pain burden",
            "details": f"Current pain intensity is {pain_score}/10; continue to monitor effectiveness of interventions.",
            "severity": "moderate",
        })
    elif not pain:
        missing.append("Pain assessment not documented")

    respiratory = form_data.get("respiratory") or {}
    sob = str(respiratory.get("sobSeverity") or "").lower()
    oxygen = respiratory.get("oxygenTherapy") or {}
    if "severe" in sob or "acute" in sob or oxygen.get("inUse"):
        findings.append({
            "category": "respiratory_distress",
            "title": "Respiratory concern",
            "details": "Oxygen or severe shortness of breath is documented; evaluation of dyspnea burden is recommended.",
            "severity": "high" if oxygen.get("inUse") else "moderate",
        })
        recommendations.append("Reassess oxygen needs, breathing pattern, and symptom triggers with the treatment team.")

    safety = form_data.get("safety") or {}
    fall_level = str(safety.get("fallRiskLevel") or "").lower()
    if "high" in fall_level or "moderate" in fall_level:
        findings.append({
            "category": "fall_risk",
            "title": "Fall risk present",
            "details": f"Fall risk level is documented as {safety.get('fallRiskLevel') or 'present'}.",
            "severity": "high" if "high" in fall_level else "moderate",
        })
        recommendations.append("Reinforce fall precautions, mobility support, and caregiver awareness.")

    musculoskeletal = form_data.get("musculoskeletal") or {}
    ambulation = str(musculoskeletal.get("mobility", {}).get("ambulatoryStatus") or "").lower()
    if "non" in ambulation or "bedbound" in ambulation or "chair" in ambulation:
        findings.append({
            "category": "mobility_limitations",
            "title": "Mobility limitation",
            "details": "Ambulation or transfer status indicates significant functional limitation.",
            "severity": "moderate",
        })
        recommendations.append("Document assistive device use, caregiver support, and transfer safety needs.")

    neuro = form_data.get("neurological") or {}
    if neuro.get("delirium") or "delirium" in str(neuro.get("cognition") or "").lower():
        findings.append({
            "category": "cognitive_risk",
            "title": "Cognitive or delirium concern",
            "details": "Cognitive status or delirium risk may require additional monitoring and communication supports.",
            "severity": "moderate",
        })
        recommendations.append("Document caregiver communication needs and monitor for delirium progression or safety risk.")

    imminent = form_data.get("imminentDeath") or {}
    if imminent.get("appearsThreeDaysOrLess"):
        findings.append({
            "category": "imminent_death",
            "title": "Imminent death indicators",
            "details": "The assessment documents approaching end-of-life criteria and comfort-focused planning.",
            "severity": "high",
        })
        recommendations.append("Confirm comfort measures, family communication, and plan for end-of-life support.")

    psychosocial = form_data.get("psychosocial") or {}
    if psychosocial.get("distressRating"):
        findings.append({
            "category": "psychosocial_support",
            "title": "Psychosocial distress noted",
            "details": "Psychosocial distress or support concerns are documented in the assessment.",
            "severity": "moderate",
        })
        recommendations.append("Review psychosocial support needs and referral needs for caregiver and patient support.")

    if not findings:
        findings.append({
            "category": "no_urgent_alerts",
            "title": "No high-risk flags from current assessment",
            "details": "The current form data does not show an immediate backlog signal based on the RN ICA review rules.",
            "severity": "low",
        })

    evidence = [
        {"section": "diagnoses", "summary": primary_text or "Primary diagnosis not yet documented"},
        {"section": "pain", "summary": _section_text(form_data, "pain") or "Pain section not documented"},
        {"section": "safety", "summary": _section_text(form_data, "safety") or "Safety section not documented"},
        {"section": "respiratory", "summary": _section_text(form_data, "respiratory") or "Respiratory section not documented"},
    ]

    return findings, recommendations, evidence, missing


def build_rnica_intelligence(
    form_data: dict[str, Any] | None,
    *,
    patient_id: str | None = None,
    patient_evidence: dict[str, Any] | None = None,
    structured_findings_signals: list[dict[str, Any]] | None = None,
    hospice_reasoning: dict[str, Any] | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    payload = form_data or {}
    findings, recommendations, evidence, missing = _collect_findings(payload)

    summary_text = " ".join(section.get("summary", "") for section in evidence)
    if patient_evidence and patient_evidence.get("text"):
        summary_text = " ".join(part for part in [summary_text, patient_evidence.get("text", "")] if part)

    priority = "low"
    highest = max((item.get("severity", "low") for item in findings), default="low", key=lambda level: {"low": 0, "moderate": 1, "high": 2}[level])
    priority = highest

    # Single authoritative diagnosis resolution -- every consumer (RNICA,
    # disease blueprint, LCD, certification, narrative, billing readiness)
    # must read this instead of independently selecting Patient.primary_diagnosis,
    # PatientFaceSheet.primary_diagnosis, or the RNICA form's own diagnoses
    # snapshot. Conflict detection against this assessment's own (possibly
    # stale) diagnoses.primaryDiagnosis field is intentionally NOT
    # duplicated here -- that is already handled end-to-end by
    # `_build_chart_diagnosis_sync` in app/api/visits.py (banner + "Update
    # RN ICA to match chart" button, already wired in
    # RNICACommandWorkspace.jsx). Adding a second conflict mechanism here
    # would itself violate the single-source-of-truth rule this fix exists
    # to enforce -- see diagnosis_resolver.py module docstring.
    diagnosis_context = None
    if db is not None and patient_id:
        from app.services.diagnosis_resolver import resolve_current_diagnosis_context

        diagnosis_context = resolve_current_diagnosis_context(db, patient_id)

    return {
        "mode": "recommendation_only",
        "patient_id": patient_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "overall_priority": priority,
            "finding_count": len(findings),
            "recommendation_count": len(recommendations),
            "missing_evidence_count": len(missing),
            "source_count": patient_evidence.get("source_count", 0) if patient_evidence else 0,
        },
        "findings": findings,
        "recommendations": [
            {"title": item, "priority": "medium" if "monitor" in item.lower() or "review" in item.lower() else "high"}
            for item in recommendations
        ],
        "missing_evidence": missing,
        "evidence": {
            "assessment_text": summary_text,
            "sections": evidence,
            "patient_evidence": patient_evidence or {},
        },
        # Evidence-derived structured findings (see
        # app.services.evidence.structured_findings) awaiting RN review --
        # each entry is one harvested signal carrying zero or more
        # validated, concept-coded findings the RNICA structured-findings
        # apply layer can offer to populate directly into blank RNICA
        # fields. Never auto-applied; always requires an explicit RN action.
        "structured_findings_signals": structured_findings_signals or [],
        # Structured, read-only hospice reasoning panel -- assembled from
        # existing wired engines (eligibility/LCD engine, diagnosis
        # recommendation service, patient_diagnoses relatedness, billing
        # readiness service). See build_hospice_reasoning_panel(). Never
        # auto-applies anything; display only.
        "hospice_reasoning": hospice_reasoning or _empty_hospice_reasoning(),
        # Single authoritative diagnosis resolution (see
        # app.services.diagnosis_resolver) -- resolved primary/secondary/
        # comorbidities from PatientDiagnosis. Chart-vs-RNICA conflict
        # detection is intentionally not duplicated here; see
        # _build_chart_diagnosis_sync in app/api/visits.py.
        "diagnosis_context": diagnosis_context,
    }


def _empty_hospice_reasoning() -> dict[str, Any]:
    return {
        "available": False,
        "why_hospice": None,
        "disease_burden": None,
        "hospice_driver_recommendation": None,
        "related_conditions": {"terminal": [], "related": [], "unrelated": []},
        "documentation_gaps": [],
        "certification_support": None,
        "billing_readiness": None,
    }


def build_hospice_reasoning_panel(db: Session, patient_id: str) -> dict[str, Any]:
    """
    Assembles the read-only "hospice reasoning" panel shown in the RNICA
    workspace from EXISTING, already-wired engines. This function does not
    implement new clinical logic -- it queries/calls:

      - app.services.eligibility.engine.evaluate_hospice_eligibility()
        (LCD/eligibility criteria evaluation) -> why_hospice,
        certification_support, documentation_gaps
      - app.models.patient_diagnosis.PatientDiagnosis rows
        (terminal / related / unrelated classification already stored on
        the chart) -> related_conditions, disease_burden
      - diagnosis_recommendations table (written by
        ReasoningResultToRecommendationService, already wired from visit
        finalize / ICA lock / F2F finalize / certification signing)
        -> hospice_driver_recommendation
      - app.billing.services.billing_readiness_service
        .check_patient_billing_readiness() -> billing_readiness

    Every section is fetched independently and defensively: a failure in
    one section (e.g. no eligibility guideline configured yet) never
    blocks the others from rendering. This is display-only -- nothing
    here writes to the chart, certifications, or billing records.
    """
    # This panel is now a thin VIEW over the shared, versioned Hospice
    # Clinical Context (see hospice_clinical_context.py) -- it no longer
    # re-derives these sections itself. This is the fix for "multiple
    # sources of truth": the context is built once per call and every
    # section here is read from it, not recomputed independently.
    from app.services.hospice_clinical_context import build_hospice_clinical_context

    context = build_hospice_clinical_context(db, patient_id)

    panel = _empty_hospice_reasoning()
    panel["available"] = context["available"]
    if not context["available"]:
        return panel

    panel["related_conditions"] = context["related_conditions"]
    panel["why_hospice"] = context["why_hospice"]
    panel["disease_burden"] = context["disease_burden"]
    panel["certification_support"] = context["certification_support"]
    panel["documentation_gaps"] = context["documentation_gaps"]
    panel["hospice_driver_recommendation"] = context["hospice_driver_recommendation"]
    panel["billing_readiness"] = context["billing_readiness"]
    panel["context_version"] = context["context_version"]
    panel["pipeline_run_id"] = context["pipeline_run_id"]
    panel["generated_at"] = context["generated_at"]

    return panel


def _load_patient_for_reasoning(db: Session, patient_id: str) -> Any | None:
    try:
        from app.models.patient import Patient

        return db.query(Patient).filter(Patient.id == patient_id).first()
    except Exception:
        logger.exception("hospice_reasoning: failed to load patient %s", patient_id)
        return None


def _build_eligibility_sections(
    patient: Any, related_conditions: dict[str, list[dict]]
) -> tuple[dict | None, dict | None, dict | None, list[dict]]:
    """
    Evaluates hospice eligibility/LCD support for `patient`.

    IMPORTANT ADAPTER NOTE (verified defect, fixed here): the eligibility
    engine (app.services.eligibility.engine) reads patient facts via
    attribute names such as `primary_diagnosis_description`,
    `primary_diagnosis_code`, and `terminal_diagnosis_category`. The real
    `Patient` ORM model does NOT define any of these columns -- it only
    has `primary_diagnosis` (free text). Passing a raw `Patient` row
    directly into `evaluate_hospice_eligibility()` therefore always
    silently falls back to the GENERAL_DECLINE_TERMINAL_STATUS pathway
    with no diagnosis facts at all, for every patient, regardless of what
    is actually charted. This is NOT a per-patient bug.

    The fix here is a thin, read-only adapter that supplies the engine's
    expected attribute names from data that is already authoritative on
    the chart: the patient's terminal diagnosis row in `patient_diagnoses`
    (already computed in `related_conditions` above) falling back to the
    patient's free-text `primary_diagnosis` column. No new diagnosis
    source is introduced -- this only maps existing fields onto the
    engine's existing (undocumented) contract.
    """
    terminal_entries = related_conditions.get("terminal") or []
    terminal_description = None
    terminal_icd10 = None
    if terminal_entries:
        terminal_description = terminal_entries[0].get("description")
        code = terminal_entries[0].get("icd10")
        terminal_icd10 = code if code and code != "N/A" else None
    if not terminal_description:
        terminal_description = getattr(patient, "primary_diagnosis", None)

    secondary_entries = (related_conditions.get("related") or []) + (related_conditions.get("unrelated") or [])
    secondary_diagnoses = [
        _EligibilitySecondaryDx(
            icd10=entry.get("icd10") if entry.get("icd10") != "N/A" else None,
            description=entry.get("description"),
            is_related=entry in (related_conditions.get("related") or []),
        )
        for entry in secondary_entries
    ]

    adapter = _EligibilityPatientAdapter(
        id=getattr(patient, "id", None),
        tenant_id=getattr(patient, "tenant_id", None),
        primary_diagnosis_description=terminal_description,
        primary_diagnosis_code=terminal_icd10,
        admission_date=getattr(patient, "admission_date", None),
        secondary_diagnoses=secondary_diagnoses,
    )

    try:
        from app.services.eligibility.engine import evaluate_hospice_eligibility

        admission_date = adapter.admission_date or date.today()
        result = evaluate_hospice_eligibility(adapter, admission_date)
    except Exception as exc:
        logger.info("hospice_reasoning: eligibility evaluation unavailable: %s", exc)
        return None, None, None, []

    criteria = result.get("criteria_summary") or {}
    # Verified defect (see engine.py _evaluate_group / evaluate_lcd_criteria
    # comments): this used to read criteria.get("met")/criteria.get("unmet"),
    # keys the engine never returns -- the real per-criterion detail lives in
    # met_criteria / not_met_criteria / unknown_criteria. That is why
    # supporting_criteria and documentation_gaps always came back empty even
    # when HEART_FAILURE was correctly selected.
    met_criteria = criteria.get("met_criteria") or []
    not_met_criteria = criteria.get("not_met_criteria") or []
    unknown_criteria = criteria.get("unknown_criteria") or []

    def _criterion_text(item: dict) -> str:
        return item.get("description") or item.get("criterion_id") or _as_text(item)

    # A criterion whose backing fact was never documented (UNKNOWN) is not
    # the same clinical statement as one whose documented fact fails the
    # comparison (NOT_MET) -- collapsing them previously made "not eligible"
    # indistinguishable from "insufficient documentation."
    if not_met_criteria:
        result_status = "NOT_MET"
    elif unknown_criteria:
        result_status = "INSUFFICIENT_DOCUMENTATION"
    elif met_criteria and result.get("eligible"):
        result_status = "MET"
    else:
        result_status = "NOT_MET" if not criteria else "EVALUATION_UNAVAILABLE"

    why_hospice = {
        "eligible": result.get("eligible"),
        "result_status": result_status,
        "selected_guideline": result.get("selected_guideline"),
        "lcd_title": result.get("lcd_title"),
        "supporting_criteria": [_criterion_text(item) for item in met_criteria],
        "unmet_criteria": [_criterion_text(item) for item in not_met_criteria],
    }
    disease_burden = {
        "guideline": result.get("selected_guideline"),
        "primary_diagnosis": getattr(patient, "primary_diagnosis_description", None)
        or getattr(patient, "primary_diagnosis", None),
    }
    certification_support = {
        "lcd_id": result.get("lcd_id"),
        "lcd_title": result.get("lcd_title"),
        "lcd_reference": result.get("lcd_reference"),
        "source_document": result.get("source_document"),
        "eligible": result.get("eligible"),
        "result_status": result_status,
    }
    # Missing facts (UNKNOWN) become RNICA documentation guidance -- this is
    # the actual "what still needs to be documented" list, distinct from
    # criteria that were documented and failed.
    documentation_gaps = [
        {"gap": _criterion_text(item), "category": "missing_evidence_for_certification"}
        for item in unknown_criteria
    ]

    return why_hospice, disease_burden, certification_support, documentation_gaps


def _build_related_conditions(
    db: Session, patient: Any, diagnosis_resolved: dict[str, Any] | None = None
) -> dict[str, list[dict]]:
    """
    Verified defect (Invariant 1 -- diagnosis consistency, fixed here):
    this previously re-derived "terminal" independently by scanning
    PatientDiagnosis.is_terminal, a SECOND diagnosis-identity path
    parallel to app.services.diagnosis_resolver.resolve_current_diagnosis_
    context(). The two could disagree (e.g. a row flagged is_terminal=True
    that is not diagnosis_type=PRIMARY/status=ACTIVE), silently feeding
    LCD/certification support a different "terminal diagnosis" than the
    one RNICA/chart-sync treat as authoritative -- exactly the disconnected-
    source failure mode this fix exists to close.

    Fix: when a resolved diagnosis context is supplied, its `primary` is
    the single terminal entry (never independently re-derived); the
    PatientDiagnosis is_related_to_terminal rows classify only the
    remaining (non-primary) related/unrelated conditions.
    """
    result = {"terminal": [], "related": [], "unrelated": []}
    try:
        from app.models.patient_diagnosis import PatientDiagnosis

        rows = (
            db.query(PatientDiagnosis)
            .filter(PatientDiagnosis.patient_id == patient.id, PatientDiagnosis.active.is_(True))
            .all()
        )
    except Exception:
        logger.exception("hospice_reasoning: failed to load patient diagnoses for %s", getattr(patient, "id", None))
        return result

    primary_record_id = None
    if diagnosis_resolved and diagnosis_resolved.get("available") and diagnosis_resolved.get("primary"):
        primary = diagnosis_resolved["primary"]
        primary_record_id = primary.get("source_record_id")
        result["terminal"].append(
            {"icd10": primary.get("icd10_code"), "description": primary.get("description")}
        )

    for row in rows:
        if primary_record_id is not None and str(row.id) == str(primary_record_id):
            continue
        entry = {
            "icd10": row.icd10_code,
            "description": row.diagnosis_description or row.display_name,
        }
        if row.is_terminal:
            if primary_record_id is None:
                # No resolver context available -- fall back to the
                # legacy is_terminal scan rather than silently dropping
                # the row (unavailable_reason already surfaces this case
                # to callers upstream).
                result["terminal"].append(entry)
            # else: resolver is authoritative; a second is_terminal=True
            # row here is a data-integrity condition, not a second truth
            # -- it is intentionally excluded from "terminal" and falls
            # through to related/unrelated below via is_related_to_terminal.
        elif row.is_related_to_terminal:
            result["related"].append(entry)
        else:
            result["unrelated"].append(entry)

    return result


def _build_driver_recommendation(db: Session, patient: Any) -> dict[str, Any] | None:
    try:
        rows = db.execute(
            text(
                """
                SELECT diagnosis_keyword, recommended_status, confidence, priority_score,
                       is_terminal_candidate, is_related_to_terminal_candidate,
                       clinical_rationale, supporting_evidence_summary, recommendation_status,
                       created_at
                FROM diagnosis_recommendations
                WHERE patient_id = :patient_id
                  AND recommendation_status = 'PENDING_REVIEW'
                ORDER BY priority_score DESC NULLS LAST, created_at DESC
                LIMIT 5
                """
            ),
            {"patient_id": str(patient.id)},
        ).mappings().all()
    except Exception:
        logger.exception("hospice_reasoning: failed to load diagnosis_recommendations for %s", getattr(patient, "id", None))
        return None

    if not rows:
        return {"pending_recommendations": []}

    return {
        "pending_recommendations": [
            {
                "diagnosis_keyword": row["diagnosis_keyword"],
                "recommended_status": row["recommended_status"],
                "confidence": row["confidence"],
                "priority_score": row["priority_score"],
                "is_terminal_candidate": row["is_terminal_candidate"],
                "is_related_to_terminal_candidate": row["is_related_to_terminal_candidate"],
                "clinical_rationale": row["clinical_rationale"],
                "supporting_evidence_summary": row["supporting_evidence_summary"],
            }
            for row in rows
        ]
    }


def _build_billing_readiness(db: Session, patient: Any) -> dict[str, Any] | None:
    try:
        from app.billing.services.billing_readiness_service import check_patient_billing_readiness

        result = check_patient_billing_readiness(
            db,
            tenant_id=str(getattr(patient, "tenant_id", None)),
            patient_id=str(patient.id),
            service_date=date.today(),
        )
    except Exception as exc:
        logger.info("hospice_reasoning: billing readiness unavailable for %s: %s", getattr(patient, "id", None), exc)
        return None

    return {
        "ready": result.ready,
        "blockers": result.blockers,
        "warnings": result.warnings,
        "period_number": result.period_number,
    }
