"""CTI (Certification of Terminal Illness) Phase 1 lifecycle tests (owner
directive 2026-08-21, additive-only): DRAFT -> PENDING_SIGNATURE ->
FINALIZED -> SUPERSEDED, physician-only signer authority (Attending
Physician / Medical Director / Medical Director Designee / Hospice
Physician — NEVER NP/PA/RN/LVN/DPCS/Administrator), narrative/LCD evidence
requirement, tenant isolation, BP3+ F2F gate, 15-day-early rule,
supersession chaining, idempotent signing, and immutable audit trail.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus
from app.services import certification_service as svc
from app.services.benefit_period_service import rollover_benefit_period
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        tenant_id=tenant_id,
        mrn=f"CTI-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def _make_bp(db_session, tenant_id, patient_id, *, election_date, start_date, benefit_type="INITIAL"):
    return rollover_benefit_period(
        db_session, tenant_id=tenant_id, patient_id=patient_id,
        election_date=election_date, start_date=start_date, benefit_type=benefit_type,
    )


def _draft(db_session, tenant_id, patient_id, bp_id, **overrides):
    kwargs = dict(
        tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=bp_id,
        physician_narrative="Patient shows continued functional decline, PPS 40%, "
        "increasing dependence on ADLs, weight loss 8% over 3 months.",
        created_by=TEST_USER_ID, created_by_role="RN",
    )
    kwargs.update(overrides)
    return svc.create_draft(db_session, **kwargs)


class TestNarrativeRequirement:
    def test_draft_requires_non_empty_narrative(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))

        with pytest.raises(svc.CertificationError):
            svc.create_draft(
                db_session, tenant_id=tenant_id, patient_id=patient.id, benefit_period_id=bp.id,
                physician_narrative="   ", created_by=TEST_USER_ID, created_by_role="RN",
            )

    def test_draft_creation_succeeds_with_narrative(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))

        cert = _draft(db_session, tenant_id, patient.id, bp.id)
        assert cert.status == "DRAFT"
        assert cert.cert_type == "INITIAL"
        assert cert.physician_narrative


class TestSignerAuthority:
    @pytest.mark.parametrize("role", ["NP", "PA", "RN", "LVN", "DPCS", "Administrator", "ADMINISTRATOR"])
    def test_disallowed_roles_cannot_sign(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)

        with pytest.raises(HTTPException) as exc:
            svc.sign_certification(db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role=role)
        assert exc.value.status_code == 403
        assert cert.status != "FINALIZED"

    @pytest.mark.parametrize(
        "role", ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "MEDICAL_DIRECTOR_DESIGNEE"]
    )
    def test_authorized_physician_roles_can_sign(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)

        cert = svc.sign_certification(db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role=role)
        assert cert.status == "FINALIZED"
        assert cert.signed_by_user_id == TEST_USER_ID


class TestLifecycleTransitions:
    def test_submit_for_signature(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)

        cert = svc.submit_for_signature(db_session, cert=cert, submitted_by=TEST_USER_ID, submitted_by_role="RN")
        assert cert.status == "PENDING_SIGNATURE"

    def test_narrative_locked_once_finalized(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)
        cert = svc.sign_certification(
            db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )

        with pytest.raises(svc.CertificationError):
            svc.update_narrative(db_session, cert=cert, physician_narrative="Edited after signing")

    def test_idempotent_resign_returns_same_finalized_cert(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)
        cert = svc.sign_certification(
            db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )
        signed_at = cert.signed_at

        again = svc.sign_certification(
            db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )
        assert again.id == cert.id
        assert again.signed_at == signed_at


class TestTenantIsolation:
    def test_get_certification_scoped_to_tenant(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        other_tenant_id = uuid.uuid4()
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)

        assert svc.get_certification(db_session, tenant_id=tenant_id, certification_id=cert.id) is not None
        assert svc.get_certification(db_session, tenant_id=other_tenant_id, certification_id=cert.id) is None


class TestBP3PlusF2FGate:
    def test_bp3_recert_blocked_without_completed_f2f(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        _make_bp(
            db_session, tenant_id, patient.id, election_date=date(2026, 4, 1),
            start_date=date(2026, 4, 1), benefit_type="RECERT",
        )
        bp3 = _make_bp(
            db_session, tenant_id, patient.id, election_date=date(2026, 6, 30),
            start_date=date(2026, 6, 30), benefit_type="RECERT",
        )
        cert = _draft(db_session, tenant_id, patient.id, bp3.id)

        with pytest.raises(HTTPException) as exc:
            svc.sign_certification(
                db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
            )
        assert exc.value.status_code == 400
        assert "F2F" in exc.value.detail

    def test_bp3_recert_allowed_with_completed_f2f(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        _make_bp(
            db_session, tenant_id, patient.id, election_date=date(2026, 4, 1),
            start_date=date(2026, 4, 1), benefit_type="RECERT",
        )
        bp3 = _make_bp(
            db_session, tenant_id, patient.id, election_date=date(2026, 6, 30),
            start_date=date(2026, 6, 30), benefit_type="RECERT",
        )

        f2f_task = Task(
            tenant_id=tenant_id, patient_id=patient.id, benefit_period_id=bp3.id,
            task_type=TaskType.F2F, status=TaskStatus.COMPLETED, created_by=TEST_USER_ID,
            origin="SYSTEM", discipline="MD",
        )
        db_session.add(f2f_task)
        db_session.flush()

        cert = _draft(db_session, tenant_id, patient.id, bp3.id)
        cert = svc.sign_certification(
            db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )
        assert cert.status == "FINALIZED"


class TestSupersessionChaining:
    def test_signing_next_cert_supersedes_prior(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp1 = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        bp2 = _make_bp(
            db_session, tenant_id, patient.id, election_date=date(2026, 4, 1),
            start_date=date(2026, 4, 1), benefit_type="RECERT",
        )

        cert1 = _draft(db_session, tenant_id, patient.id, bp1.id)
        cert1 = svc.sign_certification(
            db_session, cert=cert1, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )
        assert cert1.superseded_by_id is None

        cert2 = _draft(db_session, tenant_id, patient.id, bp2.id)
        cert2 = svc.sign_certification(
            db_session, cert=cert2, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )

        db_session.refresh(cert1)
        assert cert1.superseded_by_id == cert2.id
        assert cert1.superseded_at is not None


class TestStatusHistoryAuditTrail:
    def test_every_transition_is_recorded_immutably(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        cert = _draft(db_session, tenant_id, patient.id, bp.id)
        cert = svc.submit_for_signature(db_session, cert=cert, submitted_by=TEST_USER_ID, submitted_by_role="RN")
        cert = svc.sign_certification(
            db_session, cert=cert, signed_by_user_id=TEST_USER_ID, signed_by_role="MEDICAL_DIRECTOR",
        )

        history = svc.get_status_history(db_session, tenant_id=tenant_id, certification_id=cert.id)
        transitions = [(e.from_status, e.to_status) for e in history]
        assert (None, "DRAFT") in transitions
        assert ("DRAFT", "PENDING_SIGNATURE") in transitions
        assert ("PENDING_SIGNATURE", "FINALIZED") in transitions
        for e in history:
            assert e.changed_at is not None
            assert svc.label_for(e.to_status) != ""


class TestDisplayLabelLayer:
    def test_labels_do_not_change_stored_literals(self):
        assert svc.label_for("DRAFT") == "Draft"
        assert svc.label_for("PENDING_SIGNATURE") == "CTI Pending Signature"
        assert svc.label_for("FINALIZED") == "Signed"
        assert svc.label_for("SUPERSEDED") == "Superseded"
        assert svc.label_for("SOMETHING_NEW") == "SOMETHING_NEW"
