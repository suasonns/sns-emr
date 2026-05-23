from pathlib import Path
import yaml


TENANTS_ROOT = Path(__file__).parent


def load_policy_mapping(tenant_slug: str) -> dict:
    """
    Loads tenant policy mapping YAML.
    This is read-only configuration (not runtime data).
    """
    policy_file = TENANTS_ROOT / tenant_slug / "policy_mapping.yaml"

    if not policy_file.exists():
        return {}

    with policy_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}