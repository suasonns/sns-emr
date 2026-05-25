from __future__ import annotations

from uuid import UUID
from app.compliance.types import RuleMeta


RULE = RuleMeta(
    regulator="TJC",
    code="TJC-HOSPICE-TRACERS",
    title="Survey tracer readiness (documentation & care coordination)",
    version="2026.05",
    effective_date="2026-05-23",
    reference="The Joint Commission Hospice Survey Tracers",
    description=(
        "Defines tracer expectations for documentation integrity and care coordination. "
        "Metadata-only module until tracer tasks are modeled in task_type enum."
    ),
)


def evaluate(*, visit, tenant_id: UUID, helpers, benefit_period_id=None):
    return None
