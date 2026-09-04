from __future__ import annotations

import re
from typing import Any

from app.services.eligibility.adl_dependency_service import (
    build_adl_evidence,
)

# =========================================================
# PUBLIC API
# =========================================================

_FAST_STAGE_ORDER = {
    "1": 10,
    "2": 20,
    "3": 30,
    "4": 40,
    "5": 50,
    "6a": 61,
    "6b": 62,
    "6c": 63,
    "6d": 64,
    "6e": 65,
    "7a": 71,
    "7b": 72,
    "7c": 73,
    "7d": 74,
    "7e": 75,
    "7f": 76,
}


def harvest_clinical_facts(patient: Any) -> dict[str, Any]:
    """
    Harvest normalized eligibility facts from patient-level clinical data.
    """

    facts = {
        "pps": None,
        "kps": None,
        "fast_stage": None,
        "fast_stage_rank": None,
        "fast_stage_at_or_beyond_7a": None,
        "nyha_class": None,
        "ecog_score": None,
        "kps_or_pps_lt_70": None,
        "kps_or_pps_declining": None,
        "adl_dependency_count": None,
        "adl_dependency_level": None,
        "ambulation_assistance_required": None,
        "dressing_assistance_required": None,
        "bathing_assistance_required": None,
        "incontinence_or_catheter_ostomy_dependency": None,
        "is_bedbound": None,
        "dysphagia": None,
        "aspiration_risk": None,
        "oral_intake_decline": None,
        "weight_loss_lbs": None,
        "weight_loss_percent_6_months": None,
        "continued_weight_loss": None,
        "serum_albumin": None,
        "fall_risk": None,
        "caregiver_stress": None,
        "communication_ability": None,
        "speech_pattern": None,
        "unable_meaningful_verbal_communication": None,
        "ejection_fraction": None,
        "fev1_percent_predicted": None,
        "po2": None,
        "o2_sat_percent": None,
        "pco2": None,
        "resting_tachycardia_gt_100": None,
        "cd4_count": None,
        "viral_load": None,
        "serum_creatinine": None,
        "creatinine_clearance": None,
        "gfr": None,
        "on_dialysis": None,
        "dialysis_for_comfort_only": None,
        "prognosis_unaltered_with_dialysis": None,
        "inr": None,
        "prothrombin_time_over_control_seconds": None,
        "coagulopathy_lab_criterion_met": None,
        "ascites_refractory": None,
        "spontaneous_bacterial_peritonitis": None,
        "hepatorenal_syndrome": None,
        "hepatic_encephalopathy_refractory": None,
        "recurrent_variceal_bleeding_despite_therapy": None,
        "progressive_malnutrition": None,
        "muscle_wasting": None,
        "active_alcoholism_over_80g_day": None,
        "hepatocellular_carcinoma": None,
        "hbsag_positive": None,
        "hepatitis_c_refractory_to_interferon": None,
        "disabling_dyspnea_at_rest": None,
        "bronchodilator_poor_response": None,
        "end_stage_pulmonary_progression": None,
        "pulmonary_er_visits_increasing": None,
        "pulmonary_infectious_hospitalizations": None,
        "respiratory_failure_history": None,
        "increasing_physician_home_visits": None,
        "serial_fev1_decline_gt_40_ml_year": None,
        "right_heart_failure_cor_pulmonale": None,
        "abnormal_brainstem_response": None,
        "absent_verbal_response": None,
        "absent_withdrawal_to_pain": None,
        "aspiration_pneumonia_12_months": None,
        "pyelonephritis_12_months": None,
        "septicemia_12_months": None,
        "stage_3_or_4_decubitus_12_months": None,
        "recurrent_fever_after_antibiotics_12_months": None,
        "cns_lymphoma": None,
        "wasting_syndrome": None,
        "mac_bacteremia": None,
        "pml": None,
        "systemic_lymphoma_advanced_hiv": None,
        "visceral_kaposi_unresponsive": None,
        "renal_failure_no_dialysis": None,
        "cryptosporidium_infection": None,
        "toxoplasmosis_unresponsive": None,
        "mechanical_ventilation": None,
        "autoimmune_disease": None,
        "heart_disease_comorbidity": None,
        "pulmonary_disease_comorbidity": None,
    }

    sources = _candidate_sources(patient)

    raw_pps = _first_value(
        sources,
        [
            "pps",
            "pps_score",
        ],
    )
    facts["pps"] = _normalize_score(raw_pps)

    raw_kps = _first_value(
        sources,
        [
            "kps",
            "kps_score",
        ],
    )
    facts["kps"] = _normalize_score(raw_kps)

    raw_fast_stage = _first_value(
        sources,
        [
            "fast",
            "fast_stage",
            "fast_score",
        ],
    )
    facts["fast_stage"] = _normalize_fast_stage(raw_fast_stage)
    facts["fast_stage_rank"] = _FAST_STAGE_ORDER.get(facts["fast_stage"])
    if facts["fast_stage_rank"] is not None:
        facts["fast_stage_at_or_beyond_7a"] = facts["fast_stage_rank"] >= _FAST_STAGE_ORDER["7a"]

    raw_nyha = _first_value(
        sources,
        [
            "nyha",
            "nyha_class",
        ],
    )
    facts["nyha_class"] = _normalize_nyha_class(raw_nyha)

    raw_ecog = _first_value(
        sources,
        [
            "ecog",
            "ecog_score",
            "ecog_score_current",
        ],
    )
    facts["ecog_score"] = _normalize_ecog_score(raw_ecog)

    if facts["kps"] is not None or facts["pps"] is not None:
        facts["kps_or_pps_lt_70"] = any(
            score is not None and score < 70
            for score in (facts["kps"], facts["pps"])
        )

    facts["kps_or_pps_declining"] = _to_bool(
        _first_value(
            sources,
            [
                "kps_or_pps_declining",
                "functional_decline",
                "functional_decline_present",
            ],
        )
    )

    explicit_adl_count = _normalize_int(
        _first_value(
            sources,
            [
                "adl_dependency_count",
            ],
        )
    )

    explicit_adl_level = _first_value(
        sources,
        [
            "adl_dependency_level",
            "adl_level",
        ],
    )

    adl_payload = (
        _first_value(
            sources,
            [
                "adls",
                "adl",
            ],
        )
        or {}
    )

    adl_evidence = build_adl_evidence(
        adl_payload if isinstance(adl_payload, dict) else {},
    )

    facts["adl_dependency_count"] = (
        explicit_adl_count
        if explicit_adl_count is not None
        else adl_evidence["adl_dependency_count"]
    )

    facts["adl_dependency_level"] = (
        explicit_adl_level
        if not _empty(explicit_adl_level)
        else adl_evidence["adl_dependency_level"]
    )

    mobility_status = _first_value(
        sources,
        [
            "ambulatory_status",
            "mobility_status",
            "mobility_ambulatory_status",
        ],
    )

    braden_activity = _normalize_int(
        _first_value(
            sources,
            [
                "activity",
                "braden_activity",
            ],
        )
    )

    facts["ambulation_assistance_required"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "ambulation_assistance_required",
                    "unable_to_ambulate_without_assistance",
                ],
            )
        ),
        _derive_ambulation_assistance(mobility_status),
    )

    facts["dressing_assistance_required"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "dressing_assistance_required",
                ],
            )
        ),
        _adl_score_at_least(adl_payload, "dressing", 3),
    )

    facts["bathing_assistance_required"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "bathing_assistance_required",
                ],
            )
        ),
        _adl_score_at_least(adl_payload, "bathing", 3),
    )

    urinary_status = _first_value(
        sources,
        [
            "urinary_status",
            "continence",
        ],
    )
    bowel_status = _first_value(
        sources,
        [
            "bowel_status",
        ],
    )
    catheter_present = _to_bool(
        _first_value(
            sources,
            [
                "catheter_present",
                "has_catheter",
            ],
        )
    )
    ostomy_present = _to_bool(
        _first_value(
            sources,
            [
                "ostomy_present",
                "has_ostomy",
            ],
        )
    )

    facts["incontinence_or_catheter_ostomy_dependency"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "incontinence_or_catheter_ostomy_dependency",
                ],
            )
        ),
        _derive_incontinence_dependency(
            urinary_status=urinary_status,
            bowel_status=bowel_status,
            catheter_present=catheter_present,
            ostomy_present=ostomy_present,
        ),
    )

    facts["is_bedbound"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "is_bedbound",
                    "bedbound",
                ],
            )
        ),
        _derive_bedbound(mobility_status, braden_activity),
    )

    swallowing_issues = _first_value(
        sources,
        [
            "swallowing_issues",
            "swallowingIssues",
        ],
    )

    facts["dysphagia"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "dysphagia",
                ],
            )
        ),
        _list_contains(swallowing_issues, "dysphagia"),
    )

    facts["aspiration_risk"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "aspiration_risk",
                    "current_pulmonary_aspiration",
                ],
            )
        ),
        _list_contains(swallowing_issues, "aspiration risk")
        or _list_contains(swallowing_issues, "coughing with swallowing"),
    )

    appetite = _first_value(
        sources,
        [
            "appetite",
        ],
    )
    fluid_intake = _first_value(
        sources,
        [
            "fluid_intake",
            "fluidIntake",
        ],
    )

    facts["oral_intake_decline"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "oral_intake_decline",
                ],
            )
        ),
        _derive_oral_intake_decline(appetite, fluid_intake),
    )

    weight_loss_raw = _first_value(
        sources,
        [
            "weight_loss_lbs",
            "weight_loss_past_six_months",
            "weight_loss_past_6_months",
            "weightLossPastSixMonths",
        ],
    )
    facts["weight_loss_lbs"] = _derive_weight_loss_lbs(weight_loss_raw)
    facts["weight_loss_percent_6_months"] = _derive_weight_loss_percent(weight_loss_raw)
    facts["continued_weight_loss"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "continued_weight_loss",
                ],
            )
        ),
        (
            (facts["weight_loss_lbs"] is not None and facts["weight_loss_lbs"] > 0)
            or (
                facts["weight_loss_percent_6_months"] is not None
                and facts["weight_loss_percent_6_months"] > 0
            )
        ),
    )

    facts["serum_albumin"] = _normalize_float(
        _first_value(
            sources,
            [
                "serum_albumin",
                "albumin",
            ],
        )
    )

    falls_last_90_days = _normalize_int(
        _first_value(
            sources,
            [
                "falls_last_90_days",
                "fallsLast90Days",
            ],
        )
    )
    facts["fall_risk"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "fall_risk",
                ],
            )
        ),
        falls_last_90_days is not None and falls_last_90_days > 0,
    )

    facts["caregiver_stress"] = _first_value(
        sources,
        [
            "caregiver_stress",
        ],
    )

    facts["communication_ability"] = _first_value(
        sources,
        [
            "communication_ability",
            "communication",
        ],
    )

    facts["speech_pattern"] = _first_value(
        sources,
        [
            "speech_pattern",
            "speech",
        ],
    )

    facts["unable_meaningful_verbal_communication"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "unable_meaningful_verbal_communication",
                ],
            )
        ),
        _derive_meaningful_communication_limitation(
            facts["communication_ability"],
            facts["speech_pattern"],
        ),
    )

    facts["ejection_fraction"] = _normalize_float(
        _first_value(
            sources,
            [
                "ejection_fraction",
                "ef",
                "lvef",
            ],
        )
    )

    facts["fev1_percent_predicted"] = _normalize_float(
        _first_value(
            sources,
            [
                "fev1_percent_predicted",
                "fev1_percent",
                "fev1",
            ],
        )
    )

    facts["po2"] = _normalize_float(
        _first_value(
            sources,
            [
                "po2",
                "pao2",
            ],
        )
    )

    facts["o2_sat_percent"] = _normalize_float(
        _first_value(
            sources,
            [
                "o2_sat_percent",
                "o2_saturation",
                "oxygen_saturation",
                "oxygenSaturation",
                "spo2",
                "sat_on_o2",
            ],
        )
    )

    facts["pco2"] = _normalize_float(
        _first_value(
            sources,
            [
                "pco2",
            ],
        )
    )

    pulse = _normalize_float(
        _first_value(
            sources,
            [
                "pulse",
                "heart_rate",
            ],
        )
    )
    facts["resting_tachycardia_gt_100"] = _coalesce_bool(
        _to_bool(
            _first_value(
                sources,
                [
                    "resting_tachycardia_gt_100",
                ],
            )
        ),
        pulse is not None and pulse > 100,
    )

    facts["cd4_count"] = _normalize_float(
        _first_value(
            sources,
            [
                "cd4_count",
                "cd4",
            ],
        )
    )

    facts["viral_load"] = _normalize_float(
        _first_value(
            sources,
            [
                "viral_load",
                "hiv_viral_load",
            ],
        )
    )

    facts["serum_creatinine"] = _normalize_float(
        _first_value(
            sources,
            [
                "serum_creatinine",
                "creatinine",
            ],
        )
    )

    facts["creatinine_clearance"] = _normalize_float(
        _first_value(
            sources,
            [
                "creatinine_clearance",
                "crcl",
            ],
        )
    )

    facts["gfr"] = _normalize_float(
        _first_value(
            sources,
            [
                "gfr",
                "egfr",
            ],
        )
    )

    facts["on_dialysis"] = _to_bool(
        _first_value(
            sources,
            [
                "on_dialysis",
                "dialysis_status",
                "dialysis",
            ],
        )
    )

    facts["dialysis_for_comfort_only"] = _to_bool(
        _first_value(
            sources,
            [
                "dialysis_for_comfort_only",
            ],
        )
    )

    facts["prognosis_unaltered_with_dialysis"] = _to_bool(
        _first_value(
            sources,
            [
                "prognosis_unaltered_with_dialysis",
            ],
        )
    )

    facts["inr"] = _normalize_float(
        _first_value(
            sources,
            [
                "inr",
            ],
        )
    )

    facts["prothrombin_time_over_control_seconds"] = _normalize_float(
        _first_value(
            sources,
            [
                "prothrombin_time_over_control_seconds",
                "prothrombin_time_seconds_over_control",
                "pt_seconds_over_control",
            ],
        )
    )

    if (
        facts["prothrombin_time_over_control_seconds"] is not None
        or facts["inr"] is not None
    ):
        facts["coagulopathy_lab_criterion_met"] = (
            (
                facts["prothrombin_time_over_control_seconds"] is not None
                and facts["prothrombin_time_over_control_seconds"] > 5
            )
            or (facts["inr"] is not None and facts["inr"] > 1.5)
        )

    for key, aliases in {
        "ascites_refractory": ["ascites_refractory"],
        "spontaneous_bacterial_peritonitis": ["spontaneous_bacterial_peritonitis"],
        "hepatorenal_syndrome": ["hepatorenal_syndrome"],
        "hepatic_encephalopathy_refractory": ["hepatic_encephalopathy_refractory"],
        "recurrent_variceal_bleeding_despite_therapy": ["recurrent_variceal_bleeding_despite_therapy"],
        "progressive_malnutrition": ["progressive_malnutrition"],
        "muscle_wasting": ["muscle_wasting"],
        "active_alcoholism_over_80g_day": ["active_alcoholism_over_80g_day"],
        "hepatocellular_carcinoma": ["hepatocellular_carcinoma"],
        "hbsag_positive": ["hbsag_positive", "hbsag"],
        "hepatitis_c_refractory_to_interferon": ["hepatitis_c_refractory_to_interferon"],
        "disabling_dyspnea_at_rest": ["disabling_dyspnea_at_rest"],
        "bronchodilator_poor_response": ["bronchodilator_poor_response"],
        "end_stage_pulmonary_progression": ["end_stage_pulmonary_progression"],
        "pulmonary_er_visits_increasing": ["pulmonary_er_visits_increasing"],
        "pulmonary_infectious_hospitalizations": ["pulmonary_infectious_hospitalizations"],
        "respiratory_failure_history": ["respiratory_failure_history", "respiratory_failure"],
        "increasing_physician_home_visits": ["increasing_physician_home_visits"],
        "serial_fev1_decline_gt_40_ml_year": ["serial_fev1_decline_gt_40_ml_year"],
        "right_heart_failure_cor_pulmonale": ["right_heart_failure_cor_pulmonale"],
        "abnormal_brainstem_response": ["abnormal_brainstem_response"],
        "absent_verbal_response": ["absent_verbal_response"],
        "absent_withdrawal_to_pain": ["absent_withdrawal_to_pain"],
        "aspiration_pneumonia_12_months": ["aspiration_pneumonia_12_months"],
        "pyelonephritis_12_months": ["pyelonephritis_12_months"],
        "septicemia_12_months": ["septicemia_12_months"],
        "stage_3_or_4_decubitus_12_months": ["stage_3_or_4_decubitus_12_months"],
        "recurrent_fever_after_antibiotics_12_months": ["recurrent_fever_after_antibiotics_12_months"],
        "cns_lymphoma": ["cns_lymphoma"],
        "wasting_syndrome": ["wasting_syndrome"],
        "mac_bacteremia": ["mac_bacteremia"],
        "pml": ["pml", "progressive_multifocal_leukoencephalopathy"],
        "systemic_lymphoma_advanced_hiv": ["systemic_lymphoma_advanced_hiv"],
        "visceral_kaposi_unresponsive": ["visceral_kaposi_unresponsive"],
        "renal_failure_no_dialysis": ["renal_failure_no_dialysis"],
        "cryptosporidium_infection": ["cryptosporidium_infection"],
        "toxoplasmosis_unresponsive": ["toxoplasmosis_unresponsive"],
        "mechanical_ventilation": ["mechanical_ventilation"],
        "autoimmune_disease": ["autoimmune_disease"],
        "heart_disease_comorbidity": ["heart_disease_comorbidity"],
        "pulmonary_disease_comorbidity": ["pulmonary_disease_comorbidity"],
    }.items():
        facts[key] = _to_bool(_first_value(sources, aliases))

    if facts["disabling_dyspnea_at_rest"] is None:
        components = [
            facts["bronchodilator_poor_response"] is True,
            (
                facts["fev1_percent_predicted"] is not None
                and facts["fev1_percent_predicted"] < 30
            ),
        ]
        if any(components):
            facts["disabling_dyspnea_at_rest"] = True

    if facts["end_stage_pulmonary_progression"] is None:
        components = [
            facts["pulmonary_er_visits_increasing"] is True,
            facts["pulmonary_infectious_hospitalizations"] is True,
            facts["respiratory_failure_history"] is True,
            facts["increasing_physician_home_visits"] is True,
            facts["serial_fev1_decline_gt_40_ml_year"] is True,
        ]
        if any(components):
            facts["end_stage_pulmonary_progression"] = True

    return facts


