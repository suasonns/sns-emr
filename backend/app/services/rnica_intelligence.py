from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable


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


def build_rnica_intelligence(form_data: dict[str, Any] | None, *, patient_id: str | None = None, patient_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = form_data or {}
    findings, recommendations, evidence, missing = _collect_findings(payload)

    summary_text = " ".join(section.get("summary", "") for section in evidence)
    if patient_evidence and patient_evidence.get("text"):
        summary_text = " ".join(part for part in [summary_text, patient_evidence.get("text", "")] if part)

    priority = "low"
    highest = max((item.get("severity", "low") for item in findings), default="low", key=lambda level: {"low": 0, "moderate": 1, "high": 2}[level])
    priority = highest

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
    }
