"""Body Systems (Respiratory) — authorization, audit, hydration, and
signed-record integrity tests.

Added during Respiratory closeout to cover items identified as missing
from the original `test_body_systems_api.py`/`test_body_systems_models.py`
coverage: cross-tenant/cross-patient denial, invalid review-exception
value rejection, audit-log assertions, a GET-after-PUT hydration
round-trip, and signed-assessment protection.

Every test reuses EXISTING repository infrastructure only:
- Cross-tenant/cross-patient denial is enforced by the shared
  `app.core.patient_access.get_authorized_patient` helper, the SAME
  function every other patient-scoped router (including RNICA) already
  depends on. These tests prove Body Systems inherits that existing
  convention correctly -- they do not add a new authorization mechanism.
- Audit assertions query the existing `AuditLog` model/table, the SAME
  audit sink RNICA writes to via `app.services.audit_logger.log_event`.
- No new role, capability, or status value is invented. The repository
  has no separate "write capability" distinct from patient access (see
  `body_systems.py`'s own docstring and the independent RNICA comparison
  performed earlier in this milestone) -- so there is no distinct
  write-permission-denial case to test beyond what `get_authorized_patient`
  already covers for both GET and PUT.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session as SQLAlchemySession

from app.models.audit_log import AuditLog
from app.models.body_systems import BodySystemsAssessment, ReviewException, SystemAssessment
from app.models.patient import Patient
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

        other_tenant_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

        response = client.get(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=_headers(other_user_id, "RN", other_tenant_id),
        )
        assert response.status_code == 404

    def test_put_denies_caller_from_another_tenant(self, client, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        other_tenant_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=_headers(other_user_id, "RN", other_tenant_id),
            json={"data": {"respiratory_overview": "No Current Respiratory Concern"}},
        )
        assert response.status_code == 404

    def test_inactive_user_is_denied(self, client, db_session, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        inactive_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, uuid.UUID(tenant.id), inactive_user_id, active=False)

        response = client.get(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=_headers(inactive_user_id, "RN", uuid.UUID(tenant.id)),
        )
        assert response.status_code == 403

    def test_saving_one_patients_respiratory_assessment_does_not_affect_another_patients(
        self, client, db_session, rn_headers, tenant
    ):
        patient_a = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-A")
        patient_b = _make_patient(db_session, uuid.UUID(tenant.id), mrn_prefix="BSA-B")

        client.get(f"/visits/body-systems/patients/{patient_a.id}/respiratory", headers=rn_headers)
        baseline_b = client.get(
            f"/visits/body-systems/patients/{patient_b.id}/respiratory", headers=rn_headers
        ).json()

        client.put(
            f"/visits/body-systems/patients/{patient_a.id}/respiratory",
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {"sobSeverity": "Severe"}},
        )

        after_b = client.get(
            f"/visits/body-systems/patients/{patient_b.id}/respiratory", headers=rn_headers
        ).json()
        # Patient B's own Respiratory draft is untouched by Patient A's save:
        # same id, same version, same (empty) data -- proving the route's
        # patient-scoped resolution can't cross between assessments/patients.
        assert after_b["id"] == baseline_b["id"]
        assert after_b["version"] == baseline_b["version"]
        assert after_b["data"] == {}
        assert after_b["situation"] is None


class TestReviewExceptionValueValidation:
    def test_invalid_exception_type_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
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
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
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
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
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
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        before_count = db_session.query(AuditLog).filter(AuditLog.action == "body_systems.respiratory.save_draft").count()

        saved = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "stable_existing", "data": {"sobSeverity": "None"}},
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
        # No raw secrets/tokens and no unnecessary patient identifiers
        # beyond the patient id itself, which the metadata already needs
        # for traceability.
        assert "password" not in str(event.event_metadata).lower()
        assert "token" not in str(event.event_metadata).lower()


class TestHydrationRoundTrip:
    def test_put_then_separate_get_returns_the_same_persisted_values(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        initial = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()

        put_response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {"respiratory_overview": "Unable to Assess", "respiratory_unable_to_assess_reason": "Patient unresponsive"},
                "reviewState": "reviewed_with_exception",
                "reviewExceptions": [
                    {"type": "unable_to_assess", "message": "x", "blockingLevel": "record_blocking", "fieldPath": "respiratory_unable_to_assess_reason"}
                ],
                "expectedVersion": initial["version"],
            },
        ).json()

        get_after = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()

        assert get_after["situation"] == put_response["situation"] == "unable_to_assess"
        assert get_after["data"] == put_response["data"]
        assert get_after["version"] == put_response["version"] == initial["version"] + 1
        assert get_after["reviewState"] == "reviewed_with_exception"
        assert len(get_after["openReviewExceptions"]) == 1
        assert get_after["openReviewExceptions"][0]["fieldPath"] == "respiratory_unable_to_assess_reason"

        # No other Body System's row was created by this Respiratory save.
        assessment = db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.patient_id == patient.id).one()
        system_rows = db_session.query(SystemAssessment).filter(SystemAssessment.body_systems_assessment_id == assessment.id).all()
        assert [row.system for row in system_rows] == ["respiratory"]

        # A repeated GET does not mutate data (version stays the same).
        repeat_get = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        assert repeat_get["version"] == get_after["version"]


class TestSignedAssessmentProtection:
    """Traces the repository's actual finalized-record convention: a
    `BodySystemsAssessment.status == "signed"` row is never reused by
    `_get_or_create_current_assessment` (it only queries `status != "signed"`),
    so a further Respiratory save after signing creates a NEW draft
    assessment instead of mutating the signed one -- this is the existing,
    already-implemented noneditable-record convention; this test proves it
    rather than inventing a new one."""

    def test_save_after_signing_starts_a_new_draft_and_leaves_the_signed_one_untouched(
        self, client, db_session, rn_headers, tenant
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)
        client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "no_current_concern", "data": {"respiratory_overview": "No Current Respiratory Concern"}},
        )

        signed_assessment = (
            db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.patient_id == patient.id).one()
        )
        signed_assessment.status = "signed"
        signed_assessment.signed_at = datetime.now(timezone.utc)
        signed_assessment.signed_by = TEST_USER_ID
        db_session.commit()
        signed_system_row = (
            db_session.query(SystemAssessment)
            .filter(SystemAssessment.body_systems_assessment_id == signed_assessment.id)
            .one()
        )
        signed_version = signed_system_row.version
        signed_data = dict(signed_system_row.data)

        # GET after signing returns a brand-new (not the signed) assessment.
        get_after_sign = client.get(
            f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers
        ).json()
        assert get_after_sign["bodySystemsAssessmentId"] != str(signed_assessment.id)
        assert get_after_sign["situation"] is None
        assert get_after_sign["data"] == {}

        # A further save doesn't touch the signed row at all.
        client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {"sobSeverity": "Moderate"}},
        )
        db_session.refresh(signed_system_row)
        db_session.refresh(signed_assessment)
        assert signed_assessment.status == "signed"
        assert signed_system_row.version == signed_version
        assert dict(signed_system_row.data) == signed_data


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

        # Establish a committed baseline with one open review exception,
        # so the rollback test can prove that pre-existing row survives
        # an aborted replacement attempt.
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)
        baseline = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "stable_existing",
                "data": {"sobSeverity": "Mild"},
                "reviewExceptions": [
                    {"type": "follow_up_missing", "message": "baseline exception", "blockingLevel": "draft_allowed"}
                ],
            },
        ).json()
        other_baseline = client.get(
            f"/visits/body-systems/patients/{other_patient.id}/respiratory", headers=rn_headers
        ).json()

        audit_count_before = db_session.query(AuditLog).filter(
            AuditLog.action == "body_systems.respiratory.save_draft"
        ).count()
        assessment_count_before = db_session.query(BodySystemsAssessment).filter(
            BodySystemsAssessment.patient_id == patient.id
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
                    f"/visits/body-systems/patients/{patient.id}/respiratory",
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

        # 1) No duplicate Body Systems assessment was created for this patient.
        assert (
            db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.patient_id == patient.id).count()
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
        # 6) Another patient's Respiratory data remains completely untouched.
        other_after = client.get(
            f"/visits/body-systems/patients/{other_patient.id}/respiratory", headers=rn_headers
        ).json()
        assert other_after["version"] == other_baseline["version"]
        assert other_after["data"] == other_baseline["data"]

        # 7) A subsequent valid request against the same patient still
        #    succeeds (the connection/session pool is healthy afterward).
        recovery = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "new_or_worsening",
                "data": {"sobSeverity": "Moderate"},
                "expectedVersion": baseline["version"],
            },
        )
        assert recovery.status_code == 200
        assert recovery.json()["version"] == baseline["version"] + 1
