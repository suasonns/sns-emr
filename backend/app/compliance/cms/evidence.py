from __future__ import annotations

from app.compliance.types import RuleMeta

RULE = RuleMeta(
    regulator="CMS",
    code="CMS-EVIDENCE-LINKAGE",
    title="Evidence linkage required for task completion",
    version="2026.05",
    effective_date="2026-05-23",
    reference="Survey defensibility / audit integrity",
    description="Tasks must record evidence reference type+id at completion.",
)

# This module is primarily metadata; enforcement happens in task_completion service.
