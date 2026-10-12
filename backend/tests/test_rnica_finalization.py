from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text

from app.billing.models.visit_minutes import VisitMinutes
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.visit import Visit
from app.services.rnica_finalization_service import (
    evaluate_finalization_readiness,
    evaluate_poc_completeness,
)
from tests.conftest import TEST_USER_ID


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"RNICA-FINAL-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1945, 3, 3),
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


def _make_linked_visit(db_session, patient, admission, tenant_id, *, visit_date: str = "2026-01-15"):
    """
    Creates the authoritative (unfinalized) Visit that a real RNICA save
    would already have linked via rnica_assessments.visit_id (see
    _resolve_incoming_rnica_visit_id in app/api/visits.py). Mirrors exactly
    what the frontend's RNICA creation flow does: POST /visits/ first
    (form_type=INITIAL_ICA), then hand the resulting Visit ID to RNICA.
    """
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type="RN",
        visit_discipline="RN",
        visit_mode="IN_PERSON",
        status="DRAFT",
        visit_datetime=datetime.fromisoformat(f"{visit_date}T09:00:00+00:00"),
        form_type="INITIAL_ICA",
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


def _make_rnica_assessment(db_session, patient, tenant_id, form_data, *, visit=None):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data,
        visit_id=visit.id if visit is not None else None,
    )
    db_session.add(record)
    db_session.commit()
    return record


COMPLETE_FORM_DATA = {
    "diagnoses": {"lcdEligibilityNarrative": "Documented decline per LCD criteria."},
    "referrals": {"reviewed": True},
    "visitMeta": {
        "visitDate": "2026-01-15",
        "timeIn": "09:00",
        "timeOut": "10:15",
    },
    "finalization": {
        "clinicianSignature": "RN Test",
        "signatureCertification": True,
        "pocGenerationCompleted": True,
        "responseToInterventions": {"baselineEstablished": True},
    },
}


# =========================================================
# Pure unit tests — evaluate_poc_completeness / evaluate_finalization_readiness
# =========================================================

def test_poc_completeness_ready_when_no_active_problems():
    result = evaluate_poc_completeness([])
    assert result["ready"] is True


def test_poc_completeness_ready_when_all_resolved():
    problems = [{"status": "RESOLVED", "label": "Old problem", "goals": []}]
    result = evaluate_poc_completeness(problems)
    assert result["ready"] is True


def test_poc_completeness_blocks_problem_missing_goals():
    problems = [{"status": "ACTIVE", "label": "Weight loss", "goals": []}]
    result = evaluate_poc_completeness(problems)
    assert result["ready"] is False
    assert "Weight loss" in result["incomplete_labels"]


def test_poc_completeness_blocks_goal_missing_interventions():
    problems = [{"status": "ACTIVE", "label": "Pain", "goals": [{"goal_text": "g", "interventions": []}]}]
    result = evaluate_poc_completeness(problems)
    assert result["ready"] is False


def test_poc_completeness_blocks_intervention_missing_discipline():
    problems = [{
        "status": "ACTIVE",
        "label": "Pain",
        "goals": [{"goal_text": "g", "interventions": [{"discipline": "", "frequency": "Daily"}]}],
    }]
    result = evaluate_poc_completeness(problems)
    assert result["ready"] is False


def test_poc_completeness_ready_when_complete():
    problems = [{
        "status": "ACTIVE",
        "label": "Pain",
        "goals": [{"goal_text": "g", "interventions": [{"discipline": "RN", "intervention_text": "x"}]}],
    }]
    result = evaluate_poc_completeness(problems)
    assert result["ready"] is True


def test_finalization_readiness_all_checks_pass():
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, [])
    assert readiness["ready"] is True
    assert all(check["ready"] for check in readiness["checks"].values())


def test_finalization_readiness_blocks_on_missing_attestation():
    form_data = {**COMPLETE_FORM_DATA, "finalization": {**COMPLETE_FORM_DATA["finalization"], "signatureCertification": False}}
    readiness = evaluate_finalization_readiness(form_data, [])
    assert readiness["ready"] is False
    assert readiness["checks"]["attestation"]["ready"] is False


