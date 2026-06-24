from pathlib import Path
import json


def load_cms_rules() -> dict:
    rules_path = Path(__file__).resolve().parent / "cms" / "cms_rules.json"

    if not rules_path.exists():
        return {}

    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)