# =========================================================
# SOURCE DISCOVERY
# =========================================================

def _candidate_sources(patient: Any) -> list[dict[str, Any]]:
    """Collect possible fact containers."""

    sources: list[dict[str, Any]] = []

    if isinstance(patient, dict):
        sources.append(patient)

    if hasattr(patient, "__dict__"):
        sources.append(vars(patient))

    for attribute_name in (
        "assessment",
        "assessment_data",
        "clinical_data",
        "facts",
        "content",
        "functional_assessment",
        "functional_scores",
        "scores",
        "diagnoses",
        "performance_status",
        "performanceStatus",
        "nutrition",
        "respiratory",
        "genitourinary",
        "gastrointestinal",
        "musculoskeletal",
        "neurological",
        "skin",
        "vitals",
    ):
        value = getattr(patient, attribute_name, None)

        if isinstance(value, dict):
            sources.append(value)

    return sources


# =========================================================
# EXTRACTION HELPERS
# =========================================================

def _first_value(
    sources: list[dict[str, Any]],
    keys: list[str],
) -> Any:
    """Return first non-empty value found across all candidate sources."""

    for source in sources:
        value = _find_nested(source, keys)

        if not _empty(value):
            return value

    return None


def _find_nested(
    obj: Any,
    keys: list[str],
) -> Any:
    """Recursive nested search across dict/list payloads."""

    if isinstance(obj, dict):

        for key in keys:
            if key in obj and not _empty(obj[key]):
                return obj[key]

        normalized_lookup = {
            _normalize_key_name(existing_key): existing_key
            for existing_key in obj.keys()
            if isinstance(existing_key, str)
        }
        for key in keys:
            normalized_key = _normalize_key_name(key)
            existing_key = normalized_lookup.get(normalized_key)
            if existing_key is not None and not _empty(obj[existing_key]):
                return obj[existing_key]

        for value in obj.values():
            result = _find_nested(value, keys)

            if not _empty(result):
                return result

    elif isinstance(obj, list):

        for item in obj:
            result = _find_nested(item, keys)

            if not _empty(result):
                return result

    return None


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


