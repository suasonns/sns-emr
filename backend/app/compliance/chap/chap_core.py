from __future__ import annotations

from uuid import UUID
from app.compliance.types import RuleMeta


RULE = RuleMeta(
    regulator="CHAP",
    code="CHAP-HOSPICE-CORE",
    title="CHAP hospice accreditation core expectations",
    version="2026.05",
    effective_date="2026-05-23",
    reference="CHAP Hospice Accreditation Standards",
    description=(
        "Defines CHAP hospice accreditation expectations. "
        "Metadata-only module until CHAP-specific obligations are modeled."
    ),
)


def evaluate(*, visit, tenant_id: UUID, helpers, benefit_period_id=None):
    return None