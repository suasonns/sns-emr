import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.api.eligibility.routes import LCDEvaluateRequest, evaluate_lcd
from app.config.lcd.loader import load_lcd_configs, LCDConfigError
from app.services.eligibility.engine import evaluate_hospice_eligibility
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