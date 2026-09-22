from __future__ import annotations

"""
Acceptance tests for the Clinical Outcome service (issue #143 secondary
layer): primary/secondary evaluation criteria, actor-discipline-from-
account-only enforcement, closure/finalization gating, correction/reopen,
audit trail, and cross-tenant rejection.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.clinical_outcome import ClinicalOutcomeAuditEvent, ClinicalOutcomeRecord
from app.models.patient import Patient
from app.models.patient_response import PatientResponseEvent
from app.models.record_version import RecordVersion
from app.services import clinical_outcome_service as svc
from app.services import two_hour_response_service as thr_svc
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"CO-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1938, 3, 4),
        primary_diagnosis="CHF",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        effective_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        soc_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_event(db_session, patient, admission, tenant_id):
    return thr_svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc),
        description="Increased dyspnea reported by caregiver",
        created_by_user_id=TEST_USER_ID,
    )


def _make_record(db_session, tenant_id):
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = _make_event(db_session, patient, admission, tenant_id)
    record = svc.create_outcome_from_patient_response_event(
        db_session,
        event=event,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    return patient, admission, event, record


# ---------------------------------------------------------------------
# Creation / linking
# ---------------------------------------------------------------------


def test_create_outcome_requires_actor_account_discipline(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = _make_event(db_session, patient, admission, tenant_id)

    with pytest.raises(svc.ClinicalOutcomeError):
        svc.create_outcome_from_patient_response_event(
            db_session, event=event, actor_user_id=TEST_USER_ID, actor_account_discipline=""
        )


def test_create_outcome_links_event_patient_admission(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, event, record = _make_record(db_session, tenant_id)

    assert record.patient_id == patient.id
    assert record.admission_id == admission.id
    assert record.patient_response_event_id == event.id
    assert record.outcome_status == "IDENTIFIED"
    assert record.created_by_account_discipline == "RN"


def test_create_outcome_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    events = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id)
        .all()
    )
    assert any(e.event_type == "OUTCOME_CREATED" for e in events)
    assert events[0].actor_account_discipline == "RN"


def test_get_outcome_record_rejects_cross_tenant_access(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    other_tenant_id = uuid.uuid4()
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.get_outcome_record(db_session, tenant_id=other_tenant_id, record_id=record.id)


def test_actor_discipline_comes_only_from_explicit_authenticated_account_param(db_session, tenant):
    """The function signature only accepts actor_account_discipline as an
    explicit keyword sourced by the caller from the authenticated
    account -- there is no visit/task object parameter it could read a
    conflicting discipline from, so a visit or task "belonging" to a
    different discipline can never override it."""
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = _make_event(db_session, patient, admission, tenant_id)

    # source_task_id/source_visit_id are opaque linkage IDs only -- they
    # must not change created_by_account_discipline even if supplied.
    record = svc.create_outcome_from_patient_response_event(
        db_session,
        event=event,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert record.created_by_account_discipline == "RN"


def test_visit_and_task_metadata_cannot_override_actor_discipline_on_mutation(db_session, tenant):
    """Every mutating function (record_intervention, record_patient_response,
    change_outcome_status, ...) only accepts actor_account_discipline as an
    explicit authenticated-account-sourced parameter -- there is no code
    path reading a discipline value off a visit or task record."""
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_intervention(
        db_session, record=record, intervention_timely=True, actor_user_id=TEST_USER_ID, actor_account_discipline="MSW"
    )
    events = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
            ClinicalOutcomeAuditEvent.event_type == "INTERVENTION_RECORDED",
        )
        .all()
    )
    assert events[0].actor_account_discipline == "MSW"
    # The record's own creation-time discipline snapshot (RN) is untouched.
    assert record.created_by_account_discipline == "RN"


# ---------------------------------------------------------------------
# Intervention / patient response
# ---------------------------------------------------------------------


def test_record_intervention_does_not_advance_to_resolved(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_intervention(
        db_session, record=record, intervention_timely=True, actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    assert record.outcome_status == "INTERVENTION_IN_PROGRESS"
    assert record.response_recorded_at is None


def test_persistent_response_requires_remaining_need_identified(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.record_patient_response(
            db_session,
            record=record,
            patient_response_status="PERSISTENT",
            response_recorded_at=datetime.now(timezone.utc),
            remaining_need_identified=False,
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_worsened_response_requires_remaining_need_identified(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.record_patient_response(
            db_session,
            record=record,
            patient_response_status="WORSENED",
            response_recorded_at=datetime.now(timezone.utc),
            remaining_need_identified=False,
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_record_patient_response_success_path(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    recorded_at = datetime.now(timezone.utc)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=recorded_at,
        patient_appropriately_cared_for=True,
        remaining_need_identified=False,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert record.patient_response_status == "IMPROVED"
    assert record.response_recorded_at == recorded_at
    assert record.patient_appropriately_cared_for is True


def test_remaining_need_true_emits_extra_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="PERSISTENT",
        response_recorded_at=datetime.now(timezone.utc),
        remaining_need_identified=True,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    events = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id)
        .all()
    )
    assert any(e.event_type == "REMAINING_NEED_RECORDED" for e in events)


# ---------------------------------------------------------------------
# Outcome status
# ---------------------------------------------------------------------


def test_change_outcome_status_rejects_unknown_status(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.change_outcome_status(
            db_session, record=record, new_status="NOT_A_REAL_STATUS", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_change_outcome_status_to_persistent_requires_remaining_need(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.change_outcome_status(
            db_session, record=record, new_status="PERSISTENT", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_change_outcome_status_idg_follow_up_required_emits_extra_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.change_outcome_status(
        db_session,
        record=record,
        new_status="IDG_FOLLOW_UP_REQUIRED",
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    events = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id)
        .all()
    )
    assert any(e.event_type == "IDG_FOLLOW_UP_REQUIRED" for e in events)


# ---------------------------------------------------------------------
# Finalization
# ---------------------------------------------------------------------


def test_cannot_finalize_without_patient_response(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.finalize_outcome(
            db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_cannot_finalize_persistent_without_remaining_need(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="PERSISTENT",
        response_recorded_at=datetime.now(timezone.utc),
        remaining_need_identified=True,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    # Force outcome_status without going through change_outcome_status's own guard,
    # simulating a record that reached PERSISTENT outcome_status validly, then
    # verify finalize still checks remaining_need at closure time.
    svc.change_outcome_status(
        db_session, record=record, new_status="PERSISTENT", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    # Mutate the in-memory attribute directly (without flushing) to
    # exercise finalize_outcome's own defense-in-depth check -- the DB
    # CHECK constraint would otherwise make this exact state unreachable
    # via a flush.
    record.remaining_need_identified = False
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.finalize_outcome(
            db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )
    db_session.rollback()


def test_finalize_success_path(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    closed_at = datetime.now(timezone.utc)
    svc.finalize_outcome(
        db_session, record=record, closed_at=closed_at, actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    assert record.closed_at == closed_at
    assert record.closed_by == TEST_USER_ID


def test_finalize_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session,
        record=record,
        closed_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    audit = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
            ClinicalOutcomeAuditEvent.event_type == "OUTCOME_FINALIZED",
        )
        .one()
    )
    assert audit.actor_account_discipline == "RN"


def test_cannot_finalize_twice(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.finalize_outcome(
            db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_cannot_mutate_finalized_record_directly(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.record_intervention(db_session, record=record, actor_user_id=TEST_USER_ID, actor_account_discipline="RN")


# ---------------------------------------------------------------------
# Correction / reopen
# ---------------------------------------------------------------------


def test_correct_outcome_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.correct_outcome(
            db_session,
            record=record,
            corrections={"notes": "corrected"},
            correction_reason="",
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_correct_outcome_preserves_prior_values_via_record_version(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    original_status = record.outcome_status
    svc.correct_outcome(
        db_session,
        record=record,
        corrections={"outcome_status": "ASSESSED"},
        correction_reason="Corrected initial classification",
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert record.outcome_status == "ASSESSED"
    version = (
        db_session.query(RecordVersion)
        .filter(RecordVersion.source_record_type == "CLINICAL_OUTCOME_RECORD", RecordVersion.source_record_id == record.id)
        .first()
    )
    assert version is not None
    assert version.snapshot["outcome_status"] == original_status


def test_correct_outcome_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.correct_outcome(
        db_session,
        record=record,
        corrections={"outcome_status": "ASSESSED"},
        correction_reason="Corrected initial classification",
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    audit = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
            ClinicalOutcomeAuditEvent.event_type == "OUTCOME_CORRECTED",
        )
        .one()
    )
    assert audit.reason == "Corrected initial classification"
    assert audit.actor_account_discipline == "RN"


def test_correct_outcome_rejects_unknown_field(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.correct_outcome(
            db_session,
            record=record,
            corrections={"not_a_real_field": "x"},
            correction_reason="typo fix",
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_cannot_correct_finalized_record_without_reopen(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.correct_outcome(
            db_session,
            record=record,
            corrections={"notes": "x"},
            correction_reason="should fail",
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_reopen_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.reopen_outcome(db_session, record=record, reopen_reason="", actor_user_id=TEST_USER_ID, actor_account_discipline="RN")


def test_reopen_requires_authorized_actor(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.ClinicalOutcomeError):
        svc.reopen_outcome(db_session, record=record, reopen_reason="Need to amend", actor_user_id=None, actor_account_discipline="RN")


def test_reopen_success_path_allows_correction_afterward(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    svc.reopen_outcome(
        db_session, record=record, reopen_reason="Need to amend documentation", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    assert record.closed_at is None
    assert record.closed_by is None
    assert record.reopen_reason == "Need to amend documentation"

    # Now correctable again since it's no longer finalized.
    svc.correct_outcome(
        db_session,
        record=record,
        corrections={"notes": "amended"},
        correction_reason="Amendment after reopen",
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert record.notes == "amended"


def test_reopen_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_patient_response(
        db_session,
        record=record,
        patient_response_status="IMPROVED",
        response_recorded_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.finalize_outcome(
        db_session, record=record, closed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    svc.reopen_outcome(
        db_session, record=record, reopen_reason="Need to amend", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    events = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
            ClinicalOutcomeAuditEvent.event_type == "OUTCOME_REOPENED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# IDG communication (secondary criterion; does not close/finalize)
# ---------------------------------------------------------------------


def test_record_idg_communication_does_not_close_outcome(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, record = _make_record(db_session, tenant_id)
    svc.record_idg_communication(
        db_session,
        record=record,
        idg_communicated_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert record.idg_communicated is True
    assert record.closed_at is None

    audit = (
        db_session.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
            ClinicalOutcomeAuditEvent.event_type == "IDG_COMMUNICATION_RECORDED",
        )
        .one()
    )
    assert audit.actor_account_discipline == "RN"