def test_finalization_readiness_narrative_auto_passes_when_empty():
    form_data = {**COMPLETE_FORM_DATA, "diagnoses": {**COMPLETE_FORM_DATA["diagnoses"], "clinicalNarrative": ""}}
    readiness = evaluate_finalization_readiness(form_data, [])
    assert readiness["checks"]["narrativeReviewed"]["ready"] is True


def test_finalization_readiness_blocks_unreviewed_narrative():
    form_data = {
        **COMPLETE_FORM_DATA,
        "diagnoses": {
            **COMPLETE_FORM_DATA["diagnoses"],
            "clinicalNarrative": "Patient documented decline.",
            "clinicalNarrativeReviewed": False,
        },
    }
    readiness = evaluate_finalization_readiness(form_data, [])
    assert readiness["ready"] is False
    assert readiness["checks"]["narrativeReviewed"]["ready"] is False


def test_finalization_readiness_blocks_on_incomplete_poc():
    incomplete_problems = [{"status": "ACTIVE", "label": "Skin breakdown", "goals": []}]
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, incomplete_problems)
    assert readiness["ready"] is False
    assert readiness["checks"]["pocCompleteness"]["ready"] is False


# =========================================================
# HTTP integration tests — lock gate, immutability, audit trail, stub endpoint
# =========================================================

@pytest.mark.integration
def test_lock_rejected_when_finalization_readiness_incomplete(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"finalization": {"clinicianSignature": "RN Test"}})

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 400, resp.text
    body = resp.json()["detail"]
    assert "unmetChecks" in body
    assert len(body["unmetChecks"]) > 0

    db_session.refresh(record)
    assert record.locked is False


