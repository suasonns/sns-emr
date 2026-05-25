from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from app.compliance.types import RuleMeta, Obligation


RULE = RuleMeta(
    regulator="ACHC",
    code="ACHC-DOC-TIMELINESS",
    title="Clinical documentation timeliness (visit note completion)",
    version="2026.05",
    effective_date="2026-05-23",
    reference="ACHC Hospice documentation timeliness expectations",
    description=(
        "Ensures visit documentation is completed within an expected time window "
        "and is evidence-linked for survey defensibility."
    ),
)


def evaluate(
    *,
    visit,
    tenant_id: UUID,
    helpers,
    benefit_period_id=None,
):
    """
    Placeholder rulepack: returns an Obligation that will be actionable
    once the TaskType enum is expanded beyond POC_UPDATE.
    """

    visit_dt = helpers._get_visit_date(visit)
    patient_id = helpers._get_patient_id(visit)
    visit_id = helpers._get_visit_id(visit)

    # Example policy (adjust later): note due within 24 hours of visit time
    due = visit_dt + timedelta(hours=24)

    return Obligation(
        task_type="VISIT_NOTE_TIMELINESS",  # NOT YET SUPPORTED in DB enum
        origin="RULE",
        due_date=due,
        evidence_required=("NOTE",),
        patient_id=patient_id,
        visit_id=visit_id,
        benefit_period_id=benefit_period_id,
        notes="ACHC: visit note completion expected within 24 hours (configurable).",
    )