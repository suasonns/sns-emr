"""
Integration tests for the SOC hard gate wired into
AdmissionGuardrailService.set_soc_datetime() (Priority 5,
docs/workflows/AdmissionTypesWorkflow.md).

These exercise the real DB-backed path: no benefit-period
determination -> blocked; TRANSFER admit_type missing transfer
evidence -> blocked; fully documented -> SOC write proceeds.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.billing.services.eligibility_workflow_service import (
    SOC_GATE_BLOCKER_MESSAGE,
    record_benefit_period_determination,
    record_eligibility_source_document,
)
from app.models.admission import Admission
from app.models.patient import Patient
from app.services.admission.admission_guardrail_service import (
    AdmissionGuardrailService,
    AdmissionPrerequisiteError,
)

from tests.test_billing_readiness_service import _make_patient
from tests.test_eligibility_workflow_service import _make_document_record, _make_user

FIXED_SOC = datetime(2026, 4, 27, 10, 0, 0, tzinfo=timezone.utc)


def _make_admission(db_session, tenant_id: str, patient: Patient) -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        status="PENDING",
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def test_set_soc_datetime_blocked_when_no_benefit_period_determination(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-SOCBLOCK-1")
    _make_admission(db_session, tenant.id, patient)

    with pytest.raises(AdmissionPrerequisiteError) as excinfo:
        AdmissionGuardrailService.set_soc_datetime(
            db=db_session,
            patient=patient,
            soc_datetime=FIXED_SOC,
            actor_user_id=uuid.uuid4(),
        )

    assert str(excinfo.value) == SOC_GATE_BLOCKER_MESSAGE


def test_set_soc_datetime_blocked_for_transfer_without_transfer_evidence(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-SOCBLOCK-2")
    _make_admission(db_session, tenant.id, patient)
    user_id = _make_user(db_session, tenant.id)

    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=16,
        determined_by_user_id=str(user_id),
        admit_type="TRANSFER_FROM_ANOTHER_HOSPICE",
        starting_cert=16,
        # transfer_source / transfer_evidence_document_id intentionally omitted
    )

    with pytest.raises(AdmissionPrerequisiteError) as excinfo:
        AdmissionGuardrailService.set_soc_datetime(
            db=db_session,
            patient=patient,
            soc_datetime=FIXED_SOC,
            actor_user_id=uuid.uuid4(),
        )

    assert str(excinfo.value) == SOC_GATE_BLOCKER_MESSAGE


def test_set_soc_datetime_proceeds_once_benefit_period_and_starting_cert_documented(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-SOCOK-1")
    admission = _make_admission(db_session, tenant.id, patient)
    user_id = _make_user(db_session, tenant.id)

    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
        determined_by_user_id=str(user_id),
        admit_type="NEW_ADMISSION",
        starting_cert=1,
    )

    # SOC write itself must now succeed (not blocked by the gate). Full
    # admission promotion additionally requires election/records-release/
    # authorization, which are out of scope for this SOC-gate test.
    result = AdmissionGuardrailService.set_soc_datetime(
        db=db_session,
        patient=patient,
        soc_datetime=FIXED_SOC,
        actor_user_id=user_id,
    )

    assert result["success"] is True
    db_session.refresh(admission)
    assert admission.soc_date is not None


def test_set_soc_datetime_proceeds_for_transfer_with_full_documentation(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-SOCOK-2")
    admission = _make_admission(db_session, tenant.id, patient)
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
    esd = record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="TRANSFER_EVIDENCE",
        uploaded_by_user_id=str(user_id),
    )

    record_benefit_period_determination(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=16,
        determined_by_user_id=str(user_id),
        admit_type="TRANSFER_FROM_ANOTHER_HOSPICE",
        starting_cert=16,
        transfer_source="Prior Hospice Agency Name",
        transfer_evidence_document_id=str(esd.id),
    )

    result = AdmissionGuardrailService.set_soc_datetime(
        db=db_session,
        patient=patient,
        soc_datetime=FIXED_SOC,
        actor_user_id=user_id,
    )

    assert result["success"] is True
    db_session.refresh(admission)
    assert admission.soc_date is not None
