import json
from pathlib import Path

from app.config.lcd.loader import load_lcd_configs

LCD_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "lcd" / "ca_hospice_lcds.json"


def _hydrate_registry(data):
    configs = load_lcd_configs()
    diseases = sorted(config["disease"] for config in configs.values())
    lcd = data.setdefault("lcds", [{}])[0]
    lcd.setdefault("diagnosis_groups", diseases)
    lcd.setdefault("general_decline_criteria", [
        "KPS or PPS less than 70",
        "decline in functional status",
        "2+ ADLs dependent",
    ])
    lcd.setdefault("disease_specific_criteria", [
        config.get("lcd_reference", config["disease"]) for config in configs.values()
    ])
    lcd.setdefault("required_documentation", [
        "Primary diagnosis documentation",
        "Clinical decline summary",
        "Disease-specific LCD documentation",
    ])
    return data


def load_ca_hospice_lcds():
    with open(LCD_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _hydrate_registry(data)