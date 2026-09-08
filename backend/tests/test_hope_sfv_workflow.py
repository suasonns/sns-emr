from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.sfv_requirement import SFVRequirement
from app.models.visit import Visit
from app.services.hope_phase_b_engine import (
    SOURCE_RN_VISIT,
    complete_sfv_requirement_from_visit,
    detect_huv_designation_opportunity,
    process_rn_visit_finalize_for_sfv,
    TASK_TYPE_HUV1,
)
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1938, 2, 14),
        primary_diagnosis="Chronic obstructive pulmonary disease",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id, election_date: datetime):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=election_date,
        effective_date=election_date,
        election_signed_at=election_date,
        soc_date=election_date,
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_visit(db_session, patient, admission, tenant_id, *, visit_datetime, discipline="RN"):
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type=discipline,
        visit_discipline=discipline,
        visit_mode="IN_PERSON",
        visit_datetime=visit_datetime,
        status="FINALIZED",
        finalized_at=visit_datetime,
        created_by=TEST_USER_ID,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


def test_rn_visit_with_moderate_symptom_creates_sfv_requirement(db_session):
    """Scenario 1 setup: Day 8 RN visit, moderate SOB found -> SFV generated."""
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    trigger_visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=trigger_visit.id,
        visit_datetime=trigger_visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )

    assert outcome.created is True
    requirement = db_session.query(SFVRequirement).filter(SFVRequirement.id == outcome.requirement_id).first()
    assert requirement is not None
    assert requirement.trigger_source_type == SOURCE_RN_VISIT
    assert requirement.trigger_reference_id == trigger_visit.id
    assert requirement.status == "OPEN"
    assert requirement.due_at == trigger_visit.visit_datetime + timedelta(days=2)


def test_rn_visit_without_symptom_trigger_creates_no_sfv(db_session):
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=visit.id,
        visit_datetime=visit.visit_datetime,
        j2051_pain_impact="MILD",
        j2051_non_pain_impact=None,
    )

    assert outcome.created is False
    assert db_session.query(SFVRequirement).filter(SFVRequirement.trigger_reference_id == visit.id).count() == 0


def test_sfv_completed_same_day_by_rn_is_valid(db_session):
    """Scenario 1: same-day RN follow-up visit is a valid, separate SFV completion."""
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    trigger_visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=trigger_visit.id,
        visit_datetime=trigger_visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )

    same_day_followup = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=trigger_visit.visit_datetime + timedelta(hours=5),
        discipline="RN",
    )

    completed = complete_sfv_requirement_from_visit(
        db=db_session,
        sfv_requirement_id=outcome.requirement_id,
        completing_visit_id=same_day_followup.id,
        completing_visit_datetime=same_day_followup.visit_datetime,
        discipline="RN",
        visit_mode="IN_PERSON",
    )

    assert completed.status == "COMPLETED"
    assert completed.completed_visit_id == same_day_followup.id


def test_sfv_completed_same_day_by_lvn_is_valid(db_session):
    """Scenario 2: same-day LVN follow-up visit is also a valid SFV completion."""
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    trigger_visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=trigger_visit.id,
        visit_datetime=trigger_visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="SEVERE",
    )

    same_day_lvn_followup = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=trigger_visit.visit_datetime + timedelta(hours=5),
        discipline="LVN",
    )

    completed = complete_sfv_requirement_from_visit(
        db=db_session,
        sfv_requirement_id=outcome.requirement_id,
        completing_visit_id=same_day_lvn_followup.id,
        completing_visit_datetime=same_day_lvn_followup.visit_datetime,
        discipline="LVN",
        visit_mode="IN_PERSON",
    )

    assert completed.status == "COMPLETED"


def test_sfv_completed_36_hours_later_is_valid(db_session):
    """Scenario 3: follow-up visit 36 hours later, still within the 48-hour window."""
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    trigger_visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=trigger_visit.id,
        visit_datetime=trigger_visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )

    followup = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=trigger_visit.visit_datetime + timedelta(hours=36),
        discipline="RN",
    )

    completed = complete_sfv_requirement_from_visit(
        db=db_session,
        sfv_requirement_id=outcome.requirement_id,
        completing_visit_id=followup.id,
        completing_visit_datetime=followup.visit_datetime,
        discipline="RN",
        visit_mode="IN_PERSON",
    )

    assert completed.status == "COMPLETED"


def test_sfv_not_completed_within_48_hours_remains_open_and_overdue(db_session):
    """Scenario 4: no follow-up until after 48 hours -> compliance failure (still OPEN, due_at has passed)."""
    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)
    trigger_visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=8))

    outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=trigger_visit.id,
        visit_datetime=trigger_visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )

    requirement = db_session.query(SFVRequirement).filter(SFVRequirement.id == outcome.requirement_id).first()
    now_past_due = trigger_visit.visit_datetime + timedelta(hours=60)

    assert requirement.status == "OPEN"
    assert requirement.due_at < now_past_due  # 48-hour deadline has already elapsed with no completion


def test_sfv_and_huv1_opportunity_are_independent_for_same_visit(db_session):
    """
    Scenario 5: a Day 10 RN visit with a moderate symptom trigger both
    generates an SFV requirement AND still leaves the HUV1 designation
    opportunity open. Neither workflow satisfies or blocks the other.
    """
    from app.models.enums import TaskOrigin, TaskRegulatoryBasis, TaskStatus, TaskType
    from app.models.task import Task

    tenant_id = db_session.info.get("tenant_id")
    soc = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, soc)

    huv1_task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.HUV1,
        origin=TaskOrigin.SYSTEM,
        discipline="RN",
        regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
        status=TaskStatus.PENDING,
        due_at=soc + timedelta(days=15),
        due_date=(soc + timedelta(days=15)).date(),
    )
    db_session.add(huv1_task)
    db_session.commit()

    visit = _make_visit(db_session, patient, admission, tenant_id, visit_datetime=soc + timedelta(days=10))

    sfv_outcome = process_rn_visit_finalize_for_sfv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=visit.id,
        visit_datetime=visit.visit_datetime,
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )
    assert sfv_outcome.created is True

    huv_opportunity = detect_huv_designation_opportunity(
        db=db_session, tenant_id=tenant_id, patient_id=patient.id, visit=visit,
    )
    assert huv_opportunity is not None
    assert huv_opportunity["huv_type"] == TASK_TYPE_HUV1

    # The HUV task itself remains untouched by the SFV trigger.
    db_session.refresh(huv1_task)
    assert huv1_task.status == TaskStatus.PENDING
