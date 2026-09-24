"""
Checkpoint 1 / Defect A1 regression coverage.

RNICA_IMPLEMENTATION_AUTHORITY.md (Locked product decisions, §5) states:

    "PPS and KPS are always visible; FAST/ECOG/NYHA are diagnosis-conditional
    (dementia / oncology-metastatic-hematologic / CHF-cardiomyopathy
    respectively) -- enforced server-side today only for FAST and NYHA ...
    ECOG has no equivalent enforcement branch -- confirmed open defect."

These tests exercise `_validate_required_functional_assessments` directly
(the exact function/line range cited by that authority document) to prove:

1. The defect as documented: an oncology-diagnosis RN ICA note with no
   ECOG value historically produced no missing-field warning (regression
   guard: this test would have failed before the fix).
2. The fix: ECOG is now enforced the same way FAST/NYHA already are --
   required only when clinically relevant (oncology diagnosis) and only
   for the formal RN ICA/Update/Recertification workflows, never for
   routine/PRN visits.
3. No regression to the existing FAST (dementia) / NYHA (cardiac)
   enforcement branches.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.clinical_note_validation_engine import (
    _validate_required_functional_assessments,
    _validate_required_rn_ica_sections,
)


def _make_note(discipline: str = "RN", note_type: str = "RN_ICA") -> SimpleNamespace:
    # SimpleNamespace only exposes the attributes given here, so
    # `_note_value`'s `hasattr(note, key)` check falls through to `content`
    # for every other classification key (form_key/form_type/assessment_type/
    # visit_type), matching how a real ClinicalNote with those columns unset
    # behaves.
    return SimpleNamespace(discipline=discipline, note_type=note_type)


def _run(content: dict, assessment: dict | None = None):
    note = _make_note()
    warnings: list[str] = []
    audit_flags: list[str] = []
    compliance_blocking_items: list[dict] = []

    _validate_required_functional_assessments(
        note,
        content,
        assessment or {},
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    return warnings, audit_flags


def test_ecog_required_when_oncology_diagnosis_and_missing():
    """A1 defect reproduction: oncology diagnosis, no ECOG documented."""
    content = {
        "pps": "50",
        "kps": "50",
        "primary_diagnosis": "Metastatic lung cancer with malignant pleural effusion",
    }

    warnings, audit_flags = _run(content)

    assert "functional_assessment_missing:ecog" in warnings
    assert "functional_assessment_missing" in audit_flags


def test_ecog_satisfied_when_oncology_diagnosis_and_documented():
    content = {
        "pps": "50",
        "kps": "50",
        "primary_diagnosis": "Metastatic breast carcinoma",
        "ecog": "2",
    }

    warnings, _ = _run(content)

    assert "functional_assessment_missing:ecog" not in warnings


def test_ecog_not_required_without_oncology_diagnosis():
    """ECOG must remain diagnosis-conditional, not universally required."""
    content = {
        "pps": "50",
        "kps": "50",
        "primary_diagnosis": "End stage COPD",
    }

    warnings, _ = _run(content)

    assert "functional_assessment_missing:ecog" not in warnings


def test_fast_still_required_for_dementia_no_regression():
    content = {
        "pps": "50",
        "kps": "50",
        "primary_diagnosis": "Alzheimer's dementia, advanced stage",
    }

    warnings, _ = _run(content)

    assert "functional_assessment_missing:fast" in warnings
    assert "functional_assessment_missing:ecog" not in warnings


def test_nyha_still_required_for_cardiac_no_regression():
    content = {
        "pps": "50",
        "kps": "50",
        "primary_diagnosis": "End stage congestive heart failure",
    }

    warnings, _ = _run(content)

    assert "functional_assessment_missing:nyha" in warnings
    assert "functional_assessment_missing:ecog" not in warnings


def test_no_functional_scores_required_outside_formal_rn_ica_workflow():
    """Routine/PRN visits are exempt, per the existing docstring contract."""
    note = SimpleNamespace(discipline="RN", note_type="ROUTINE_VISIT")
    content = {"primary_diagnosis": "Metastatic lung cancer"}
    warnings: list[str] = []
    audit_flags: list[str] = []
    compliance_blocking_items: list[dict] = []

    _validate_required_functional_assessments(
        note,
        content,
        {},
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    assert warnings == []
    assert audit_flags == []


# ---------------------------------------------------------------------------
# ACP six-field parity (product decision, RNICA_ACP_SIX_FIELD_RECONCILIATION_
# DECISION.md): CPR/Life-Sustaining/Hospitalization Discussion Status are now
# hard-required alongside their existing Preference/Code-Status counterparts.
# The requirement is satisfied by ANY documented status (including "not
# discussed" / "declined" / "unable") -- only a missing value is a gap.
# ---------------------------------------------------------------------------

def _run_rn_ica_sections(assessment: dict):
    note = SimpleNamespace(discipline="RN", note_type="RN_ICA")
    content: dict = {}
    warnings: list[str] = []
    audit_flags: list[str] = []
    compliance_blocking_items: list[dict] = []

    _validate_required_rn_ica_sections(
        note,
        content,
        assessment,
        warnings,
        audit_flags,
        compliance_blocking_items,
    )

    return warnings


def _full_acp_assessment(**overrides):
    assessment = {
        "diagnoses": {
            "primaryDiagnosis": "Terminal diagnosis",
            "lcdEligibilityNarrative": "Documented decline per LCD criteria.",
            "diseaseTrajectory": "Progressive decline",
        },
        "finalization": {"clinicalNarrative": "Narrative present"},
        "performanceStatus": {"pps": "50", "kps": "50"},
        "pain": {"verbalizesPain": "No"},
        "advancedCarePlanning": {
            "codeStatus": "Full Code",
            "cprPreferenceAskedStatus": "1",
            "lifeSustainingAskedStatus": "1",
            "lifeSustainingTreatmentPreference": "Undecided",
            "hospitalizationAskedStatus": "1",
            "hospitalizationPreference": "Undecided",
        },
    }
    for key, value in overrides.items():
        assessment["advancedCarePlanning"][key] = value
    return assessment


def test_acp_discussion_status_missing_is_flagged():
    assessment = _full_acp_assessment(cprPreferenceAskedStatus="")
    warnings = _run_rn_ica_sections(assessment)

    assert any(
        "advancedCarePlanning.cprPreferenceAskedStatus" in w for w in warnings
    )


def test_acp_documented_non_discussion_status_satisfies_requirement():
    """A documented 'declined'/'unable'/'not discussed' status is complete --
    RNICA must not require that a discussion actually occurred."""
    assessment = _full_acp_assessment(
        cprPreferenceAskedStatus="0",
        lifeSustainingAskedStatus="2",
        hospitalizationAskedStatus="0",
    )
    warnings = _run_rn_ica_sections(assessment)

    assert not any("advancedCarePlanning" in w for w in warnings)


def test_acp_all_six_fields_required_when_missing():
    assessment = _full_acp_assessment(
        cprPreferenceAskedStatus="",
        lifeSustainingAskedStatus="",
        hospitalizationAskedStatus="",
    )
    warnings = _run_rn_ica_sections(assessment)

    assert any("cprPreferenceAskedStatus" in w for w in warnings)
    assert any("lifeSustainingAskedStatus" in w for w in warnings)
    assert any("hospitalizationAskedStatus" in w for w in warnings)
