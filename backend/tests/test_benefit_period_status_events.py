"""
Dedicated tests for BenefitPeriodStatusEvent (Eligibility Traceability
Epic, Workstream 1) -- the append-only, actor-attributed audit trail
behind every BenefitPeriod lifecycle action.

These tests exercise ONLY the behavior actually implemented in
app.services.benefit_period_service (rollover_benefit_period /
record_benefit_period_event). Nothing here asserts a guarantee that
doesn't already exist in the source; where a guarantee doesn't hold,
the source is the thing that gets fixed, not the test.
"""

from __future__ import annotations

import threading
import uuid
from datetime import date

import pytest
from sqlalchemy import inspect as sa_inspect

from app.models.benefit_period import BenefitPeriod
from app.models.benefit_period_status_event import BenefitPeriodStatusEvent
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.services import benefit_period_service as svc
from app.services.benefit_period_service import rollover_benefit_period
from tests.conftest import TEST_USER_ID, TestSessionLocal


def _make_patient(db_session, tenant_id, **overrides):
    kwargs = dict(
        tenant_id=tenant_id,
        mrn=f"BPE-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1935, 6, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=TEST_USER_ID,
    )
    kwargs.update(overrides)
    patient = Patient(**kwargs)
    db_session.add(patient)
    db_session.flush()
    return patient


def _events_for(db_session, benefit_period_id):
    return (
        db_session.query(BenefitPeriodStatusEvent)
        .filter(BenefitPeriodStatusEvent.benefit_period_id == benefit_period_id)
        .order_by(BenefitPeriodStatusEvent.occurred_at.asc())
        .all()
    )


class TestDatabaseLevelConstraints:
    """
    Constraint tests that go around the service layer entirely -- raw
    ORM inserts against the mapped tables -- to confirm the schema itself
    (not just application code) enforces the guarantees this workstream
    depends on.
    """

    def test_actor_user_id_is_not_null_at_db_level(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()
        bp = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )

        from sqlalchemy.exc import IntegrityError

        event = BenefitPeriodStatusEvent(
            tenant_id=tenant.id,
            benefit_period_id=bp.id,
            event_type="CORRECTED",
            actor_user_id=None,
            new_value={"note": "missing actor"},
        )
        db_session.add(event)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_benefit_period_id_foreign_key_is_enforced(self, db_session, tenant):
        from sqlalchemy.exc import IntegrityError

        event = BenefitPeriodStatusEvent(
            tenant_id=tenant.id,
            benefit_period_id=uuid.uuid4(),
            event_type="CREATED",
            actor_user_id=TEST_USER_ID,
            new_value={"note": "orphan"},
        )
        db_session.add(event)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_duplicate_benefit_period_violates_unique_constraint(
        self, db_session, tenant
    ):
        """
        Direct proof (bypassing the service's idempotency check and
        IntegrityError-recovery path entirely) that the raw schema itself
        rejects a duplicate (tenant_id, patient_id, benefit_type,
        start_date) row -- the backstop migration v3w4x5y6z7a8 depends on.
        """
        from sqlalchemy.exc import IntegrityError

        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        bp1 = BenefitPeriod(
            tenant_id=tenant.id,
            patient_id=patient.id,
            benefit_type="INITIAL",
            period_number=1,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            is_current=True,
            created_by=TEST_USER_ID,
        )
        db_session.add(bp1)
        db_session.commit()

        bp2_duplicate = BenefitPeriod(
            tenant_id=tenant.id,
            patient_id=patient.id,
            benefit_type="INITIAL",
            period_number=2,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            is_current=True,
            created_by=TEST_USER_ID,
        )
        db_session.add(bp2_duplicate)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()


