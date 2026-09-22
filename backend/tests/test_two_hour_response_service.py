from __future__ import annotations

"""
Acceptance tests for the California Two-Hour In-Person Licensed-Nurse
Response service (issue #143; Title 22 Section 74820/74848).
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_response import PatientResponseAuditEvent, PatientResponseEvent
from app.services import two_hour_response_service as svc
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"THR-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="COPD",
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


def _received_at():
    return datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)


def test_event_deadline_is_received_at_plus_two_hours(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)

    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="New onset dyspnea reported by caregiver",
        created_by_user_id=TEST_USER_ID,
    )
    db_session.commit()

    assert event.response_deadline_at == _received_at() + timedelta(hours=2)

    audit = (
        db_session.query(PatientResponseAuditEvent)
        .filter(PatientResponseAuditEvent.patient_response_event_id == event.id)
        .all()
    )
    assert any(a.event_type == "REQUIREMENT_CREATED" for a in audit)


def test_assignment_and_reassignment_do_not_change_deadline(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="SAFETY_CONCERN",
        received_at=_received_at(),
        description="Fall risk reported",
        created_by_user_id=TEST_USER_ID,
    )
    original_deadline = event.response_deadline_at

    assignment_1 = svc.assign_nurse(
        db_session,
        event=event,
        nurse_user_id=TEST_USER_ID,
        assigned_at=_received_at() + timedelta(minutes=5),
        created_by_user_id=TEST_USER_ID,
    )
    svc.record_dispatch(db_session, assignment=assignment_1, dispatched_at=_received_at() + timedelta(minutes=10))

    assignment_2 = svc.assign_nurse(
        db_session,
        event=event,
        nurse_user_id=TEST_USER_ID,
        assigned_at=_received_at() + timedelta(minutes=20),
        reassigned_from_assignment_id=assignment_1.id,
        reassignment_reason="Original nurse unavailable",
        created_by_user_id=TEST_USER_ID,
    )
    db_session.commit()

    assert event.response_deadline_at == original_deadline
    assert assignment_2.reassigned_from_assignment_id == assignment_1.id


def test_reassignment_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="Pain crisis",
        created_by_user_id=TEST_USER_ID,
    )
    assignment_1 = svc.assign_nurse(
        db_session, event=event, nurse_user_id=TEST_USER_ID, assigned_at=_received_at(), created_by_user_id=TEST_USER_ID
    )

    with pytest.raises(svc.TwoHourResponseError):
        svc.assign_nurse(
            db_session,
            event=event,
            nurse_user_id=TEST_USER_ID,
            assigned_at=_received_at() + timedelta(minutes=15),
            reassigned_from_assignment_id=assignment_1.id,
            created_by_user_id=TEST_USER_ID,
        )


def test_on_time_in_person_arrival_stops_clock(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="Respiratory distress",
        created_by_user_id=TEST_USER_ID,
    )
    assignment = svc.assign_nurse(
        db_session, event=event, nurse_user_id=TEST_USER_ID, assigned_at=_received_at(), created_by_user_id=TEST_USER_ID
    )

    svc.record_in_person_arrival(
        db_session,
        event=event,
        assignment=assignment,
        arrived_at=_received_at() + timedelta(hours=1, minutes=30),
        created_by_user_id=TEST_USER_ID,
    )
    db_session.commit()

    assert assignment.is_late is False
    assert assignment.arrived_at is not None


def test_late_arrival_requires_variance_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="Uncontrolled symptoms",
        created_by_user_id=TEST_USER_ID,
    )
    assignment = svc.assign_nurse(
        db_session, event=event, nurse_user_id=TEST_USER_ID, assigned_at=_received_at(), created_by_user_id=TEST_USER_ID
    )

    with pytest.raises(svc.TwoHourResponseError):
        svc.record_in_person_arrival(
            db_session,
            event=event,
            assignment=assignment,
            arrived_at=_received_at() + timedelta(hours=3),
            created_by_user_id=TEST_USER_ID,
        )

    svc.record_in_person_arrival(
        db_session,
        event=event,
        assignment=assignment,
        arrived_at=_received_at() + timedelta(hours=3),
        variance_reason="Severe weather delayed travel",
        created_by_user_id=TEST_USER_ID,
    )
    db_session.commit()
    assert assignment.is_late is True

    audit_types = {
        a.event_type
        for a in db_session.query(PatientResponseAuditEvent)
        .filter(PatientResponseAuditEvent.patient_response_event_id == event.id)
        .all()
    }
    assert "DEADLINE_MISSED" in audit_types


def test_interim_support_does_not_satisfy_arrival_requirement(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="SAFETY_CONCERN",
        received_at=_received_at(),
        description="Wandering risk",
        created_by_user_id=TEST_USER_ID,
    )
    svc.record_interim_support(
        db_session,
        event=event,
        support_type="TELEPHONE",
        provided_at=_received_at() + timedelta(minutes=10),
        provided_by_user_id=TEST_USER_ID,
    )
    db_session.commit()

    with pytest.raises(svc.TwoHourResponseError):
        svc.close_patient_response_event(db_session, event=event, closed_at=datetime.now(timezone.utc))


def test_close_requires_patient_response_after_arrival(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="Severe pain",
        created_by_user_id=TEST_USER_ID,
    )
    assignment = svc.assign_nurse(
        db_session, event=event, nurse_user_id=TEST_USER_ID, assigned_at=_received_at(), created_by_user_id=TEST_USER_ID
    )
    svc.record_in_person_arrival(
        db_session,
        event=event,
        assignment=assignment,
        arrived_at=_received_at() + timedelta(minutes=45),
        created_by_user_id=TEST_USER_ID,
    )
    intervention = svc.record_intervention(
        db_session,
        event=event,
        assignment=assignment,
        intervention_type="PAIN_MANAGEMENT",
        description="Administered PRN morphine per order",
        performed_at=_received_at() + timedelta(minutes=50),
        performed_by_user_id=TEST_USER_ID,
    )

    # Arrival recorded but no patient response yet -> must not close.
    with pytest.raises(svc.TwoHourResponseError):
        svc.close_patient_response_event(db_session, event=event, closed_at=datetime.now(timezone.utc))

    svc.record_patient_response(
        db_session,
        event=event,
        intervention=intervention,
        patient_response_recorded_at=_received_at() + timedelta(hours=1),
        patient_response_summary="Pain reduced from 8/10 to 3/10; patient resting comfortably",
        actor_user_id=TEST_USER_ID,
    )
    closed = svc.close_patient_response_event(
        db_session, event=event, closed_at=_received_at() + timedelta(hours=1, minutes=5)
    )
    db_session.commit()

    assert closed.closed_at is not None


def test_idg_notification_does_not_stop_clock_or_substitute_for_response(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    event = svc.create_patient_response_event(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        event_type="MEDICAL_NEED",
        received_at=_received_at(),
        description="Symptom escalation",
        created_by_user_id=TEST_USER_ID,
    )
    assignment = svc.assign_nurse(
        db_session, event=event, nurse_user_id=TEST_USER_ID, assigned_at=_received_at(), created_by_user_id=TEST_USER_ID
    )
    intervention = svc.record_intervention(
        db_session,
        event=event,
        assignment=assignment,
        intervention_type="ASSESSMENT",
        description="Full symptom assessment",
        performed_at=_received_at() + timedelta(minutes=5),
        performed_by_user_id=TEST_USER_ID,
    )
    svc.record_idg_notification(
        db_session, event=event, intervention=intervention, idg_notified_at=_received_at() + timedelta(minutes=6)
    )
    db_session.commit()

    # Arrival still not recorded -- must not be closeable despite IDG notification.
    with pytest.raises(svc.TwoHourResponseError):
        svc.close_patient_response_event(db_session, event=event, closed_at=datetime.now(timezone.utc))
