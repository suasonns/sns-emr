from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Type, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_rule_toggle import TenantRuleToggle
from app.rules.base import BaseRule, Workflow

# Rule imports (explicit only - NO auto-discovery)
from app.rules.diagnosis.prohibited_primary_dx_prefix import (
    ProhibitedPrimaryDxPrefixRule,
)
from app.rules.eligibility.chf_readiness import CHFReadinessRule
from app.rules.eligibility.copd_readiness import COPDReadinessRule
from app.rules.eligibility.end_stage_parkinsons import EndStageParkinsonRule
from app.rules.eligibility.esrd_readiness import ESRDReadinessRule
from app.rules.eligibility.functional_decline_readiness import (
    FunctionalDeclineReadinessRule,
)


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Rule class registry: rule_id -> rule class
# Explicit registration only.
# ------------------------------------------------------------------
RULE_CLASS_REGISTRY: Dict[str, Type[BaseRule]] = {
    "DX_PRIMARY_PREFIX_DENY": ProhibitedPrimaryDxPrefixRule,
    "CHF_AUDIT_READINESS": CHFReadinessRule,
    "COPD_AUDIT_READINESS": COPDReadinessRule,
    "ESRD_AUDIT_READINESS": ESRDReadinessRule,
    "FUNCTIONAL_DECLINE_READINESS": FunctionalDeclineReadinessRule,
    "END_STAGE_PARKINSON": EndStageParkinsonRule,
}


# ------------------------------------------------------------------
# Mandatory rules (owner-controlled; never toggleable)
# ------------------------------------------------------------------
MANDATORY_RULE_IDS = frozenset(
    {
        "DX_PRIMARY_PREFIX_DENY",
    }
)


# ------------------------------------------------------------------
# Default rules when tenant context is unavailable (DEV-ONLY)
# This should NOT be used silently in production code paths.
# ------------------------------------------------------------------
DEFAULT_RULES_BY_WORKFLOW: Dict[Workflow, List[str]] = {
    Workflow.ADMISSION: [
        "DX_PRIMARY_PREFIX_DENY",
        "CHF_AUDIT_READINESS",
        "COPD_AUDIT_READINESS",
        "ESRD_AUDIT_READINESS",
        "FUNCTIONAL_DECLINE_READINESS",
        "END_STAGE_PARKINSON",
    ],
    Workflow.RECERTIFICATION: [
        "DX_PRIMARY_PREFIX_DENY",
        "FUNCTIONAL_DECLINE_READINESS",
        "END_STAGE_PARKINSON",
    ],
    Workflow.IDG: [
        "DX_PRIMARY_PREFIX_DENY",
    ],
}


def _normalize_tenant_id(tenant_id: Optional[Union[str, UUID]]) -> Optional[str]:
    if tenant_id is None:
        return None
    if isinstance(tenant_id, UUID):
        return str(tenant_id)
    value = str(tenant_id).strip()
    return value or None


def _build_rule_instances(rule_ids: Iterable[str]) -> List[BaseRule]:
    """
    Deterministic instantiation of registered rules.
    Unknown rule IDs are ignored safely.
    Mandatory rules are ordered first, then alphabetical by rule_id.
    """
    valid_ids = [rule_id for rule_id in rule_ids if rule_id in RULE_CLASS_REGISTRY]

    valid_ids.sort(
        key=lambda rid: (
            0 if rid in MANDATORY_RULE_IDS else 1,
            rid,
        )
    )

    return [RULE_CLASS_REGISTRY[rule_id]() for rule_id in valid_ids]


def rules_for_workflow(
    workflow: Workflow,
    *,
    tenant_id: Optional[Union[str, UUID]] = None,
    db: Optional[Session] = None,
    allow_dev_fallback: bool = False,
) -> List[BaseRule]:
    """
    Tenant-aware rule selection.

    Rules:
    - Explicit registry only
    - No auto-discovery
    - Mandatory rules always run
    - Tenant-enabled rules run only when enabled for that tenant/workflow
    - DEV fallback is used only when explicitly requested
    - If tenant context is unavailable and fallback is not allowed,
      mandatory rules only are returned
    """

    if not isinstance(workflow, Workflow):
        raise ValueError(f"workflow must be a Workflow enum, got: {workflow!r}")

    normalized_tenant_id = _normalize_tenant_id(tenant_id)

    # --------------------------------------------------------------
    # 1) Tenant-scoped mode (NO leakage)
    # --------------------------------------------------------------
    if normalized_tenant_id and db is not None:
        enabled_rows = (
            db.query(TenantRuleToggle)
            .filter(
                TenantRuleToggle.tenant_id == normalized_tenant_id,
                TenantRuleToggle.workflow == workflow.value,
                TenantRuleToggle.enabled.is_(True),
            )
            .all()
        )

        enabled_rule_ids = {
            str(row.rule_id)
            for row in enabled_rows
            if str(row.rule_id) in RULE_CLASS_REGISTRY
        }

        final_rule_ids = set(MANDATORY_RULE_IDS) | enabled_rule_ids

        logger.info(
            "Tenant-scoped rule resolution",
            extra={
                "workflow": workflow.value,
                "tenant_id": normalized_tenant_id,
                "enabled_rule_ids": sorted(enabled_rule_ids),
                "mandatory_rule_ids": sorted(MANDATORY_RULE_IDS),
                "final_rule_ids": sorted(final_rule_ids),
            },
        )

        return _build_rule_instances(final_rule_ids)

    # --------------------------------------------------------------
    # 2) DEV fallback mode (EXPLICIT ONLY)
    # --------------------------------------------------------------
    if allow_dev_fallback:
        default_rule_ids = DEFAULT_RULES_BY_WORKFLOW.get(workflow, [])
        fallback_rule_ids = list(dict.fromkeys([*MANDATORY_RULE_IDS, *default_rule_ids]))

        logger.warning(
            "Using DEV fallback rule resolution",
            extra={
                "workflow": workflow.value,
                "tenant_id": normalized_tenant_id,
                "db_present": db is not None,
                "fallback_rule_ids": fallback_rule_ids,
            },
        )

        return _build_rule_instances(fallback_rule_ids)

    # --------------------------------------------------------------
    # 3) Safe production fallback = mandatory only
    # --------------------------------------------------------------
    logger.warning(
        "Tenant context unavailable; returning mandatory rules only",
        extra={
            "workflow": workflow.value,
            "tenant_id": normalized_tenant_id,
            "db_present": db is not None,
            "mandatory_rule_ids": sorted(MANDATORY_RULE_IDS),
        },
    )

    return _build_rule_instances(MANDATORY_RULE_IDS)

# ------------------------------------------------------------------
# BACKWARD COMPATIBILITY (REQUIRED FOR EXISTING IMPORTS)
# ------------------------------------------------------------------

def get_rules_for_workflow(
    workflow: Workflow,
    *,
    tenant_id: Optional[Union[str, UUID]] = None,
    db: Optional[Session] = None,
    allow_dev_fallback: bool = False,
) -> List[BaseRule]:
    return rules_for_workflow(
        workflow,
        tenant_id=tenant_id,
        db=db,
        allow_dev_fallback=allow_dev_fallback,
    )