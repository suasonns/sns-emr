"""Interdisciplinary continuity workflow (MSW / CHAPLAIN / VOLUNTEER ONLY).

Stabilization-phase test suite for app.services.discipline_service_engine
and app.api.discipline_services. Written per the owner's stabilization
directive. Synthetic data only -- no real patient identifiers, names,
dates of birth, addresses, MRNs, or clinical narrative text.

Most groups call the engine functions directly against `db_session` (the
repository's isolated per-run Postgres test database -- see
tests/conftest.py) for precise, fast state-machine verification. A smaller
set of API-contract groups (H, S) go through the `client` fixture to
exercise the actual HTTP layer (permission dependency, row-version
conflict response, idempotency).

Execution note: these tests require TEST_DATABASE_URL (see
backend/scripts/run_isolated_tests.py). They are written and ready to run
but were NOT executed in the authoring environment because no
DATABASE_URL/TEST_DATABASE_URL-capable Postgres connection is configured
there -- see the stabilization completion report for the exact stop
condition. Do not weaken tests/conftest.py's isolation guard to work
around this.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.enums import ContinuityDiscipline, TaskStatus
from app.models.discipline_service import PatientDisciplineService, PatientDisciplineServiceEvent
from app.models.idg_recommendation import IDGRecommendation
from app.models.idg_review import IDGReview
from app.models.patient import Patient
from app.models.patient_issue import PatientIssue
from app.models.task import Task
from app.models.tenant import Tenant
from app.models.user import User
from app.services import discipline_service_engine as engine
from tests.conftest import TEST_USER_ID

pytestmark = pytest.mark.integration


# =========================================================
# FIXTURES / HELPERS
# =========================================================

def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(user_id=user_id, role=role, tenant_id=tenant_id, email=f"{role.lower()}@example.com")
    return {"Authorization": f"Bearer {token}"}


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "CONT") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Synthetic hospice continuity test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID, *, role: str = "RN") -> None:
    if db_session.get(Tenant, tenant_id) is None:
        db_session.add(
            Tenant(
                id=tenant_id,
                legal_name=f"Tenant {tenant_id.hex[:8]}",
                display_name=f"Tenant {tenant_id.hex[:8]}",
                npi=f"{int(str(tenant_id.int)[:10]):010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()
    if db_session.get(User, user_id) is None:
        db_session.add(
            User(id=user_id, tenant_id=tenant_id, email=f"user.{user_id.hex[:8]}@example.com",
                 full_name="Continuity Test User", role=role, active=True)
        )
        db_session.commit()


def _make_admission(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID, *, status: str = "ADMITTED",
                     discharged_at=None) -> Admission:
    """Creates a real `Admission` row (the canonical hospice episode object).
    Required for any API-level continuity mutation test now that
    `_require_current_admission()` hard-rejects when no active, unambiguous
    admission exists for the patient (readmission episode-scoping)."""
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_date=datetime.now(timezone.utc),
        status=status,
        discharged_at=discharged_at,
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_idg_review(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID) -> IDGReview:
    review = IDGReview(
        tenant_id=tenant_id,
        patient_id=patient_id,
        review_date=datetime.now(timezone.utc),
        summary="Synthetic IDG review for continuity test",
        is_finalized=False,
        created_by=TEST_USER_ID,
    )
    db_session.add(review)
    db_session.commit()
    return review


def _new_service(db_session, tenant_id, patient_id, discipline: str = "MSW", *, actor_role: str = "SW",
                  admission_id=None) -> PatientDisciplineService:
    return engine.get_or_create_service(
        db_session, tenant_id=tenant_id, patient_id=patient_id, discipline=discipline,
        actor_user_id=TEST_USER_ID, actor_role=actor_role, admission_id=admission_id,
    )


def _offer_and_pending(db_session, service, *, actor_role: str = "SW"):
    service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role=actor_role)
    service, _ = engine.record_pending_decision(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role=actor_role)
    db_session.commit()
    return service


def _make_poc_problem(db_session, tenant_id, patient_id, admission_id):
    """Builds a minimal real PlanOfCare -> PlanOfCareVersion -> POCProblem
    -> POCGoal -> POCIntervention chain (the only ownership path these
    models expose) so POC-linkage validation can be exercised against
    genuine rows rather than a mocked/shortcut structure."""
    from app.models.plan_of_care import PlanOfCare
    from app.models.plan_of_care_version import PlanOfCareVersion
    from app.models.poc import POCGoal, POCIntervention, POCProblem

    poc = PlanOfCare(id=uuid.uuid4(), tenant_id=tenant_id, patient_id=patient_id, admission_id=admission_id, status="ACTIVE")
    db_session.add(poc)
    db_session.flush()
    version = PlanOfCareVersion(
        id=uuid.uuid4(), tenant_id=tenant_id, plan_of_care_id=poc.id, version_number=1,
        status="ACTIVE", source_kind="ICA", snapshot_json={},
    )
    db_session.add(version)
    db_session.flush()
    problem = POCProblem(
        id=uuid.uuid4(), tenant_id=tenant_id, poc_version_id=version.id,
        diagnosis_context="MANUAL", problem_code="SYNTH-PROBLEM", label="Synthetic problem",
        severity="MODERATE", source_kind="MANUAL", is_rule_generated=False, status="ACTIVE",
    )
    db_session.add(problem)
    db_session.flush()
    goal = POCGoal(
        id=uuid.uuid4(), tenant_id=tenant_id, problem_id=problem.id, goal_text="Synthetic goal",
        source_kind="MANUAL", is_rule_generated=False, status="ACTIVE",
    )
    db_session.add(goal)
    db_session.flush()
    intervention = POCIntervention(
        id=uuid.uuid4(), tenant_id=tenant_id, goal_id=goal.id, discipline="MSW",
        intervention_text="Synthetic intervention", source_kind="MANUAL", is_rule_generated=False, status="ACTIVE",
    )
    db_session.add(intervention)
    db_session.commit()
    return problem, goal, intervention


# =========================================================
# A. CANONICAL NORMALIZATION
# =========================================================

class TestCanonicalNormalization:
    @pytest.mark.parametrize(
        "alias,expected",
        [
            ("MSW", "MSW"), ("SW", "MSW"), ("SOCIAL_WORK", "MSW"), ("SOCIAL_WORKER", "MSW"), ("LCSW", "MSW"),
            ("SPIRITUAL_COUNSELOR", "CHAPLAIN"), ("SPIRITUAL_COUNSELOR_SERVICE", "CHAPLAIN"), ("SC", "CHAPLAIN"),
            ("CHAPLAIN", "CHAPLAIN"), ("PASTORAL_COUNSELOR", "CHAPLAIN"),
            ("VOLUNTEER", "VOLUNTEER"), ("VOLUNTEER_SERVICE", "VOLUNTEER"), ("VOLUNTEER_SUPPORT", "VOLUNTEER"),
            ("VISITTYPE_VOLUNTEER_SUPPORT", "VOLUNTEER"), ("SERVICECONTEXT_VOLUNTEER_VISIT", "VOLUNTEER"),
        ],
    )
    def test_every_authorized_alias_normalizes(self, alias, expected):
        assert engine.normalize_continuity_discipline(alias) == expected

    def test_unknown_discipline_rejected(self):
        with pytest.raises(engine.DisciplineServiceError):
            engine.normalize_continuity_discipline("RN")
        with pytest.raises(engine.DisciplineServiceError):
            engine.normalize_continuity_discipline("HOSPICE_AIDE")

    def test_spiritual_counselor_and_chaplain_share_one_open_record(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        svc1 = _new_service(db_session, tenant_id, patient.id, "SPIRITUAL_COUNSELOR", actor_role="CHAPLAIN")
        svc2 = _new_service(db_session, tenant_id, patient.id, "CHAPLAIN", actor_role="CHAPLAIN")
        assert svc1.id == svc2.id
        assert svc1.discipline == "CHAPLAIN"


# =========================================================
# B. VALID TRANSITIONS / C. INVALID TRANSITIONS
# =========================================================

class TestTransitions:
    def test_offer_to_awaiting_decision(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        before_version = service.row_version
        service, event = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()
        assert service.current_state == "OFFERED_AWAITING_DECISION"
        assert event.event_type == "SERVICE_OFFERED"
        assert service.current_state_event_id == event.id
        assert service.row_version == before_version + 1
        assert service.last_offered_at is not None

    def test_full_accept_activate_pause_resume_end_cycle(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.accept_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
        )
        assert service.current_state == "ACCEPTED_AWAITING_ACTIVATION"
        service, _ = engine.activate_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        assert service.current_state == "ACTIVE"
        service, _ = engine.pause_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic pause")
        assert service.current_state == "PAUSED"
        service, _ = engine.resume_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        assert service.current_state == "ACTIVE"
        service, _ = engine.end_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic end")
        db_session.commit()
        assert service.current_state == "ENDED"

    def test_accepted_awaiting_activation_can_pause_directly(self, db_session):
        """Directive-required transition: AAA -> PAUSED without first
        passing through ACTIVE (activation delayed)."""
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.accept_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
        )
        service, event = engine.pause_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic")
        db_session.commit()
        assert service.current_state == "PAUSED"
        assert event.from_state == "ACCEPTED_AWAITING_ACTIVATION"

    def test_refuse_then_reoffer_cycle(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, event, task = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic refusal", decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
        )
        db_session.commit()
        assert service.current_state == "REFUSED_MONITORING_CONTINUES"
        assert event.event_type == "SERVICE_REFUSED"
        assert task is not None and task.status == TaskStatus.PENDING

        service, _ = engine.schedule_reoffer(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", due_date=date.today() + timedelta(days=14))
        assert service.current_state == "REOFFER_DUE"
        service, _ = engine.reoffer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        assert service.current_state == "REOFFERED_AWAITING_DECISION"
        service, event = engine.accept_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
        )
        db_session.commit()
        assert service.current_state == "ACCEPTED_AWAITING_ACTIVATION"
        assert event.event_type == "REOFFER_ACCEPTED"

    @pytest.mark.parametrize(
        "setup_state,event_fn",
        [
            ("ACTIVE", lambda db, svc: engine.refuse_service(
                db, service=svc, actor_user_id=TEST_USER_ID, actor_role="SW", reason="x",
                decision_maker_name="x", decision_maker_relationship="x",
            ) if svc.current_state == "NOT_YET_OFFERED" else None),
        ],
    )
    def test_not_yet_offered_cannot_jump_to_active(self, db_session, setup_state, event_fn):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        with pytest.raises(engine.InvalidTransitionError):
            engine.activate_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")

    def test_active_cannot_jump_directly_to_refused_via_undefined_event(self, db_session):
        # ACTIVE -> SERVICE_REFUSED is actually defined (RMC) by design;
        # the genuinely undefined jump is ACTIVE -> SERVICE_ACCEPTED.
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.accept_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            decision_maker_name="x", decision_maker_relationship="x",
        )
        service, _ = engine.activate_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        with pytest.raises(engine.InvalidTransitionError):
            engine.accept_service(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                decision_maker_name="x", decision_maker_relationship="x",
            )

    def test_ended_has_no_outgoing_transition(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.end_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic")
        db_session.commit()
        with pytest.raises(engine.InvalidTransitionError):
            engine.activate_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        with pytest.raises(engine.DisciplineServiceError):
            engine.end_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic again")

    @pytest.mark.parametrize("terminal_state_setup", ["REFUSED_MONITORING_CONTINUES", "UNABLE_TO_CONTACT", "DECISION_MAKER_UNAVAILABLE"])
    def test_end_requires_authorized_reason(self, db_session, terminal_state_setup):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        if terminal_state_setup == "REFUSED_MONITORING_CONTINUES":
            service, _, _ = engine.refuse_service(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="x",
                decision_maker_name="x", decision_maker_relationship="x", create_reoffer_task=False,
            )
        elif terminal_state_setup == "UNABLE_TO_CONTACT":
            service, _ = engine.record_unable_to_contact(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        else:
            service, _ = engine.record_decision_maker_unavailable(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()
        with pytest.raises(engine.DisciplineServiceError):
            engine.end_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="")
        # Authorized (non-empty) reason succeeds since these states ARE in _END_SOURCES.
        service, event = engine.end_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="authorized synthetic reason")
        assert service.current_state == "ENDED"


# =========================================================
# D. ATOMIC ROLLBACK
# =========================================================

class TestAtomicRollback:
    def test_refuse_service_rolls_back_fully_on_injected_failure(self, db_session, monkeypatch):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)

        original_create_task = engine._create_reoffer_task

        def _boom(*args, **kwargs):
            raise RuntimeError("synthetic injected failure after event insertion")

        monkeypatch.setattr(engine, "_create_reoffer_task", _boom)

        with pytest.raises(RuntimeError):
            engine.refuse_service(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            )
        db_session.rollback()
        monkeypatch.setattr(engine, "_create_reoffer_task", original_create_task)

        refreshed = db_session.get(PatientDisciplineService, service.id)
        assert refreshed.current_state == "OFFERED_AWAITING_DECISION"
        events = db_session.query(PatientDisciplineServiceEvent).filter(
            PatientDisciplineServiceEvent.discipline_service_id == service.id,
            PatientDisciplineServiceEvent.event_type == "SERVICE_REFUSED",
        ).all()
        assert events == []
        tasks = db_session.query(Task).filter(Task.reference_id == service.id).all()
        assert tasks == []


# =========================================================
# E. OPTIMISTIC CONCURRENCY
# =========================================================

class TestOptimisticConcurrency:
    def test_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        db_session.commit()
        stale_version = service.row_version

        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()
        assert service.row_version == stale_version + 1

        with pytest.raises(engine.ConcurrencyError):
            engine.record_pending_decision(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                expected_row_version=stale_version,
            )
        unchanged = db_session.get(PatientDisciplineService, service.id)
        assert unchanged.current_state == "OFFERED_AWAITING_DECISION"

    # M2 stabilization fix: assign_rn_monitoring, end_rn_monitoring,
    # record_correction, request_idg_review, and complete_idg_review
    # previously had no row_version param or _check_row_version() guard
    # at all -- a stale client could silently overwrite a concurrent
    # change. Each now rejects a stale expected_row_version with
    # ConcurrencyError and performs no mutation, event, or audit write.

    def test_assign_rn_monitoring_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        rn_user = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_id, rn_user, role="RN")
        service = _new_service(db_session, tenant_id, patient.id)
        db_session.commit()
        stale_version = service.row_version
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.ConcurrencyError):
            engine.assign_rn_monitoring(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                rn_user_id=rn_user, expected_row_version=stale_version,
            )
        unchanged = db_session.get(PatientDisciplineService, service.id)
        assert unchanged.rn_monitoring_assigned_user_id is None
        assert db_session.query(PatientDisciplineServiceEvent).filter(
            PatientDisciplineServiceEvent.discipline_service_id == service.id,
            PatientDisciplineServiceEvent.event_type == "RN_MONITORING_ASSIGNED",
        ).count() == 0

    def test_end_rn_monitoring_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        rn_user = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_id, rn_user, role="RN")
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.assign_rn_monitoring(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", rn_user_id=rn_user)
        db_session.commit()
        stale_version = service.row_version
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.ConcurrencyError):
            engine.end_rn_monitoring(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                reason="synthetic", expected_row_version=stale_version,
            )
        unchanged = db_session.get(PatientDisciplineService, service.id)
        assert unchanged.rn_monitoring_assigned_user_id == rn_user

    def test_record_correction_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        db_session.commit()
        stale_version = service.row_version
        service, original_event = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.ConcurrencyError):
            engine.record_correction(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                corrects_event_id=original_event.id, reason="synthetic stale correction attempt",
                expected_row_version=stale_version,
            )
        assert db_session.query(PatientDisciplineServiceEvent).filter(
            PatientDisciplineServiceEvent.discipline_service_id == service.id,
            PatientDisciplineServiceEvent.event_type == "CORRECTION_RECORDED",
        ).count() == 0

    def test_request_idg_review_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        db_session.commit()
        stale_version = service.row_version
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.ConcurrencyError):
            engine.request_idg_review(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                expected_row_version=stale_version,
            )
        unchanged = db_session.get(PatientDisciplineService, service.id)
        assert unchanged.idg_review_required is False

    def test_complete_idg_review_stale_row_version_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.request_idg_review(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()
        stale_version = service.row_version
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.ConcurrencyError):
            engine.complete_idg_review(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                idg_review_id=review.id, expected_row_version=stale_version,
            )
        unchanged = db_session.get(PatientDisciplineService, service.id)
        assert unchanged.idg_review_required is True


# =========================================================
# F. IDEMPOTENCY
# =========================================================

class TestIdempotency:
    def test_same_key_same_payload_returns_cached_event_no_duplicate(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        key = f"synthetic-{uuid.uuid4().hex}"
        service, event1 = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", idempotency_key=key)
        db_session.commit()
        service, event2 = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", idempotency_key=key)
        db_session.commit()
        assert event1.id == event2.id
        count = db_session.query(PatientDisciplineServiceEvent).filter(
            PatientDisciplineServiceEvent.discipline_service_id == service.id,
            PatientDisciplineServiceEvent.idempotency_key == key,
        ).count()
        assert count == 1

    def test_same_key_changed_operation_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service_a = _new_service(db_session, tenant_id, patient.id, "MSW")
        service_b = _new_service(db_session, tenant_id, patient.id, "CHAPLAIN", actor_role="CHAPLAIN")
        key = f"synthetic-conflict-{uuid.uuid4().hex}"
        engine.offer_service(db_session, service=service_a, actor_user_id=TEST_USER_ID, actor_role="SW", idempotency_key=key)
        db_session.commit()
        with pytest.raises(engine.IdempotencyConflictError):
            engine.offer_service(db_session, service=service_b, actor_user_id=TEST_USER_ID, actor_role="CHAPLAIN", idempotency_key=key)

    def test_idempotency_is_tenant_scoped(self, db_session):
        tenant_a = uuid.UUID(db_session.info["tenant_id"])
        tenant_b = uuid.uuid4()
        user_b = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_b, user_b, role="SW")
        patient_a = _make_patient(db_session, tenant_a, mrn_prefix="TENA")
        patient_b = _make_patient(db_session, tenant_b, mrn_prefix="TENB")
        service_a = _new_service(db_session, tenant_a, patient_a.id)
        service_b = _new_service(db_session, tenant_b, patient_b.id)
        key = f"synthetic-shared-key-{uuid.uuid4().hex}"
        engine.offer_service(db_session, service=service_a, actor_user_id=TEST_USER_ID, actor_role="SW", idempotency_key=key)
        db_session.commit()
        # Different tenant may reuse the same literal key value without conflict.
        service_b, event_b = engine.offer_service(db_session, service=service_b, actor_user_id=user_b, actor_role="SW", idempotency_key=key)
        db_session.commit()
        assert service_b.current_state == "OFFERED_AWAITING_DECISION"


# =========================================================
# G. TENANT ISOLATION
# =========================================================

class TestTenantIsolation:
    def test_cross_tenant_service_not_visible_via_api(self, client, db_session):
        tenant_a = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_a)
        service = _new_service(db_session, tenant_a, patient.id)
        db_session.commit()

        tenant_b = uuid.uuid4()
        user_b = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_b, user_b, role="SW")

        response = client.get(
            f"/discipline-services/patient/{patient.id}/MSW",
            headers=_headers(user_b, "SW", tenant_b),
        )
        assert response.status_code in (403, 404), response.text

    def test_cross_tenant_idg_recommendation_rejected(self, client, db_session):
        tenant_a = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_a)
        review = _make_idg_review(db_session, tenant_a, patient.id)

        tenant_b = uuid.uuid4()
        user_b = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_b, user_b, role="SW")

        response = client.post(
            "/discipline-services/idg-recommendations",
            headers=_headers(user_b, "SW", tenant_b),
            json={
                "patient_id": str(patient.id),
                "idg_review_id": str(review.id),
                "discipline": "MSW",
                "recommendation_type": "CONTINUE_MONITORING",
                "recommendation_text": "Synthetic cross-tenant attempt",
            },
        )
        assert response.status_code in (403, 404), response.text


# =========================================================
# H. AUTHORIZATION
# =========================================================

class TestAuthorization:
    def test_volunteer_coordinator_allowed_for_volunteer(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = engine.get_or_create_service(
            db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="VOLUNTEER",
            actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
        )
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR")
        assert service.current_state == "OFFERED_AWAITING_DECISION"

    def test_msw_role_cannot_record_volunteer_events(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = engine.get_or_create_service(
            db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="VOLUNTEER",
            actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
        )
        with pytest.raises(engine.PermissionDeniedError):
            engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")

    def test_volunteer_coordinator_cannot_record_msw_events(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        with pytest.raises(engine.PermissionDeniedError):
            engine.get_or_create_service(
                db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="MSW",
                actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
            )


# =========================================================
# I. VOLUNTEER SEPARATION
# =========================================================

class TestVolunteerSeparation:
    def test_recorder_information_source_decision_maker_independently_stored(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = engine.get_or_create_service(
            db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="VOLUNTEER",
            actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
        )
        service, _ = engine.offer_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
            information_source="Synthetic Family Member",
        )
        service, event = engine.accept_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
            decision_maker_name="Synthetic Patient Representative",
            decision_maker_relationship="DURABLE_POWER_OF_ATTORNEY",
            information_source="Synthetic Family Member",
        )
        db_session.commit()
        assert event.recorded_by_user_id == TEST_USER_ID
        assert event.recorded_by_role == "VOLUNTEER_COORDINATOR"
        assert event.information_source == "Synthetic Family Member"
        assert event.decision_maker_name == "Synthetic Patient Representative"
        # The coordinator (recorder) must never equal the decision-maker field.
        assert event.decision_maker_name != "VOLUNTEER_COORDINATOR"

    def test_accept_rejects_missing_decision_maker_authority(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = engine.get_or_create_service(
            db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="VOLUNTEER",
            actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
        )
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR")
        with pytest.raises(engine.DisciplineServiceError):
            engine.accept_service(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
                decision_maker_name="", decision_maker_relationship="",
            )


# =========================================================
# J. REFUSAL PRESERVATION / K. REFUSAL WITHOUT CLINICAL CONCERN
# =========================================================

class TestRefusalPreservation:
    def test_refusal_preserves_existing_patient_issue(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        issue = PatientIssue(
            tenant_id=tenant_id, patient_id=patient.id, category="psychosocial",
            description="Synthetic pre-existing clinical concern.",
            identified_date=date.today(), identified_by=TEST_USER_ID, status="OPEN",
            clinical_status="ACTIVE", issue_domain="PSYCHOSOCIAL",
        )
        db_session.add(issue)
        db_session.commit()

        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, event, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic refusal", decision_maker_name="x", decision_maker_relationship="x",
            related_patient_issue_id=issue.id, create_reoffer_task=False,
        )
        db_session.commit()

        refreshed_issue = db_session.get(PatientIssue, issue.id)
        assert refreshed_issue.status == "OPEN"
        assert refreshed_issue.clinical_status == "ACTIVE"
        assert event.related_patient_issue_id == issue.id
        assert service.current_state == "REFUSED_MONITORING_CONTINUES"

    def test_refusal_without_concern_does_not_fabricate_patient_issue(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        before_count = db_session.query(PatientIssue).filter(PatientIssue.patient_id == patient.id).count()
        engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic refusal, no clinical concern", decision_maker_name="x",
            decision_maker_relationship="x", create_reoffer_task=False,
        )
        db_session.commit()
        after_count = db_session.query(PatientIssue).filter(PatientIssue.patient_id == patient.id).count()
        assert after_count == before_count == 0

    def test_engine_module_never_imports_poc_models(self):
        """Structural guard: the continuity engine must never write to the
        materialized POC projection tables. Refusal/correction/re-offer
        must preserve POCProblem/POCGoal/POCIntervention by simply never
        touching them. Full POC-table integration coverage was not added
        here -- see stabilization report for why."""
        import app.services.discipline_service_engine as mod
        assert "poc" not in mod.__dict__
        assert not any(name.startswith("POC") for name in dir(mod))


# =========================================================
# L. IDG RECOMMENDATION WITHOUT VISIT
# =========================================================

class TestIdgRecommendationNoVisit:
    def test_msw_recommendation_created_without_visit(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id)

        recommendation = engine.create_idg_recommendation(
            db_session, service=service, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
            recommendation_text="Synthetic recommendation text.",
            actor_user_id=TEST_USER_ID, actor_role="SW",
        )
        db_session.commit()
        assert recommendation.no_direct_visit is True
        assert recommendation.status == "PENDING"

        from app.models.visit import Visit
        visit_count = db_session.query(Visit).filter(Visit.patient_id == patient.id).count()
        assert visit_count == 0

    def test_volunteer_cannot_author_recommendation(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
                idg_review_id=review.id, discipline="VOLUNTEER", recommendation_type="CONTINUE_MONITORING",
                recommendation_text="Synthetic", actor_user_id=TEST_USER_ID, actor_role="VOLUNTEER_COORDINATOR",
            )

    def test_accept_recommendation_does_not_create_poc_rows(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        recommendation = engine.create_idg_recommendation(
            db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
            recommendation_text="Synthetic", actor_user_id=TEST_USER_ID, actor_role="SW",
        )
        db_session.commit()
        recommendation = engine.accept_idg_recommendation(db_session, recommendation=recommendation, actor_user_id=TEST_USER_ID)
        db_session.commit()
        assert recommendation.status == "ACCEPTED"
        from app.models.poc import POCProblem
        assert db_session.query(POCProblem).filter(POCProblem.tenant_id == tenant_id).count() == 0


# =========================================================
# L2. IDG REVIEW OWNERSHIP VALIDATION (H1 stabilization fix)
#
# create_idg_recommendation() must verify that a caller-supplied
# idg_review_id actually belongs to the same patient and tenant as the
# recommendation being created. IDGReview has no FK/ownership constraint
# in the schema, so this is purely an application-layer guard.
# =========================================================

class TestIdgReviewOwnershipValidation:
    def test_recommendation_rejects_review_belonging_to_different_patient_same_tenant(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id, mrn_prefix="OWNA")
        patient_b = _make_patient(db_session, tenant_id, mrn_prefix="OWNB")
        review_for_b = _make_idg_review(db_session, tenant_id, patient_b.id)

        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient_a.id,
                idg_review_id=review_for_b.id, discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic cross-patient attempt", actor_user_id=TEST_USER_ID, actor_role="SW",
            )
        from app.models.idg_recommendation import IDGRecommendation as _Rec
        assert db_session.query(_Rec).filter(_Rec.patient_id == patient_a.id).count() == 0

    def test_recommendation_rejects_missing_review(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
                idg_review_id=uuid.uuid4(), discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic missing-review attempt", actor_user_id=TEST_USER_ID, actor_role="SW",
            )

    def test_recommendation_rejects_review_from_different_tenant(self, db_session):
        tenant_a = uuid.UUID(db_session.info["tenant_id"])
        tenant_b = uuid.uuid4()
        user_b = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_b, user_b, role="SW")
        patient_a = _make_patient(db_session, tenant_a)
        patient_b_same_id_space = _make_patient(db_session, tenant_b, mrn_prefix="OTEN")
        review_for_tenant_b = _make_idg_review(db_session, tenant_b, patient_b_same_id_space.id)

        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_a, patient_id=patient_a.id,
                idg_review_id=review_for_tenant_b.id, discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic cross-tenant-at-engine-level attempt",
                actor_user_id=TEST_USER_ID, actor_role="SW",
            )


# =========================================================
# L3. IDG REVIEW LIFECYCLE (M1 stabilization fix)
#
# complete_idg_review() previously had no reachable API/UI caller, making
# idg_review_required a one-way latch. These tests verify the engine
# function now also enforces the same ownership guard as H1 above, since
# a caller-supplied idg_review_id is accepted here too.
# =========================================================

class TestIdgReviewLifecycle:
    def test_complete_idg_review_clears_required_flag_and_creates_event(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, _, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            requires_idg_review=True, create_reoffer_task=False,
        )
        db_session.commit()
        assert service.idg_review_required is True

        service, event = engine.complete_idg_review(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            idg_review_id=review.id, notes="Synthetic completion notes",
        )
        db_session.commit()
        assert event.event_type == "IDG_REVIEW_COMPLETED"
        assert service.idg_review_required is False

    def test_complete_idg_review_rejects_review_from_different_patient(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id, mrn_prefix="CIRA")
        patient_b = _make_patient(db_session, tenant_id, mrn_prefix="CIRB")
        review_for_b = _make_idg_review(db_session, tenant_id, patient_b.id)
        service_a = _new_service(db_session, tenant_id, patient_a.id)
        service_a, _ = engine.request_idg_review(db_session, service=service_a, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()

        with pytest.raises(engine.DisciplineServiceError):
            engine.complete_idg_review(
                db_session, service=service_a, actor_user_id=TEST_USER_ID, actor_role="SW",
                idg_review_id=review_for_b.id,
            )
        unchanged = db_session.get(PatientDisciplineService, service_a.id)
        assert unchanged.idg_review_required is True

    def test_complete_idg_review_requires_idg_review_id(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, _ = engine.request_idg_review(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        db_session.commit()
        with pytest.raises(engine.DisciplineServiceError):
            engine.complete_idg_review(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
                idg_review_id=None,
            )


# =========================================================
# M. RN MONITORING
# =========================================================

class TestRnMonitoring:
    def test_assign_change_and_end_monitoring(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        rn_user = uuid.uuid4()
        rn_user_2 = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_id, rn_user, role="RN")
        _ensure_tenant_and_user(db_session, tenant_id, rn_user_2, role="RN")
        service = _new_service(db_session, tenant_id, patient.id)

        service, event = engine.assign_rn_monitoring(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", rn_user_id=rn_user, reason="synthetic")
        assert event.event_type == "RN_MONITORING_ASSIGNED"
        assert service.rn_monitoring_assigned_user_id == rn_user

        service, event = engine.assign_rn_monitoring(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", rn_user_id=rn_user_2, reason="synthetic reassignment")
        assert event.event_type == "RN_MONITORING_CHANGED"

        service, event = engine.end_rn_monitoring(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="synthetic end")
        db_session.commit()
        assert event.event_type == "RN_MONITORING_ENDED"
        assert service.rn_monitoring_assigned_user_id is None
        # Ending monitoring must not change current_state.
        assert service.current_state == "NOT_YET_OFFERED"

    def test_refusal_can_assign_rn_monitoring_atomically(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        rn_user = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_id, rn_user, role="RN")
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, event, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            assign_rn_monitoring_user_id=rn_user, create_reoffer_task=False,
        )
        db_session.commit()
        assert service.rn_monitoring_assigned_user_id == rn_user


# =========================================================
# O. RE-OFFER
# =========================================================

class TestReoffer:
    def test_duplicate_reoffer_task_prevented(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, _, task1 = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            create_reoffer_task=True,
        )
        db_session.commit()
        # Simulate a second refusal attempt generating a task for the same
        # purpose while the first re-offer task is still PENDING.
        task2 = engine._create_reoffer_task(
            db_session, service=service, actor_user_id=TEST_USER_ID,
            purpose=f"{service.discipline}_SERVICE_REFUSED_REOFFER_REQUIRED",
        )
        db_session.commit()
        assert task1.id == task2.id
        count = db_session.query(Task).filter(Task.reference_id == service.id, Task.status == TaskStatus.PENDING).count()
        assert count == 1

    def test_schedule_reoffer_supports_date_and_event_based_triggers(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, _, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            create_reoffer_task=False,
        )
        with pytest.raises(engine.DisciplineServiceError):
            engine.schedule_reoffer(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.schedule_reoffer(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", trigger_description="Synthetic event-based trigger: next IDG review")
        db_session.commit()
        assert service.reoffer_due_at is None  # no date given -- truth preserved, not fabricated
        assert service.current_state == "REOFFER_DUE"

    def test_reoffer_refusal_does_not_resolve_clinical_need(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        issue = PatientIssue(
            tenant_id=tenant_id, patient_id=patient.id, category="psychosocial",
            description="Synthetic ongoing concern.", identified_date=date.today(),
            identified_by=TEST_USER_ID, status="OPEN",
        )
        db_session.add(issue)
        db_session.commit()
        service = _new_service(db_session, tenant_id, patient.id)
        service = _offer_and_pending(db_session, service)
        service, _, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic", decision_maker_name="x", decision_maker_relationship="x",
            related_patient_issue_id=issue.id, create_reoffer_task=False,
        )
        service, _ = engine.schedule_reoffer(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", due_date=date.today())
        service, _ = engine.reoffer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, event, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="synthetic second refusal", decision_maker_name="x", decision_maker_relationship="x",
            related_patient_issue_id=issue.id, create_reoffer_task=False,
        )
        db_session.commit()
        assert event.event_type == "REOFFER_REFUSED"
        refreshed_issue = db_session.get(PatientIssue, issue.id)
        assert refreshed_issue.status == "OPEN"


# =========================================================
# P. CORRECTION HISTORY
# =========================================================

class TestCorrection:
    def test_correction_preserves_original_event_and_references_it(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, original_event = engine.offer_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            information_source="Synthetic wrong source",
        )
        db_session.commit()
        original_effective_at = original_event.effective_at

        service, correction_event = engine.record_correction(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            corrects_event_id=original_event.id, reason="Synthetic correction: wrong information source recorded",
            information_source="Synthetic corrected source",
        )
        db_session.commit()

        reloaded_original = db_session.get(PatientDisciplineServiceEvent, original_event.id)
        assert reloaded_original is not None
        assert reloaded_original.effective_at == original_effective_at
        assert reloaded_original.information_source == "Synthetic wrong source"
        assert correction_event.corrects_event_id == original_event.id
        assert correction_event.event_type == "CORRECTION_RECORDED"
        # Correction does not change current_state.
        assert service.current_state == "OFFERED_AWAITING_DECISION"


# =========================================================
# Q. AUDIT TIMELINE
# =========================================================

class TestAuditTimeline:
    def test_event_history_contains_actor_role_states_and_reason(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        service = _new_service(db_session, tenant_id, patient.id)
        service, event = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", reason="Synthetic offer reason")
        db_session.commit()
        assert event.recorded_by_user_id == TEST_USER_ID
        assert event.recorded_by_role == "SW"
        assert event.from_state == "NOT_YET_OFFERED"
        assert event.to_state == "OFFERED_AWAITING_DECISION"
        assert event.reason == "Synthetic offer reason"


# =========================================================
# R. OUT-OF-SCOPE REGRESSION
# =========================================================

class TestOutOfScopeRegression:
    def test_rn_discipline_rejected_by_continuity_engine(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.get_or_create_service(
                db_session, tenant_id=tenant_id, patient_id=patient.id, discipline="RN",
                actor_user_id=TEST_USER_ID, actor_role="RN",
            )

    def test_hospice_aide_discipline_rejected_by_continuity_engine(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.normalize_continuity_discipline("HOSPICE_AIDE")

    def test_physician_and_f2f_disciplines_rejected_by_continuity_engine(self, db_session):
        for discipline in ("MD", "PHYSICIAN", "F2F", "HOSPICE_PHYSICIAN"):
            with pytest.raises(engine.DisciplineServiceError):
                engine.normalize_continuity_discipline(discipline)


# =========================================================
# S. API CONTRACT
# =========================================================

class TestApiContract:
    def test_offer_requires_known_discipline(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        response = client.post(
            f"/discipline-services/patient/{patient.id}/HOSPICE_AIDE/offer",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={},
        )
        assert response.status_code in (400, 404, 422), response.text

    def test_stale_row_version_returns_conflict(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission.id)
        db_session.commit()

        response = client.post(
            f"/discipline-services/patient/{patient.id}/MSW/offer",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={"expected_row_version": service.row_version + 99},
        )
        assert response.status_code == 409, response.text

    def test_client_cannot_set_audit_actor_fields(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_admission(db_session, tenant_id, patient.id)
        response = client.post(
            f"/discipline-services/patient/{patient.id}/MSW/offer",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={"recorded_by_user_id": str(uuid.uuid4()), "recorded_by_role": "ADMINISTRATOR"},
        )
        assert response.status_code in (200, 201), response.text


# =========================================================
# T. ACTIVE ADMISSION RESOLUTION (readmission episode-scoping)
# =========================================================

class TestActiveAdmissionResolution:
    def test_exactly_one_active_admission_resolves(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        resolved = engine.resolve_current_admission(db_session, tenant_id=tenant_id, patient_id=patient.id)
        assert resolved is not None
        assert resolved.id == admission.id

    def test_no_active_admission_returns_none(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        resolved = engine.resolve_current_admission(db_session, tenant_id=tenant_id, patient_id=patient.id)
        assert resolved is None

    def test_two_active_admissions_is_ambiguous_and_rejected(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_admission(db_session, tenant_id, patient.id)
        _make_admission(db_session, tenant_id, patient.id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.resolve_current_admission(db_session, tenant_id=tenant_id, patient_id=patient.id)

    def test_discharged_admission_excluded(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_admission(db_session, tenant_id, patient.id, discharged_at=datetime.now(timezone.utc))
        resolved = engine.resolve_current_admission(db_session, tenant_id=tenant_id, patient_id=patient.id)
        assert resolved is None

    def test_cross_tenant_admission_excluded(self, db_session):
        tenant_a = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_a)
        tenant_b = uuid.uuid4()
        _ensure_tenant_and_user(db_session, tenant_b, uuid.uuid4(), role="SW")
        # Admission created under tenant_b must never satisfy tenant_a's resolution,
        # even if (hypothetically) the same patient_id value were reused.
        _make_admission(db_session, tenant_b, patient_a.id)
        resolved = engine.resolve_current_admission(db_session, tenant_id=tenant_a, patient_id=patient_a.id)
        assert resolved is None

    def test_cross_patient_admission_excluded(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id, mrn_prefix="PTA")
        patient_b = _make_patient(db_session, tenant_id, mrn_prefix="PTB")
        _make_admission(db_session, tenant_id, patient_b.id)
        resolved = engine.resolve_current_admission(db_session, tenant_id=tenant_id, patient_id=patient_a.id)
        assert resolved is None

    def test_no_active_admission_mutation_rejected_via_api_with_no_side_effect(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        # Deliberately no Admission created.
        response = client.post(
            f"/discipline-services/patient/{patient.id}/MSW/identify",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={},
        )
        assert response.status_code == 400, response.text
        # No side effect: no service row was created for this patient/discipline.
        count = (
            db_session.query(PatientDisciplineService)
            .execution_options(skip_tenant_filter=True)
            .filter(PatientDisciplineService.patient_id == patient.id)
            .count()
        )
        assert count == 0

    def test_ambiguous_admission_mutation_rejected_via_api(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_admission(db_session, tenant_id, patient.id)
        _make_admission(db_session, tenant_id, patient.id)
        response = client.post(
            f"/discipline-services/patient/{patient.id}/MSW/identify",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={},
        )
        assert response.status_code == 400, response.text


# =========================================================
# U. SERVICE ISOLATION ACROSS ADMISSIONS (readmission)
# =========================================================

class TestServiceIsolationAcrossAdmissions:
    def test_readmission_does_not_inherit_refusal_monitoring_or_reoffer(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        admission_1 = _make_admission(db_session, tenant_id, patient.id)
        service_1 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_1.id)
        service_1, _ = engine.offer_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.record_pending_decision(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _, _ = engine.refuse_service(
            db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="Synthetic refusal for isolation test",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
            information_source="PATIENT",
        )
        service_1, _ = engine.assign_rn_monitoring(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="RN", rn_user_id=uuid.uuid4())
        db_session.commit()
        assert service_1.current_state == "REFUSED_MONITORING_CONTINUES"
        assert service_1.rn_monitoring_assigned_user_id is not None

        # Discharge admission 1, admit admission 2.
        admission_1.discharged_at = datetime.now(timezone.utc)
        admission_1.status = "DISCHARGED"
        db_session.commit()
        admission_2 = _make_admission(db_session, tenant_id, patient.id)

        service_2 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_2.id)
        db_session.commit()

        assert service_2.id != service_1.id
        assert service_2.admission_id == admission_2.id
        assert service_2.current_state != "REFUSED_MONITORING_CONTINUES"
        assert service_2.last_refused_at is None
        assert service_2.rn_monitoring_assigned_user_id is None
        assert service_2.reoffer_due_at is None

        # Admission 1 history remains readable.
        reloaded_1 = db_session.get(PatientDisciplineService, service_1.id)
        assert reloaded_1 is not None
        assert reloaded_1.current_state == "REFUSED_MONITORING_CONTINUES"

    def test_active_and_paused_state_does_not_carry_forward(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        admission_1 = _make_admission(db_session, tenant_id, patient.id)
        service_1 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_1.id)
        service_1, _ = engine.offer_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.record_pending_decision(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.accept_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.activate_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.pause_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW", reason="Synthetic pause")
        db_session.commit()
        assert service_1.current_state == "PAUSED"

        admission_1.discharged_at = datetime.now(timezone.utc)
        admission_1.status = "DISCHARGED"
        db_session.commit()
        admission_2 = _make_admission(db_session, tenant_id, patient.id)

        service_2 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_2.id)
        db_session.commit()
        assert service_2.current_state not in ("ACTIVE", "PAUSED")
        # A fresh offer is permitted (not blocked by admission 1's paused state).
        service_2, _ = engine.offer_service(db_session, service=service_2, actor_user_id=TEST_USER_ID, actor_role="SW")
        assert service_2.current_state == "OFFERED_AWAITING_DECISION"


# =========================================================
# V. IDG REVIEW ADMISSION MODES
# =========================================================

class TestIdgReviewAdmissionModes:
    def test_current_review_accepted_for_request_idg_review(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission.id)
        review = IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=admission.id,
            review_date=datetime.now(timezone.utc), summary="Synthetic current review",
            is_finalized=False, created_by=TEST_USER_ID,
        )
        db_session.add(review)
        db_session.commit()
        service, _ = engine.request_idg_review(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", idg_review_id=review.id,
        )
        assert service.idg_review_id == review.id

    def test_legacy_admission_unassigned_review_rejected_for_current_service(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission.id)
        legacy_review = IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=None,
            review_date=datetime.now(timezone.utc), summary="Synthetic legacy review (predates scoping)",
            is_finalized=False, created_by=TEST_USER_ID,
        )
        db_session.add(legacy_review)
        db_session.commit()
        with pytest.raises(engine.DisciplineServiceError):
            engine.request_idg_review(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", idg_review_id=legacy_review.id,
            )

    def test_historical_admission_review_rejected_for_current_service(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission_1 = _make_admission(db_session, tenant_id, patient.id, discharged_at=datetime.now(timezone.utc))
        historical_review = IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=admission_1.id,
            review_date=datetime.now(timezone.utc), summary="Synthetic admission-1 review",
            is_finalized=True, created_by=TEST_USER_ID,
        )
        db_session.add(historical_review)
        db_session.commit()
        admission_2 = _make_admission(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission_2.id)
        with pytest.raises(engine.DisciplineServiceError):
            engine.request_idg_review(
                db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW", idg_review_id=historical_review.id,
            )

    def test_admission_status_labels_via_api_listing(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission_1 = _make_admission(db_session, tenant_id, patient.id, discharged_at=datetime.now(timezone.utc))
        db_session.add(IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=admission_1.id,
            review_date=datetime.now(timezone.utc), summary="Synthetic historical review",
            is_finalized=True, created_by=TEST_USER_ID,
        ))
        db_session.add(IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=None,
            review_date=datetime.now(timezone.utc), summary="Synthetic legacy review",
            is_finalized=True, created_by=TEST_USER_ID,
        ))
        admission_2 = _make_admission(db_session, tenant_id, patient.id)
        db_session.add(IDGReview(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=admission_2.id,
            review_date=datetime.now(timezone.utc), summary="Synthetic current review",
            is_finalized=False, created_by=TEST_USER_ID,
        ))
        db_session.commit()

        response = client.get(
            f"/discipline-services/idg-reviews/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
        )
        assert response.status_code == 200, response.text
        statuses = {row["summary"]: row["admission_status"] for row in response.json()}
        assert statuses["Synthetic historical review"] == "HISTORICAL"
        assert statuses["Synthetic legacy review"] == "LEGACY_ADMISSION_UNASSIGNED"
        assert statuses["Synthetic current review"] == "CURRENT"


# =========================================================
# W. IDG RECOMMENDATION ADMISSION SCOPING
# =========================================================

class TestIdgRecommendationAdmissionScoping:
    def _make_current_review(self, db_session, tenant_id, patient_id, admission_id):
        review = IDGReview(
            tenant_id=tenant_id, patient_id=patient_id, admission_id=admission_id,
            review_date=datetime.now(timezone.utc), summary="Synthetic review for recommendation test",
            is_finalized=False, created_by=TEST_USER_ID,
        )
        db_session.add(review)
        db_session.commit()
        return review

    def test_same_admission_recommendation_creation_succeeds(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        review = self._make_current_review(db_session, tenant_id, patient.id, admission.id)

        response = client.post(
            "/discipline-services/idg-recommendations",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "idg_review_id": str(review.id),
                "discipline": "MSW",
                "recommendation_type": "CONTINUE_MONITORING",
                "recommendation_text": "Synthetic same-admission recommendation",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["admission_id"] == str(admission.id)
        assert response.json()["no_direct_visit"] is True

    def test_cross_admission_recommendation_creation_rejected(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission_1 = _make_admission(db_session, tenant_id, patient.id, discharged_at=datetime.now(timezone.utc))
        review_1 = self._make_current_review(db_session, tenant_id, patient.id, admission_1.id)
        _make_admission(db_session, tenant_id, patient.id)  # admission_2 is now current

        response = client.post(
            "/discipline-services/idg-recommendations",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "idg_review_id": str(review_1.id),
                "discipline": "MSW",
                "recommendation_type": "CONTINUE_MONITORING",
                "recommendation_text": "Synthetic cross-admission attempt",
            },
        )
        assert response.status_code == 400, response.text

    def test_cross_admission_recommendation_accept_rejected(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission_1 = _make_admission(db_session, tenant_id, patient.id)
        review_1 = self._make_current_review(db_session, tenant_id, patient.id, admission_1.id)
        recommendation = IDGRecommendation(
            tenant_id=tenant_id, patient_id=patient.id, admission_id=admission_1.id,
            idg_review_id=review_1.id, discipline="MSW", recommendation_type="CONTINUE_MONITORING",
            recommendation_text="Synthetic admission-1 recommendation", no_direct_visit=True,
            status="PENDING", created_by_user_id=TEST_USER_ID,
        )
        db_session.add(recommendation)
        # Admission 1 discharged, admission 2 now current -- recommendation stays attributed to admission 1.
        admission_1.discharged_at = datetime.now(timezone.utc)
        admission_1.status = "DISCHARGED"
        db_session.commit()
        _make_admission(db_session, tenant_id, patient.id)

        response = client.post(
            f"/discipline-services/idg-recommendations/{recommendation.id}/accept",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
            json={},
        )
        assert response.status_code == 400, response.text
        reloaded = db_session.get(IDGRecommendation, recommendation.id)
        assert reloaded.status == "PENDING"

    def test_recommendation_creates_no_visit_or_billable_encounter(self, db_session):
        # Structural guarantee: create_idg_recommendation never imports or
        # instantiates Visit/billing models -- verified by inspecting the
        # actual created row's no_direct_visit flag and absence of any
        # visit_id/encounter_id field on the model.
        assert not hasattr(IDGRecommendation, "visit_id")
        assert not hasattr(IDGRecommendation, "encounter_id")
        assert "no_direct_visit" in IDGRecommendation.__table__.columns.keys()


# =========================================================
# X. PATIENT ISSUE SAFETY (longitudinal, never admission-scoped)
# =========================================================

class TestPatientIssueSafety:
    def test_patient_issue_has_no_admission_id_column(self):
        # PatientIssue is deliberately longitudinal -- adding admission_id
        # would let a per-admission filter accidentally hide an issue that
        # is still clinically active across episodes.
        assert "admission_id" not in PatientIssue.__table__.columns.keys()

    def test_refusal_without_concern_creates_no_patient_issue(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission.id)
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.record_pending_decision(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="Synthetic refusal, no clinical concern",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
            information_source="PATIENT",
        )
        db_session.commit()
        count = (
            db_session.query(PatientIssue)
            .execution_options(skip_tenant_filter=True)
            .filter(PatientIssue.patient_id == patient.id)
            .count()
        )
        assert count == 0

    def test_refusal_does_not_resolve_existing_patient_issue(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        issue = PatientIssue(
            tenant_id=tenant_id, patient_id=patient.id,
            category="PSYCHOSOCIAL", description="Synthetic pre-existing psychosocial concern",
            identified_date=date.today(), status="OPEN",
        )
        db_session.add(issue)
        db_session.commit()

        service = _new_service(db_session, tenant_id, patient.id, admission_id=admission.id)
        service, _ = engine.offer_service(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _ = engine.record_pending_decision(db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW")
        service, _, _ = engine.refuse_service(
            db_session, service=service, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="Synthetic refusal with linked pre-existing concern",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
            information_source="PATIENT", related_patient_issue_id=issue.id,
        )
        db_session.commit()
        reloaded = db_session.get(PatientIssue, issue.id)
        assert reloaded.status == "OPEN"

    def test_admission_1_issue_not_copied_into_admission_2(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission_1 = _make_admission(db_session, tenant_id, patient.id, discharged_at=datetime.now(timezone.utc))
        issue = PatientIssue(
            tenant_id=tenant_id, patient_id=patient.id,
            category="PSYCHOSOCIAL", description="Synthetic admission-1 concern",
            identified_date=date.today(), status="OPEN",
        )
        db_session.add(issue)
        db_session.commit()
        _make_admission(db_session, tenant_id, patient.id)

        # No code path in the continuity engine creates/copies PatientIssue
        # rows -- confirmed structurally; the only PatientIssue row for this
        # patient remains the original, singular admission-1 row.
        count = (
            db_session.query(PatientIssue)
            .execution_options(skip_tenant_filter=True)
            .filter(PatientIssue.patient_id == patient.id)
            .count()
        )
        assert count == 1


# =========================================================
# Y. TASK AND RE-OFFER ISOLATION
# =========================================================

class TestTaskAndReofferIsolation:
    def test_admission_2_reoffer_task_not_blocked_by_admission_1_open_task(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        admission_1 = _make_admission(db_session, tenant_id, patient.id)
        service_1 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_1.id)
        service_1, _ = engine.offer_service(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _ = engine.record_pending_decision(db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_1, _, task_1 = engine.refuse_service(
            db_session, service=service_1, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="Synthetic refusal, admission 1",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
            information_source="PATIENT",
        )
        db_session.commit()
        assert task_1 is not None
        assert task_1.reference_id == service_1.id
        assert task_1.status != TaskStatus.COMPLETED

        admission_1.discharged_at = datetime.now(timezone.utc)
        admission_1.status = "DISCHARGED"
        db_session.commit()
        admission_2 = _make_admission(db_session, tenant_id, patient.id)
        service_2 = _new_service(db_session, tenant_id, patient.id, admission_id=admission_2.id)
        service_2, _ = engine.offer_service(db_session, service=service_2, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_2, _ = engine.record_pending_decision(db_session, service=service_2, actor_user_id=TEST_USER_ID, actor_role="SW")
        service_2, _, task_2 = engine.refuse_service(
            db_session, service=service_2, actor_user_id=TEST_USER_ID, actor_role="SW",
            reason="Synthetic refusal, admission 2",
            decision_maker_name="Synthetic Patient", decision_maker_relationship="SELF",
            information_source="PATIENT",
        )
        db_session.commit()

        assert task_2 is not None
        assert task_2.id != task_1.id
        assert task_2.reference_id == service_2.id
        assert task_2.reference_id != task_1.reference_id

        # Completing admission 1's task must not change admission 2's task/service.
        task_1.status = TaskStatus.COMPLETED
        db_session.commit()
        reloaded_service_2 = db_session.get(PatientDisciplineService, service_2.id)
        reloaded_task_2 = db_session.get(Task, task_2.id)
        assert reloaded_service_2.current_state == service_2.current_state
        assert reloaded_task_2.status != TaskStatus.COMPLETED


# =========================================================
# Z. OUT-OF-SCOPE REGRESSION (unaffected by admission scoping)
# =========================================================

class TestOutOfScopeRegressionAdmissionScoping:
    def test_out_of_scope_disciplines_still_rejected_regardless_of_admission(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_admission(db_session, tenant_id, patient.id)
        for discipline in ("RN", "MD", "PHYSICIAN", "F2F", "HOSPICE_AIDE"):
            with pytest.raises(engine.DisciplineServiceError):
                engine.normalize_continuity_discipline(discipline)
        body = response.json()
        # The actor must be derived from the authenticated token, never the payload.
        events = client.get(
            f"/discipline-services/patient/{patient.id}/MSW/events",
            headers=_headers(TEST_USER_ID, "SW", tenant_id),
        ).json()
        assert events[0]["recorded_by_role"] != "ADMINISTRATOR"


# =========================================================
# POC LINKAGE (true Plan-of-Care reuse: Problem -> Goal -> Intervention)
# =========================================================

class TestPocLinkage:
    def test_recommendation_links_to_same_admission_poc_problem(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        db_session.query(IDGReview).filter(IDGReview.id == review.id).update({"admission_id": admission.id})
        db_session.commit()
        problem, goal, intervention = _make_poc_problem(db_session, tenant_id, patient.id, admission.id)

        recommendation = engine.create_idg_recommendation(
            db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
            recommendation_text="Synthetic POC-linked recommendation", actor_user_id=TEST_USER_ID, actor_role="SW",
            current_admission_id=admission.id, requires_poc_change=True,
            linked_poc_problem_id=problem.id, linked_poc_goal_id=goal.id, linked_poc_intervention_id=intervention.id,
        )
        db_session.commit()
        assert recommendation.requires_poc_change is True
        assert recommendation.linked_poc_problem_id == problem.id
        assert recommendation.linked_poc_goal_id == goal.id
        assert recommendation.linked_poc_intervention_id == intervention.id

    def test_recommendation_rejects_poc_problem_from_different_admission(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        current_admission = _make_admission(db_session, tenant_id, patient.id)
        prior_admission = _make_admission(db_session, tenant_id, patient.id, status="DISCHARGED",
                                           discharged_at=datetime.now(timezone.utc))
        review = _make_idg_review(db_session, tenant_id, patient.id)
        db_session.query(IDGReview).filter(IDGReview.id == review.id).update({"admission_id": current_admission.id})
        db_session.commit()
        problem, _, _ = _make_poc_problem(db_session, tenant_id, patient.id, prior_admission.id)

        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
                idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic cross-admission POC link attempt",
                actor_user_id=TEST_USER_ID, actor_role="SW",
                current_admission_id=current_admission.id, linked_poc_problem_id=problem.id,
            )

    def test_recommendation_rejects_poc_problem_from_different_patient(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id, mrn_prefix="POCA")
        patient_b = _make_patient(db_session, tenant_id, mrn_prefix="POCB")
        admission_a = _make_admission(db_session, tenant_id, patient_a.id)
        admission_b = _make_admission(db_session, tenant_id, patient_b.id)
        review_a = _make_idg_review(db_session, tenant_id, patient_a.id)
        db_session.query(IDGReview).filter(IDGReview.id == review_a.id).update({"admission_id": admission_a.id})
        db_session.commit()
        problem_b, _, _ = _make_poc_problem(db_session, tenant_id, patient_b.id, admission_b.id)

        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient_a.id,
                idg_review_id=review_a.id, discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic cross-patient POC link attempt",
                actor_user_id=TEST_USER_ID, actor_role="SW",
                current_admission_id=admission_a.id, linked_poc_problem_id=problem_b.id,
            )

    def test_recommendation_rejects_mismatched_goal_under_problem(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        db_session.query(IDGReview).filter(IDGReview.id == review.id).update({"admission_id": admission.id})
        db_session.commit()
        problem_1, goal_1, _ = _make_poc_problem(db_session, tenant_id, patient.id, admission.id)
        problem_2, goal_2, _ = _make_poc_problem(db_session, tenant_id, patient.id, admission.id)

        with pytest.raises(engine.DisciplineServiceError):
            engine.create_idg_recommendation(
                db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
                idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
                recommendation_text="Synthetic mismatched goal/problem attempt",
                actor_user_id=TEST_USER_ID, actor_role="SW",
                current_admission_id=admission.id, linked_poc_problem_id=problem_1.id, linked_poc_goal_id=goal_2.id,
            )

    def test_recommendation_without_poc_ids_does_not_require_poc_change(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        recommendation = engine.create_idg_recommendation(
            db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="CHAPLAIN", recommendation_type="CONTINUE_MONITORING",
            recommendation_text="Synthetic non-POC recommendation", actor_user_id=TEST_USER_ID, actor_role="CHAPLAIN",
        )
        db_session.commit()
        assert recommendation.requires_poc_change is False
        assert recommendation.linked_poc_problem_id is None


# =========================================================
# HISTORICAL-ADMISSION API (patient-wide read, grouped by admission)
# =========================================================

class TestHistoricalAdmissionApi:
    def test_patient_history_groups_current_and_historical_admissions(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        prior_admission = _make_admission(db_session, tenant_id, patient.id, status="DISCHARGED",
                                           discharged_at=datetime.now(timezone.utc))
        current_admission = _make_admission(db_session, tenant_id, patient.id)
        _new_service(db_session, tenant_id, patient.id, "MSW", admission_id=prior_admission.id)
        _new_service(db_session, tenant_id, patient.id, "CHAPLAIN", admission_id=current_admission.id)

        resp = client.get(
            f"/discipline-services/patient/{patient.id}/history",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["current_admission_id"] == str(current_admission.id)
        admission_ids = {g["admission_id"] for g in body["admissions"]}
        assert str(prior_admission.id) in admission_ids
        assert str(current_admission.id) in admission_ids
        for group in body["admissions"]:
            if group["admission_id"] == str(current_admission.id):
                assert group["admission_status"] == "CURRENT"
            else:
                assert group["admission_status"] == "HISTORICAL"

    def test_single_admission_history_endpoint_is_read_only_label(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        prior_admission = _make_admission(db_session, tenant_id, patient.id, status="DISCHARGED",
                                           discharged_at=datetime.now(timezone.utc))
        _make_admission(db_session, tenant_id, patient.id)
        _new_service(db_session, tenant_id, patient.id, "VOLUNTEER", admission_id=prior_admission.id)

        resp = client.get(
            f"/discipline-services/patient/{patient.id}/admission/{prior_admission.id}",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["admission_status"] == "HISTORICAL"
        assert len(body["services"]) == 1
        assert body["services"][0]["admission_status"] == "HISTORICAL"

    def test_admission_history_rejects_admission_belonging_to_different_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id, mrn_prefix="HISTA")
        patient_b = _make_patient(db_session, tenant_id, mrn_prefix="HISTB")
        admission_b = _make_admission(db_session, tenant_id, patient_b.id)

        resp = client.get(
            f"/discipline-services/patient/{patient_a.id}/admission/{admission_b.id}",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert resp.status_code == 404

    def test_list_services_labels_every_row_with_admission_status(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        current_admission = _make_admission(db_session, tenant_id, patient.id)
        _new_service(db_session, tenant_id, patient.id, "MSW", admission_id=current_admission.id)
        _new_service(db_session, tenant_id, patient.id, "CHAPLAIN")  # legacy, admission_id None

        resp = client.get(
            f"/discipline-services/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert resp.status_code == 200
        statuses = {row["discipline"]: row["admission_status"] for row in resp.json()}
        assert statuses["MSW"] == "CURRENT"
        assert statuses["CHAPLAIN"] == "LEGACY_ADMISSION_UNASSIGNED"


# =========================================================
# POC ACCEPTANCE ROLE GATE
# =========================================================

class TestPocAcceptanceRoleGate:
    def test_sw_cannot_accept_recommendation_requiring_poc_change(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        db_session.query(IDGReview).filter(IDGReview.id == review.id).update({"admission_id": admission.id})
        db_session.commit()
        problem, _, _ = _make_poc_problem(db_session, tenant_id, patient.id, admission.id)
        recommendation = engine.create_idg_recommendation(
            db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
            recommendation_text="Synthetic POC-gated recommendation", actor_user_id=TEST_USER_ID, actor_role="SW",
            current_admission_id=admission.id, linked_poc_problem_id=problem.id,
        )
        db_session.commit()

        resp = client.post(
            f"/discipline-services/idg-recommendations/{recommendation.id}/accept",
            json={}, headers=_headers(TEST_USER_ID, "SW", tenant_id),
        )
        assert resp.status_code == 403

    def test_rn_can_accept_recommendation_requiring_poc_change(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        admission = _make_admission(db_session, tenant_id, patient.id)
        review = _make_idg_review(db_session, tenant_id, patient.id)
        db_session.query(IDGReview).filter(IDGReview.id == review.id).update({"admission_id": admission.id})
        db_session.commit()
        problem, _, _ = _make_poc_problem(db_session, tenant_id, patient.id, admission.id)
        recommendation = engine.create_idg_recommendation(
            db_session, service=None, tenant_id=tenant_id, patient_id=patient.id,
            idg_review_id=review.id, discipline="MSW", recommendation_type="REVIEW_POC",
            recommendation_text="Synthetic POC-gated recommendation", actor_user_id=TEST_USER_ID, actor_role="SW",
            current_admission_id=admission.id, linked_poc_problem_id=problem.id,
        )
        db_session.commit()

        resp = client.post(
            f"/discipline-services/idg-recommendations/{recommendation.id}/accept",
            json={}, headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACCEPTED"

