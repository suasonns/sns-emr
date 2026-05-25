from __future__ import annotations

from uuid import UUID
from app.compliance.types import RuleMeta


RULE = RuleMeta(
    regulator="CDPH",
    code="CDPH-CA-HOSPICE-BASELINE",
    title="California hospice compliance baseline",
    version="2026.05",
    effective_date="2026-05-23",
    reference="CDPH Hospice Program Expectations (CA)",
    description=(
        "California-specific hospice compliance expectations. "
        "Metadata-only module until specific CA rules are encoded as obligations."
    ),
)


def evaluate(*, visit, tenant_id: UUID, helpers, benefit_period_id=None):
    return None
