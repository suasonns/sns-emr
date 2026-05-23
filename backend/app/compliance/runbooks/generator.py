from pathlib import Path
from typing import List, Dict, Any

from app.compliance.registry import ACTIVE_RULEPACKS
from app.compliance.runbooks.templates import render_rule_markdown
from app.tenants.loader import load_policy_mapping

# -----------------------------
# Configuration
# -----------------------------

OUTPUT_DIR = Path("app/compliance/runbooks/out")

# NOTE:
# This is intentionally static for now.
# It will later be resolved from tenant_id.
TENANT_SLUG = "love_and_faith"


# -----------------------------
# Helpers
# -----------------------------

def find_policy_refs(rule_code: str, tenant_policies: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Locate tenant PP / HR policies that map to a given system rule.
    """
    matches: List[Dict[str, str]] = []

    policy_mapping = tenant_policies.get("policy_mapping", {})

    for section in ("PP", "HR"):
        for policy_id, policy in policy_mapping.get(section, {}).items():
            if rule_code in policy.get("system_rules", []):
                matches.append(
                    {
                        "section": section,
                        "policy_id": policy_id,
                        "policy_number": policy.get("policy_number", ""),
                        "title": policy.get("title", ""),
                    }
                )

    return matches


# -----------------------------
# Main generator
# -----------------------------

def generate_runbooks() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tenant_policies = load_policy_mapping(TENANT_SLUG)

    for regulator, modules in ACTIVE_RULEPACKS.items():
        lines: List[str] = [
            f"# {regulator} Compliance Runbook\n\n",
            "This runbook is generated directly from active compliance rules.\n",
            "It reflects enforced system behavior.\n\n",
        ]

        for module in modules:
            rule = getattr(module, "RULE", None)
            if rule is None:
                continue

            # Core rule content
            lines.append(render_rule_markdown(rule))

            # Tenant policy mapping
            policy_refs = find_policy_refs(rule.code, tenant_policies)
            if policy_refs:
                lines.append("\n### Tenant Policy Mapping\n")
                for p in policy_refs:
                    lines.append(
                        f"- **{p['section']} Policy {p['policy_number']}** — "
                        f"{p['title']} (Policy ID: {p['policy_id']})\n"
                    )

            lines.append("\n")

        output_file = OUTPUT_DIR / f"{regulator.lower()}_runbook.md"
        output_file.write_text("".join(lines), encoding="utf-8")


# -----------------------------
# Entrypoint
# -----------------------------

if __name__ == "__main__":
    generate_runbooks()
    print(f"Runbooks generated in: {OUTPUT_DIR.resolve()}")