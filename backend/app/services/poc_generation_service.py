# backend/app/services/poc_generation_service.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.clinical_note import ClinicalNote

from app.services.poc_rule_loader import get_rule_by_icd
from app.services.text_negation_service import (
    keyword_present,
)
from app.rules.base import RuleContext, Workflow
from app.rules.eligibility.end_stage_parkinsons import (
    EndStageParkinsonRule,
)

POC_GENERATION_SERVICE_VERSION = "1.0.0"


def generate_initial_poc_draft(note: ClinicalNote) -> dict[str, Any]:
    """
    Generate a draft Plan of Care from RN ICA / clinical note data.

    This service:
    - Generates draft POC content only.
    - Does not persist.
    - Does not finalize.
    - Does not approve.
    - Does not replace clinician review.
    """

    content = _content_dict(note)
    observed = _obj(content.get("observed_data") or content.get("observed"))
    assessment = _obj(content.get("assessment"))
    interventions = _obj(content.get("interventions"))
    
    primary_icd10_code = _first_value(
        content,
        assessment,
        [
            "primary_dx_code",
            "primary_icd10_code",
            "icd10_code",
        ],
    )
    
    primary_icd10_rule = get_rule_by_icd(primary_icd10_code)
    
    note_text = _note_text(note, content)
    normalized_text = note_text.lower()

    diagnosis_text = _collect_diagnosis_text(content, assessment)
    functional_evidence = _extract_functional_evidence(content, assessment)

    pocs: list[dict[str, Any]] = []

    if _pain_present(observed, assessment, normalized_text):
        pocs.append(_pain_poc(note, observed, assessment, interventions))

    if (
        primary_icd10_rule
        and primary_icd10_code
        and primary_icd10_code.startswith("J44")
    ):
        pocs.extend(
            _build_pocs_from_rule(
                note,
                primary_icd10_rule,
            )
        )

    elif _respiratory_problem_present(
        observed,
        assessment,
        normalized_text,
    ):
        pocs.append(
            _respiratory_poc(
                note,
                observed,
                assessment,
                interventions,
            )
        )

    if _skin_problem_present(observed, assessment, normalized_text):
        pocs.append(_skin_poc(note, observed, assessment, interventions))

    if _nutrition_problem_present(observed, assessment, normalized_text):
        pocs.append(_nutrition_poc(note, observed, assessment))

    if _fall_or_safety_risk_present(observed, assessment, normalized_text):
        pocs.append(_fall_safety_poc(note, observed, assessment))

    if (
        primary_icd10_rule
        and primary_icd10_rule.get("condition")
        in {
            "ALZHEIMERS_DISEASE",
            "SENILE_DEGENERATION_OF_BRAIN",
            "ALS",
            "STROKE_SEQUELAE",
        }
    ):
        pocs.extend(
            _build_pocs_from_rule(
                note,
                primary_icd10_rule,
            )
        )

    elif _cognitive_decline_present(
        diagnosis_text,
        functional_evidence,
        normalized_text,
    ):
        pocs.append(
            _cognitive_decline_poc(
                note,
                diagnosis_text,
                functional_evidence,
            )
        )
    if (
        primary_icd10_rule
        and primary_icd10_rule.get("condition")
        == "END_STAGE_PARKINSON_DISEASE"
    ):
        if _passes_parkinson_evidence_gate(
            content,
            assessment,
            observed,
        ):
            pocs.extend(
                _build_pocs_from_rule(
                    note,
                    primary_icd10_rule,
                )
            )
        
    if (
        primary_icd10_rule
        and primary_icd10_code
        and primary_icd10_code.startswith("I50")
    ):
        pocs.extend(
            _build_pocs_from_rule(
                note,
                primary_icd10_rule,
            )
        )

    elif (
        not primary_icd10_rule
        and _cardiac_decline_present(
            diagnosis_text,
            functional_evidence,
            normalized_text,
        )
    ):
        pocs.append(
            _cardiac_decline_poc(
                note,
                diagnosis_text,
                functional_evidence,
            )
        )

    elif _cardiac_decline_present(
        diagnosis_text,
        functional_evidence,
        normalized_text,
    ):
        pocs.append(
            _cardiac_decline_poc(
                note,
                diagnosis_text,
                functional_evidence,
            )
        )
    
    if _functional_decline_present(functional_evidence, observed, assessment, normalized_text):
        pocs.append(_functional_decline_poc(note, functional_evidence, observed, assessment))

    if _caregiver_support_need_present(observed, assessment, normalized_text):
        pocs.append(_caregiver_support_poc(note, observed, assessment))

    return {
        "status": "DRAFT_GENERATED",
        "source": {
            "source_type": "CLINICAL_NOTE",
            "clinical_note_id": str(getattr(note, "id", None)) if getattr(note, "id", None) else None,
            "patient_id": str(getattr(note, "patient_id", None)) if getattr(note, "patient_id", None) else None,
            "visit_id": str(getattr(note, "visit_id", None)) if getattr(note, "visit_id", None) else None,
            "form_key": getattr(note, "form_key", None),
            "note_type": getattr(note, "note_type", None),
            "discipline": _safe_text(getattr(note, "discipline", None)),
        },
        "primary_icd10_code": primary_icd10_code,

        "rule_match": {
            "found": primary_icd10_rule is not None,
            "condition": (
                primary_icd10_rule.get("condition")
                if primary_icd10_rule
                else None
            ),
        },
        "primary_diagnosis": _first_value(
            content,
            assessment,
            ["primary_diagnosis", "primary_dx", "primary_dx_code"],
        ),
        "functional_evidence": functional_evidence,
        "pocs": pocs,
        "generated_at": _utc_now_iso(),
        "generator": {
            "service": "poc_generation_service",
            "version": POC_GENERATION_SERVICE_VERSION,
            "mode": "draft_only",
            "requires_clinician_review": True,
            "auto_finalized": False,
        },
    }


