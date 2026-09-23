"""API-level tests for the authoritative SFV completion command
(POST /visits/sfv-requirements/{id}/complete).

This exercises the real HTTP route (not just the service function
covered in test_sfv_completion_visit_separation.py) so the P3-009/P3-017
frontend-callable completion path -- the piece previously missing
entirely -- is verified end-to-end: authentication, tenant/patient
authorization via get_authorized_patient, structured error codes, and
idempotent replay.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.sfv_requirement import SFVRequirement
from app.models.tenant import Tenant
from app.models.visit import Visit
from app.services.hope_phase_b_engine import maybe_trigger_sfv_from_hope_timepoint
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient_and_admission(db_session):
    tenant_id = _tenant_id()
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-API-{uuid.uuid4().hex[:10]}",
        date_of_birth=datetime(1940, 1, 1).date(),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()
    return patient, admission


def _make_visit(db_session, patient, admission, *, visit_type, visit_discipline, visit_datetime):
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type=visit_type,
        visit_discipline=visit_discipline,
        visit_mode="IN_PERSON",
        status="COMPLETED",
        visit_datetime=visit_datetime,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


def _trigger_requirement(db_session, patient, trigger_visit_id, trigger_datetime):
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type="INITIAL_RN_ICA",
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=trigger_datetime,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    db_session.commit()
    assert outcome.created is True, outcome.reason
    return outcome


def test_complete_sfv_requirement_endpoint_happy_path(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["completionVisitId"] == str(completion_visit.id)
    assert body["triggerVisitId"] == str(trigger_visit.id)
    assert body["completedBy"]["userId"]


def test_complete_sfv_requirement_endpoint_rejects_same_visit(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(trigger_visit.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "SAME_VISIT_NOT_ALLOWED"

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_requirement_not_found(client, rn_headers):
    resp = client.post(
        f"/visits/sfv-requirements/{uuid.uuid4()}/complete",
        json={"completionVisitId": str(uuid.uuid4())},
        headers=rn_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "SFV_REQUIREMENT_NOT_FOUND"


def test_complete_sfv_requirement_endpoint_completion_visit_not_found(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(uuid.uuid4())},
        headers=rn_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "COMPLETION_VISIT_NOT_FOUND"


def test_complete_sfv_requirement_endpoint_idempotent_replay(client, db_session, rn_headers):
    """A repeated completion request against an already-COMPLETED
    requirement must return the existing authoritative state, not error
    and not create a second completion."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    first = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=rn_headers,
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=rn_headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "COMPLETED"
    assert second.json()["completionVisitId"] == str(completion_visit.id)


def test_complete_sfv_requirement_endpoint_cross_tenant_visit_rejected(client, db_session, rn_headers):
    """A completion visit belonging to a different tenant must be
    treated as not found -- never revealed as a mismatch of an
    otherwise-existing resource (security-consistent 404, matches
    get_authorized_patient's own cross-tenant convention)."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    other_tenant_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=other_tenant_id,
            legal_name="Other Tenant Hospice (cross-tenant guard test)",
            display_name="Other Tenant",
            npi="9876543210",
            tenant_type="DEV",
            status="ACTIVE",
        )
    )
    db_session.commit()
    other_patient = Patient(
        id=uuid.uuid4(),
        tenant_id=other_tenant_id,
        mrn=f"SFV-API-OTHER-{uuid.uuid4().hex[:8]}",
        date_of_birth=datetime(1945, 1, 1).date(),
        primary_diagnosis="Other-tenant patient (cross-tenant guard test)",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(other_patient)
    db_session.commit()
    other_admission = Admission(
        id=uuid.uuid4(),
        tenant_id=other_tenant_id,
        patient_id=other_patient.id,
        status="ACTIVE",
    )
    db_session.add(other_admission)
    db_session.commit()

    other_tenant_visit = Visit(
        id=uuid.uuid4(),
        tenant_id=other_tenant_id,
        patient_id=other_patient.id,
        admission_id=other_admission.id,
        provider_id=TEST_USER_ID,
        visit_type="SKILLED_NURSING",
        visit_discipline="RN",
        visit_mode="IN_PERSON",
        status="COMPLETED",
        visit_datetime=now + timedelta(hours=6),
    )
    db_session.add(other_tenant_visit)
    db_session.commit()

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(other_tenant_visit.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "TENANT_MISMATCH"
