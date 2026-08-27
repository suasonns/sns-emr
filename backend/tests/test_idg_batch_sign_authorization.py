"""Regression coverage for the IDG batch-signature Physician Identity gate.

Guards two real bugs found and fixed together in the RNICA integration PR:

1. `idg_physician_review_service.batch_sign()` never passed
   `approved_by_role` through to `physician_order_service.approve_order()`,
   so `is_authorized_order_signer()` always received `None` and every
   batch-sign call unconditionally raised `PhysicianOrderError` — batch
   signing was completely broken regardless of caller authorization.
2. The IDG batch-signature-queue GET and batch-sign POST endpoints
   (`app/api/idg/router.py`) checked only the `MD_ONLY` role, never each
   signer's per-patient Physician Identity linkage/assignment via
   `get_authorized_patient()` — an `ATTENDING_PHYSICIAN` (assigned-patient
   -scoped) could see/sign orders for patients outside their care team.

These tests exercise the real service call (would have caught bug #1) and
the real HTTP endpoints end-to-end via TestClient (would have caught bug
#2 and any regression reintroducing either).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.enums import Discipline
from app.models.idg_meeting import IDGMeeting
from app.models.idg_meeting_patient_review import IDGMeetingPatientReview
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.physician import Physician
from app.models.physician_order import PhysicianOrder
from app.models.user import User
from app.services import idg_physician_review_service as review_svc
from app.services import physician_identity_service as identity_svc
from app.services import physician_order_service as order_svc
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient(db_session):
    patient = Patient(
        tenant_id=_tenant_id(),
        mrn=f"IDG-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def _make_attending_physician_user(db_session):
    user = User(
        tenant_id=_tenant_id(),
        email=f"attending.{uuid.uuid4().hex[:6]}@sns.local",
        full_name="Dr. Attending Test",
        role="ATTENDING_PHYSICIAN",
        active=True,
    )
    db_session.add(user)
    db_session.flush()

    physician = Physician(
        tenant_id=_tenant_id(),
        display_name=user.full_name,
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.flush()

    identity_svc.link_physician(
        db_session,
        tenant_id=_tenant_id(),
        target_user=user,
        physician=physician,
        linked_by_user_id=TEST_USER_ID,
        reason="Initial credential verification",
    )
    return user


def _assign(db_session, *, patient_id, user_id):
    assignment = PatientAssignment(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        user_id=user_id,
        discipline=Discipline.ATTENDING_PHYSICIAN,
    )
    db_session.add(assignment)
    db_session.flush()
    return assignment


def _make_meeting(db_session):
    meeting = IDGMeeting(
        tenant_id=_tenant_id(),
        meeting_date=datetime.now(timezone.utc),
        status="IN_PROGRESS",
        created_by=TEST_USER_ID,
    )
    db_session.add(meeting)
    db_session.flush()
    return meeting


def _make_reviewed_entry(db_session, *, meeting_id, patient_id, physician_user_id):
    review = IDGMeetingPatientReview(
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        idg_meeting_id=meeting_id,
        physician_user_id=physician_user_id,
        review_status="REVIEWED",
        reviewed_at=datetime.now(timezone.utc),
        poc_reviewed=True,
        medication_list_reviewed=True,
        medication_reconciliation_reviewed=True,
        orders_reviewed=True,
        discussion_reviewed=True,
    )
    db_session.add(review)
    db_session.flush()
    return review


def _make_signable_order(db_session, *, patient_id) -> PhysicianOrder:
    order = order_svc.create_draft(
        db_session,
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        order_text="Increase morphine to 5mg q4h PRN",
        order_category="LAB",
        source_type="VERBAL_PHONE",
        ordered_by_provider_name="Dr. Smith",
        ordered_by_provider_role="MD",
        ordered_at=datetime.now(timezone.utc),
        prescriber_authenticated=True,
        phone_readback_confirmed=True,
        created_by=TEST_USER_ID,
        priority="ROUTINE",
    )
    order = order_svc.submit_for_approval(
        db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN",
    )
    assert order.status == "PENDING_HOSPICE_MD_APPROVAL"
    return order


class TestBatchSignServiceAppliesRolePassthrough:
    """Direct service-level regression for the `approved_by_role=None` bug:
    every call to `batch_sign()` previously raised `PhysicianOrderError`
    unconditionally because the role was never forwarded to
    `approve_order()` -> `is_authorized_order_signer()`."""

    def test_batch_sign_actually_signs_when_scoped_to_authorized_patient(self, db_session):
        attending = _make_attending_physician_user(db_session)
        patient = _make_patient(db_session)
        _assign(db_session, patient_id=patient.id, user_id=attending.id)
        meeting = _make_meeting(db_session)
        _make_reviewed_entry(
            db_session, meeting_id=meeting.id, patient_id=patient.id, physician_user_id=attending.id,
        )
        order = _make_signable_order(db_session, patient_id=patient.id)
        db_session.commit()

        result = review_svc.batch_sign(
            db_session,
            tenant_id=_tenant_id(),
            idg_meeting_id=meeting.id,
            physician_user_id=attending.id,
            physician_role="ATTENDING_PHYSICIAN",
            patient_ids=[patient.id],
        )

        assert result["failed_count"] == 0, result["failed"]
        assert result["signed_count"] == 1
        db_session.refresh(order)
        assert order.status == "APPROVED"
        assert order.signed_by_user_id == attending.id


@pytest.mark.integration
class TestBatchSignEndpointsEnforcePhysicianIdentityScope:
    """End-to-end HTTP-level regression for the per-patient linkage gate:
    an ATTENDING_PHYSICIAN with a verified identity but NO assignment to a
    given patient must never see or sign that patient's orders via the IDG
    batch-signature endpoints, even though their role passes MD_ONLY."""

    def _attending_headers(self, attending_user_id):
        token = create_access_token(
            user_id=attending_user_id,
            role="ATTENDING_PHYSICIAN",
            tenant_id=_tenant_id(),
            email="attending.headers@sns.local",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_queue_and_batch_sign_exclude_unassigned_patient(self, client, db_session):
        attending = _make_attending_physician_user(db_session)

        assigned_patient = _make_patient(db_session)
        _assign(db_session, patient_id=assigned_patient.id, user_id=attending.id)

        unassigned_patient = _make_patient(db_session)  # deliberately NOT assigned to `attending`

        meeting = _make_meeting(db_session)
        _make_reviewed_entry(
            db_session, meeting_id=meeting.id, patient_id=assigned_patient.id, physician_user_id=attending.id,
        )
        _make_reviewed_entry(
            db_session, meeting_id=meeting.id, patient_id=unassigned_patient.id, physician_user_id=attending.id,
        )
        assigned_order = _make_signable_order(db_session, patient_id=assigned_patient.id)
        unassigned_order = _make_signable_order(db_session, patient_id=unassigned_patient.id)
        db_session.commit()

        headers = self._attending_headers(attending.id)

        # GET queue must silently exclude the unassigned patient.
        queue_resp = client.get(
            f"/idg/sessions/{meeting.id}/batch-signature-queue", headers=headers,
        )
        assert queue_resp.status_code == 200, queue_resp.text
        queue = queue_resp.json()
        queue_patient_ids = {entry["patient_id"] for entry in queue}
        assert str(assigned_patient.id) in queue_patient_ids
        assert str(unassigned_patient.id) not in queue_patient_ids

        # POST batch-sign, explicitly requesting BOTH patients, must only
        # sign the assigned one — never silently sign for the unassigned
        # patient just because it was requested.
        sign_resp = client.post(
            f"/idg/sessions/{meeting.id}/batch-sign",
            json={"patient_ids": [str(assigned_patient.id), str(unassigned_patient.id)]},
            headers=headers,
        )
        assert sign_resp.status_code == 200, sign_resp.text
        result = sign_resp.json()
        assert result["signed_count"] == 1
        signed_patient_ids = {entry["patient_id"] for entry in result["signed"]}
        assert str(assigned_patient.id) in signed_patient_ids
        assert str(unassigned_patient.id) not in signed_patient_ids

        db_session.refresh(assigned_order)
        db_session.refresh(unassigned_order)
        assert assigned_order.status == "APPROVED"
        assert unassigned_order.status == "PENDING_HOSPICE_MD_APPROVAL"  # untouched, fail-closed