def _pain_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
) -> dict[str, Any]:
    pain = _obj(observed.get("pain") or assessment.get("pain") or assessment.get("pain_assessment"))

    return _poc_item(
        note=note,
        problem_code="PAIN",
        problem_label="Pain requiring ongoing hospice management",
        severity="MODERATE",
        evidence=[
            _evidence("pain", pain or "Pain documented in assessment or narrative."),
        ],
        goals=[
            "Patient pain will be maintained at an acceptable comfort level as defined by patient or caregiver.",
            "Patient or caregiver will verbalize understanding of the pain management plan.",
        ],
        interventions=[
            _intervention("RN", "Assess pain intensity, location, pattern, and response to interventions each visit."),
            _intervention("RN", "Evaluate effectiveness of ordered pain medications and non-pharmacologic comfort measures."),
            _intervention("RN", "Notify provider of uncontrolled pain, worsening pain, or change in pain pattern."),
            _intervention("IDG", "Review pain status and effectiveness of pain management plan during IDG review."),
        ],
    )


def _respiratory_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
) -> dict[str, Any]:
    respiratory = _obj(observed.get("respiratory") or assessment.get("respiratory"))

    return _poc_item(
        note=note,
        problem_code="RESPIRATORY",
        problem_label="Respiratory distress or dyspnea requiring hospice management",
        severity="MODERATE",
        evidence=[
            _evidence("respiratory", respiratory or "Respiratory concern documented in assessment or narrative."),
        ],
        goals=[
            "Patient will remain comfortable with reduced respiratory distress.",
            "Caregiver will verbalize understanding of dyspnea management and when to notify hospice.",
        ],
        interventions=[
            _intervention("RN", "Assess respiratory rate, effort, breath sounds, oxygen use, and dyspnea each visit."),
            _intervention("RN", "Reinforce ordered oxygen and medication use as applicable."),
            _intervention("RN", "Educate caregiver on positioning, pacing activity, and comfort measures for dyspnea."),
            _intervention("IDG", "Review respiratory status and need for medication, oxygen, or care plan changes."),
        ],
    )


