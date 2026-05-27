import json
from pathlib import Path
from typing import Dict, Any, Optional


# Absolute source of truth for required LCD files
REQUIRED_LCD_FILES = {
    "cancer_metastatic.json",
    "heart_failure_chf.json",
    "pulmonary_copd_respiratory_failure.json",
    "esrd_kidney_disease.json",
    "dementia_alzheimers_senile_degeneration.json",
    "als_end_stage.json",
    "stroke_coma.json",
    "hiv_end_stage.json",
    "liver_disease_end_stage.json",
    "general_decline_terminal_status.json",
}


class LCDConfigError(RuntimeError):
    """Fatal startup error for LCD configuration problems."""


def load_lcd_configs(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads and validates all LCD JSON configuration files.

    Fails hard at startup if:
      - a required file is missing
      - JSON is invalid
      - required keys are missing

    base_dir:
      - Optional override for LCD directory (required for unit tests)
      - Defaults to the directory containing this module
    """
    lcd_dir = Path(base_dir) if base_dir is not None else Path(__file__).parent

    if not lcd_dir.exists() or not lcd_dir.is_dir():
        raise LCDConfigError(f"LCD config directory not found: {lcd_dir}")

    found_files = {f.name for f in lcd_dir.glob("*.json")}

    # 1️⃣ Validate file presence
    missing_files = REQUIRED_LCD_FILES - found_files
    if missing_files:
        raise LCDConfigError(
            f"Missing required LCD config files: {sorted(missing_files)}"
        )

    lcd_configs: Dict[str, Any] = {}

    # 2️⃣ Load and validate each file
    for file_name in REQUIRED_LCD_FILES:
        file_path = lcd_dir / file_name

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise LCDConfigError(
                f"Invalid JSON in {file_name}: {str(e)}"
            )

        # 3️⃣ Minimal schema validation (compliance‑critical)
        _validate_lcd_schema(file_name, data)

        lcd_configs[data["disease"]] = data

    return lcd_configs


def _validate_lcd_schema(file_name: str, data: Dict[str, Any]) -> None:
    """
    Enforces non‑negotiable LCD structure.
    This prevents silent survey risk.
    """
    required_top_level_keys = {
        "disease",
        "lcd_reference",
        "eligibility_result",
        "activation_rules",
        "clinical_scores",
        "criteria_groups",
        "source_document",
    }

    missing_keys = required_top_level_keys - data.keys()
    if missing_keys:
        raise LCDConfigError(
            f"{file_name} missing required keys: {sorted(missing_keys)}"
        )

    # activation_rules must explicitly define FAST and NYHA
    activation = data["activation_rules"]
    for key in ("FAST", "NYHA"):
        if key not in activation:
            raise LCDConfigError(
                f"{file_name} activation_rules missing '{key}'"
            )

    # criteria_groups must be a list
    if not isinstance(data["criteria_groups"], list):
        raise LCDConfigError(
            f"{file_name} criteria_groups must be a list"
        )