"""
Shared test helper for establishing a Benefit Period Determination so
SOCValidationService.ensure_ready() (and therefore authorize_admission() /
set_soc_datetime()) will pass.

Tests exercising SOC-establishment paths must call this before invoking
authorize_admission()/set_soc_datetime(), since both now enforce the SOC
gate: staff must document Benefit Period + Starting Cert (and, for
TRANSFER_FROM_ANOTHER_HOSPICE, Transfer Source + Transfer Evidence) before
SOC can be set. See docs/workflows/AdmissionTypesWorkflow.md.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.billing.services.eligibility_workflow_service import (
    record_benefit_period_determination,
)


def ensure_benefit_period_documented(
    db_session: Session,
    *,
    tenant_id,
    patient_id,
    admit_type: str = "NEW_ADMISSION",
    starting_cert: int = 1,
    anticipated_benefit_period_number: int = 1,
    determined_by_user_id=None,
) -> None:
    """
    Record a resolved BENEFIT_PERIOD_CONFIRMED determination for the given
    patient so the SOC gate is satisfied. Only the presence of a resolved
    determination matters to the gate, not who signed it.
    """
    record_benefit_period_determination(
        db_session,
        tenant_id=str(tenant_id),
        patient_id=str(patient_id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=anticipated_benefit_period_number,
        determined_by_user_id=str(determined_by_user_id) if determined_by_user_id else None,
        admit_type=admit_type,
        starting_cert=starting_cert,
    )
    db_session.commit()