def _skin_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
    interventions: dict[str, Any],
) -> dict[str, Any]:
    skin = _obj(observed.get("skin") or assessment.get("skin") or assessment.get("wound"))

    return _poc_item(
        note=note,
        problem_code="SKIN_INTEGRITY",
        problem_label="Impaired skin integrity or risk for skin breakdown",
        severity="HIGH",
        evidence=[
            _evidence("skin", skin or "Skin or wound concern documented in assessment or narrative."),
        ],
        goals=[
            "Skin integrity will be maintained or decline minimized within disease progression.",
            "Caregiver will verbalize understanding of skin protection and pressure relief measures.",
        ],
        interventions=[
            _intervention("RN", "Assess skin integrity, wounds, pressure areas, drainage, odor, and signs of infection."),
            _intervention("RN", "Reinforce pressure reduction, repositioning, hygiene, and wound care instructions."),
            _intervention("RN", "Coordinate wound care orders, supplies, and provider notification as needed."),
            _intervention("HHA", "Assist with hygiene and skin protection measures within aide plan of care."),
        ],
    )


def _nutrition_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    nutrition = _obj(
        observed.get("nutrition")
        or assessment.get("nutrition")
        or assessment.get("gastrointestinal")
    )

    return _poc_item(
        note=note,
        problem_code="NUTRITION",
        problem_label="Nutritional decline or decreased oral intake",
        severity="MODERATE",
        evidence=[
            _evidence("nutrition", nutrition or "Nutrition concern documented in assessment or narrative."),
        ],
        goals=[
            "Patient nutritional comfort needs will be supported according to disease progression and patient tolerance.",
            "Caregiver will verbalize understanding of comfort feeding and aspiration precautions as applicable.",
        ],
        interventions=[
            _intervention("RN", "Assess appetite, intake, swallowing ability, weight change, and signs of dehydration."),
            _intervention("RN", "Educate caregiver on comfort feeding, small frequent meals, and aspiration precautions as appropriate."),
            _intervention("IDG", "Review nutritional decline and need for dietary, medication, or care plan adjustment."),
        ],
    )


def _fall_safety_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    safety = _obj(
        observed.get("safety")
        or assessment.get("safety")
        or assessment.get("environment_safety")
    )

    return _poc_item(
        note=note,
        problem_code="SAFETY_FALL_RISK",
        problem_label="Risk for falls or injury",
        severity="HIGH",
        evidence=[
            _evidence("safety", safety or "Fall risk or safety concern documented in assessment or narrative."),
        ],
        goals=[
            "Patient will remain free from avoidable injury.",
            "Caregiver will verbalize understanding of fall prevention and safety plan.",
        ],
        interventions=[
            _intervention("RN", "Assess fall risk, transfer safety, assistive device use, and environmental hazards."),
            _intervention("RN", "Educate caregiver on fall precautions, supervision needs, and safe transfers."),
            _intervention("IDG", "Review fall risk and need for equipment, therapy input, or caregiver support."),
        ],
    )


def _cognitive_decline_poc(
    note: ClinicalNote,
    diagnosis_text: str,
    functional_evidence: dict[str, Any],
) -> dict[str, Any]:
    return _poc_item(
        note=note,
        problem_code="COGNITIVE_DECLINE",
        problem_label="Progressive cognitive decline with increasing care needs",
        severity="MODERATE",
        evidence=[
            _evidence("diagnosis", diagnosis_text),
            _evidence("functional_evidence", functional_evidence),
        ],
        goals=[
            "Patient will remain safe and comfortable with support appropriate to cognitive decline.",
            "Caregiver will verbalize understanding of cognitive decline, safety needs, and hospice support plan.",
        ],
        interventions=[
            _intervention("RN", "Assess cognitive status, communication ability, safety risks, behavior changes, and caregiver understanding."),
            _intervention("MSW", "Assess caregiver coping, support system, and psychosocial needs as indicated."),
            _intervention("IDG", "Review cognitive decline, FAST stage if applicable, caregiver burden, and safety plan."),
        ],
    )


def _cardiac_decline_poc(
    note: ClinicalNote,
    diagnosis_text: str,
    functional_evidence: dict[str, Any],
) -> dict[str, Any]:
    return _poc_item(
        note=note,
        problem_code="CARDIAC_DECLINE",
        problem_label="Cardiac disease progression with activity intolerance or symptom burden",
        severity="MODERATE",
        evidence=[
            _evidence("diagnosis", diagnosis_text),
            _evidence("functional_evidence", functional_evidence),
        ],
        goals=[
            "Patient will remain comfortable with reduced cardiac symptom burden.",
            "Caregiver will verbalize understanding of cardiac symptom monitoring and when to notify hospice.",
        ],
        interventions=[
            _intervention("RN", "Assess edema, dyspnea, fatigue, chest discomfort, activity tolerance, and medication effectiveness."),
            _intervention("RN", "Educate caregiver on symptom escalation, comfort measures, and ordered medication plan."),
            _intervention("IDG", "Review cardiac decline, NYHA class if applicable, and care plan effectiveness."),
        ],
    )


