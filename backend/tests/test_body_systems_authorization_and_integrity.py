"""Body Systems (Respiratory) — authorization, audit, hydration,
episode-isolation, and signed/locked-record integrity tests.

Episode scoping update: every route is now `/visits/body-systems/rnica/
{assessment_id}/respiratory` (the SAME `RnicaAssessment.id` identity
`/rnica/{assessment_id}` already authorizes on in app/api/visits.py), NOT
patient-only. Every test below constructs an explicit `RnicaAssessment`
row rather than relying on an implicit patient-only lookup.

Every test reuses EXISTING repository infrastructure only:
- Cross-tenant/cross-patient denial is enforced by the shared
  `app.core.patient_access.get_authorized_patient` helper, the SAME
  function every other patient-scoped router (including RNICA) already
  depends on. These tests prove Body Systems inherits that existing
  convention correctly -- they do not add a new authorization mechanism.
- Episode/RNICA isolation is enforced by scoping `BodySystemsAssessment`
  by `rnica_assessment_id`, mirroring the same identity RNICA's own save/
  lock routes already authorize by.
- Audit assertions query the existing `AuditLog` model/table, the SAME
  audit sink RNICA writes to via `app.services.audit_logger.log_event`.
- No new role, capability, or status value is invented.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session as SQLAlchemySession

from app.models.audit_log import AuditLog
from app.models.body_systems import BodySystemsAssessment, ReviewException, SystemAssessment
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import create_access_token
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _make_patient(db_session, tenant_id, *, mrn_prefix="BODYSYSAUTH"):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1948, 3, 2),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_rnica_assessment(db_session, patient, tenant_id, *, status="DRAFT"):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=tenant_id,
        assessment_type="RNICA",
        status=status,
    )
    db_session.add(record)
    db_session.commit()
    return record


def _url(assessment_id) -> str:
    return f"/visits/body-systems/rnica/{assessment_id}/respiratory"


def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}.{user_id.hex[:8]}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID, *, active: bool = True) -> None:
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
            User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"user.{user_id.hex[:8]}@example.com",
                full_name="Body Systems Auth Test User",
                role="RN",
                active=active,
                access_level="FULL_ACCESS",
            )
        )
        db_session.commit()


class TestCrossTenantAndCrossPatientIsolation:
    """Respiratory inherits `get_authorized_patient`'s existing tenant +
    care-team isolation -- the same mechanism every other patient-scoped
    router (including RNICA) already relies on."""

    def test_get_denies_caller_from_another_tenant(self, client, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        other_tenant_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

        response = client.get(_url(rnica.id), headers=_headers(other_user_id, "RN", other_tenant_id))
        assert response.status_code == 404

    def test_put_denies_caller_from_another_tenant(self, client, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        other_tenant_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

        response = client.put(
            _url(rnica.id),
            headers=_headers(other_user_id, "RN", other_tenant_id),
            json={"data": {"respiratoryNoCurrentConcern": True}},
        )
        assert response.status_code == 404

    def test_inactive_user_is_denied(self, client, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        inactive_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, uuid.UUID(tenant.id), inactive_user_id, active=False)

        response = client.get(_url(rnica.id), headers=_headers(inactive_user_id, "RN", uuid.UUID(tenant.id)))
        assert response.status_code == 403

    def test_saving_one_patients_respiratory_assessment_does_not_affect_another_patients(
        self, client, db_session, rn_headers, tenant
    ):
        patient_a = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-A")
        patient_b = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-B")
        rnica_a = _make_rnica_assessment(db_session, patient_a, uuid.UUID(tenant.id))
        rnica_b = _make_rnica_assessment(db_session, patient_b, uuid.UUID(tenant.id))

        client.get(_url(rnica_a.id), headers=rn_headers)
        baseline_b = client.get(_url(rnica_b.id), headers=rn_headers).json()

        client.put(
            _url(rnica_a.id),
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {"sobSeverity": "Severe"}},
        )

        after_b = client.get(_url(rnica_b.id), headers=rn_headers).json()
        # Patient B's own Respiratory draft is untouched by Patient A's save:
        # same id, same version, same (empty) data -- proving the route's
        # episode-scoped resolution can't cross between assessments/patients.
        assert after_b["id"] == baseline_b["id"]
        assert after_b["version"] == baseline_b["version"]
        assert after_b["data"] == {}
        assert after_b["situation"] is None


class TestEpisodeIsolation:
    """A patient may have multiple RNICA episodes over time; Respiratory
    must never let one episode's save leak into, or be read back as,
    another episode's record -- even for the SAME patient."""

    def test_mismatched_assessment_id_never_returns_another_episodes_data(
        self, client, db_session, rn_headers, tenant
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-EPISODE")
        episode_one = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        episode_two = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        client.put(
            _url(episode_one.id),
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {"sobSeverity": "Severe - episode one only"}},
        )

        fresh_episode_two = client.get(_url(episode_two.id), headers=rn_headers).json()
        assert fresh_episode_two["data"] == {}
        assert fresh_episode_two["situation"] is None

    def test_nonexistent_assessment_id_is_rejected_even_for_a_real_patient(self, client, db_session, rn_headers, tenant):
        _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-NOEPISODE")
        response = client.get(_url(uuid.uuid4()), headers=rn_headers)
        assert response.status_code == 404


