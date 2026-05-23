from __future__ import annotations

from typing import Dict, List, Optional, Type

from sqlalchemy.orm import Session

from app.rules.base import Workflow, BaseRule
from app.models.tenant_rule_toggle import TenantRuleToggle

# Rule imports (explicit only — NO auto-discovery)
from app.rules.diagnosis.prohibited_primary_dx_prefix import ProhibitedPrimaryDxPrefixRule
from app.rules.eligibility.chf_readiness import CHFReadinessRule
from app.rules.eligibility.copd_readiness import COPDReadinessRule
from app.rules.eligibility.esrd_readiness import ESRDReadinessRule


# ------------------------------------------------------------------
# Rule class registry: rule_id -> rule class
# ------------------------------------------------------------------
RULE_CLASS_REGISTRY: Dict[str, Type[BaseRule]] = {
    "DX_PRIMARY_PREFIX_DENY": ProhibitedPrimaryDxPrefixRule,
    "CHF_AUDIT_READINESS": CHFReadinessRule,
    "COPD_AUDIT_READINESS": COPDReadinessRule,
    "ESRD_AUDIT_READINESS": ESRDReadinessRule,
}

# ------------------------------------------------------------------
# Mandatory rules (owner-controlled; never toggleable)
# ------------------------------------------------------------------
MANDATORY_RULE_IDS = {
    "DX_PRIMARY_PREFIX_DENY",
}

# ------------------------------------------------------------------
# Default rules when tenant context is unavailable (dev-only fallback)
# ------------------------------------------------------------------
DEFAULT_RULES_BY_WORKFLOW: Dict[Workflow, List[str]] = {
    Workflow.ADMISSION: [
        "DX_PRIMARY_PREFIX_DENY",
        "CHF_AUDIT_READINESS",
        "COPD_AUDIT_READINESS",
        "ESRD_AUDIT_READINESS",
    ],
    Workflow.RECERTIFICATION: [
        "DX_PRIMARY_PREFIX_DENY",
    ],
    Workflow.IDG: [
        "DX_PRIMARY_PREFIX_DENY",
    ],
}


def get_rules_for_workflow(
    workflow: Workflow,
    *,
    tenant_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> List[BaseRule]:
    """
    Tenant-aware rule selection.
    """

    # --------------------------------------------------------------
    # 1) Tenant-scoped mode (NO leakage)
    # --------------------------------------------------------------
    if tenant_id and db:
        # ✅ CRITICAL LINE (THIS FIXES THE 500)
        tenant_id = str(tenant_id)

        enabled_rows = (
            db.query(TenantRuleToggle)
            .filter(
                TenantRuleToggle.tenant_id == tenant_id,
                TenantRuleToggle.workflow == workflow.value,
                TenantRuleToggle.enabled.is_(True),
            )
            .all()
        )

        enabled_rule_ids = {row.rule_id for row in enabled_rows}

        # Always include mandatory rules
        final_rule_ids = set(MANDATORY_RULE_IDS) | enabled_rule_ids

        rules: List[BaseRule] = []
        for rule_id in final_rule_ids:
            cls = RULE_CLASS_REGISTRY.get(rule_id)
            if cls:
                rules.append(cls())

        rules.sort(
            key=lambda r: (
                0 if r.rule_id in MANDATORY_RULE_IDS else 1,
                r.rule_id,
            )
        )
        return rules

    # --------------------------------------------------------------
    # 2) Default fallback mode (DEV ONLY)
    # --------------------------------------------------------------
    default_ids = DEFAULT_RULES_BY_WORKFLOW.get(workflow, [])
    return [
        RULE_CLASS_REGISTRY[rid]()
        for rid in default_ids
        if rid in RULE_CLASS_REGISTRY
    ]