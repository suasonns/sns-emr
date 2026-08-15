from __future__ import annotations

from datetime import datetime, date, UTC
from typing import Any, List, Optional
from uuid import UUID

from app.compliance.types import RuleMeta, Obligation


RULE = RuleMeta(
    regulator="CMS",
    code="CMS-EVIDENCE-LINKAGE",
    title="Evidence linkage required for task completion",
    version="2026.05",
    effective_date=date(2026, 5, 23),
    reference="Survey defensibility / audit integrity",
    description="Tasks must record evidence reference type and evidence reference id at completion.",
)

RULES = [RULE]


def get_rules() -> List[RuleMeta]:
    return RULES


def _norm(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def evaluate(
    *,
    patient_id: UUID,
    tenant_id: UUID,
    completed_at: Optional[datetime] = None,
    evidence_ref_type: Optional[str] = None,
    evidence_ref_id: Optional[str] = None,
    visit_id: Optional[UUID] = None,
    benefit_period_id: Optional[UUID] = None,
    **_: Any,
) -> List[Obligation]:
    """
    Metadata-driven evidence requirement rule.

    Returns an Obligation only when evidence linkage is missing.
    No DB writes happen here.
    """

    if completed_at is None:
        return []

    evidence_type = _norm(evidence_ref_type)
    evidence_id = _norm(evidence_ref_id)

    has_type = bool(evidence_type)
    has_id = bool(evidence_id)

    if has_type and has_id:
        return []

    now = datetime.now(UTC)

    return [
        Obligation(
            rule_code=RULE.code,
            regulator=RULE.regulator,
            task_type="DOCUMENTATION",
            origin="rule_engine.cms.evidence",
            created_at=now,
            due_date=now,
            evidence_required=("NOTE", "VISIT"),
            patient_id=patient_id,
            tenant_id=tenant_id,
            visit_id=visit_id,
            benefit_period_id=benefit_period_id,
            notes=(
                "Completed task is missing required evidence linkage "
                "(evidence_ref_type and/or evidence_ref_id)."
            ),
        )
    ]