class TestReviewExceptionValueValidation:
    def test_invalid_exception_type_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "data": {},
                "reviewExceptions": [
                    {"type": "not_a_real_exception_type", "message": "x", "blockingLevel": "informational"}
                ],
            },
        )
        assert response.status_code == 422

    def test_invalid_blocking_level_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "data": {},
                "reviewExceptions": [
                    {"type": "unable_to_assess", "message": "x", "blockingLevel": "not_a_real_level"}
                ],
            },
        )
        assert response.status_code == 422

    def test_informational_exception_does_not_block_save(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "data": {},
                "reviewExceptions": [
                    {"type": "follow_up_missing", "message": "informational only", "blockingLevel": "informational"}
                ],
            },
        )
        assert response.status_code == 200
        assert response.json()["openReviewExceptions"][0]["blockingLevel"] == "informational"


class TestAuditLogging:
    def test_save_creates_an_audit_event_with_required_context(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        before_count = db_session.query(AuditLog).filter(AuditLog.action == "body_systems.respiratory.save_draft").count()

        saved = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": "stable_existing", "data": {"sobSeverity": "None", "clinicalStatusChange": "Stable"}},
        ).json()

        events = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "body_systems.respiratory.save_draft")
            .order_by(AuditLog.created_at.desc())
            .all()
        )
        assert len(events) == before_count + 1
        event = events[0]
        assert str(event.tenant_id) == tenant.id
        assert event.user_id is not None
        assert event.entity_type == "system_assessment"
        assert event.entity_id == saved["id"]
        assert event.created_at is not None
        assert event.event_metadata.get("situation") == "stable_existing"
        assert event.event_metadata.get("rnicaAssessmentId") == str(rnica.id)
        # No raw secrets/tokens and no unnecessary patient identifiers
        # beyond the patient id itself, which the metadata already needs
        # for traceability.
        assert "password" not in str(event.event_metadata).lower()
        assert "token" not in str(event.event_metadata).lower()

    def test_audit_actor_is_always_the_authenticated_caller_not_a_client_supplied_value(
        self, client, db_session, rn_headers, tenant
    ):
        """A client cannot forge the audit actor by sending a different
        user id anywhere in the payload -- the backend only ever reads it
        from `current_user` (the verified JWT), never from the request
        body."""
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        forged_user_id = str(uuid.uuid4())

        saved = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "data": {"userId": forged_user_id, "assessedBy": forged_user_id},
            },
        ).json()

        event = (
            db_session.query(AuditLog)
            .filter(AuditLog.entity_id == saved["id"])
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert event is not None
        assert event.user_id != forged_user_id
        assert str(event.user_id) == str(TEST_USER_ID)


class TestHydrationRoundTrip:
    def test_put_then_separate_get_returns_the_same_persisted_values(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        initial = client.get(_url(rnica.id), headers=rn_headers).json()

        put_response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {
                    "respiratoryUnableToAssess": True,
                    "respiratoryUnableToAssessReason": "Patient unresponsive",
                    "assessmentContext": "NO_CURRENT_RESPIRATORY_CONCERN",
                    "clinicalComparison": "COMPARISON_UNAVAILABLE",
                    "oxygenUse": "NO",
                    "coughType": "None",
                    "respiratorySupportStatus": "NONE",
                },
                "reviewState": "reviewed_with_exception",
                "reviewExceptions": [
                    {"type": "unable_to_assess", "message": "x", "blockingLevel": "record_blocking", "fieldPath": "respiratoryUnableToAssessReason"}
                ],
                "expectedVersion": initial["version"],
            },
        ).json()

        get_after = client.get(_url(rnica.id), headers=rn_headers).json()

        assert get_after["situation"] == put_response["situation"] == "unable_to_assess"
        assert get_after["data"] == put_response["data"]
        assert get_after["version"] == put_response["version"] == initial["version"] + 1
        assert get_after["reviewState"] == "reviewed_with_exception"
        assert len(get_after["openReviewExceptions"]) == 1
        assert get_after["openReviewExceptions"][0]["fieldPath"] == "respiratoryUnableToAssessReason"

        # No other Body System's row was created by this Respiratory save.
        assessment = db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.rnica_assessment_id == rnica.id).one()
        system_rows = db_session.query(SystemAssessment).filter(SystemAssessment.body_systems_assessment_id == assessment.id).all()
        assert [row.system for row in system_rows] == ["respiratory"]

        # A repeated GET does not mutate data (version stays the same).
        repeat_get = client.get(_url(rnica.id), headers=rn_headers).json()
        assert repeat_get["version"] == get_after["version"]


