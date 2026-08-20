import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.api.eligibility.routes import (
    LCDEvaluateRequest,
    detect_lcd_rule,
    evaluate_lcd,
    get_lcd_rule_config,
)
from app.config.lcd.loader import load_lcd_configs, LCDConfigError
from app.services.eligibility.engine import (
    evaluate_hospice_eligibility,
    evaluate_lcd_criteria,
)
from app.services.eligibility.lcd_loader import load_ca_hospice_lcds


def test_general_decline_config_is_loaded():
    configs = load_lcd_configs()
    assert "GENERAL_DECLINE_TERMINAL_STATUS" in configs

    cfg = configs["GENERAL_DECLINE_TERMINAL_STATUS"]
    assert cfg["disease"] == "GENERAL_DECLINE_TERMINAL_STATUS"
    assert "criteria_groups" in cfg


def test_ca_registry_contains_live_disease_families():
    registry = load_ca_hospice_lcds()
    disease_groups = registry["lcds"][0]["diagnosis_groups"]
    assert "HEART_FAILURE" in disease_groups
    assert "STROKE_COMA" in disease_groups
    assert "CANCER_METASTATIC" in disease_groups


def test_hospice_engine_selects_the_matching_disease_guideline():
    patient = SimpleNamespace(
        id="pt-123",
        tenant_id="tenant-1",
        primary_diagnosis_description="CHF with edema and dyspnea",
        primary_diagnosis_code="I50.9",
        kps=30,
        pps=30,
    )

    result = evaluate_hospice_eligibility(patient, admission_date="2026-01-01")
    assert result["selected_guideline"] == "HEART_FAILURE"
    assert result["lcd_id"] == "L33393"
    assert "source_document" in result


def test_lcd_evaluate_route_returns_guideline_result():
    response = evaluate_lcd(
        LCDEvaluateRequest(
            patient={
                "id": "pt-123",
                "tenant_id": "tenant-1",
                "primary_diagnosis_description": "CHF with edema and dyspnea",
                "primary_diagnosis_code": "I50.9",
                "kps": 30,
                "pps": 30,
            },
            admission_date="2026-01-01",
        ),
        db=None,
    )

    assert response["selected_guideline"] == "HEART_FAILURE"
    assert response["lcd_id"] == "L33393"


def test_lcd_detect_and_config_routes_return_matching_rules():
    detected = detect_lcd_rule(text="advanced CHF with dyspnea", db=None)
    assert detected["disease"] == "HEART_FAILURE"

    config = get_lcd_rule_config("HEART_FAILURE", db=None)
    assert config["disease"] == "HEART_FAILURE"
    assert config["criteria_groups"][0]["group_name"] == "Untreatable Condition"


def test_heart_failure_rule_is_not_always_true_without_manual_answers():
    guideline = load_lcd_configs()["HEART_FAILURE"]

    result = evaluate_lcd_criteria(
        guideline,
        facts={
            "nyha_class": "IV",
            "criteria_answers": {"HEART_FAILURE": {}},
        },
    )

    assert result["eligible"] is False
    assert result["group_results"][0]["passed"] is False
    assert result["group_results"][1]["passed"] is True


def test_heart_failure_rule_passes_when_required_path_is_satisfied():
    guideline = load_lcd_configs()["HEART_FAILURE"]

    result = evaluate_lcd_criteria(
        guideline,
        facts={
            "nyha_class": "IV",
            "criteria_answers": {"HEART_FAILURE": {"1a": True}},
        },
    )

    assert result["eligible"] is True


def test_als_requires_group_one_and_one_of_groups_two_or_three():
    guideline = load_lcd_configs()["ALS_END_STAGE"]

    result = evaluate_lcd_criteria(
        guideline,
        facts={
            "oral_intake_decline": True,
            "continued_weight_loss": True,
            "criteria_answers": {
                "ALS_END_STAGE": {
                    "1a": True,
                    "1b": True,
                    "1c": True,
                    "1d": True,
                    "2c": True,
                    "2d": True,
                }
            },
        },
    )

    assert result["eligible"] is True

    missing_support = evaluate_lcd_criteria(
        guideline,
        facts={
            "criteria_answers": {
                "ALS_END_STAGE": {
                    "1a": True,
                    "1b": True,
                    "1c": True,
                    "1d": True,
                }
            },
        },
    )

    assert missing_support["eligible"] is False


def test_stroke_coma_rule_supports_coma_path():
    guideline = load_lcd_configs()["STROKE_COMA"]

    result = evaluate_lcd_criteria(
        guideline,
        facts={
            "kps": 30,
            "pps": 30,
            "criteria_answers": {
                "STROKE_COMA": {
                    "3a": True,
                    "3b": True,
                    "3c": True,
                }
            },
        },
    )

    assert result["eligible"] is True


def test_loader_fails_when_general_decline_missing(tmp_path):
    # Requires load_lcd_configs(base_dir=...) support in loader
    lcd_dir = tmp_path / "lcd"
    lcd_dir.mkdir()

    def write_stub(name: str):
        (lcd_dir / name).write_text(json.dumps({
            "disease": name.replace(".json", "").upper(),
            "lcd_reference": "TEST",
            "eligibility_result": "PENDING",
            "activation_rules": {},
            "clinical_scores": {},
            "criteria_groups": [],
            "source_document": "TEST"
        }), encoding="utf-8")

    # Create all required files except general decline
    required = {
        "cancer_metastatic.json",
        "heart_failure_chf.json",
        "pulmonary_copd_respiratory_failure.json",
        "esrd_kidney_disease.json",
        "dementia_alzheimers_senile_degeneration.json",
        "als_end_stage.json",
        "stroke_coma.json",
        "hiv_end_stage.json",
        "liver_disease_end_stage.json",
        # Intentionally omit:
        # "general_decline_terminal_status.json"
    }

    for f in required:
        write_stub(f)

    with pytest.raises(LCDConfigError):
        load_lcd_configs(base_dir=lcd_dir)