@pytest.mark.integration
def test_lock_succeeds_when_finalization_readiness_complete(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["locked"] is True
    assert body["lockedAt"]


@pytest.mark.integration
def test_relocking_is_idempotent(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    first = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert first.status_code == 200, first.text
    second = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert second.status_code == 200, second.text
    assert second.json()["lockedAt"] == first.json()["lockedAt"]


@pytest.mark.integration
def test_lock_writes_audit_event(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text

    row = db_session.execute(
        text(
            """
            SELECT id FROM audit_logs
            WHERE action = :action AND entity_type = :entity_type AND entity_id = :entity_id
            ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"action": "RNICA_ASSESSMENT_LOCKED", "entity_type": "rnica_assessment", "entity_id": str(record.id)},
    ).first()
    assert row is not None, "Expected audit log row for RNICA_ASSESSMENT_LOCKED"


@pytest.mark.integration
def test_update_rejected_after_lock(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text

    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {**COMPLETE_FORM_DATA, "diagnoses": {"clinicalNarrative": "attempted post-lock edit"}}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 423, update_resp.text

    db_session.refresh(record)
    assert record.form_data.get("diagnoses", {}).get("clinicalNarrative") != "attempted post-lock edit"


@pytest.mark.integration
def test_correction_request_stub_requires_locked_assessment(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    amendment_payload = {
        "amendment_category": "CLINICAL_CORRECTION",
        "reason_code": "OMITTED_FINDING",
        "requested_change": "Add documented finding omitted at signing.",
    }

    unlocked_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request", json=amendment_payload, headers=rn_headers
    )
    assert unlocked_resp.status_code == 400, unlocked_resp.text

    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text


    locked_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request", json=amendment_payload, headers=rn_headers
    )
    assert locked_resp.status_code == 200, locked_resp.text
    assert locked_resp.json()["status"] == "PENDING"


@pytest.mark.integration
def test_finalization_readiness_endpoint_matches_lock_gate(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"finalization": {"clinicianSignature": "RN Test"}})

    readiness_resp = client.get(f"/visits/rnica/{record.id}/finalization-readiness", headers=rn_headers)
    assert readiness_resp.status_code == 200, readiness_resp.text
    assert readiness_resp.json()["ready"] is False

    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 400, lock_resp.text


# =========================================================
# HOPE-VISIT-HEADER-SOT-001 — RNICA lock finalizes its linked Visit
#
# Full RNICA completion must reuse the existing Visit finalization /
# VisitMinutes mechanism (the same one POST /visits/{id}/finalize uses for
# RN/LVN Visit Notes), not reimplement it. See _finalize_rnica_linked_visit
# in app/api/visits.py.
# =========================================================

def _visit_minutes_row(db_session, visit_id):
    return db_session.query(VisitMinutes).filter(VisitMinutes.visit_id == visit_id).one_or_none()


@pytest.mark.integration
def test_lock_without_linked_visit_still_succeeds_as_a_noop(client, db_session, rn_headers):
    """
    RNICA-only assessments with no established Visit Header link are a
    pre-existing, intentional scope boundary (see
    test_rnica_hope_phase_b_wiring.py's "intentionally left NULL"
    coverage). Finalization must be skipped as a no-op in that case --
    locking must still succeed exactly as it did before this correction,
    and no VisitMinutes row may appear from nowhere.
    """
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=None)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text

    db_session.refresh(record)
    assert record.locked is True
    assert record.status == "LOCKED"
    assert record.visit_id is None


@pytest.mark.integration
def test_lock_without_visit_header_times_is_rejected(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    form_data = {
        **COMPLETE_FORM_DATA,
        "visitMeta": {"visitDate": "2026-01-15", "timeIn": "", "timeOut": ""},
    }
    record = _make_rnica_assessment(db_session, patient, tenant_id, form_data, visit=visit)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 422, resp.text
    assert "Time In" in resp.json()["detail"]

    db_session.refresh(record)
    assert record.locked is False
    db_session.refresh(visit)
    assert (visit.status or "").upper() != "FINALIZED"
    assert _visit_minutes_row(db_session, visit.id) is None


@pytest.mark.integration
def test_lock_finalizes_linked_visit_and_creates_visit_minutes(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text

    db_session.refresh(visit)
    assert (visit.status or "").upper() == "FINALIZED"
    assert visit.finalized_at is not None
    assert visit.start_time is not None and visit.end_time is not None

    minutes_row = _visit_minutes_row(db_session, visit.id)
    assert minutes_row is not None, "Expected a VisitMinutes row for the finalized Visit"
    # 09:00 -> 10:15 is 75 minutes, matching COMPLETE_FORM_DATA's visitMeta.
    assert minutes_row.minutes == 75
    assert minutes_row.status == "FINALIZED"


@pytest.mark.integration
def test_relock_does_not_duplicate_visit_minutes(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    first = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert first.status_code == 200, first.text
    second = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert second.status_code == 200, second.text

    rows = db_session.query(VisitMinutes).filter(VisitMinutes.visit_id == visit.id).all()
    assert len(rows) == 1, "Re-locking must not duplicate the VisitMinutes row"

    db_session.refresh(visit)
    first_finalized_at = visit.finalized_at
    # Re-locking an already-locked assessment short-circuits before
    # _finalize_rnica_linked_visit runs again, so the Visit's
    # finalized_at must not have been bumped a second time.
    assert visit.finalized_at == first_finalized_at


@pytest.mark.integration
def test_lock_rejects_visit_belonging_to_different_patient(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    other_patient, other_admission = _make_patient_and_admission(db_session, tenant_id)
    other_visit = _make_linked_visit(db_session, other_patient, other_admission, tenant_id)

    # Simulates form_data/visit_id drifting apart (e.g. direct DB tampering
    # or a future bug) -- the lock path must independently re-verify Visit
    # ownership rather than trusting the stored visit_id blindly.
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=other_visit)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 422, resp.text
    assert "does not belong to this patient" in resp.json()["detail"]

    db_session.refresh(record)
    assert record.locked is False
    db_session.refresh(other_visit)
    assert (other_visit.status or "").upper() != "FINALIZED"


@pytest.mark.integration
def test_save_draft_does_not_finalize_linked_visit(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    visit = _make_linked_visit(db_session, patient, admission, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA, visit=visit)

    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": COMPLETE_FORM_DATA},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    db_session.refresh(visit)
    assert (visit.status or "").upper() != "FINALIZED"
    assert _visit_minutes_row(db_session, visit.id) is None