def _normalize_score(value: Any) -> int | None:
    number = _normalize_float(value)
    if number is None:
        return None
    return int(round(number))


def _normalize_float(value: Any) -> float | None:
    if _empty(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None

    return None


def _normalize_int(value: Any) -> int | None:
    number = _normalize_float(value)
    if number is None:
        return None
    return int(round(number))


def _normalize_fast_stage(value: Any) -> str | None:
    if _empty(value):
        return None
    normalized = str(value).strip().lower().replace(" ", "")
    return normalized or None


def _normalize_nyha_class(value: Any) -> str | None:
    if _empty(value):
        return None
    normalized = str(value).strip().upper().replace("CLASS ", "")
    if normalized in {"1", "2", "3", "4"}:
        return {"1": "I", "2": "II", "3": "III", "4": "IV"}[normalized]
    if normalized in {"I", "II", "III", "IV"}:
        return normalized
    return normalized or None


def _normalize_ecog_score(value: Any) -> int | None:
    """ECOG performance status is an integer 0-5. Out-of-range values are
    treated as a normalization failure (returns None) rather than silently
    clamped, so the caller can distinguish MISSING from UNVERIFIED."""
    number = _normalize_int(value)
    if number is None:
        return None
    if number < 0 or number > 5:
        return None
    return number


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1", "present", "positive", "on"}:
            return True
        if normalized in {"false", "no", "n", "0", "absent", "negative", "off"}:
            return False
    return None


# =========================================================
# TYPED RUNTIME HARVESTER (Commit 2 of the clinical_runtime
# pipeline -- see app/domain/clinical_runtime/contracts.py)
# =========================================================
#
# harvest_clinical_facts() above remains the single source of truth for
# extraction logic. ClinicalEvidenceHarvester does not reimplement or
# duplicate that extraction -- it wraps its output into the typed
# ClinicalEvidenceBundle/ClinicalEvidenceItem contracts so downstream
# runtime stages (ontology resolution, functional assessment, terminal
# status, recertification) have a single well-typed input shape instead of
# an untyped dict.
#
# KNOWN LIMITATION (must not be silently "fixed" by fabricating data):
# harvest_clinical_facts() takes an opaque, duck-typed `patient` payload
# (dict / object with dict-like attributes) and has no database session and
# no reference to real ORM records. It therefore cannot supply true
# record-level provenance (source_id, source_recorded_at, source_author_id).
# ClinicalSourceReference.source_field is populated (which raw fact key
# produced the value); the remaining provenance fields are left None until a
# follow-up commit sources facts directly from real ORM models (the pattern
# already used in app/services/recertification_evidence_synthesis.py) rather
# than an opaque dict payload. Callers must not assume source_id/
# source_recorded_at are populated by this harvester today.

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
from typing import Optional as _Optional
from uuid import UUID as _UUID

from app.domain.clinical_runtime.contracts import (
    ClinicalEvidenceBundle,
    ClinicalEvidenceItem,
    ClinicalSourceReference,
    EvidenceStatus,
)

# Facts that represent a validated, ranged clinical scale. For these keys we
# distinguish "no value supplied" (MISSING) from "a value was supplied but
# failed normalization/range validation" (UNVERIFIED) -- see
# harvest_clinical_facts' _normalize_* helpers, none of which silently clamp
# an out-of-range value into something else.
_SCALE_FACT_KEYS = {
    "pps": ["pps", "pps_score"],
    "kps": ["kps", "kps_score"],
    "fast_stage": ["fast", "fast_stage", "fast_score"],
    "nyha_class": ["nyha", "nyha_class"],
    "ecog_score": ["ecog", "ecog_score", "ecog_score_current"],
}


@_dataclass(frozen=True)
class PatientEvidenceContext:
    """
    Explicit typed input to ClinicalEvidenceHarvester.harvest().

    `patient` is the same opaque duck-typed payload harvest_clinical_facts()
    already accepts (dict, or object exposing dict-like clinical-data
    attributes). It is intentionally left untyped here (Any is not imported
    to keep the boundary obvious) -- it is a legacy-shaped input being
    adapted into the typed pipeline, not a new contract.
    """

    patient_id: _UUID
    patient: Any
    encounter_id: _Optional[str] = None
    benefit_period_id: _Optional[_UUID] = None


class ClinicalEvidenceHarvester:
    """
    Typed wrapper around harvest_clinical_facts() producing a
    ClinicalEvidenceBundle for the clinical_runtime pipeline.

    Guarantees:
      - never returns an eligibility, prognosis, certification,
        recertification, or discharge conclusion (this class only classifies
        and packages facts; it draws no clinical conclusions)
      - deterministic ordering (items sorted by concept_code)
      - one evidence item per fact key (harvest_clinical_facts already
        dedupes across its candidate sources internally)
      - a present-but-unparseable scale value is reported as UNVERIFIED, not
        silently coerced to MISSING or to an apparently-valid DOCUMENTED value
    """

    def harvest(self, context: PatientEvidenceContext) -> ClinicalEvidenceBundle:
        facts = harvest_clinical_facts(context.patient)
        sources = _candidate_sources(context.patient)
        generated_at = _datetime.now(_timezone.utc)

        items: list[ClinicalEvidenceItem] = []
        for concept_code in sorted(facts.keys()):
            normalized_value = facts[concept_code]
            status = self._classify_status(concept_code, normalized_value, sources)

            source_reference = ClinicalSourceReference(
                source_type="STRUCTURED_FIELD",
                source_field=concept_code,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{context.patient_id}:{concept_code}",
                    patient_id=context.patient_id,
                    concept_code=concept_code,
                    canonical_name=concept_code,
                    status=status,
                    source_reference=source_reference,
                    encounter_id=context.encounter_id,
                    benefit_period_id=context.benefit_period_id,
                    observed_value=normalized_value,
                    normalized_value=normalized_value,
                    recorded_at=generated_at if normalized_value is not None else None,
                    extraction_method="STRUCTURED_FIELD_LOOKUP",
                )
            )

        return ClinicalEvidenceBundle(
            patient_id=context.patient_id,
            items=items,
            encounter_id=context.encounter_id,
            benefit_period_id=context.benefit_period_id,
            generated_at=generated_at,
        )

    @staticmethod
    def _classify_status(
        concept_code: str,
        normalized_value: Any,
        sources: list[dict[str, Any]],
    ) -> EvidenceStatus:
        if normalized_value is not None:
            return EvidenceStatus.DOCUMENTED

        raw_keys = _SCALE_FACT_KEYS.get(concept_code)
        if raw_keys is not None:
            raw_value = _first_value(sources, raw_keys)
            if not _empty(raw_value):
                # A raw value was supplied for this scale but normalization
                # rejected it (out of range / unparseable) -- this is a real
                # data-quality problem, not an absence of data.
                return EvidenceStatus.UNVERIFIED

        return EvidenceStatus.MISSING