class TestBenefitPeriodStatusEventCreation:
    def test_initial_rollover_creates_created_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        bp = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )

        events = _events_for(db_session, bp.id)
        assert len(events) == 1
        assert events[0].event_type == "CREATED"
        assert events[0].previous_value is None
        assert events[0].new_value["id"] == str(bp.id)
        assert events[0].actor_user_id == TEST_USER_ID

    def test_second_rollover_creates_rolled_event_with_previous_snapshot(
        self, db_session, tenant
    ):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        bp1 = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )
        bp2 = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 4, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )

        bp2_events = _events_for(db_session, bp2.id)
        assert len(bp2_events) == 1
        assert bp2_events[0].event_type == "ROLLED"
        # previous_value is the snapshot of bp1 as it stood *before* being
        # closed (is_current still True) -- taken prior to the close step.
        assert bp2_events[0].previous_value["id"] == str(bp1.id)
        assert bp2_events[0].previous_value["is_current"] is True
        assert bp2_events[0].new_value["id"] == str(bp2.id)
        assert bp2_events[0].new_value["is_current"] is True


class TestActorAttributionRequired:
    def test_actor_user_id_required_kwarg(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        with pytest.raises(TypeError):
            rollover_benefit_period(
                db_session,
                tenant_id=tenant.id,
                patient_id=patient.id,
                election_date=date(2025, 1, 1),
                start_date=date(2025, 1, 1),
                benefit_type="INITIAL",
            )  # type: ignore[call-arg]


class TestTransactionalIntegrity:
    def test_event_write_failure_rolls_back_benefit_period_mutation(
        self, db_session, tenant, monkeypatch
    ):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        def _boom(*args, **kwargs):
            raise RuntimeError("simulated event-write failure")

        monkeypatch.setattr(svc, "record_benefit_period_event", _boom)

        with pytest.raises(RuntimeError):
            rollover_benefit_period(
                db_session,
                tenant_id=tenant.id,
                patient_id=patient.id,
                election_date=date(2025, 1, 1),
                start_date=date(2025, 1, 1),
                benefit_type="INITIAL",
                actor_user_id=TEST_USER_ID,
            )

        db_session.rollback()

        bp_rows = (
            db_session.query(BenefitPeriod)
            .filter(BenefitPeriod.patient_id == patient.id)
            .all()
        )
        assert bp_rows == []

        event_rows = (
            db_session.query(BenefitPeriodStatusEvent)
            .join(
                BenefitPeriod,
                BenefitPeriodStatusEvent.benefit_period_id == BenefitPeriod.id,
            )
            .filter(BenefitPeriod.patient_id == patient.id)
            .all()
        )
        assert event_rows == []


class TestTenantIsolation:
    def test_cross_tenant_patient_rejected_no_rows_created(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id)

        other_tenant_id = uuid.uuid4()
        db_session.add(
            Tenant(
                id=other_tenant_id,
                legal_name="Other Agency (BPE isolation test)",
                display_name="Other Agency",
                npi=f"{other_tenant_id.int % 10**10:010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()

        with pytest.raises(ValueError, match="Patient not found for tenant"):
            rollover_benefit_period(
                db_session,
                tenant_id=other_tenant_id,
                patient_id=patient.id,
                election_date=date(2025, 1, 1),
                start_date=date(2025, 1, 1),
                benefit_type="INITIAL",
                actor_user_id=TEST_USER_ID,
            )

        db_session.rollback()

        assert (
            db_session.query(BenefitPeriod)
            .filter(BenefitPeriod.tenant_id == other_tenant_id)
            .count()
            == 0
        )


class TestForwardLinkageDeferred:
    def test_related_certification_id_not_populated_by_workstream_one(
        self, db_session, tenant
    ):
        """
        Certification -> BenefitPeriod linkage is Workstream 6, explicitly
        deferred pending product review. This test locks in the CURRENT,
        correct behavior (nullable, unpopulated) so a future change to
        this is a deliberate decision, not an accidental regression.
        """
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        bp = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )

        events = _events_for(db_session, bp.id)
        assert events[0].related_certification_id is None


class TestIdempotentRetry:
    def test_duplicate_retry_does_not_create_new_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        bp_first = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )
        bp_retry = rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )

        assert bp_first.id == bp_retry.id
        assert len(_events_for(db_session, bp_first.id)) == 1


