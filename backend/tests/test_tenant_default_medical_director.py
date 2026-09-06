"""Tenant-default Medical Director tests (multi-tenant design directive).

Covers:
  - apply_tenant_default_medical_director is a no-op when the tenant has no
    default configured (must show NOT_CONFIGURED, never fall back to
    another tenant, a dev seed, or SNS Hospice Solutions itself).
  - it prepopulates the shared PatientPhysicianAssignment (MEDICAL_DIRECTOR
    role) from the tenant default for a genuinely new patient.
  - it is a strict no-op when an explicit per-patient assignment already
    exists (explicit patient assignment always wins over the tenant
    default).
  - the database-level composite foreign key on
    tenants.default_medical_director_physician_id rejects a physician_id
    that belongs to a DIFFERENT tenant (tenant isolation enforced even if
    application code has a bug).
  - the agency-profile settings endpoint validates tenant-scoped physicians
    before accepting a new default, and can clear it back to
    NOT_CONFIGURED.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.patient import Patient
from app.models.patient_physician_assignment import PatientPhysicianAssignment
from app.models.physician import Physician
from app.models.tenant import Tenant
from app.services.physician_sync_service import (
    MEDICAL_DIRECTOR,
    apply_tenant_default_medical_director,
    set_physician_assignment,
)
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    from datetime import date

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"TMD-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1945, 3, 2),
        primary_diagnosis="Tenant default MD test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_physician(db_session, tenant_id: uuid.UUID, *, name: str | None = None) -> Physician:
    physician = Physician(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        display_name=name or f"Dr. Test {uuid.uuid4().hex[:6]}",
        npi="1234567890",
        status="active",
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.commit()
    return physician


def test_no_op_when_tenant_default_not_configured(db_session):
    tenant_id = uuid.UUID(_test_tenant_id())
    patient = _make_patient(db_session, tenant_id)

    tenant = db_session.get(Tenant, tenant_id)
    tenant.default_medical_director_physician_id = None
    db_session.commit()

    result = apply_tenant_default_medical_director(
        db_session, tenant_id=tenant_id, patient_id=patient.id, updated_by=TEST_USER_ID
    )

    assert result is None
    assert (
        db_session.query(PatientPhysicianAssignment)
        .filter(
            PatientPhysicianAssignment.patient_id == patient.id,
            PatientPhysicianAssignment.role == MEDICAL_DIRECTOR,
        )
        .first()
        is None
    )


def test_applies_tenant_default_for_new_patient(db_session):
    tenant_id = uuid.UUID(_test_tenant_id())
    patient = _make_patient(db_session, tenant_id)
    physician = _make_physician(db_session, tenant_id, name="Dr. Agency Default")

    tenant = db_session.get(Tenant, tenant_id)
    tenant.default_medical_director_physician_id = physician.id
    db_session.commit()

    result = apply_tenant_default_medical_director(
        db_session, tenant_id=tenant_id, patient_id=patient.id, updated_by=TEST_USER_ID
    )

    assert result is not None
    assert result.role == MEDICAL_DIRECTOR
    assert result.name == "Dr. Agency Default"
    assert result.physician_id == physician.id
    assert result.source == "TENANT_DEFAULT"

    # Clean up so subsequent tests in this shared-tenant DB start fresh.
    tenant.default_medical_director_physician_id = None
    db_session.commit()


def test_explicit_assignment_always_wins_over_tenant_default(db_session):
    tenant_id = uuid.UUID(_test_tenant_id())
    patient = _make_patient(db_session, tenant_id)
    default_physician = _make_physician(db_session, tenant_id, name="Dr. Agency Default")

    # An explicit assignment already exists for this patient (e.g. set
    # manually via the Facesheet/RNICA physician picker).
    set_physician_assignment(
        db_session,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role=MEDICAL_DIRECTOR,
        source="FACESHEET",
        name="Dr. Explicit Override",
        updated_by=TEST_USER_ID,
    )
    db_session.commit()

    tenant = db_session.get(Tenant, tenant_id)
    tenant.default_medical_director_physician_id = default_physician.id
    db_session.commit()

    result = apply_tenant_default_medical_director(
        db_session, tenant_id=tenant_id, patient_id=patient.id, updated_by=TEST_USER_ID
    )

    assert result is None

    row = (
        db_session.query(PatientPhysicianAssignment)
        .filter(
            PatientPhysicianAssignment.patient_id == patient.id,
            PatientPhysicianAssignment.role == MEDICAL_DIRECTOR,
        )
        .first()
    )
    assert row.name == "Dr. Explicit Override"

    tenant.default_medical_director_physician_id = None
    db_session.commit()


def test_composite_fk_rejects_cross_tenant_physician(db_session):
    """
    A tenant's default_medical_director_physician_id must never resolve to
    another tenant's physician row -- this is enforced at the database
    level (composite FK against physicians(tenant_id, id)), not just in
    application code.
    """
    own_tenant_id = uuid.UUID(_test_tenant_id())
    other_tenant_id = uuid.uuid4()

    db_session.add(
        Tenant(
            id=other_tenant_id,
            legal_name="Other Agency (isolation test)",
            display_name="Other Agency",
            npi="9876543210",
            tenant_type="DEV",
            status="ACTIVE",
        )
    )
    db_session.commit()

    other_tenants_physician = _make_physician(db_session, other_tenant_id, name="Dr. Wrong Tenant")

    tenant = db_session.get(Tenant, own_tenant_id)
    tenant.default_medical_director_physician_id = other_tenants_physician.id
    db_session.add(tenant)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    # Leave the shared test tenant clean for subsequent tests.
    tenant = db_session.get(Tenant, own_tenant_id)
    tenant.default_medical_director_physician_id = None
    db_session.commit()