def _coalesce_bool(*values: Any) -> bool | None:
    for value in values:
        if value is not None:
            return bool(value)
    return None


def _normalize_key_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _adl_score_at_least(adl_payload: Any, key: str, threshold: int) -> bool | None:
    if not isinstance(adl_payload, dict):
        return None
    score = _normalize_int(adl_payload.get(key))
    if score is None:
        return None
    return score >= threshold


def _derive_ambulation_assistance(mobility_status: Any) -> bool | None:
    if _empty(mobility_status):
        return None
    normalized = str(mobility_status).strip().lower()
    if normalized in {"assisted", "dependent", "bedbound"}:
        return True
    if normalized in {"independent", "supervised"}:
        return False
    return None


def _derive_bedbound(mobility_status: Any, braden_activity: int | None) -> bool | None:
    if not _empty(mobility_status):
        normalized = str(mobility_status).strip().lower()
        if normalized == "bedbound":
            return True
        if normalized in {"independent", "supervised", "assisted", "dependent"}:
            return False
    if braden_activity is not None:
        return braden_activity == 1
    return None


def _derive_incontinence_dependency(
    urinary_status: Any,
    bowel_status: Any,
    catheter_present: bool | None,
    ostomy_present: bool | None,
) -> bool | None:
    signals: list[bool] = []

    if not _empty(urinary_status):
        normalized = str(urinary_status).strip().lower()
        signals.append(
            normalized
            in {
                "stress incontinence",
                "urge incontinence",
                "functional incontinence",
                "total incontinence",
                "catheterized",
            }
        )

    if not _empty(bowel_status):
        signals.append(str(bowel_status).strip().lower() == "incontinent")

    if catheter_present is not None:
        signals.append(catheter_present)

    if ostomy_present is not None:
        signals.append(ostomy_present)

    return any(signals) if signals else None