class TestConcurrentRolloverSafety:
    def test_concurrent_rollover_serializes_via_row_locking(self, db_session, tenant):
        """
        `.with_for_update()` locks existing BP rows for a patient/tenant,
        which serializes most concurrent rollover attempts. But PostgreSQL
        READ COMMITTED does not retroactively surface a competing,
        already-committed transaction's brand-new INSERT to a query that
        was blocked waiting on a *different*, existing row -- so two truly
        concurrent attempts to create the same "next" benefit period can
        still both pass the in-memory idempotency check and attempt to
        insert. The database-level unique constraint (migration
        v3w4x5y6z7a8) plus the IntegrityError-recovery path in
        rollover_benefit_period() is what actually closes this race,
        confirmed here by driving two real, separate DB sessions from two
        threads released at the same instant via a Barrier (not a mocked
        substitute for concurrency).
        """
        patient = _make_patient(db_session, tenant.id)
        db_session.commit()

        rollover_benefit_period(
            db_session,
            tenant_id=tenant.id,
            patient_id=patient.id,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            benefit_type="INITIAL",
            actor_user_id=TEST_USER_ID,
        )
        db_session.commit()

        results: list = []
        errors: list = []
        barrier = threading.Barrier(2)

        def _attempt():
            session = TestSessionLocal()
            try:
                barrier.wait(timeout=10)
                bp = rollover_benefit_period(
                    session,
                    tenant_id=tenant.id,
                    patient_id=patient.id,
                    election_date=date(2025, 1, 1),
                    start_date=date(2025, 4, 1),
                    benefit_type="INITIAL",
                    actor_user_id=TEST_USER_ID,
                )
                results.append(bp.id)
            except Exception as exc:  # pragma: no cover - diagnostic only
                errors.append(exc)
            finally:
                session.close()

        threads = [threading.Thread(target=_attempt) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"unexpected errors from concurrent attempts: {errors}"
        assert len(results) == 2

        # Both threads must resolve to the SAME row (one created it, the
        # other recovered the IntegrityError from the unique constraint
        # and re-fetched the winning row) -- never two distinct
        # period_number=2 rows for the same patient.
        assert results[0] == results[1]

        second_period_rows = (
            db_session.query(BenefitPeriod)
            .filter(
                BenefitPeriod.patient_id == patient.id,
                BenefitPeriod.period_number == 2,
            )
            .all()
        )
        assert len(second_period_rows) == 1


class TestEventImmutabilityContract:
    def test_no_update_or_delete_function_exists_for_status_events(self):
        """
        BenefitPeriodStatusEvent is append-only by convention (mirroring
        CertificationStatusEvent / AdmissionStatusHistory): there is no
        service-layer function that updates or deletes an existing event
        row. This test locks in that contract at the code level so an
        update/delete path can't be added without a deliberate,
        reviewable change to this test.
        """
        public_names = [name for name in dir(svc) if not name.startswith("_")]
        mutating_names = [
            name
            for name in public_names
            if ("update" in name.lower() or "delete" in name.lower())
            and "event" in name.lower()
        ]
        assert mutating_names == []

    def test_status_event_table_has_no_onupdate_columns(self):
        """
        Only audit-content columns must never be mutated in place. The
        inherited BaseModel bookkeeping column `updated_at` legitimately
        carries an onupdate clause (standard across every model in this
        codebase) and isn't itself proof of a mutable audit record --
        what matters is that the actual event content columns never do.
        """
        mutable_content_columns = {
            "event_type",
            "actor_user_id",
            "occurred_at",
            "reason",
            "previous_value",
            "new_value",
            "related_certification_id",
        }
        mapper = sa_inspect(BenefitPeriodStatusEvent)
        for column in mapper.columns:
            if column.name not in mutable_content_columns:
                continue
            assert column.onupdate is None, (
                f"{column.name} has an onupdate clause -- "
                "BenefitPeriodStatusEvent must remain append-only"
            )
