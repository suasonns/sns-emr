import json
from pathlib import Path
import pytest

from app.config.lcd.loader import load_lcd_configs, LCDConfigError


def test_general_decline_config_is_loaded():
    configs = load_lcd_configs()
    assert "GENERAL_DECLINE_TERMINAL_STATUS" in configs

    cfg = configs["GENERAL_DECLINE_TERMINAL_STATUS"]
    assert cfg["disease"] == "GENERAL_DECLINE_TERMINAL_STATUS"
    assert "criteria_groups" in cfg


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