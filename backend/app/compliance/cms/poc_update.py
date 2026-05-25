from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from app.compliance.types import RuleMeta, Obligation


RULE = RuleMeta(
    regulator="CMS",
    code="CMS-418.56-POC-UPDATE",
    title="Plan of Care update timing (ROUTINE vs CRISIS)",
    version="2026.05",
    effective_date="2026-05-23",
    reference="CMS Hospice CoPs §418.56",
    description="Defines timing and evidence requirements for POC updates.",
)


def evaluate(
    *,
    visit,
    tenant_id: UUID,
    helpers,
    benefit_period_id=None,
):
    """
    CMS Hospice CoP §418.56

    CRISIS:
      - Every finalized RN visit triggers same-day POC_UPDATE
      - Completed immediately with VISIT evidence

    ROUTINE:
      - Only supervisory RN visits anchor POC updates
      - Next POC_UPDATE due visit_date + 14 days
    """

    visit_type = helpers._get_visit_type(visit)
    if visit_type != "RN":
        return None

    care_level = helpers._get_care_level(visit)
    visit_date = helpers._get_visit_date(visit)
    patient_id = helpers._get_patient_id(visit)
    visit_id = helpers._get_visit_id(visit)

    # CRISIS → same day
    if care_level == "CRISIS":
        return Obligation(
            task_type="POC_UPDATE",
            origin="MANUAL",
            due_date=visit_date,
            evidence_required=("VISIT",),
            patient_id=patient_id,
            visit_id=visit_id,
            benefit_period_id=benefit_period_id,
            notes="CMS CRISIS RN visit → same-day POC update.",
        )

    # ROUTINE → supervisory RN +14 days
    if care_level == "ROUTINE" and helpers._is_supervisory(visit):
        return Obligation(
            task_type="POC_UPDATE",
            origin="PERIODIC",
            due_date=visit_date + timedelta(days=14),
            evidence_required=("VISIT",),
            patient_id=patient_id,
            visit_id=visit_id,
            benefit_period_id=benefit_period_id,
            notes="CMS ROUTINE supervisory RN visit → POC update due +14 days.",
        )

    return None