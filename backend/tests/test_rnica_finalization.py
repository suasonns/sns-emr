from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.services.rnica_finalization_service import (
    evaluate_finalization_readiness,
    evaluate_poc_completeness,
)


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


def _make_rnica_assessment(db_session, patient, tenant_id, form_data):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data,
    )
    db_session.add(record)
    db_session.commit()
    return record


COMPLETE_FORM_DATA = {
    "diagnoses": {"lcdEligibilityNarrative": "Documented decline per LCD criteria."},
    "referrals": {"reviewed": True},
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
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA)

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["locked"] is True
    assert body["lockedAt"]


@pytest.mark.integration
def test_relocking_is_idempotent(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA)

    first = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert first.status_code == 200, first.text
    second = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert second.status_code == 200, second.text
    assert second.json()["lockedAt"] == first.json()["lockedAt"]


@pytest.mark.integration
def test_lock_writes_audit_event(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA)

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
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA)

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
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, COMPLETE_FORM_DATA)

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
# Medicare Non-Covered Items Review + benefit-period readiness
# (Reason For Assessment: Update Assessment / Recertification Assessment)
# =========================================================

def _make_rnica_assessment_typed(db_session, patient, tenant_id, form_data, assessment_type):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        assessment_type=assessment_type,
        form_data=form_data,
    )
    db_session.add(record)
    db_session.commit()
    return record


def _make_benefit_period(db_session, tenant_id, patient_id, *, start_date, end_date=None):
    from app.models.benefit_period import BenefitPeriod

    period = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_type="RECERT",
        period_number=3,
        election_date=start_date,
        start_date=start_date,
        end_date=end_date,
        is_current=True,
    )
    db_session.add(period)
    db_session.commit()
    return period


def test_medicare_review_not_applicable_for_update_assessment():
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, [], "UPDATE")
    assert readiness["checks"]["medicareNonCoveredReview"]["ready"] is True


def test_medicare_review_blocks_recert_when_missing():
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, [], "RECERT")
    assert readiness["ready"] is False
    assert readiness["checks"]["medicareNonCoveredReview"]["ready"] is False


def test_benefit_period_not_applicable_for_update_assessment():
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, [], "UPDATE")
    assert readiness["checks"]["benefitPeriod"]["ready"] is True


def test_benefit_period_blocks_recert_without_db_context():
    readiness = evaluate_finalization_readiness(COMPLETE_FORM_DATA, [], "RECERT")
    assert readiness["checks"]["benefitPeriod"]["ready"] is False


@pytest.mark.integration
def test_benefit_period_blocks_recert_lock_without_active_period(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    form_data = {
        **COMPLETE_FORM_DATA,
        "medicareNonCoveredReview": {"outcome": "NO_ITEMS_IDENTIFIED"},
    }
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, form_data, "RECERT")

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 400, resp.text
    unmet = resp.json()["detail"]["unmetChecks"]
    assert "Benefit-Period Context" in unmet


@pytest.mark.integration
def test_recert_lock_succeeds_with_active_benefit_period_and_medicare_review(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    _make_benefit_period(db_session, tenant_id, patient.id, start_date=date(2026, 1, 1))
    form_data = {
        **COMPLETE_FORM_DATA,
        "medicareNonCoveredReview": {"outcome": "NO_ITEMS_IDENTIFIED"},
    }
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, form_data, "RECERT")

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["locked"] is True


@pytest.mark.integration
def test_update_assessment_lock_does_not_require_benefit_period_or_medicare_review(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "UPDATE")

    resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert resp.status_code == 200, resp.text


@pytest.mark.integration
def test_medicare_review_endpoint_rejects_non_recert_assessment(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "UPDATE")

    resp = client.put(
        f"/visits/rnica/{record.id}/medicare-non-covered-review",
        json={"outcome": "NO_ITEMS_IDENTIFIED"},
        headers=rn_headers,
    )
    assert resp.status_code == 400, resp.text


@pytest.mark.integration
def test_medicare_review_endpoint_requires_explanation_when_changed(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "RECERT")

    resp = client.put(
        f"/visits/rnica/{record.id}/medicare-non-covered-review",
        json={"outcome": "CHANGED"},
        headers=rn_headers,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.integration
def test_medicare_review_endpoint_requires_blocking_reason_and_follow_up_when_unable(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "RECERT")

    resp = client.put(
        f"/visits/rnica/{record.id}/medicare-non-covered-review",
        json={"outcome": "UNABLE_TO_COMPLETE"},
        headers=rn_headers,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.integration
def test_medicare_review_endpoint_saves_and_round_trips(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "RECERT")

    put_resp = client.put(
        f"/visits/rnica/{record.id}/medicare-non-covered-review",
        json={"outcome": "NO_ITEMS_IDENTIFIED"},
        headers=rn_headers,
    )
    assert put_resp.status_code == 200, put_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}/medicare-non-covered-review", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["medicareNonCoveredReview"]["outcome"] == "NO_ITEMS_IDENTIFIED"


@pytest.mark.integration
def test_medicare_review_endpoint_rejected_after_lock(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    _make_benefit_period(db_session, tenant_id, patient.id, start_date=date(2026, 1, 1))
    form_data = {
        **COMPLETE_FORM_DATA,
        "medicareNonCoveredReview": {"outcome": "NO_ITEMS_IDENTIFIED"},
    }
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, form_data, "RECERT")
    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text

    resp = client.put(
        f"/visits/rnica/{record.id}/medicare-non-covered-review",
        json={"outcome": "CHANGED", "explanation": "late edit"},
        headers=rn_headers,
    )
    assert resp.status_code == 423, resp.text


@pytest.mark.integration
def test_election_addendum_candidates_endpoint_scoped_to_admission(client, db_session, rn_headers):
    from app.billing.models.election_addendum_request import ElectionAddendumRequest

    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment_typed(db_session, patient, tenant_id, COMPLETE_FORM_DATA, "RECERT")
    record.admission_id = admission.id
    db_session.add(record)
    db_session.commit()

    addendum = ElectionAddendumRequest(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
    )
    db_session.add(addendum)
    db_session.commit()

    resp = client.get(f"/visits/rnica/{record.id}/election-addendum-candidates", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    candidate_ids = [c["id"] for c in resp.json()["candidates"]]
    assert str(addendum.id) in candidate_ids
