from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_RULES_CACHE: Dict[str, Any] | None = None


def load_flag_rules() -> Dict[str, Any]:
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE

    base_dir = Path(__file__).resolve().parent.parent  # backend/app
    rules_path = base_dir / "config" / "flag_rules.v1.json"

    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    # minimal validation (enterprise-safe)
    if "rules" not in rules or not isinstance(rules["rules"], list):
        raise RuntimeError("flag_rules.v1.json must contain a top-level 'rules' list")

    _RULES_CACHE = rules
    return rules
