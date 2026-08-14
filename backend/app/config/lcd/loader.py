import json
from pathlib import Path
from typing import Any, Dict, Optional


# Absolute source of truth for required LCD rule files ONLY
# (Do NOT include registry or metadata files here)
REQUIRED_LCD_FILES = {
    "als_end_stage.json",
    "cancer_metastatic.json",
    "dementia_alzheimers_senile_degeneration.json",
    "esrd_kidney_disease.json",
    "general_decline_terminal_status.json",
    "heart_failure_chf.json",
    "hiv_end_stage.json",
    "liver_disease_end_stage.json",
    "pulmonary_copd_respiratory_failure.json",
    "stroke_coma.json",
}


class LCDConfigError(RuntimeError):
    """Fatal startup error for LCD configuration problems."""


def load_lcd_configs(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate all required LCD JSON configuration files.

    Fails hard at startup if:
      - a required file is missing
      - JSON is invalid
      - required keys are missing
      - top-level structure is invalid

    Args:
        base_dir:
            Optional override for LCD directory (useful for tests).
            Defaults to the directory containing this module.

    Returns:
        Dict[str, Any]:
            Mapping of disease name -> LCD config object.
    """
    lcd_dir = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent

    if not lcd_dir.exists() or not lcd_dir.is_dir():
        raise LCDConfigError(f"LCD config directory not found: {lcd_dir}")

    found_files = {f.name for f in lcd_dir.glob("*.json")}

    # 1) Validate file presence
    missing_files = REQUIRED_LCD_FILES - found_files
    if missing_files:
        raise LCDConfigError(
            f"Missing required LCD config files: {sorted(missing_files)}"
        )

    lcd_configs: Dict[str, Any] = {}

    # 2) Load and validate each required file in deterministic order
    for file_name in sorted(REQUIRED_LCD_FILES):
        file_path = lcd_dir / file_name

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise LCDConfigError(f"Invalid JSON in {file_name}: {str(e)}") from e
        except OSError as e:
            raise LCDConfigError(f"Unable to read {file_name}: {str(e)}") from e

        if not isinstance(data, dict):
            raise LCDConfigError(f"{file_name} must contain a top-level JSON object")

        # 3) Minimal schema validation
        _validate_lcd_schema(file_name, data)

        disease = data["disease"]
        if disease in lcd_configs:
            raise LCDConfigError(
                f"Duplicate disease key '{disease}' found while loading {file_name}"
            )

        lcd_configs[disease] = data

    return lcd_configs


def _validate_lcd_schema(file_name: str, data: Dict[str, Any]) -> None:
    """
    Enforce non-negotiable LCD structure.

    This validates the common schema shared by all LCD JSON files.
    Disease-specific rule details should be validated in disease-specific loaders/rules,
    not forced globally here.
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

    if not isinstance(data["disease"], str) or not data["disease"].strip():
        raise LCDConfigError(f"{file_name} field 'disease' must be a non-empty string")

    if not isinstance(data["lcd_reference"], str) or not data["lcd_reference"].strip():
        raise LCDConfigError(f"{file_name} field 'lcd_reference' must be a non-empty string")

    if not isinstance(data["eligibility_result"], (dict, str)):
        raise LCDConfigError(f"{file_name} field 'eligibility_result' must be an object or string")

    if not isinstance(data["activation_rules"], dict):
        raise LCDConfigError(f"{file_name} field 'activation_rules' must be an object")

    if not isinstance(data["clinical_scores"], dict):
        raise LCDConfigError(f"{file_name} field 'clinical_scores' must be an object")

    if not isinstance(data["criteria_groups"], list):
        raise LCDConfigError(f"{file_name} field 'criteria_groups' must be a list")

    if not isinstance(data["source_document"], str) or not data["source_document"].strip():
        raise LCDConfigError(f"{file_name} field 'source_document' must be a non-empty string")
