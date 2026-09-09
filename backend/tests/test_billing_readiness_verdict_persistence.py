"""
Dedicated tests for BillingReadinessVerdict (Eligibility Traceability
Epic, Workstream 3) -- the immutable, append-only history of every
billing-readiness evaluation performed by
check_patient_billing_readiness().

Reuses the fixture helpers from test_billing_readiness_service.py (the
established cross-test-module import pattern already used elsewhere in
this suite, e.g. test_facility_payment_visibility.py importing from
test_aging_report_service.py) rather than duplicating patient/benefit
period/certification/POC/payer setup.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict
from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.models.tenant import Tenant
from tests.test_billing_readiness_service import (
    SERVICE_DATE,
    _fully_ready_patient,
    _make_benefit_period,
    _make_patient,
)


def _verdicts_for(db_session, patient_id):
    return (
        db_session.query(BillingReadinessVerdict)
        .filter(BillingReadinessVerdict.patient_id == patient_id)
        .order_by(BillingReadinessVerdict.evaluated_at.asc())
        .all()
    )


class TestReadyVerdictPersistence:
    def test_ready_verdict_is_persisted(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-READY")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        assert result.ready is True
        verdicts = _verdicts_for(db_session, patient.id)
        assert len(verdicts) == 1
        assert verdicts[0].is_ready is True
        assert verdicts[0].blockers == []
        assert str(verdicts[0].benefit_period_id) == result.benefit_period_id
        assert verdicts[0].certification_id is not None


class TestBlockedVerdictPersistence:
    def test_blocked_verdict_is_persisted_with_blockers(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-VERDICT-BLOCKED")
        _make_benefit_period(db_session, tenant.id, patient)
        # No certification, no POC, no payer -> multiple blockers.

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        assert result.ready is False
        assert result.blockers != []

        verdicts = _verdicts_for(db_session, patient.id)
        assert len(verdicts) == 1
        assert verdicts[0].is_ready is False
        assert verdicts[0].blockers == result.blockers
        assert verdicts[0].certification_id is None


class TestNoBenefitPeriodVerdictPersistence:
    def test_no_benefit_period_still_persists_a_blocked_verdict(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-VERDICT-NOBP")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        assert result.ready is False
        assert result.benefit_period_id is None

        verdicts = _verdicts_for(db_session, patient.id)
        assert len(verdicts) == 1
        assert verdicts[0].benefit_period_id is None
        assert verdicts[0].is_ready is False


class TestUnknownPatientNoVerdict:
    def test_unknown_patient_creates_no_verdict(self, db_session, tenant):
        unknown_patient_id = uuid.uuid4()

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(unknown_patient_id),
            service_date=SERVICE_DATE,
        )

        assert result.ready is False
        assert "not found" in result.blockers[0].lower()
        assert _verdicts_for(db_session, unknown_patient_id) == []


class TestCrossTenantNoVerdict:
    def test_cross_tenant_patient_denied_creates_no_verdict(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-XTENANT")

        other_tenant_id = uuid.uuid4()
        db_session.add(
            Tenant(
                id=other_tenant_id,
                legal_name="Other Agency (verdict isolation test)",
                display_name="Other Agency",
                npi=f"{other_tenant_id.int % 10**10:010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=str(other_tenant_id),
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        assert result.ready is False
        assert "not found" in result.blockers[0].lower()
        # No verdict persisted at all -- neither under the real tenant
        # (this evaluation never ran under it) nor under the foreign one
        # (patient doesn't resolve there).
        assert _verdicts_for(db_session, patient.id) == []


class TestHistoricalAppendOnlyBehavior:
    def test_repeated_evaluations_append_new_verdicts_not_overwrite(
        self, db_session, tenant
    ):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-HISTORY")

        check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )
        check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        verdicts = _verdicts_for(db_session, patient.id)
        assert len(verdicts) == 2
        # Two distinct rows, not one row updated in place.
        assert verdicts[0].id != verdicts[1].id
        assert verdicts[0].evaluated_at <= verdicts[1].evaluated_at


class TestCertificationIdCapture:
    def test_finalized_certification_id_is_captured_on_ready_verdict(
        self, db_session, tenant
    ):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-CERT")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        verdicts = _verdicts_for(db_session, patient.id)
        assert verdicts[0].certification_id is not None
        # The verdict's certification_id is a real, resolvable UUID string
        # form, not a placeholder.
        uuid.UUID(str(verdicts[0].certification_id))
        assert result.blockers == []


class TestTriggeredByAttribution:
    def test_triggered_by_defaults_to_manual_check(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-TRIGGER1")

        check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        verdicts = _verdicts_for(db_session, patient.id)
        assert verdicts[0].triggered_by == "MANUAL_CHECK"

    def test_triggered_by_is_captured_when_explicitly_provided(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-TRIGGER2")

        check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
            triggered_by="SCHEDULED_CHECK",
        )

        verdicts = _verdicts_for(db_session, patient.id)
        assert verdicts[0].triggered_by == "SCHEDULED_CHECK"


class TestBlockerCodeStability:
    def test_blocked_verdict_blocker_text_matches_categorizable_prefixes(
        self, db_session, tenant
    ):
        """
        The Blocker Breakdown feature (categorize_blocker) matches on the
        raw blocker string prefixes. If check_patient_billing_readiness
        ever changes a blocker's wording without updating that mapping,
        blockers silently fall into "Other" instead of their real
        category. This test locks the current blocker text produced for
        a patient missing everything, so an accidental wording drift is
        caught here rather than only discovered downstream.
        """
        from app.billing.services.billing_readiness_service import categorize_blocker

        patient = _make_patient(db_session, tenant.id, mrn="MRN-VERDICT-BLOCKERTEXT")
        _make_benefit_period(db_session, tenant.id, patient)

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        assert result.blockers != []
        categories = {categorize_blocker(b) for b in result.blockers}
        assert "Other" not in categories


class TestReadOnlyEvaluationHasNoSideEffectsBeyondVerdict:
    def test_reading_readiness_does_not_mutate_benefit_period_or_certification(
        self, db_session, tenant
    ):
        from app.models.benefit_period import BenefitPeriod
        from app.models.certification import Certification

        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-VERDICT-READONLY")

        bp_before = (
            db_session.query(BenefitPeriod)
            .filter(BenefitPeriod.patient_id == patient.id)
            .one()
        )
        bp_snapshot_before = (
            bp_before.is_current,
            bp_before.end_date,
            bp_before.start_date,
        )
        cert_before = (
            db_session.query(Certification)
            .filter(Certification.patient_id == patient.id)
            .one()
        )
        cert_snapshot_before = (cert_before.status, cert_before.signed_at)

        check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )

        db_session.expire_all()

        bp_after = (
            db_session.query(BenefitPeriod)
            .filter(BenefitPeriod.patient_id == patient.id)
            .one()
        )
        cert_after = (
            db_session.query(Certification)
            .filter(Certification.patient_id == patient.id)
            .one()
        )

        assert (
            bp_after.is_current,
            bp_after.end_date,
            bp_after.start_date,
        ) == bp_snapshot_before
        assert (cert_after.status, cert_after.signed_at) == cert_snapshot_before
