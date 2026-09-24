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


def test_list_sfv_requirements_endpoint_returns_open_requirement(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.get(
        "/visits/sfv-requirements",
        params={"patientId": str(patient.id)},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["sfvRequirementId"] == outcome.requirement_id
    assert body[0]["status"] == "OPEN"
    assert body[0]["triggerVisitId"] == str(trigger_visit.id)
    # SFV ownership remediation (docs/tenant-platform/
    # P0_SFV_OWNERSHIP_REMEDIATION.md): triggerSourceType must be exposed
    # so a caller can scope its lookup to (triggerSourceType,
    # triggerVisitId) instead of a patient-wide "most recent" pick.
    assert body[0]["triggerSourceType"] == "INITIAL_RN_ICA"
    assert body[0]["completionVisitId"] is None


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


def test_complete_sfv_requirement_endpoint_unauthorized_role_rejected(client, db_session, volunteer_headers):
    """A caller whose role has no RN-scope clinical documentation
    capability (and is not RN/LVN) must be rejected -- authorization is
    NOT merely `tenant matches`, it also requires clinical capability."""
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
        headers=volunteer_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_concurrent_requests_single_winner(client, db_session, rn_headers):
    """Two concurrent completion requests against the SAME OPEN requirement,
    each naming a DIFFERENT valid completion visit, must not both "win":
    exactly one completion visit becomes authoritative and both HTTP
    responses converge on that single result (verifies the with_for_update
    row lock actually serializes concurrent completion, not merely that
    the call exists)."""
    import concurrent.futures

    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit_a = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    completion_visit_b = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=7),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    def _post(completion_visit_id):
        return client.post(
            f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
            json={"completionVisitId": str(completion_visit_id)},
            headers=rn_headers,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(_post, completion_visit_a.id)
        future_b = pool.submit(_post, completion_visit_b.id)
        resp_a = future_a.result()
        resp_b = future_b.result()

    assert resp_a.status_code == 200, resp_a.text
    assert resp_b.status_code == 200, resp_b.text

    winning_completion_id = resp_a.json()["completionVisitId"]
    assert resp_b.json()["completionVisitId"] == winning_completion_id
    assert winning_completion_id in {str(completion_visit_a.id), str(completion_visit_b.id)}

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "COMPLETED"
    assert str(requirement.completed_visit_id) == winning_completion_id


def test_complete_sfv_requirement_endpoint_authorized_lvn_different_clinician(client, db_session, rn_headers):
    """An LVN completing a SEPARATE, different clinician's visit must be
    allowed -- clinician identity (which nurse) is not the determining
    factor; the caller's clinical capability and visit separateness are."""
    from tests.conftest import login_headers

    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    lvn_headers = login_headers(client, user_id="lvn_test", role="LVN")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=lvn_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_authorized_np(client, db_session):
    """A Nurse Practitioner (functioning under RN licensure for this
    purpose) is an AUTHORIZED SFV COMPLETER ROLE per the product rule --
    NP must not be excluded merely because the naive `role == "RN"` check
    would miss it.

    NP is also a provider-identity role gated by the platform's separate
    Physician Identity Mapping requirement (see
    app.core.patient_access.get_authorized_patient /
    app.services.physician_identity_service): an NP account gets ZERO
    patient visibility at all -- SFV-related or otherwise -- without a
    verified, ACTIVE physician_id linkage and an explicit patient
    assignment. That gate is independent of and unrelated to SFV
    completion authorization; it is satisfied here so this test isolates
    the SFV-specific `can_complete_sfv` role check."""
    from app.models.physician import Physician
    from app.models.patient_assignment import PatientAssignment
    from app.models.user import User
    from tests.conftest import login_headers

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

    physician = Physician(
        tenant_id=uuid.UUID(_test_tenant_id()),
        display_name="Test NP Provider",
        status="active",
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.flush()

    db_user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
    db_user.physician_id = physician.id
    db_user.physician_link_status = "ACTIVE"

    db_session.add(
        PatientAssignment(
            tenant_id=uuid.UUID(_test_tenant_id()),
            patient_id=patient.id,
            user_id=TEST_USER_ID,
            discipline="NP",
            active=True,
        )
    )
    db_session.commit()

    np_headers = login_headers(client, user_id="np_test", role="NP")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=np_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_np_discipline_visit_completes(client, db_session):
    """NP-001 (issue #158): the SFV is COMPLETED on an NP-discipline
    visit itself (visit_discipline="NP"), not merely called by an
    NP-role user acting on an RN-discipline visit (that distinct check
    is test_complete_sfv_requirement_endpoint_authorized_np above). This
    is the service-layer allow-list path that previously raised
    CLINICIAN_NOT_AUTHORIZED for NP-discipline visits; it now succeeds,
    aligning hope_phase_b_engine.py with app.core.patient_access's
    already-documented SFV authorization policy."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="NP",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    from app.models.physician import Physician
    from app.models.patient_assignment import PatientAssignment
    from app.models.user import User
    from tests.conftest import login_headers

    physician = Physician(
        tenant_id=uuid.UUID(_test_tenant_id()),
        display_name="Test NP Provider 2",
        status="active",
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.flush()

    db_user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
    db_user.physician_id = physician.id
    db_user.physician_link_status = "ACTIVE"

    db_session.add(
        PatientAssignment(
            tenant_id=uuid.UUID(_test_tenant_id()),
            patient_id=patient.id,
            user_id=TEST_USER_ID,
            discipline="NP",
            active=True,
        )
    )
    db_session.commit()

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=login_headers(client, user_id="np_test2", role="NP"),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["completionVisitId"] == str(completion_visit.id)


def test_complete_sfv_requirement_endpoint_administrator_rejected(client, db_session):
    """ADMINISTRATOR holds the same RN-scope PERFORM_RN_ASSESSMENT /
    FINALIZE_RN_DOCUMENTATION capabilities as RN (clinical-admin
    convenience access, per app.core.capabilities), but is explicitly an
    EXCLUDED NON-NURSING ROLE for SFV completion -- "Administrative user"
    per the product rule. General RN-scope documentation capability must
    NOT be sufficient here; only a qualifying nursing credential is."""
    from tests.conftest import login_headers

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

    admin_headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=admin_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_physician_assistant_rejected(client, db_session):
    """PA (Physician Assistant) also holds RN-scope capabilities in
    app.core.capabilities (a physician-tier role may always do at least
    what an RN can), but is not a NURSING credential and must be rejected
    -- "any authorized clinician" is explicitly not the rule; only RN,
    LVN/LPN, NP, and CASE_MANAGER (RN Case Manager) qualify.

    PA is also a provider-identity role gated by the platform's Physician
    Identity Mapping requirement (see get_authorized_patient); physician
    identity + an explicit assignment are set up here so this test
    isolates the SFV-specific role rejection, not the unrelated identity
    gate (which would otherwise also produce a rejection, just for a
    different reason and a different status code)."""
    from app.models.physician import Physician
    from app.models.patient_assignment import PatientAssignment
    from app.models.user import User
    from tests.conftest import login_headers

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

    physician = Physician(
        tenant_id=uuid.UUID(_test_tenant_id()),
        display_name="Test PA Provider",
        status="active",
        created_by=TEST_USER_ID,
    )
    db_session.add(physician)
    db_session.flush()

    db_user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
    db_user.physician_id = physician.id
    db_user.physician_link_status = "ACTIVE"

    db_session.add(
        PatientAssignment(
            tenant_id=uuid.UUID(_test_tenant_id()),
            patient_id=patient.id,
            user_id=TEST_USER_ID,
            discipline="PA",
            active=True,
        )
    )
    db_session.commit()

    pa_headers = login_headers(client, user_id="pa_test", role="PA")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=pa_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_authorized_lpn(client, db_session):
    """LPN is an alias for LVN (app.core.roles._ALIASES) and must be
    directly authorized -- both spellings of the same credential
    qualify."""
    from tests.conftest import login_headers

    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    lpn_headers = login_headers(client, user_id="lpn_test", role="LPN")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=lpn_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def _set_discipline(db_session, discipline):
    """Set the shared TEST_USER_ID row's `discipline` field, the
    repository's existing free-text nursing-discipline field (see
    app/api/_compliance_common.py:101), used as the underlying-credential
    source for CASE_MANAGER-role callers."""
    from app.models.user import User

    db_user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
    db_user.discipline = discipline
    db_session.commit()


def test_complete_sfv_requirement_endpoint_authorized_rn_case_manager(client, db_session):
    """"Case Manager" is a job title, not a credential: a CASE_MANAGER-
    role caller is authorized ONLY when their underlying discipline ALSO
    qualifies. An RN Case Manager (role=CASE_MANAGER, discipline=RN) must
    PASS."""
    from tests.conftest import login_headers

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
    _set_discipline(db_session, "RN")

    cm_headers = login_headers(client, user_id="rn_case_manager_test", role="CASE_MANAGER")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=cm_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_authorized_lvn_case_manager(client, db_session):
    """An LVN Case Manager (role=CASE_MANAGER, discipline=LVN) must
    PASS."""
    from tests.conftest import login_headers

    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)
    _set_discipline(db_session, "LVN")

    cm_headers = login_headers(client, user_id="lvn_case_manager_test", role="CASE_MANAGER")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=cm_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_non_nursing_case_manager_rejected(client, db_session):
    """A CASE_MANAGER-role caller whose underlying discipline is NOT a
    qualifying nursing credential (e.g. a social-work case manager, or a
    case manager with no discipline recorded at all) must be REJECTED --
    the CASE_MANAGER role title alone is never sufficient."""
    from tests.conftest import login_headers

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
    _set_discipline(db_session, "SW")

    cm_headers = login_headers(client, user_id="sw_case_manager_test", role="CASE_MANAGER")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=cm_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_on_call_rn_completes(client, db_session):
    """An on-call RN is authorized under the SAME rule as any staff RN:
    qualifying nursing credential + patient access + visit access +
    documentation/authentication permission. No dedicated on-call
    subsystem exists or is required (per directive) -- on-call status is
    operational routing, not a separate authorization source. Modeled as
    an ordinary RN-role caller completing a follow-up visit authored by
    a different clinician."""
    from tests.conftest import login_headers

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

    on_call_rn_headers = login_headers(client, user_id="oncall_rn_test", role="RN")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=on_call_rn_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_on_call_lvn_completes(client, db_session):
    """An on-call LVN is authorized under the SAME rule as any staff
    LVN/LPN -- on-call status is operational routing, never a distinct
    authorization path."""
    from tests.conftest import login_headers

    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    completion_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    on_call_lvn_headers = login_headers(client, user_id="oncall_lvn_test", role="LVN")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=on_call_lvn_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_complete_sfv_requirement_endpoint_chaplain_rejected(client, db_session):
    """Chaplain is an explicitly EXCLUDED NON-NURSING ROLE per the
    product rule, even with ordinary chart/patient access."""
    from tests.conftest import login_headers

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

    chaplain_headers = login_headers(client, user_id="chaplain_test", role="CHAPLAIN")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=chaplain_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_volunteer_rejected(client, db_session):
    """VOLUNTEER_COORDINATOR (this repository's closest existing role to
    "Volunteer" -- no separate bare VOLUNTEER role exists in
    app.core.auth.VALID_ROLES) is an explicitly EXCLUDED NON-NURSING
    ROLE."""
    from tests.conftest import login_headers

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

    volunteer_coordinator_headers = login_headers(
        client, user_id="volunteer_coordinator_test", role="VOLUNTEER_COORDINATOR"
    )
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=volunteer_coordinator_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_platform_user_rejected(client, db_session):
    """A billing/finance platform-tier role (BILLING) has no clinical
    role at all and must be rejected -- confirms "patient access alone
    must never authorize SFV completion" holds even for non-clinical
    business roles, not just clinical-but-non-nursing roles."""
    from tests.conftest import login_headers

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

    billing_headers = login_headers(client, user_id="billing_test", role="BILLING")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=billing_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_complete_sfv_requirement_endpoint_social_worker_rejected(client, db_session):
    """Social Worker (SW) is an explicitly EXCLUDED NON-NURSING ROLE per
    the product rule, even though a social worker on the care team may
    have ordinary chart/patient access. General chart access is
    insufficient."""
    from tests.conftest import login_headers

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

    sw_headers = login_headers(client, user_id="sw_test", role="SW")
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=sw_headers,
    )

    assert resp.status_code == 403

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"

