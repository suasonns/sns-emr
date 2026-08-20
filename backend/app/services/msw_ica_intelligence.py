from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.msw_ica_assessment import merge_msw_ica_form_data



def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()



def _has_any(values: list[str] | None) -> bool:
    return any(_text(value) for value in (values or []))



def _suicide_risk_indicated(payload: dict[str, Any]) -> bool:
    patient_concerns = set((payload.get("patientDistress") or {}).get("patientConcerns") or [])
    family_crisis = set((payload.get("familyDistress") or {}).get("familyCrisis") or [])
    return "Suicide risks" in patient_concerns or "Suicide risks" in family_crisis



def _abuse_categories(payload: dict[str, Any]) -> list[str]:
    return list((((payload.get("patientDistress") or {}).get("abuseNeglectExploitation") or {}).get("categories") or []))



def build_msw_ica_intelligence(form_data: dict[str, Any] | None, *, patient_id: str | None = None, patient_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = merge_msw_ica_form_data(form_data)
    psychosocial = payload.get("psychosocial") or {}
    patient_distress = payload.get("patientDistress") or {}
    family_distress = payload.get("familyDistress") or {}
    financial_legal = payload.get("financialLegal") or {}
    referrals = payload.get("referrals") or {}
    suicide_risk = patient_distress.get("suicideRisk") or {}
    abuse_workflow = patient_distress.get("abuseNeglectExploitation") or {}
    legacy_social = payload.get("social") or {}
    legacy_caregiver = payload.get("caregiver") or {}
    legacy_risk = payload.get("risk") or {}
    legacy_interventions = payload.get("interventions") or {}

    findings: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    missing: list[str] = []
    risk_flags: list[str] = []

    if _suicide_risk_indicated(payload):
        risk_flags.append("suicide_risk")
        findings.append({
            "category": "suicide_risk",
            "title": "Suicide-risk escalation documented",
            "details": "A suicide-risk concern is present in the assessment and requires immediate interdisciplinary notification and follow-up.",
            "severity": "high",
        })
        recommendations.append({
            "title": "Confirm Case Manager/Supervisor and Attending Physician notifications before lock.",
            "priority": "high",
        })
        if not suicide_risk.get("notifiedCaseManagerSupervisor"):
            missing.append("Suicide risk: Case Manager/Supervisor notification")
        if not suicide_risk.get("notifiedAttendingPhysician"):
            missing.append("Suicide risk: Attending Physician notification")

    abuse_categories = _abuse_categories(payload)
    if abuse_categories:
        risk_flags.append("abuse_neglect_exploitation")
        findings.append({
            "category": "abuse_reporting",
            "title": "Abuse/neglect/exploitation workflow active",
            "details": f"Selected categories: {', '.join(abuse_categories)}.",
            "severity": "high",
        })
        recommendations.append({
            "title": "Track mandated external reporting details and supervisor follow-up for the abuse/neglect workflow.",
            "priority": "high",
        })
        if not _text(abuse_workflow.get("reportedTo")):
            missing.append("Abuse/Neglect/Exploitation: Reported to")

    legacy_financial_risk = _text(legacy_risk.get("financial_stress")).lower()
    if (
        financial_legal.get("allNeedsMet") == "No"
        or _has_any(financial_legal.get("patientLacks"))
        or legacy_financial_risk in {"moderate", "high"}
    ):
        risk_flags.append("financial_barrier")
        findings.append({
            "category": "financial_barrier",
            "title": "Financial/basic-needs barrier documented",
            "details": "Patient or family needs are not fully met and may affect care-plan adherence.",
            "severity": "moderate",
        })
        recommendations.append({
            "title": "Complete benefits/resource follow-up and document the response to financial referrals.",
            "priority": "medium",
        })

    legacy_support_level = _text(legacy_social.get("support_level")).lower()
    if (
        psychosocial.get("supportSystem") == "None"
        or psychosocial.get("socialInteraction") in {"Limited", "Isolated"}
        or legacy_support_level in {"limited", "none", "unknown", "declined", "declined to answer"}
    ):
        risk_flags.append("support_gap")
        findings.append({
            "category": "support_gap",
            "title": "Support-system limitation identified",
            "details": "The assessment indicates limited support or isolation that may require additional community linkage.",
            "severity": "moderate",
        })
        recommendations.append({
            "title": "Reassess caregiver/community support availability and capability.",
            "priority": "medium",
        })

    legacy_caregiver_burden = _text(legacy_caregiver.get("burden_level")).lower()
    legacy_caregiver_concerns = {
        _text(value).lower()
        for value in legacy_caregiver.get("caregiver_concerns") or []
    }
    if legacy_caregiver_burden in {"high", "severe"} or legacy_caregiver_concerns.intersection(
        {"burnout", "fatigue", "work-life strain"}
    ):
        risk_flags.append("caregiver_burden")
        findings.append({
            "category": "caregiver_burden",
            "title": "Caregiver burden elevated",
            "details": "Caregiver strain is significant and requires respite, education, or support-resource follow-up.",
            "severity": "high",
        })
        recommendations.append({
            "title": "Review caregiver capacity and offer respite, role support, and caregiver education resources.",
            "priority": "high",
        })

    legacy_notes = " ".join(
        [
            _text(legacy_social.get("notes")),
            _text(legacy_caregiver.get("respite_needs")),
            _text(legacy_risk.get("notes")),
            _text(legacy_interventions.get("intervention_plan")),
        ]
    ).lower()
    legacy_safety = _text(legacy_risk.get("safety_concerns")).lower()
    if legacy_safety in {"yes", "moderate", "high"} or "safety" in legacy_notes or "abuse" in legacy_notes:
        risk_flags.append("safety_concern")
        findings.append({
            "category": "safety_concern",
            "title": "Safety or abuse concern",
            "details": "Safety concerns or possible risk factors require interdisciplinary follow-up and escalation review.",
            "severity": "high",
        })
        recommendations.append({
            "title": "Escalate safety concerns through the clinical and social-work response pathway and document follow-up.",
            "priority": "high",
        })

    legacy_crisis = _text(legacy_risk.get("mental_health_crisis")).lower()
    if legacy_crisis in {"yes", "moderate", "high"} or "crisis" in legacy_notes:
        risk_flags.append("mental_health_crisis")
        findings.append({
            "category": "mental_health_crisis",
            "title": "Mental health or crisis risk",
            "details": "Mental-health crisis indicators may require urgent interdisciplinary coordination.",
            "severity": "high",
        })
        recommendations.append({
            "title": "Assess immediate crisis-support needs and escalate to the appropriate care-management workflow.",
            "priority": "high",
        })

    if psychosocial.get("mentalCompetency") in {"Impaired", "Unable to assess"}:
        risk_flags.append("decision_support")
        findings.append({
            "category": "mental_competency",
            "title": "Mental competency follow-up needed",
            "details": "Decision-making capacity is impaired or could not be assessed, requiring responsible-party and planning follow-up.",
            "severity": "moderate",
        })

    if psychosocial.get("spiritualIssuesConcern"):
        findings.append({
            "category": "spiritual_cross_reference",
            "title": "Spiritual concern cross-reference flagged",
            "details": "The assessment notes spiritual issues/concerns that should be coordinated with Spiritual/SCICA assessment follow-up.",
            "severity": "low",
        })
        recommendations.append({
            "title": "Coordinate chaplain/SCICA follow-up for spiritual issues or concerns.",
            "priority": "medium",
        })

    if referrals.get("communityProgram") == "Yes" and not _text(referrals.get("communityReferralSatisfaction")):
        missing.append("Referrals: response/satisfaction tracking")

    if _text(patient_distress.get("anxietyRating")) and not _text(patient_distress.get("anxietyRatedBy")):
        missing.append("Patient anxiety rated by")
    if _text(patient_distress.get("distressRating")) and not _text(patient_distress.get("distressRatedBy")):
        missing.append("Patient distress rated by")
    if _text(family_distress.get("pcgAnxietyRating")) and not _text(family_distress.get("pcgAnxietyRatedBy")):
        missing.append("PCG anxiety rated by")
    if not _text(psychosocial.get("responsiblePartyName")):
        missing.append("Responsible party name")
    if not _text(psychosocial.get("mentalCompetency")):
        missing.append("Mental competency evaluation")
    if not _text(psychosocial.get("literacyLanguageSkills")):
        missing.append("Literacy and language skills")

    if not findings:
        findings.append({
            "category": "no_urgent_social_risk",
            "title": "No acute psychosocial escalation identified",
            "details": "The current assessment does not indicate an unaddressed urgent MSW escalation based on the documented fields.",
            "severity": "low",
        })

    priority_rank = {"low": 0, "moderate": 1, "high": 2}
    overall_priority = max((finding.get("severity", "low") for finding in findings), key=lambda level: priority_rank.get(level, 0))

    return {
        "mode": "recommendation_only",
        "patient_id": patient_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "overall_priority": overall_priority,
            "finding_count": len(findings),
            "recommendation_count": len(recommendations),
            "missing_evidence_count": len(missing),
            "source_count": patient_evidence.get("source_count", 0) if patient_evidence else 0,
            "risk_flags": risk_flags,
        },
        "findings": findings,
        "recommendations": recommendations,
        "missing_evidence": missing,
        "evidence": {
            "assessment_text": " ".join(filter(None, [
                _text(psychosocial.get("notes")),
                _text(patient_distress.get("notes")),
                _text(family_distress.get("notes")),
                _text(financial_legal.get("notes")),
                _text(referrals.get("notes")),
            ])),
            "sections": [
                {"section": "psychosocial", "summary": _text(psychosocial.get("notes"))},
                {"section": "patientDistress", "summary": _text(patient_distress.get("notes"))},
                {"section": "familyDistress", "summary": _text(family_distress.get("notes"))},
                {"section": "financialLegal", "summary": _text(financial_legal.get("notes"))},
                {"section": "referrals", "summary": _text(referrals.get("notes"))},
            ],
            "patient_evidence": patient_evidence or {},
        },
    }
