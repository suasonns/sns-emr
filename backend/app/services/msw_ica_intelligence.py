from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


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


def _flatten(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        output: list[str] = []
        for item in value.values():
            output.extend(_flatten(item))
        return output
    if isinstance(value, (list, tuple, set)):
        output: list[str] = []
        for item in value:
            text = _as_text(item).strip()
            if text:
                output.append(text)
        return output
    text = _as_text(value).strip()
    return [text] if text else []


def build_msw_ica_intelligence(form_data: dict[str, Any] | None, *, patient_id: str | None = None, patient_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = form_data or {}
    social = payload.get("social") or {}
    caregiver = payload.get("caregiver") or {}
    risk = payload.get("risk") or {}
    interventions = payload.get("interventions") or {}
    finalization = payload.get("finalization") or {}

    findings: list[dict[str, Any]] = []
    recommendations: list[str] = []
    missing: list[str] = []

    support = _as_text(social.get("support_level")).lower()
    support_concerns = [str(item).lower() for item in social.get("concerns") or []]
    caregiver_burden = _as_text(caregiver.get("burden_level")).lower()
    caregiver_concerns = [str(item).lower() for item in caregiver.get("caregiver_concerns") or []]

    financial = _as_text(risk.get("financial_stress")).lower()
    housing = _as_text(risk.get("housing_insecurity")).lower()
    isolation = _as_text(risk.get("social_isolation")).lower()
    anger = _as_text(risk.get("anger_or_conflict")).lower()
    safety = _as_text(risk.get("safety_concerns")).lower()
    crisis = _as_text(risk.get("mental_health_crisis")).lower()
    transportation = _as_text(risk.get("transportation_barrier")).lower()
    referral = _as_text(interventions.get("referral_type")).lower()
    priority_level = _as_text(interventions.get("priority_level")).lower()

    notes_text = " ".join([
        str(social.get("notes") or ""),
        str(caregiver.get("respite_needs") or ""),
        str(risk.get("notes") or ""),
        str(interventions.get("intervention_plan") or ""),
    ]).lower()

    if support in {"limited", "none", "unknown", "declined", "declined to answer"}:
        findings.append({
            "category": "support_gap",
            "title": "Limited social support",
            "details": "Support is limited or absent, which raises risk for missed follow-up, caregiver strain, and reduced access to community resources.",
            "severity": "moderate",
        })
        recommendations.append("Coordinate active support planning and assess whether outreach, caregiver education, or community resource linkage is needed.")

    if caregiver_burden in {"high", "severe"} or any(token in caregiver_concerns for token in {"burnout", "fatigue", "work-life strain"}):
        findings.append({
            "category": "caregiver_burden",
            "title": "Caregiver burden elevated",
            "details": "Caregiver strain is significant and should be reviewed for respite planning, education, and caregiver support resources.",
            "severity": "high",
        })
        recommendations.append("Review caregiver capacity and offer respite, role support, and caregiver education resources.")

    if financial in {"high", "moderate"} or "financial" in notes_text or "benefits" in notes_text:
        findings.append({
            "category": "financial_barrier",
            "title": "Financial or access barrier",
            "details": "Financial stress or service barriers are documented and may delay adherence to care and access to needed supports.",
            "severity": "moderate",
        })
        recommendations.append("Assess benefits navigation, transportation funding, and financial assistance options for the family.")

    if housing in {"high", "moderate"} or "housing" in notes_text or "eviction" in notes_text:
        findings.append({
            "category": "housing_insecurity",
            "title": "Housing or basic needs instability",
            "details": "Housing instability or basic-needs insecurity is present and may affect care continuity and caregiver capacity.",
            "severity": "moderate",
        })
        recommendations.append("Address housing and utility support needs, which may directly affect the family’s ability to maintain care plan adherence.")

    if isolation in {"yes", "high", "moderate"} or "isolated" in notes_text or "lonely" in notes_text:
        findings.append({
            "category": "isolation_risk",
            "title": "Social isolation risk",
            "details": "The assessment indicates isolation or limited community engagement, which can reduce coping and increase unmet service needs.",
            "severity": "moderate",
        })
        recommendations.append("Reinforce engagement opportunities, peer support, and targeted outreach to reduce social isolation.")

    if anger in {"yes", "high", "moderate"} or "conflict" in notes_text:
        findings.append({
            "category": "family_conflict",
            "title": "Family conflict or distress noted",
            "details": "Conflict or interpersonal strain is present and may affect communication, caregiver participation, and care plan stability.",
            "severity": "moderate",
        })
        recommendations.append("Document family dynamics and coordinate a communication plan consistent with patient and caregiver goals.")

    if safety in {"yes", "high", "moderate"} or "safety" in notes_text or "abuse" in notes_text:
        findings.append({
            "category": "safety_concern",
            "title": "Safety or abuse concern",
            "details": "Safety concerns or possible risk factors are present and require follow-up by the care team and consideration of escalation pathways.",
            "severity": "high",
        })
        recommendations.append("Escalate safety concerns through the appropriate clinical and social-work response pathway and document follow-up steps.")

    if crisis in {"yes", "high", "moderate"} or "crisis" in notes_text:
        findings.append({
            "category": "mental_health_crisis",
            "title": "Mental health or crisis risk",
            "details": "Mental health or crisis indicators are present and may require urgent coordination with the interdisciplinary team.",
            "severity": "high",
        })
        recommendations.append("Assess for immediate crisis support and escalate to the appropriate mental health or care management workflow.")

    if transportation in {"yes", "high", "moderate"} or "transport" in notes_text:
        findings.append({
            "category": "transportation_barrier",
            "title": "Transportation barrier identified",
            "details": "Transportation or mobility barriers may reduce access to care and increase missed visits or delayed resources.",
            "severity": "moderate",
        })
        recommendations.append("Review transportation supports and access planning, including community resource referral and scheduling coordination.")

    if referral and referral not in {"none", "not needed"}:
        findings.append({
            "category": "referral_plan",
            "title": f"Referral pathway identified: {referral}",
            "details": "The assessment includes a defined referral plan that should be tracked to ensure follow-through and interdisciplinary continuity.",
            "severity": "low" if priority_level in {"routine", "standard"} else "moderate",
        })

    if not findings:
        findings.append({
            "category": "no_urgent_social_risk",
            "title": "No acute psychosocial escalation in current assessment",
            "details": "The available assessment data does not suggest an immediate social-work crisis or high-risk pattern requiring urgent escalation.",
            "severity": "low",
        })

    missing_fields = {
        "Support level": not support,
        "Caregiver burden": not caregiver_burden,
        "Financial stress": not financial,
        "Social isolation": not isolation,
        "Safety concerns": not safety,
    }
    missing.extend(label for label, is_missing in missing_fields.items() if is_missing)

    if not payload:
        missing.append("MSW ICA assessment not started")

    evidence_sections: list[dict[str, Any]] = []
    for key in ["social", "caregiver", "risk", "interventions"]:
        value = payload.get(key)
        if value:
            evidence_sections.append({"section": key, "summary": " ".join(_flatten(value)[:12])})

    if patient_evidence and patient_evidence.get("text"):
        evidence_sections.append({"section": "patient_evidence", "summary": patient_evidence.get("text", "")[:800]})

    priority = max((item.get("severity", "low") for item in findings), default="low", key=lambda level: {"low": 0, "moderate": 1, "high": 2}[level])

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
        "recommendations": [{"title": item, "priority": "medium" if "review" in item.lower() or "consider" in item.lower() else "high"} for item in recommendations],
        "missing_evidence": missing,
        "evidence": {
            "assessment_text": " ".join(part.get("summary", "") for part in evidence_sections if part.get("summary")),
            "sections": evidence_sections,
            "patient_evidence": patient_evidence or {},
        },
    }
