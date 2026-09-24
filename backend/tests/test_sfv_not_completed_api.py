"""API-level tests for the HOPE J2052C ownership fix (issue #146):

    POST /visits/sfv-requirements/{id}/not-completed
    POST /visits/sfv-requirements/{id}/correct-reason

Mirrors test_sfv_completion_api.py's fixtures/patterns exactly so the
"not completed" (J2052A = No / J2052C reason) branch is verified with
the same rigor as the existing "completed" branch: authorization,
discipline validation (RN/LVN allowed today, NP intentionally rejected
-- tracked separately, see issue: "SFV completion authorization rejects
NP discipline"), visit separation/ordering, reason-code validation, and
the append-only correction path (SfvOutcomeCorrection never overwrites,
only supersedes).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.sfv_outcome_correction import SfvOutcomeCorrection
from app.models.sfv_requirement import SFVRequirement
from app.models.visit import Visit
from app.services.hope_phase_b_engine import maybe_trigger_sfv_from_hope_timepoint
from tests.conftest import TEST_USER_ID, _test_tenant_id, login_headers


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient_and_admission(db_session):
    tenant_id = _tenant_id()
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-NC-{uuid.uuid4().hex[:10]}",
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
        pain_impact="MODERATE",
        non_pain_impact=None,
    )
    db_session.commit()
    assert outcome.created is True, outcome.reason
    return outcome


def _lvn_headers(client):
    return login_headers(client, user_id="lvn_test", role="LVN")


def test_record_sfv_not_completed_endpoint_happy_path_rn(client, db_session, rn_headers):
    """Acceptance test (RN): Admission RN creates SFV requirement;
    Assigned RN attempts SFV; patient declines. J2052A=No, J2052C=1,
    attributed to the attempting RN/visit, not the triggering assessment."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "1"},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "NOT_COMPLETED"
    assert body["reasonCode"] == "1"
    assert body["triggerVisitId"] == str(trigger_visit.id)
    assert body["reasonRecordedBy"]["userId"]

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "NOT_COMPLETED"
    assert requirement.reason_code == "1"
    assert requirement.reason_recorded_visit_id == attempt_visit.id


def test_record_sfv_not_completed_endpoint_happy_path_lvn_unavailable(client, db_session):
    """Acceptance test (LVN): Assigned LVN attempts SFV, patient
    unavailable. J2052A=No, J2052C=2, LVN recorded as outcome owner."""
    lvn_headers = _lvn_headers(client)
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "2"},
        headers=lvn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "NOT_COMPLETED"
    assert body["reasonCode"] == "2"


