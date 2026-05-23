from __future__ import annotations

from typing import List, Dict, Type

from app.rules.base import Workflow, BaseRule

# ------------------------------------------------------------------
# Rule imports (explicit only — no auto-discovery)
# ------------------------------------------------------------------
from app.rules.diagnosis.prohibited_primary_dx_prefix import (
    ProhibitedPrimaryDxPrefixRule,
)

# ------------------------------------------------------------------
# Central rule registry (SINGLE SOURCE OF TRUTH)
# ------------------------------------------------------------------
_RULES_BY_WORKFLOW: Dict[Workflow, List[Type[BaseRule]]] = {
    Workflow.ADMISSION: [
        ProhibitedPrimaryDxPrefixRule,
    ],
    Workflow.RECERTIFICATION: [
        ProhibitedPrimaryDxPrefixRule,
    ],
    Workflow.IDG: [
        ProhibitedPrimaryDxPrefixRule,
    ],
}


def get_rules_for_workflow(workflow: Workflow) -> List[BaseRule]:
    """
    Central rule registry.

    Rules are:
    - Explicitly registered
    - Workflow-scoped
    - Inert unless enforcement is enabled
    """
    rule_classes = _RULES_BY_WORKFLOW.get(workflow, [])
    return [rule_class() for rule_class in rule_classes]