class TestLockedRnicaAssessmentProtection:
    """Traces the actual production invariant this milestone introduced:
    once the owning `RnicaAssessment.status == "LOCKED"`, Respiratory can
    no longer be saved at all (409), and its last-persisted data/version
    are left completely untouched -- rather than silently starting a new
    draft, which would have let a clinician believe they successfully
    documented something against a finalized episode."""

    def test_locked_episode_rejects_further_saves_and_preserves_prior_data(
        self, client, db_session, rn_headers, tenant
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)
        baseline = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": "no_current_concern", "data": {"respiratoryNoCurrentConcern": True}},
        ).json()

        rnica.status = "LOCKED"
        db_session.commit()

        rejected = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {"sobSeverity": "Severe - should not persist"}},
        )
        assert rejected.status_code == 409

        system_row = db_session.get(SystemAssessment, uuid.UUID(baseline["id"]))
        db_session.refresh(system_row)
        assert system_row.version == baseline["version"]
        assert dict(system_row.data) == baseline["data"]
        assert system_row.situation == baseline["situation"]


class TestTransactionRollback:
    """Forces a controlled failure inside `save_respiratory_draft`'s own
    transaction, AFTER mutations are staged on the request's SQLAlchemy
    `Session` but BEFORE `db.commit()` succeeds. Uses pytest's
    `monkeypatch` to arm exactly one failing `Session.commit()` call --
    the repository's own isolated-test-database pattern, not a
    production-only failure hook. The patch is disarmed (self-disarms
    after firing, and is explicitly undone) before any verification
    query runs, so it cannot leak into other tests or into this test's
    own read-back assertions.
    """

    def test_failed_commit_leaves_no_partial_respiratory_update(
        self, client, db_session, rn_headers, tenant, monkeypatch
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-ROLLBACK")
        other_patient = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-ROLLBACK-OTHER")
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        other_rnica = _make_rnica_assessment(db_session, other_patient, uuid.UUID(tenant.id))

        # Establish a committed baseline with one open review exception,
        # so the rollback test can prove that pre-existing row survives
        # an aborted replacement attempt.
        client.get(_url(rnica.id), headers=rn_headers)
        baseline = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "stable_existing",
                "data": {"sobSeverity": "Mild"},
                "reviewExceptions": [
                    {"type": "follow_up_missing", "message": "baseline exception", "blockingLevel": "draft_allowed"}
                ],
            },
        ).json()
        other_baseline = client.get(_url(other_rnica.id), headers=rn_headers).json()

        audit_count_before = db_session.query(AuditLog).filter(
            AuditLog.action == "body_systems.respiratory.save_draft"
        ).count()
        assessment_count_before = db_session.query(BodySystemsAssessment).filter(
            BodySystemsAssessment.rnica_assessment_id == rnica.id
        ).count()
        system_assessment_count_before = db_session.query(SystemAssessment).filter(
            SystemAssessment.id == uuid.UUID(baseline["id"])
        ).count()

        state = {"armed": True}
        original_commit = SQLAlchemySession.commit

        def failing_commit(self, *args, **kwargs):
            if state["armed"]:
                state["armed"] = False
                self.rollback()
                raise RuntimeError("Simulated commit failure for Respiratory rollback test")
            return original_commit(self, *args, **kwargs)

        monkeypatch.setattr(SQLAlchemySession, "commit", failing_commit)
        try:
            with pytest.raises(Exception):
                client.put(
                    _url(rnica.id),
                    headers=rn_headers,
                    json={
                        "situation": "new_or_worsening",
                        "data": {"sobSeverity": "Severe - should not persist"},
                        "reviewExceptions": [
                            {"type": "nurse_judgment_required", "message": "should not persist", "blockingLevel": "record_blocking"}
                        ],
                        "expectedVersion": baseline["version"],
                    },
                )
        finally:
            # Disarm immediately so every subsequent query/request in this
            # test (and any other test) uses the real Session.commit.
            monkeypatch.setattr(SQLAlchemySession, "commit", original_commit)

        # 1) No duplicate Body Systems assessment was created for this episode.
        assert (
            db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.rnica_assessment_id == rnica.id).count()
            == assessment_count_before
        )
        # 2) No duplicate Respiratory system assessment row exists.
        assert (
            db_session.query(SystemAssessment).filter(SystemAssessment.id == uuid.UUID(baseline["id"])).count()
            == system_assessment_count_before
        )
        # 3) The previous Respiratory payload and version are unchanged.
        system_row = db_session.get(SystemAssessment, uuid.UUID(baseline["id"]))
        db_session.refresh(system_row)
        assert system_row.version == baseline["version"]
        assert dict(system_row.data) == baseline["data"]
        assert system_row.situation == baseline["situation"]
        # 4) No orphaned/duplicate review exception: the original baseline
        #    exception still exists exactly once, and the failed attempt's
        #    exception was never persisted.
        open_exceptions = (
            db_session.query(ReviewException)
            .filter(
                ReviewException.body_systems_assessment_id == uuid.UUID(baseline["bodySystemsAssessmentId"]),
                ReviewException.system == "respiratory",
                ReviewException.status == "open",
            )
            .all()
        )
        assert len(open_exceptions) == 1
        assert open_exceptions[0].message == "baseline exception"
        assert open_exceptions[0].resolved_at is None
        # 5) No false success audit entry was created for the failed save.
        assert (
            db_session.query(AuditLog).filter(AuditLog.action == "body_systems.respiratory.save_draft").count()
            == audit_count_before
        )
        # 6) Another episode's Respiratory data remains completely untouched.
        other_after = client.get(_url(other_rnica.id), headers=rn_headers).json()
        assert other_after["version"] == other_baseline["version"]
        assert other_after["data"] == other_baseline["data"]

        # 7) A subsequent valid request against the same episode still
        #    succeeds (the connection/session pool is healthy afterward).
        recovery = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "new_or_worsening",
                "data": {"sobSeverity": "Moderate", "treatmentInitiated": True},
                "expectedVersion": baseline["version"],
            },
        )
        assert recovery.status_code == 200
        assert recovery.json()["version"] == baseline["version"] + 1
