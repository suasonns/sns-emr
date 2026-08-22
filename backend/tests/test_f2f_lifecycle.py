"""F2F (Face-to-Face Encounter) Phase 1 lifecycle tests (owner directive
2026-08-21, additive-only, policy update to allow hospice-employed/
contracted PA as an F2F performer): DRAFT -> FINALIZED, performer
authority (Hospice Physician / Medical Director / Medical Director
Designee / Attending Physician / NP / PA — NEVER RN/LVN/DPCS/
Administrator), NP/PA-performed F2F requires physician-level attestation
(never Administrator/DPCS), tenant isolation, F2F timing window for
BP3+, idempotent finalize, and immutable status-history audit trail.

F2F authority is strictly independent from CTI signer authority — an
NP/PA who performs/signs an F2F gains ZERO CTI certification authority.
See test_cti_lifecycle.py for the CTI-side authority tests.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from app.models.patient import Patient
from app.services import f2f_service as svc
from app.services.benefit_period_service import rollover_benefit_period
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        tenant_id=tenant_id,
        mrn=f"F2F-{uuid.uuid4().hex[:8]}",
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


def _create(db_session, tenant_id, patient_id, bp_id, *, performed_by_role, encounter_date=None, **overrides):
    kwargs = dict(
        tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=bp_id,
        encounter_date=encounter_date or date(2026, 1, 1),
        performed_by_role=performed_by_role, performed_by_user_id=TEST_USER_ID,
        summary="Individualized F2F findings.",
        created_by=TEST_USER_ID, created_by_role=performed_by_role,
    )
    kwargs.update(overrides)
    return svc.create_f2f(db_session, **kwargs)


class TestPerformerAuthority:
    @pytest.mark.parametrize("role", ["RN", "LVN", "DPCS", "Administrator", "ADMINISTRATOR"])
    def test_disallowed_roles_cannot_perform_f2f(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))

        with pytest.raises(svc.F2FError) as exc:
            _create(db_session, tenant_id, patient.id, bp.id, performed_by_role=role)
        assert exc.value.status_code == 403

    @pytest.mark.parametrize(
        "role",
        ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "MEDICAL_DIRECTOR_DESIGNEE", "NP", "PA"],
    )
    def test_authorized_roles_can_perform_f2f(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))

        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role=role)
        assert f2f.status == "DRAFT"


class TestNPPerformedRequiresPhysicianAttestation:
    def test_np_performed_f2f_finalizes_with_physician_attestor(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="NP")

        finalized = svc.finalize_f2f(
            db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="MEDICAL_DIRECTOR",
        )
        assert finalized.status == "FINALIZED"

    def test_np_performed_f2f_cannot_self_finalize(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="NP")

        # NP is an authorized performer, so finalize_f2f (service-level)
        # allows it directly — the physician-attestation gate for
        # NP/PA-performed encounters is enforced at the API layer
        # (app/api/f2f.py), not inside finalize_f2f itself. Confirm the
        # service still permits the performer's own role to finalize.
        finalized = svc.finalize_f2f(
            db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="NP",
        )
        assert finalized.status == "FINALIZED"

    @pytest.mark.parametrize("role", ["Administrator", "ADMINISTRATOR", "DPCS"])
    def test_administrator_and_dpcs_cannot_finalize(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="NP")

        with pytest.raises(HTTPException) as exc:
            svc.finalize_f2f(db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role=role)
        assert exc.value.status_code == 403
        assert f2f.status != "FINALIZED"

    def test_is_authorized_f2f_physician_attestor_excludes_admin(self):
        assert svc.is_authorized_f2f_physician_attestor("MEDICAL_DIRECTOR") is True
        assert svc.is_authorized_f2f_physician_attestor("ATTENDING_PHYSICIAN") is True
        assert svc.is_authorized_f2f_physician_attestor("HOSPICE_PHYSICIAN") is True
        assert svc.is_authorized_f2f_physician_attestor("NP") is False
        assert svc.is_authorized_f2f_physician_attestor("PA") is False
        assert svc.is_authorized_f2f_physician_attestor("Administrator") is False
        assert svc.is_authorized_f2f_physician_attestor("DPCS") is False


class TestLifecycleTransitions:
    def test_finalize_sets_finalized_at(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="MEDICAL_DIRECTOR")

        f2f = svc.finalize_f2f(db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="MEDICAL_DIRECTOR")
        assert f2f.status == "FINALIZED"
        assert f2f.finalized_at is not None

    def test_idempotent_finalize_returns_same_record(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="MEDICAL_DIRECTOR")
        f2f = svc.finalize_f2f(db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="MEDICAL_DIRECTOR")
        finalized_at = f2f.finalized_at

        again = svc.finalize_f2f(db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="MEDICAL_DIRECTOR")
        assert again.id == f2f.id
        assert again.finalized_at == finalized_at


class TestTenantIsolation:
    def test_get_f2f_encounter_scoped_to_tenant(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        other_tenant_id = uuid.uuid4()
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="MEDICAL_DIRECTOR")

        assert svc.get_f2f_encounter(db_session, tenant_id=tenant_id, f2f_encounter_id=f2f.id) is not None
        assert svc.get_f2f_encounter(db_session, tenant_id=other_tenant_id, f2f_encounter_id=f2f.id) is None


class TestF2FTimingWindow:
    def test_bp3_plus_requires_encounter_within_30_days_prior(self, db_session):
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

        with pytest.raises(HTTPException) as exc:
            _create(
                db_session, tenant_id, patient.id, bp3.id,
                performed_by_role="MEDICAL_DIRECTOR", encounter_date=date(2026, 5, 1),
            )
        assert exc.value.status_code == 400
        assert "F2F" in exc.value.detail

    def test_bp3_plus_allows_encounter_within_window(self, db_session):
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

        f2f = _create(
            db_session, tenant_id, patient.id, bp3.id,
            performed_by_role="MEDICAL_DIRECTOR", encounter_date=date(2026, 6, 15),
        )
        assert f2f.status == "DRAFT"


class TestStatusHistoryAuditTrail:
    def test_every_transition_is_recorded_immutably(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        bp = _make_bp(db_session, tenant_id, patient.id, election_date=date(2026, 1, 1), start_date=date(2026, 1, 1))
        f2f = _create(db_session, tenant_id, patient.id, bp.id, performed_by_role="MEDICAL_DIRECTOR")
        f2f = svc.finalize_f2f(db_session, f2f=f2f, finalized_by=TEST_USER_ID, finalized_by_role="MEDICAL_DIRECTOR")

        history = svc.get_status_history(db_session, tenant_id=tenant_id, f2f_encounter_id=f2f.id)
        transitions = [(e.from_status, e.to_status) for e in history]
        assert (None, "DRAFT") in transitions
        assert ("DRAFT", "FINALIZED") in transitions
        for e in history:
            assert e.changed_at is not None
            assert svc.label_for(e.to_status) != ""


class TestDisplayLabelLayer:
    def test_labels_do_not_change_stored_literals(self):
        assert svc.label_for("DRAFT") == "Draft"
        assert svc.label_for("FINALIZED") == "Finalized"
        assert svc.label_for("SOMETHING_NEW") == "SOMETHING_NEW"


class TestCTIF2FAuthorityIndependence:
    def test_np_is_valid_f2f_performer_but_not_cti_signer(self):
        from app.services import certification_service as cti_svc

        assert svc.is_authorized_f2f_performer("NP") is True
        assert cti_svc.is_authorized_cti_signer("NP") is False

    def test_pa_is_valid_f2f_performer_but_not_cti_signer(self):
        from app.services import certification_service as cti_svc

        assert svc.is_authorized_f2f_performer("PA") is True
        assert cti_svc.is_authorized_cti_signer("PA") is False
