from __future__ import annotations

"""
Acceptance tests for the IDG follow-up service (issue #143 layer,
app.services.idg_follow_up_service): creation/required-fields, multi-
discipline contribution, assignment/reassignment with reason+history,
completion gating, persistent/worsening continuing-plan requirement,
reopen, audit events, backward-compat with existing idg_reviews rows,
and cross-tenant rejection.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.idg_review import IDGReview, IDGReviewAuditEvent
from app.models.patient import Patient
from app.models.record_version import RecordVersion
from app.services import clinical_outcome_service as co_svc
from app.services import idg_follow_up_service as svc
from app.services import two_hour_response_service as thr_svc
from tests.conftest import TEST_USER_ID

OTHER_USER_ID = TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"IDGF-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1935, 8, 12),
        primary_diagnosis="ALS",
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


def _make_clinical_outcome_record(db_session, tenant_id):
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = thr_svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc),
        description="Worsening pain reported",
        created_by_user_id=TEST_USER_ID,
    )
    record = co_svc.create_outcome_from_patient_response_event(
        db_session, event=event, actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    return patient, admission, record


def _make_follow_up(db_session, tenant_id):
    patient, admission, record = _make_clinical_outcome_record(db_session, tenant_id)
    review = svc.create_idg_follow_up(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        desired_patient_outcome="Adequate pain control within 24 hours",
        follow_up_action="MSW and RN joint visit to reassess pain plan",
        follow_up_due_date=datetime.now(timezone.utc) + timedelta(days=1),
        source_clinical_outcome_record_id=record.id,
        created_by_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    return patient, admission, record, review


# ---------------------------------------------------------------------
# Creation / required fields
# ---------------------------------------------------------------------


def test_create_requires_desired_patient_outcome(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, record = _make_clinical_outcome_record(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.create_idg_follow_up(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            desired_patient_outcome="",
            follow_up_action="Reassess",
            follow_up_due_date=datetime.now(timezone.utc),
            source_clinical_outcome_record_id=record.id,
            created_by_user_id=TEST_USER_ID,
        )


def test_create_requires_follow_up_action(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, record = _make_clinical_outcome_record(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.create_idg_follow_up(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            desired_patient_outcome="Adequate pain control",
            follow_up_action="",
            follow_up_due_date=datetime.now(timezone.utc),
            source_clinical_outcome_record_id=record.id,
            created_by_user_id=TEST_USER_ID,
        )


def test_create_requires_follow_up_due_date(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, record = _make_clinical_outcome_record(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.create_idg_follow_up(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            desired_patient_outcome="Adequate pain control",
            follow_up_action="Reassess",
            follow_up_due_date=None,
            source_clinical_outcome_record_id=record.id,
            created_by_user_id=TEST_USER_ID,
        )


def test_create_requires_a_source_link(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, record = _make_clinical_outcome_record(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.create_idg_follow_up(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            desired_patient_outcome="Adequate pain control",
            follow_up_action="Reassess",
            follow_up_due_date=datetime.now(timezone.utc),
            created_by_user_id=TEST_USER_ID,
        )


def test_create_success_path_reuses_idg_reviews_table(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient, admission, record, review = _make_follow_up(db_session, tenant_id)
    assert isinstance(review, IDGReview)
    assert review.follow_up_required is True
    assert review.source_clinical_outcome_record_id == record.id
    assert review.desired_patient_outcome.startswith("Adequate pain control")


def test_create_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(IDGReviewAuditEvent.idg_review_id == review.id)
        .all()
    )
    assert any(e.event_type == "IDG_FOLLOW_UP_CREATED" for e in events)


def test_get_idg_follow_up_rejects_cross_tenant(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    other_tenant_id = uuid.uuid4()
    with pytest.raises(svc.IDGFollowUpError):
        svc.get_idg_follow_up(db_session, tenant_id=other_tenant_id, idg_review_id=review.id)


# ---------------------------------------------------------------------
# Multi-discipline contribution
# ---------------------------------------------------------------------


def test_multiple_disciplines_can_each_record_a_recommendation(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.record_idg_recommendation(
        db_session, review=review, summary="RN: adjust medication timing", actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    svc.record_idg_recommendation(
        db_session, review=review, summary="MSW: arrange caregiver respite", actor_user_id=TEST_USER_ID, actor_account_discipline="MSW"
    )
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "IDG_RECOMMENDATION_RECORDED",
        )
        .all()
    )
    assert len(events) == 2
    disciplines = {e.actor_account_discipline for e in events}
    assert disciplines == {"RN", "MSW"}


# ---------------------------------------------------------------------
# Assignment / reassignment
# ---------------------------------------------------------------------


def test_assign_follow_up_sets_status_assigned(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.assign_follow_up(
        db_session,
        review=review,
        assigned_to_user_id=TEST_USER_ID,
        assigned_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert review.follow_up_status == "ASSIGNED"
    assert review.follow_up_assigned_to_user_id == TEST_USER_ID


def test_reassignment_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.assign_follow_up(
        db_session,
        review=review,
        assigned_to_user_id=TEST_USER_ID,
        assigned_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    with pytest.raises(svc.IDGFollowUpError):
        svc.assign_follow_up(
            db_session,
            review=review,
            assigned_to_user_id=OTHER_USER_ID,
            assigned_at=datetime.now(timezone.utc),
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_reassignment_preserves_history_via_record_version(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    first_assigned_at = datetime.now(timezone.utc)
    svc.assign_follow_up(
        db_session,
        review=review,
        assigned_to_user_id=TEST_USER_ID,
        assigned_at=first_assigned_at,
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    svc.assign_follow_up(
        db_session,
        review=review,
        assigned_to_user_id=OTHER_USER_ID,
        assigned_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
        reassignment_reason="Original assignee unavailable",
    )
    version = (
        db_session.query(RecordVersion)
        .filter(RecordVersion.source_record_type == "IDG_REVIEW", RecordVersion.source_record_id == review.id)
        .first()
    )
    assert version is not None
    assert version.snapshot["follow_up_assigned_to_user_id"] == str(TEST_USER_ID)
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "FOLLOW_UP_REASSIGNED",
        )
        .all()
    )
    assert len(events) == 1


def test_initial_assignment_does_not_require_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    # No reassignment_reason supplied -- must succeed for a first-time assignment.
    svc.assign_follow_up(
        db_session,
        review=review,
        assigned_to_user_id=TEST_USER_ID,
        assigned_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "FOLLOW_UP_ASSIGNED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# Progress / linking
# ---------------------------------------------------------------------


def test_record_progress_sets_in_progress_status(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.record_progress(db_session, review=review, notes="Visit scheduled for tomorrow", actor_user_id=TEST_USER_ID, actor_account_discipline="RN")
    assert review.follow_up_status == "IN_PROGRESS"
    assert review.poc_action == "Visit scheduled for tomorrow"


def test_link_patient_response(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, record, review = _make_follow_up(db_session, tenant_id)
    other_patient, other_admission, other_record = _make_clinical_outcome_record(db_session, tenant_id)
    svc.link_patient_response(
        db_session, review=review, clinical_outcome_record_id=other_record.id, actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    assert review.source_clinical_outcome_record_id == other_record.id
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "PATIENT_RESPONSE_LINKED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# Completion gating
# ---------------------------------------------------------------------


def test_cannot_complete_without_linked_clinical_outcome_record(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = thr_svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc),
        description="Test",
        created_by_user_id=TEST_USER_ID,
    )
    review = svc.create_idg_follow_up(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        desired_patient_outcome="Comfort achieved",
        follow_up_action="Reassess",
        follow_up_due_date=datetime.now(timezone.utc),
        source_patient_response_event_id=event.id,
        created_by_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.IDGFollowUpError):
        svc.complete_follow_up(
            db_session, review=review, closure_summary="Resolved", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_cannot_complete_without_closure_summary(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.complete_follow_up(
            db_session, review=review, closure_summary="", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
        )


def test_remaining_need_requires_continuing_plan_before_completion(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.complete_follow_up(
            db_session,
            review=review,
            closure_summary="Some progress but pain persists",
            completed_at=datetime.now(timezone.utc),
            remaining_need=True,
            continuing_plan=None,
            actor_user_id=TEST_USER_ID,
            actor_account_discipline="RN",
        )


def test_complete_follow_up_success_path(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session,
        review=review,
        closure_summary="Pain controlled, patient comfortable",
        completed_at=datetime.now(timezone.utc),
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert review.follow_up_status == "COMPLETED"
    assert review.closure_summary == "Pain controlled, patient comfortable"


def test_complete_follow_up_with_remaining_need_and_continuing_plan(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session,
        review=review,
        closure_summary="Partial improvement",
        completed_at=datetime.now(timezone.utc),
        remaining_need=True,
        continuing_plan="Continue current regimen and reassess at next IDG",
        actor_user_id=TEST_USER_ID,
        actor_account_discipline="RN",
    )
    assert review.continuing_plan == "Continue current regimen and reassess at next IDG"


def test_complete_follow_up_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session, review=review, closure_summary="Resolved", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "FOLLOW_UP_COMPLETED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# Reopen
# ---------------------------------------------------------------------


def test_reopen_requires_completed_status(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    with pytest.raises(svc.IDGFollowUpError):
        svc.reopen_follow_up(db_session, review=review, reopen_reason="Need more work", actor_user_id=TEST_USER_ID, actor_account_discipline="RN")


def test_reopen_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session, review=review, closure_summary="Resolved", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.IDGFollowUpError):
        svc.reopen_follow_up(db_session, review=review, reopen_reason="", actor_user_id=TEST_USER_ID, actor_account_discipline="RN")


def test_reopen_requires_authorized_actor(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session, review=review, closure_summary="Resolved", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    with pytest.raises(svc.IDGFollowUpError):
        svc.reopen_follow_up(db_session, review=review, reopen_reason="More work needed", actor_user_id=None, actor_account_discipline="RN")


def test_reopen_success_path(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, _, _, review = _make_follow_up(db_session, tenant_id)
    svc.complete_follow_up(
        db_session, review=review, closure_summary="Resolved", completed_at=datetime.now(timezone.utc), actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    svc.reopen_follow_up(db_session, review=review, reopen_reason="Symptoms recurred", actor_user_id=TEST_USER_ID, actor_account_discipline="RN")
    assert review.follow_up_status == "IN_PROGRESS"
    assert review.follow_up_completed_at is None
    assert review.reopen_reason == "Symptoms recurred"

    events = (
        db_session.query(IDGReviewAuditEvent)
        .filter(
            IDGReviewAuditEvent.idg_review_id == review.id,
            IDGReviewAuditEvent.event_type == "FOLLOW_UP_REOPENED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# Backward compatibility with existing idg_reviews rows
# ---------------------------------------------------------------------


def test_existing_idg_review_rows_without_follow_up_fields_are_unaffected(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    legacy_review = IDGReview(
        tenant_id=tenant_id,
        patient_id=patient.id,
        review_date=datetime.now(timezone.utc),
        summary="Routine IDG discussion, no follow-up needed",
        is_finalized=True,
        created_by=TEST_USER_ID,
    )
    db_session.add(legacy_review)
    db_session.commit()

    fetched = db_session.get(IDGReview, legacy_review.id)
    assert fetched.follow_up_required is False
    assert fetched.follow_up_status is None
    assert fetched.desired_patient_outcome is None