def _list_contains(values: Any, needle: str) -> bool | None:
    if not isinstance(values, list):
        return None
    normalized_needle = needle.strip().lower()
    return any(str(item).strip().lower() == normalized_needle for item in values)


def _derive_oral_intake_decline(appetite: Any, fluid_intake: Any) -> bool | None:
    appetite_flag = None
    if not _empty(appetite):
        appetite_flag = str(appetite).strip().lower() in {"poor", "anorexic"}

    fluid_flag = None
    if not _empty(fluid_intake):
        fluid_flag = str(fluid_intake).strip().lower() in {"decreased", "minimal"}

    return _coalesce_bool(appetite_flag, fluid_flag)


def _derive_weight_loss_lbs(value: Any) -> float | None:
    if _empty(value):
        return None
    if isinstance(value, str) and "%" in value:
        return None
    return _normalize_float(value)


def _derive_weight_loss_percent(value: Any) -> float | None:
    if _empty(value):
        return None
    if isinstance(value, str) and "%" not in value:
        return None
    return _normalize_float(value)


def _derive_meaningful_communication_limitation(
    communication_ability: Any,
    speech_pattern: Any,
) -> bool | None:
    candidates = [communication_ability, speech_pattern]
    decisions: list[bool] = []
    for candidate in candidates:
        if _empty(candidate):
            continue
        normalized = str(candidate).strip().lower()
        if any(
            phrase in normalized
            for phrase in (
                "non-verbal",
                "unable",
                "unintelligible",
                "stereotyped",
                "stereotypical",
                "few words",
                "six or fewer",
            )
        ):
            decisions.append(True)
        elif any(
            phrase in normalized
            for phrase in ("normal", "clear", "meaningful", "intact")
        ):
            decisions.append(False)
    return decisions[0] if decisions else None