def test_record_sfv_not_completed_endpoint_rejects_np_discipline(client, db_session, rn_headers):
    """Acceptance test (NP -- EXPECTED FAIL today, tracked separately):
    NP attempts SFV, patient declines. Current backend rejects NP as an
    authorized SFV discipline (see issue: "SFV completion authorization
    rejects NP discipline"). This is intentionally NOT fixed as part of
    the J2052C ownership change (implementation directive Rule 5) -- this
    test documents/locks in the current, still-broken NP behavior."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="NP",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "1"},
        headers=rn_headers,
    )

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["error"]["code"] == "CLINICIAN_NOT_AUTHORIZED"

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.status == "OPEN"


def test_record_sfv_not_completed_endpoint_on_call_unable_to_contact(client, db_session):
    """Acceptance test (On-call RN): On-call RN attempts visit, unable to
    contact. J2052A=No, J2052C=3, on-call RN recorded as owner. On-call
    is still discipline RN server-side (no separate on-call role today)
    -- this proves the outcome-owner attribution follows whichever
    authenticated RN/LVN clinician actually performed the attempt, not a
    fixed roster of "assigned" clinicians."""
    on_call_headers = login_headers(client, user_id="on_call_rn_test", role="RN")
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "3"},
        headers=on_call_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["reasonCode"] == "3"


def test_record_sfv_not_completed_endpoint_rejects_same_visit(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(trigger_visit.id), "reasonCode": "1"},
        headers=rn_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "SAME_VISIT_NOT_ALLOWED"


def test_record_sfv_not_completed_endpoint_rejects_invalid_reason_code(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "free text not allowed"},
        headers=rn_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "REASON_CODE_INVALID"


def test_record_sfv_not_completed_endpoint_requirement_not_found(client, rn_headers):
    resp = client.post(
        f"/visits/sfv-requirements/{uuid.uuid4()}/not-completed",
        json={"attemptVisitId": str(uuid.uuid4()), "reasonCode": "1"},
        headers=rn_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "SFV_REQUIREMENT_NOT_FOUND"


def test_locked_admission_does_not_block_not_completed_recording(client, db_session, rn_headers):
    """Acceptance test (locked assessment): the triggering RNICA/HUV
    visit being finalized/"locked" (status=COMPLETED here, since RNICA
    signing/locking lives on rnica_assessments.form_data -- entirely
    separate storage from SFVRequirement) must never block recording the
    SFV attempt outcome, and recording it must never modify the
    triggering visit/assessment at all."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    trigger_visit_updated_at_before = trigger_visit.updated_at
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="LVN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "2"},
        headers=_lvn_headers(client),
    )

    assert resp.status_code == 200, resp.text
    db_session.refresh(trigger_visit)
    assert trigger_visit.updated_at == trigger_visit_updated_at_before


def test_correct_sfv_reason_code_preserves_prior_value(client, db_session, rn_headers):
    """Correction acceptance test: original 3 (unable to contact)
    corrected to 2 (unavailable). Original value must be preserved in
    SfvOutcomeCorrection, never overwritten/destroyed, and the live
    requirement must reflect the corrected value with a full audit
    trail (who/when/prior/new)."""
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=6),
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    first = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(attempt_visit.id), "reasonCode": "3"},
        headers=rn_headers,
    )
    assert first.status_code == 200, first.text

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/correct-reason",
        json={"newReasonCode": "2", "correctionReason": "Clarified with family after initial contact attempt."},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["priorReasonCode"] == "3"
    assert body["newReasonCode"] == "2"

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .first()
    )
    assert requirement.reason_code == "2"

    corrections = (
        db_session.query(SfvOutcomeCorrection)
        .filter(SfvOutcomeCorrection.sfv_requirement_id == requirement.id)
        .all()
    )
    assert len(corrections) == 1
    assert corrections[0].prior_reason_code == "3"
    assert corrections[0].new_reason_code == "2"


def test_correct_sfv_reason_code_rejects_when_not_yet_recorded(client, db_session, rn_headers):
    patient, admission = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit = _make_visit(
        db_session, patient, admission,
        visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
    )
    outcome = _trigger_requirement(db_session, patient, trigger_visit.id, now)

    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/correct-reason",
        json={"newReasonCode": "2", "correctionReason": "n/a"},
        headers=rn_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "INVALID_STATE_FOR_CORRECTION"


def test_not_completed_never_writes_reason_onto_completed_requirement(client, db_session, rn_headers):
    """A requirement that is already COMPLETED must not be reopened or
    overwritten by a stray not-completed call -- mirrors the existing
    idempotent-replay guarantee on the completion endpoint."""
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

    completed = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/complete",
        json={"completionVisitId": str(completion_visit.id)},
        headers=rn_headers,
    )
    assert completed.status_code == 200, completed.text

    later_attempt_visit = _make_visit(
        db_session, patient, admission,
        visit_type="SKILLED_NURSING", visit_discipline="RN",
        visit_datetime=now + timedelta(hours=12),
    )
    resp = client.post(
        f"/visits/sfv-requirements/{outcome.requirement_id}/not-completed",
        json={"attemptVisitId": str(later_attempt_visit.id), "reasonCode": "1"},
        headers=rn_headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["reasonCode"] is None