def _functional_decline_poc(
    note: ClinicalNote,
    functional_evidence: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    return _poc_item(
        note=note,
        problem_code="FUNCTIONAL_DECLINE",
        problem_label="Functional decline with increasing dependence in care needs",
        severity="MODERATE",
        evidence=[
            _evidence("functional_evidence", functional_evidence),
            _evidence("adls", _obj(observed.get("adls") or assessment.get("adls"))),
        ],
        goals=[
            "Patient care needs will be met safely according to current functional status.",
            "Caregiver will verbalize understanding of assistance required for ADLs and transfers.",
        ],
        interventions=[
            _intervention("RN", "Assess functional status, ADL dependence, mobility, transfers, and caregiver ability each visit."),
            _intervention("HHA", "Assist with personal care needs according to aide plan of care when ordered."),
            _intervention("IDG", "Review functional decline, PPS, KPS, and related care needs during IDG review."),
        ],
    )


def _caregiver_support_poc(
    note: ClinicalNote,
    observed: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    caregiver = _obj(
        observed.get("caregiver")
        or assessment.get("caregiver")
        or assessment.get("support_assessment")
        or assessment.get("psychosocial")
    )

    return _poc_item(
        note=note,
        problem_code="CAREGIVER_SUPPORT",
        problem_label="Caregiver support needs or caregiver strain",
        severity="MODERATE",
        evidence=[
            _evidence("caregiver", caregiver or "Caregiver or support concern documented in assessment or narrative."),
        ],
        goals=[
            "Caregiver will verbalize understanding of hospice plan and available support.",
            "Caregiver strain will be monitored and addressed through interdisciplinary support.",
        ],
        interventions=[
            _intervention("RN", "Assess caregiver understanding, ability, availability, and need for education each visit."),
            _intervention("MSW", "Assess caregiver coping, resources, respite needs, and psychosocial support needs."),
            _intervention("SC", "Offer spiritual support according to patient and caregiver preference."),
            _intervention("IDG", "Review caregiver support needs and update plan as appropriate."),
        ],
    )


def _poc_item(
    *,
    note: ClinicalNote,
    problem_code: str,
    problem_label: str,
    severity: str,
    evidence: list[dict[str, Any]],
    goals: list[str],
    interventions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "poc_id": f"AUTO_{problem_code}",
        "status": "DRAFT",
        "problem": {
            "code": problem_code,
            "label": problem_label,
        },
        "clinical_summary": {
            "severity": severity,
        },
        "goals": [
            {
                "goal_id": f"AUTO_{problem_code}_GOAL_{index + 1}",
                "goal_text": goal,
                "status": "DRAFT",
            }
            for index, goal in enumerate(goals)
        ],
        "interventions": interventions,
        "evidence": evidence,
        "source": {
            "source_type": "CLINICAL_NOTE",
            "clinical_note_id": str(getattr(note, "id", None)) if getattr(note, "id", None) else None,
        },
        "created_at": _utc_now_iso(),
        "engine_version": POC_GENERATION_SERVICE_VERSION,
        "requires_clinician_review": True,
    }


def _intervention(discipline: str, text: str) -> dict[str, Any]:
    return {
        "discipline": discipline,
        "intervention_text": text,
        "status": "DRAFT",
    }


def _evidence(source: str, value: Any) -> dict[str, Any]:
    return {
        "source": source,
        "value": value,
    }

def _build_pocs_from_rule(
    note: ClinicalNote,
    rule: dict[str, Any],
) -> list[dict[str, Any]]:
    pocs: list[dict[str, Any]] = []

    for problem in rule.get("problems", []):
        pocs.append(
            _poc_item(
                note=note,
                problem_code=problem["code"],
                problem_label=problem["label"],
                severity=problem.get("severity", "MODERATE"),
                evidence=[
                    _evidence(
                        "icd_rule",
                        rule.get("condition"),
                    )
                ],
                goals=rule.get("goals", []),
                interventions=[
                    _intervention(
                        item["discipline"],
                        item["text"],
                    )
                    for item in rule.get("interventions", [])
                ],
            )
        )

    return pocs

def _passes_parkinson_evidence_gate(
    content: dict[str, Any],
    assessment: dict[str, Any],
    observed: dict[str, Any],
) -> bool:
    facts = {
        "pps": _first_value(
            content,
            assessment,
            ["pps", "pps_score"],
        ),
        "kps": _first_value(
            content,
            assessment,
            ["kps", "kps_score"],
        ),

        "adl_dependency_count": _first_value(
            content,
            assessment,
            [
                "adl_dependency_count",
                "adl_count",
            ],
        ),

        "is_bedbound": _first_value(
            content,
            assessment,
            [
                "is_bedbound",
                "bedbound",
            ],
        ),

        "dysphagia": _first_value(
            content,
            assessment,
            ["dysphagia"],
        ),

        "oral_intake_decline": _first_value(
            content,
            assessment,
            ["oral_intake_decline"],
        ),

        "weight_loss_lbs": _first_value(
            content,
            assessment,
            ["weight_loss_lbs"],
        ),

        "fall_risk": _first_value(
            content,
            assessment,
            ["fall_risk"],
        ),

        "caregiver_stress": _first_value(
            content,
            assessment,
            ["caregiver_stress"],
        ),

        "communication_ability": _first_value(
            content,
            assessment,
            ["communication_ability"],
        ),

        "speech_pattern": _first_value(
            content,
            assessment,
            ["speech_pattern"],
        ),
    }

    ctx = RuleContext(
        tenant_id="POC_GENERATOR",
        patient_id=None,
        workflow=Workflow.ADMISSION,
        facts=facts,
    )

    result = EndStageParkinsonRule().evaluate(ctx)

    return result.outcome.value == "PASS"

def _content_dict(note: ClinicalNote) -> dict[str, Any]:
    content = getattr(note, "content", None)
    return content if isinstance(content, dict) else {}


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _note_text(note: ClinicalNote, content: dict[str, Any]) -> str:
    candidates = [
        getattr(note, "narrative", None),
        getattr(note, "body", None),
        getattr(note, "note_text", None),
        content.get("narrative"),
        content.get("body"),
        content.get("note_text"),
        content.get("summary"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    return _flatten_text(content)


def _flatten_text(value: Any) -> str:
    parts: list[str] = []

    def collect(item: Any) -> None:
        if item is None:
            return

        if isinstance(item, str):
            if item.strip():
                parts.append(item.strip())
            return

        if isinstance(item, (int, float, bool)):
            parts.append(str(item))
            return

        if isinstance(item, dict):
            for nested in item.values():
                collect(nested)
            return

        if isinstance(item, list):
            for nested in item:
                collect(nested)
            return

    collect(value)
    return " ".join(parts)


def _first_value(
    content: dict[str, Any],
    assessment: dict[str, Any],
    keys: list[str],
) -> Any:
    for key in keys:
        if not _empty(content.get(key)):
            return content.get(key)

        if not _empty(assessment.get(key)):
            return assessment.get(key)

    return None


def _extract_functional_evidence(
    content: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "pps": _first_value(content, assessment, ["pps", "pps_score"]),
        "kps": _first_value(content, assessment, ["kps", "kps_score"]),
        "fast_stage": _first_value(content, assessment, ["fast", "fast_stage", "fast_score"]),
        "nyha_class": _first_value(content, assessment, ["nyha", "nyha_class"]),
    }


def _collect_diagnosis_text(
    content: dict[str, Any],
    assessment: dict[str, Any],
) -> str:
    values = [
        content.get("primary_diagnosis"),
        content.get("primary_dx"),
        content.get("primary_dx_code"),
        content.get("primary_diagnosis_description"),
        content.get("diagnosis"),
        content.get("diagnoses"),
        content.get("secondary_diagnoses"),
        assessment.get("primary_diagnosis"),
        assessment.get("primary_dx"),
        assessment.get("primary_dx_code"),
        assessment.get("primary_diagnosis_description"),
        assessment.get("diagnosis"),
        assessment.get("diagnoses"),
        assessment.get("secondary_diagnoses"),
    ]

    return _flatten_text(values).upper()


def _pain_present(observed: dict[str, Any], assessment: dict[str, Any], text: str) -> bool:
    pain = _obj(observed.get("pain") or assessment.get("pain") or assessment.get("pain_assessment"))

    return (
        bool(pain)
        or "pain" in text
        or "/10" in text
    )


def _respiratory_problem_present(observed: dict[str, Any], assessment: dict[str, Any], text: str) -> bool:
    respiratory = _obj(observed.get("respiratory") or assessment.get("respiratory"))

    return (
        bool(respiratory)
        or "dyspnea" in text
        or "shortness of breath" in text
        or "oxygen" in text
        or "sob" in text
    )

def _skin_problem_present(observed: dict[str, Any], assessment: dict[str, Any], text: str) -> bool:
    skin = _obj(observed.get("skin") or assessment.get("skin") or assessment.get("wound"))

    return (
        bool(skin)
        or "wound" in text
        or "pressure injury" in text
        or "pressure ulcer" in text
        or "skin tear" in text
    )

def _nutrition_problem_present(observed: dict[str, Any], assessment: dict[str, Any], text: str) -> bool:
    nutrition = _obj(
        observed.get("nutrition")
        or assessment.get("nutrition")
        or assessment.get("gastrointestinal")
    )

    return (
        bool(nutrition)
        or keyword_present(
            text,
            "poor intake",
        )
        or keyword_present(
            text,
            "weight loss",
        )
        or keyword_present(
            text,
            "dysphagia",
        )
        or keyword_present(
            text,
            "appetite",
        )
    )

def _fall_or_safety_risk_present(
    observed: dict[str, Any],
    assessment: dict[str, Any],
    text: str,
) -> bool:
    safety = _obj(
        observed.get("safety")
        or assessment.get("safety")
        or assessment.get("environment_safety")
    )

    return (
        bool(safety)
        or keyword_present(
            text,
            "fall",
        )
        or keyword_present(
            text,
            "falls",
        )
        or keyword_present(
            text,
            "fall risk",
        )
        or keyword_present(
            text,
            "unsafe",
        )
    )

def _cognitive_decline_present(
    diagnosis_text: str,
    functional_evidence: dict[str, Any],
    text: str,
) -> bool:
    return (
        "DEMENTIA" in diagnosis_text
        or "ALZHEIMER" in diagnosis_text
        or "F01" in diagnosis_text
        or "F02" in diagnosis_text
        or "F03" in diagnosis_text
        or "G30" in diagnosis_text
        or not _empty(functional_evidence.get("fast_stage"))
        or "confusion" in text
        or "cognitive" in text
    )


def _cardiac_decline_present(
    diagnosis_text: str,
    functional_evidence: dict[str, Any],
    text: str,
) -> bool:
    return (
        "CHF" in diagnosis_text
        or "HEART FAILURE" in diagnosis_text
        or "I50" in diagnosis_text
        # or not _empty(functional_evidence.get("nyha_class"))
        or "edema" in text
        or "cardiac" in text
    )


def _functional_decline_present(
    functional_evidence: dict[str, Any],
    observed: dict[str, Any],
    assessment: dict[str, Any],
    text: str,
) -> bool:
    pps = _numeric(functional_evidence.get("pps"))
    kps = _numeric(functional_evidence.get("kps"))
    adls = _obj(observed.get("adls") or assessment.get("adls"))

    return (
        bool(adls)
        or (pps > 0 and pps <= 50)
        or (kps > 0 and kps <= 50)
        or "bedbound" in text
        or "dependent" in text
        or "total care" in text
    )


def _caregiver_support_need_present(
    observed: dict[str, Any],
    assessment: dict[str, Any],
    text: str,
) -> bool:
    caregiver = _obj(
        observed.get("caregiver")
        or assessment.get("caregiver")
        or assessment.get("support_assessment")
        or assessment.get("psychosocial")
    )

    return (
        bool(caregiver)
        or keyword_present(
            text,
            "caregiver",
        )
        or keyword_present(
            text,
            "family support",
        )
        or keyword_present(
            text,
            "caregiver stress",
        )
    )

def _numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return len(value) == 0

    if isinstance(value, dict):
        return len(value) == 0

    return False


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None

    raw = getattr(value, "value", value)
    return str(raw)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()