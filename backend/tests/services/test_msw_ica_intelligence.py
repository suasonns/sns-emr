from app.services.msw_ica_intelligence import build_msw_ica_intelligence


def test_build_msw_ica_intelligence_flags_high_risk_context():
    payload = {
        "social": {
            "support_level": "Limited",
            "concerns": ["Isolation", "Caregiver burden"],
            "notes": "Patient reports little engagement and lacking support.",
        },
        "caregiver": {
            "burden_level": "High",
            "caregiver_concerns": ["Burnout", "Transportation"],
            "respite_needs": "Needs respite and caregiver education",
        },
        "risk": {
            "financial_stress": "High",
            "housing_insecurity": "Moderate",
            "social_isolation": "High",
            "anger_or_conflict": "Moderate",
            "safety_concerns": "High",
            "mental_health_crisis": "Moderate",
            "transportation_barrier": "High",
            "notes": "Safety concern due to family conflict and transportation barriers.",
        },
        "interventions": {
            "referral_type": "MSW",
            "priority_level": "Urgent",
            "intervention_plan": "Arrange crisis follow-up and caregiver support plan.",
        },
    }

    result = build_msw_ica_intelligence(payload, patient_id="5d31a53f-eebd-468f-bcb6-1b43771fe113")

    assert result["summary"]["overall_priority"] == "high"
    assert any(f["category"] == "support_gap" for f in result["findings"])
    assert any(f["category"] == "caregiver_burden" for f in result["findings"])
    assert any(f["category"] == "safety_concern" for f in result["findings"])
    assert len(result["recommendations"]) >= 3


def test_build_msw_ica_intelligence_uses_default_low_risk_when_clear():
    result = build_msw_ica_intelligence(
        {
            "social": {"support_level": "Strong", "concerns": []},
            "caregiver": {"burden_level": "Low", "caregiver_concerns": []},
            "risk": {"financial_stress": "Low", "social_isolation": "No", "anger_or_conflict": "No"},
            "interventions": {"referral_type": "", "intervention_plan": "Monitor and continue support."},
        },
        patient_id="5d31a53f-eebd-468f-bcb6-1b43771fe113",
    )

    assert result["summary"]["overall_priority"] == "low"
    assert result["findings"][0]["category"] == "no_urgent_social_risk"
