"""Physician Identity Mapping tests (owner directive 2026-08-21).

Covers the fail-closed User-to-Physician linkage model:
  - identity verification (physician_id + ACTIVE status) is required before
    ANY provider-identity-role account (MD/MEDICAL_DIRECTOR/
    MEDICAL_DIRECTOR_DESIGNEE/ATTENDING_PHYSICIAN/HOSPICE_PHYSICIAN/NP/PA)
    gets patient visibility — never an agency-wide fallback.
  - after verification, Medical Director (and legacy "MD") get tenant-wide
    oversight visibility; Attending/Hospice Physician/NP/PA get
    assigned-patient-only visibility (no "unclaimed caseload" fallback).
  - unlink revokes access immediately; duplicate active links and
    cross-tenant links are rejected; audit events are recorded.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.core.patient_access import get_authorized_patient
from app.models.enums import Discipline
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.physician import Physician
from app.models.user import User
from app.services import physician_identity_service as svc
from tests.conftest import TEST_USER_ID, _test_tenant_id


@dataclass
class _FakeCurrentUser:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient(db_session):
    patient = Patient(
        tenant_id=_tenant_id(),
        mrn=f"TEST-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def _make_provider_user(db_session, role: str) -> User:
    user = User(
        tenant_id=_tenant_id(),
        email=f"{role.lower()}.{uuid.uuid4().hex[:6]}@sns.local",
        full_name=f"Test {role}",
        role=role,
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _make_physician(db_session, *, status: str = "active", tenant_id=None):
    physician = Physician(
        tenant_id=tenant_id or _tenant_id(),
        display_name=f"Dr. Test {uuid.uuid4().hex[:6]}",
        status=status,
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.flush()
    return physician


def _assign(db_session, *, patient_id, user_id, discipline=Discipline.ATTENDING_PHYSICIAN):
    assignment = PatientAssignment(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        user_id=user_id,
        discipline=discipline,
        active=True,
    )
    db_session.add(assignment)
    db_session.flush()
    return assignment


class TestFailClosedVisibility:
    def test_unverified_medical_director_gets_zero_patients(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        patient = _make_patient(db_session)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=md_user.id, tenant_id=_tenant_id(), role="MEDICAL_DIRECTOR")
        with pytest.raises(HTTPException) as exc:
            get_authorized_patient(db_session, patient.id, caller)
        assert exc.value.status_code == 404

    def test_unverified_attending_physician_gets_zero_patients_even_when_assigned(self, db_session):
        attending = _make_provider_user(db_session, "ATTENDING_PHYSICIAN")
        patient = _make_patient(db_session)
        _assign(db_session, patient_id=patient.id, user_id=attending.id)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=attending.id, tenant_id=_tenant_id(), role="ATTENDING_PHYSICIAN")
        with pytest.raises(HTTPException) as exc:
            get_authorized_patient(db_session, patient.id, caller)
        assert exc.value.status_code == 404

    def test_changing_display_name_alone_does_not_grant_access(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        md_user.full_name = "Dr. Attending Physician Smith"
        patient = _make_patient(db_session)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=md_user.id, tenant_id=_tenant_id(), role="MEDICAL_DIRECTOR")
        with pytest.raises(HTTPException):
            get_authorized_patient(db_session, patient.id, caller)


class TestVerifiedVisibilityTiers:
    def test_verified_medical_director_sees_any_patient_tenant_wide(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        physician = _make_physician(db_session)
        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=md_user, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        patient = _make_patient(db_session)  # deliberately unassigned to anyone
        db_session.commit()

        caller = _FakeCurrentUser(user_id=md_user.id, tenant_id=_tenant_id(), role="MEDICAL_DIRECTOR")
        result = get_authorized_patient(db_session, patient.id, caller)
        assert result.id == patient.id

    def test_verified_attending_sees_only_assigned_patient(self, db_session):
        attending = _make_provider_user(db_session, "ATTENDING_PHYSICIAN")
        physician = _make_physician(db_session)
        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=attending, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        assigned_patient = _make_patient(db_session)
        unassigned_patient = _make_patient(db_session)
        _assign(db_session, patient_id=assigned_patient.id, user_id=attending.id)
        # Give the unassigned patient SOME OTHER active assignment so the
        # "unclaimed caseload" fallback does not apply to it either.
        other_user = _make_provider_user(db_session, "RN")
        _assign(db_session, patient_id=unassigned_patient.id, user_id=other_user.id, discipline=Discipline.RN)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=attending.id, tenant_id=_tenant_id(), role="ATTENDING_PHYSICIAN")
        result = get_authorized_patient(db_session, assigned_patient.id, caller)
        assert result.id == assigned_patient.id

        with pytest.raises(HTTPException) as exc:
            get_authorized_patient(db_session, unassigned_patient.id, caller)
        assert exc.value.status_code == 404

    def test_verified_attending_does_not_get_unclaimed_caseload_fallback(self, db_session):
        """A verified Attending Physician must NOT receive the generic
        'unclaimed caseload' fallback that unassigned clinical roles get —
        provider-identity roles require an explicit PatientAssignment."""
        attending = _make_provider_user(db_session, "ATTENDING_PHYSICIAN")
        physician = _make_physician(db_session)
        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=attending, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        brand_new_patient = _make_patient(db_session)  # no assignment for ANYONE yet
        db_session.commit()

        caller = _FakeCurrentUser(user_id=attending.id, tenant_id=_tenant_id(), role="ATTENDING_PHYSICIAN")
        with pytest.raises(HTTPException) as exc:
            get_authorized_patient(db_session, brand_new_patient.id, caller)
        assert exc.value.status_code == 404


class TestLinkageLifecycle:
    def test_unlink_revokes_access_immediately(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        physician = _make_physician(db_session)
        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=md_user, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        patient = _make_patient(db_session)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=md_user.id, tenant_id=_tenant_id(), role="MEDICAL_DIRECTOR")
        assert get_authorized_patient(db_session, patient.id, caller).id == patient.id

        svc.unlink_physician(
            db_session, tenant_id=_tenant_id(), target_user=md_user,
            unlinked_by_user_id=TEST_USER_ID, reason="Credential expired",
        )
        db_session.commit()

        with pytest.raises(HTTPException):
            get_authorized_patient(db_session, patient.id, caller)

    def test_duplicate_active_link_rejected(self, db_session):
        physician = _make_physician(db_session)
        first_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        second_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=first_user, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        db_session.commit()

        with pytest.raises(svc.PhysicianIdentityError):
            svc.link_physician(
                db_session, tenant_id=_tenant_id(), target_user=second_user, physician=physician,
                linked_by_user_id=TEST_USER_ID, reason="Attempted duplicate link",
            )

    def test_cross_tenant_link_rejected(self, db_session):
        other_tenant_id = uuid.uuid4()
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        physician = _make_physician(db_session)
        db_session.commit()

        # Both records genuinely belong to the real test tenant; passing a
        # mismatched tenant_id into link_physician() simulates an admin
        # acting outside their own tenant scope.
        with pytest.raises(svc.PhysicianIdentityError):
            svc.link_physician(
                db_session, tenant_id=other_tenant_id, target_user=md_user, physician=physician,
                linked_by_user_id=TEST_USER_ID, reason="Cross tenant attempt",
            )

    def test_reason_required_for_link_and_unlink(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        physician = _make_physician(db_session)
        db_session.commit()

        with pytest.raises(svc.PhysicianIdentityError):
            svc.link_physician(
                db_session, tenant_id=_tenant_id(), target_user=md_user, physician=physician,
                linked_by_user_id=TEST_USER_ID, reason="   ",
            )

    def test_audit_events_recorded_for_link_unlink_and_blocked_access(self, db_session):
        md_user = _make_provider_user(db_session, "MEDICAL_DIRECTOR")
        physician = _make_physician(db_session)
        patient = _make_patient(db_session)
        db_session.commit()

        caller = _FakeCurrentUser(user_id=md_user.id, tenant_id=_tenant_id(), role="MEDICAL_DIRECTOR")
        with pytest.raises(HTTPException):
            get_authorized_patient(db_session, patient.id, caller)

        svc.link_physician(
            db_session, tenant_id=_tenant_id(), target_user=md_user, physician=physician,
            linked_by_user_id=TEST_USER_ID, reason="Initial credential verification",
        )
        svc.unlink_physician(
            db_session, tenant_id=_tenant_id(), target_user=md_user,
            unlinked_by_user_id=TEST_USER_ID, reason="Credential expired",
        )
        db_session.commit()

        # Queried via raw SQL rather than the AuditLog ORM class: some
        # other test modules in this suite replace sys.modules
        # ["app.models.audit_log"] with an unrelated stub at import time
        # and never restore it, which would otherwise make the ORM class
        # reference unreliable depending on test run order.
        rows = db_session.execute(
            text(
                "SELECT action FROM audit_logs WHERE entity_id = :entity_id "
                "AND action IN ('PROVIDER_LINK_CREATED', 'PROVIDER_LINK_REMOVED')"
            ),
            {"entity_id": str(md_user.id)},
        ).fetchall()
        actions = {row[0] for row in rows}
        assert "PROVIDER_LINK_CREATED" in actions
        assert "PROVIDER_LINK_REMOVED" in actions
