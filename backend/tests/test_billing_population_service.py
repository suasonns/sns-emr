"""
Tests for the canonical billing-candidate population selector
(app.billing.services.billing_population_service.select_billing_candidate_patients),
the fix for the discovered defect where both the readiness report and the
batch claim generator excluded any patient whose *current* status was not
ACTIVE -- silently dropping legitimately billable pre-termination service
dates for discharged, deceased, revoked, and transferred patients.

Covers the core status x service-date-cutoff matrix:
  - currently admitted, unbilled service date -> included
  - discharged, service date before discharge -> included
  - discharged, service date after discharge -> excluded
  - deceased (discharge_reason captures death), pre-cutoff -> included
  - deceased, post-cutoff -> excluded
  - revoked (discharge_reason captures revocation), pre-cutoff -> included
  - revoked, post-cutoff -> excluded
  - pending admission (no admission row) -> excluded
  - referral (admission status DRAFT) -> excluded
  - readiness report and batch-generation population consistency
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.billing.services.billing_population_service import (
    compute_timely_filing_deadline,
    select_billing_candidate_patients,
)
from app.billing.services.billing_readiness_service import build_tenant_billing_readiness_report
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: str, *, status: str = "ACTIVE") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=f"POPSVC-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="J44.9",
        status=status,
    )
    db_session.add(patient)
    db_session.commit()
    fs = PatientFaceSheet(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        first_name="Test",
        last_name="Patient",
        created_by=TEST_USER_ID,
    )
    db_session.add(fs)
    db_session.commit()
    return patient


def _make_admission(
    db_session,
    tenant_id: str,
    patient: Patient,
    *,
    status: str,
    effective_date: date,
    discharged_at: date | None = None,
    discharge_reason: str | None = None,
) -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_date=datetime(effective_date.year, effective_date.month, effective_date.day, tzinfo=timezone.utc),
        effective_date=datetime(effective_date.year, effective_date.month, effective_date.day, tzinfo=timezone.utc),
        status=status,
        discharged_at=(
            datetime(discharged_at.year, discharged_at.month, discharged_at.day, tzinfo=timezone.utc)
            if discharged_at
            else None
        ),
        discharge_reason=discharge_reason,
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def test_currently_admitted_patient_is_a_candidate_for_unbilled_service_date(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, status="ACTIVE")
    _make_admission(db_session, tenant.id, patient, status="ACTIVE", effective_date=date(2026, 1, 1))

    candidates = select_billing_candidate_patients(
        db_session, tenant_id=str(tenant.id), service_date=date(2026, 3, 1)
    )
    assert str(patient.id) in {c.patient_id for c in candidates}


@pytest.mark.parametrize("discharge_reason", ["Patient discharged", "Patient death", "Hospice benefit revoked"])
def test_discharged_deceased_or_revoked_patient_included_for_pre_cutoff_service_date(
    db_session, tenant, discharge_reason
):
    """
    A patient whose *current* status is no longer ACTIVE (discharge,
    death, or revocation all set admissions.status='DISCHARGED' with a
    discharge_reason describing which) must still be a billing candidate
    for a service date delivered *before* the discharge cutoff.
    """
    patient = _make_patient(db_session, tenant.id, status="DISCHARGED")
    _make_admission(
        db_session,
        tenant.id,
        patient,
        status="DISCHARGED",
        effective_date=date(2026, 1, 1),
        discharged_at=date(2026, 4, 15),
        discharge_reason=discharge_reason,
    )

    candidates = select_billing_candidate_patients(
        db_session, tenant_id=str(tenant.id), service_date=date(2026, 3, 1)
    )
    assert str(patient.id) in {c.patient_id for c in candidates}


@pytest.mark.parametrize("discharge_reason", ["Patient discharged", "Patient death", "Hospice benefit revoked"])
def test_discharged_deceased_or_revoked_patient_excluded_for_post_cutoff_service_date(
    db_session, tenant, discharge_reason
):
    """No service date after the discharge/death/revocation cutoff is billable."""
    patient = _make_patient(db_session, tenant.id, status="DISCHARGED")
    _make_admission(
        db_session,
        tenant.id,
        patient,
        status="DISCHARGED",
        effective_date=date(2026, 1, 1),
        discharged_at=date(2026, 4, 15),
        discharge_reason=discharge_reason,
    )

    candidates = select_billing_candidate_patients(
        db_session, tenant_id=str(tenant.id), service_date=date(2026, 5, 1)
    )
    assert str(patient.id) not in {c.patient_id for c in candidates}


def test_pending_admission_with_no_admission_row_is_excluded(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, status="ACTIVE")
    # No Admission row at all -- referral/pre-admission record.

    candidates = select_billing_candidate_patients(
        db_session, tenant_id=str(tenant.id), service_date=date(2026, 3, 1)
    )
    assert str(patient.id) not in {c.patient_id for c in candidates}


def test_referral_only_draft_admission_is_excluded(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, status="ACTIVE")
    _make_admission(db_session, tenant.id, patient, status="DRAFT", effective_date=date(2026, 3, 1))

    candidates = select_billing_candidate_patients(
        db_session, tenant_id=str(tenant.id), service_date=date(2026, 3, 1)
    )
    assert str(patient.id) not in {c.patient_id for c in candidates}


def test_readiness_report_population_matches_canonical_selector(db_session, tenant):
    """
    build_tenant_billing_readiness_report must evaluate exactly the
    canonical candidate population -- no independent population filter.
    """
    from sqlalchemy import text

    db_session.execute(
        text(
            "UPDATE tenants SET billing_enabled = true, "
            "ein = COALESCE(ein, '123456789'), "
            "ptan = COALESCE(ptan, 'P1234567') "
            "WHERE id = :tenant_id"
        ),
        {"tenant_id": uuid.UUID(str(tenant.id))},
    )
    db_session.commit()

    active_patient = _make_patient(db_session, tenant.id, status="ACTIVE")
    _make_admission(db_session, tenant.id, active_patient, status="ACTIVE", effective_date=date(2026, 1, 1))

    discharged_patient = _make_patient(db_session, tenant.id, status="DISCHARGED")
    _make_admission(
        db_session,
        tenant.id,
        discharged_patient,
        status="DISCHARGED",
        effective_date=date(2026, 1, 1),
        discharged_at=date(2026, 4, 15),
        discharge_reason="Patient death",
    )

    referral_patient = _make_patient(db_session, tenant.id, status="ACTIVE")
    _make_admission(db_session, tenant.id, referral_patient, status="DRAFT", effective_date=date(2026, 3, 1))

    service_date = date(2026, 3, 1)
    report = build_tenant_billing_readiness_report(
        db_session, tenant_id=str(tenant.id), service_date=service_date
    )
    report_patient_ids = {p["patient_id"] for p in report["patients"]}
    canonical_ids = {
        c.patient_id
        for c in select_billing_candidate_patients(
            db_session, tenant_id=str(tenant.id), service_date=service_date
        )
    }

    assert report_patient_ids == canonical_ids
    assert str(active_patient.id) in report_patient_ids
    assert str(discharged_patient.id) in report_patient_ids
    assert str(referral_patient.id) not in report_patient_ids


def test_compute_timely_filing_deadline_defaults_to_365_days_from_service_date():
    service_date = date(2026, 1, 15)
    deadline = compute_timely_filing_deadline(service_date)
    assert deadline == service_date + timedelta(days=365)


def test_compute_timely_filing_deadline_uses_payer_override_when_provided():
    service_date = date(2026, 1, 15)
    deadline = compute_timely_filing_deadline(service_date, payer_override_days=180)
    assert deadline == service_date + timedelta(days=180)
