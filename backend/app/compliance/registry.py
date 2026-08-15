from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from app.compliance.types import Regulator


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


# Map folder -> regulator code
REGULATOR_FOLDERS: Dict[str, Regulator] = {
    "cms": "CMS",
    "achc": "ACHC",
    "cdph": "CDPH",
    "tjc": "TJC",
    "chap": "CHAP",
}


def _import_module_from_file(file_path: Path):
    """
    Dynamically import a Python file as a module.

    Returns:
        The imported module object, or None if import failed.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module_rules(module) -> List[Any]:
    """
    Extract rules from a Python module.

    Supported patterns:
    - module.RULES -> list
    - module.get_rules() -> list
    """
    if hasattr(module, "RULES"):
        rules = getattr(module, "RULES")
        if isinstance(rules, list):
            return rules

    if hasattr(module, "get_rules"):
        rules = module.get_rules()
        if isinstance(rules, list):
            return rules

    return []


def _load_yaml_rulepack(file_path: Path, regulator: Regulator) -> Any:
    """
    Load a YAML rule/config pack.

    Returns:
        - dict for a standard rule/config pack
        - list if the YAML file itself contains a list
        - None on load failure
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.exception(
            "RULE_LOAD_ERROR_YAML",
            extra={
                "file": str(file_path),
                "regulator": regulator,
                "error": str(e),
            },
        )
        return None

    if data is None:
        return None

    # Attach metadata only if this is a dict
    if isinstance(data, dict):
        data.setdefault("source", regulator)
        data.setdefault("_file", file_path.name)

    return data


def load_active_rulepacks() -> Dict[Regulator, List[Any]]:
    """
    Dynamically discover and load all active rule/config packs.

    Supported:
    - YAML rule/config files (*.yaml, *.yml)
    - Python rule modules (*.py) exposing RULES or get_rules()

    No hardcoded imports.
    No manual registration.

    Returns:
        Dict[Regulator, List[Any]]
    """
    active_rulepacks: Dict[Regulator, List[Any]] = {
        "CMS": [],
        "ACHC": [],
        "CDPH": [],
        "TJC": [],
        "CHAP": [],
    }

    for folder_name, regulator in REGULATOR_FOLDERS.items():
        folder_path = BASE_DIR / folder_name

        if not folder_path.exists():
            continue

        # 1) Load YAML/YML packs first (rules/config)
        for file_path in sorted(folder_path.glob("*.yaml")):
            data = _load_yaml_rulepack(file_path, regulator)
            if data is None:
                continue

            if isinstance(data, list):
                active_rulepacks[regulator].extend(data)
            else:
                active_rulepacks[regulator].append(data)

        for file_path in sorted(folder_path.glob("*.yml")):
            data = _load_yaml_rulepack(file_path, regulator)
            if data is None:
                continue

            if isinstance(data, list):
                active_rulepacks[regulator].extend(data)
            else:
                active_rulepacks[regulator].append(data)

        # 2) Load Python rule modules (RULES/get_rules)
        for file_path in sorted(folder_path.glob("*.py")):
            if file_path.name.startswith("_") or file_path.name == "__init__.py":
                continue

            module = _import_module_from_file(file_path)
            if module is None:
                continue

            try:
                rules = _load_module_rules(module)
                if rules:
                    active_rulepacks[regulator].extend(rules)
            except Exception as e:
                logger.exception(
                    "RULE_LOAD_ERROR_PY",
                    extra={
                        "file": str(file_path),
                        "regulator": regulator,
                        "error": str(e),
                    },
                )

    return active_rulepacks


def load_all_rules() -> List[Any]:
    """
    Flatten all active rule/config packs into a single list.
    Useful for diagnostics or global inspection.
    """
    packs = load_active_rulepacks()
    all_rules: List[Any] = []

    for regulator in ("CMS", "ACHC", "CDPH", "TJC", "CHAP"):
        all_rules.extend(packs.get(regulator, []))

    return all_rules


def load_cms_rules() -> List[Any]:
    """
    Backward compatibility helper for legacy modules.

    Returns:
        List[Any] of active CMS rule/config packs.
    """
    rulepacks = load_active_rulepacks()
    return rulepacks.get("CMS", [])