from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.body_systems import BodySystemsAssessment, ReviewException, SystemAssessment
from app.models.patient import Patient

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"BODYSYS-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_assessment(db_session, patient, tenant_id, **overrides):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_mode="routine_rn",
        status="draft",
    )
    defaults.update(overrides)
    assessment = BodySystemsAssessment(**defaults)
    db_session.add(assessment)
    db_session.commit()
    return assessment


class TestBodySystemsAssessment:
    def test_creates_with_defaults(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        db_session.refresh(assessment)
        assert assessment.status == "draft"
        assert assessment.version == 1
        assert assessment.started_at is not None

    def test_rejects_invalid_visit_mode(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        with pytest.raises(IntegrityError):
            _make_assessment(db_session, patient, uuid.UUID(tenant.id), visit_mode="not_a_real_mode")
        db_session.rollback()

    def test_rejects_invalid_status(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        with pytest.raises(IntegrityError):
            _make_assessment(db_session, patient, uuid.UUID(tenant.id), status="not_a_real_status")
        db_session.rollback()


class TestSystemAssessment:
    def test_creates_respiratory_row_with_verified_field_data(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        system_assessment = SystemAssessment(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant.id),
            body_systems_assessment_id=assessment.id,
            system="respiratory",
            situation="no_current_concern",
            review_state="reviewed",
            data={"respiratory_overview": "No Current Respiratory Concern"},
        )
        db_session.add(system_assessment)
        db_session.commit()
        db_session.refresh(system_assessment)

        assert system_assessment.data["respiratory_overview"] == "No Current Respiratory Concern"
        assert system_assessment.version == 1

    def test_rejects_invalid_system_code(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        system_assessment = SystemAssessment(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant.id),
            body_systems_assessment_id=assessment.id,
            system="not_a_real_system",
        )
        db_session.add(system_assessment)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_rejects_invalid_situation(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        system_assessment = SystemAssessment(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant.id),
            body_systems_assessment_id=assessment.id,
            system="respiratory",
            situation="not_a_real_situation",
        )
        db_session.add(system_assessment)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_enforces_one_row_per_system_per_assessment(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        db_session.add(
            SystemAssessment(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant.id),
                body_systems_assessment_id=assessment.id,
                system="respiratory",
            )
        )
        db_session.commit()

        db_session.add(
            SystemAssessment(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant.id),
                body_systems_assessment_id=assessment.id,
                system="respiratory",
            )
        )
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestReviewException:
    def test_creates_record_blocking_exception(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        exception = ReviewException(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant.id),
            body_systems_assessment_id=assessment.id,
            system="respiratory",
            type="unable_to_assess",
            message="respiratory is marked unable to assess but has no documented limitation (scope and reason).",
            blocking_level="record_blocking",
        )
        db_session.add(exception)
        db_session.commit()
        db_session.refresh(exception)

        assert exception.status == "open"
        assert exception.resolved_at is None

    def test_rejects_resolved_status_without_resolved_at(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        exception = ReviewException(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant.id),
            body_systems_assessment_id=assessment.id,
            system="respiratory",
            type="unable_to_assess",
            message="test",
            blocking_level="record_blocking",
            status="resolved",
            resolved_at=None,
        )
        db_session.add(exception)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_cascade_deletes_with_parent_assessment(self, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        assessment = _make_assessment(db_session, patient, uuid.UUID(tenant.id))

        db_session.add(
            ReviewException(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant.id),
                body_systems_assessment_id=assessment.id,
                system="respiratory",
                type="unable_to_assess",
                message="test",
                blocking_level="informational",
            )
        )
        db_session.commit()

        db_session.delete(assessment)
        db_session.commit()

        remaining = (
            db_session.query(ReviewException)
            .filter(ReviewException.body_systems_assessment_id == assessment.id)
            .count()
        )
        assert remaining == 0
