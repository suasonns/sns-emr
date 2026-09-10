"""
Priority 8 -- end-to-end Billing Readiness validation matrix.

This is the requested "run all workflows, do not spot test" validation:
one parametrized, end-to-end pass through check_patient_billing_readiness()
across the payer / contracted-status / authorization / consent axes it
actually consumes, plus the admission-gate (SOC blocking) axes which are
already covered by test_eligibility_workflow_service.py and
tests/guardrails/test_soc_gate_guardrail.py (referenced, not duplicated,
below).

Each case builds a fully-ready baseline patient (see
_fully_ready_patient in test_billing_readiness_service.py) and then
layers on exactly the one axis under test, so a failure here can only be
attributed to that axis's readiness contribution -- not to an unrelated
missing prerequisite.
"""

from __future__ import annotations

import uuid

import pytest

from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.services.eligibility_workflow_service import record_eligibility_source_document
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_payer import PatientPayer

from tests.test_billing_readiness_service import SERVICE_DATE, _fully_ready_patient
from tests.test_eligibility_workflow_service import _make_document_record, _make_user


def _set_payer_review(
    db_session,
    tenant_id: str,
    patient_id,
    *,
    contracted_status=None,
    authorization_required_status=None,
) -> None:
    actor_id = _make_user(db_session, tenant_id)
    facesheet = PatientFaceSheet(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient_id,
        first_name="Matrix",
        last_name="Patient",
        contracted_status=contracted_status,
        authorization_required_status=authorization_required_status,
        created_by=actor_id,
    )
    db_session.add(facesheet)
    db_session.commit()


def _set_payer_type(db_session, patient, payer_type: str) -> None:
    # _fully_ready_patient already attached a MEDICARE PatientPayer row via
    # _make_payer(); overwrite payer_type/name on that row for this axis
    # instead of adding a second payer (would trip the ambiguous-sequence
    # blocker, which is a different, already-covered check).
    payer = (
        db_session.query(PatientPayer)
        .filter(PatientPayer.patient_id == patient.id, PatientPayer.is_primary.is_(True))
        .one()
    )
    payer.payer_type = payer_type
    payer.payer_name = payer_type
    db_session.commit()


def _add_consent_document(db_session, tenant_id: str, patient) -> None:
    from app.models.document_record import DocumentRecord

    user_id = _make_user(db_session, tenant_id)
    doc = DocumentRecord(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        document_type="CONSENT_FORM",
        uploaded_by=user_id,
    )
    db_session.add(doc)
    db_session.commit()


@pytest.mark.parametrize("payer_type", ["MEDICARE", "HMO", "PPO", "COMMERCIAL", "UNKNOWN_PAYER"])
def test_payer_type_axis_does_not_gate_readiness_alone(db_session, tenant, payer_type):
    """
    Payer type/name is descriptive only -- billing readiness is gated by
    contracted_status / authorization_required_status (staff-reviewed),
    never by payer type directly. A fully-documented patient stays READY
    regardless of which payer type is on file.
    """
    patient = _fully_ready_patient(db_session, tenant.id, mrn=f"MRN-MTX-PAYER-{payer_type}")
    _set_payer_type(db_session, patient, payer_type)
    _add_consent_document(db_session, tenant.id, patient)

    result = check_patient_billing_readiness(
        db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE
    )

    assert result.ready is True
    assert result.blockers == []
    assert result.warnings == []


@pytest.mark.parametrize(
    "authorization_required_status,has_evidence,expected_blocked,expected_warned",
    [
        ("YES", False, True, False),   # AUTH_REQUIRED, no evidence -> BLOCKED
        ("YES", True, False, False),   # AUTH_REQUIRED, evidence on file -> READY
        ("NO", False, False, True),    # AUTH_NOT_REQUIRED, unverified -> AT_RISK
        ("UNKNOWN", False, False, True),  # AUTH_UNKNOWN -> AT_RISK
    ],
)
def test_authorization_axis(
    db_session, tenant, authorization_required_status, has_evidence, expected_blocked, expected_warned
):
    patient = _fully_ready_patient(
        db_session, tenant.id, mrn=f"MRN-MTX-AUTH-{authorization_required_status}-{has_evidence}"
    )
    _add_consent_document(db_session, tenant.id, patient)
    _set_payer_review(
        db_session,
        tenant.id,
        patient.id,
        contracted_status="YES",
        authorization_required_status=authorization_required_status,
    )
    if has_evidence:
        user_id = _make_user(db_session, tenant.id)
        doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
        record_eligibility_source_document(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            document_record_id=str(doc_record.id),
            document_type="AUTHORIZATION_DOCUMENT",
            uploaded_by_user_id=str(user_id),
        )

    result = check_patient_billing_readiness(
        db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE
    )

    assert (len(result.blockers) > 0) is expected_blocked
    assert (len(result.warnings) > 0) is expected_warned
    assert result.ready is (not expected_blocked)


@pytest.mark.parametrize(
    "contracted_status,expected_warned",
    [
        ("YES", False),       # CONTRACTED -> READY
        ("NO", True),         # NOT_CONTRACTED -> AT_RISK (never a blocker; documented, unchanged behavior)
        ("UNKNOWN", True),    # UNKNOWN_CONTRACTED -> AT_RISK
    ],
)
def test_contracted_status_axis(db_session, tenant, contracted_status, expected_warned):
    patient = _fully_ready_patient(db_session, tenant.id, mrn=f"MRN-MTX-CONTRACTED-{contracted_status}")
    _add_consent_document(db_session, tenant.id, patient)
    _set_payer_review(
        db_session,
        tenant.id,
        patient.id,
        contracted_status=contracted_status,
        authorization_required_status="YES",
    )
    # Isolate the contracted-status axis: authorization required WITH
    # evidence on file contributes no finding of its own.
    user_id = _make_user(db_session, tenant.id)
    doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
    record_eligibility_source_document(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="AUTHORIZATION_DOCUMENT",
        uploaded_by_user_id=str(user_id),
    )

    result = check_patient_billing_readiness(
        db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE
    )

    assert result.blockers == []  # contracted status is never a blocker
    assert (len(result.warnings) > 0) is expected_warned
    assert result.ready is True  # never blocks


@pytest.mark.parametrize(
    "has_consent_doc,expected_warned",
    [
        (True, False),   # CONSENT_PRESENT -> no warning
        (False, True),   # CONSENT_MISSING -> AT_RISK, never blocked
    ],
)
def test_consent_axis(db_session, tenant, has_consent_doc, expected_warned):
    patient = _fully_ready_patient(db_session, tenant.id, mrn=f"MRN-MTX-CONSENT-{has_consent_doc}")
    if has_consent_doc:
        _add_consent_document(db_session, tenant.id, patient)

    result = check_patient_billing_readiness(
        db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE
    )

    assert result.blockers == []  # consent is never a blocker
    assert (len(result.warnings) > 0) is expected_warned
    assert result.ready is True


def test_combined_worst_case_scenario_is_blocked(db_session, tenant):
    """
    All independent axes stacked (auth required + no evidence, not
    contracted, no consent) -- verdict must still be BLOCKED (any single
    blocker forces NOT_READY), with every applicable warning also present
    (severity aggregation is additive/union, not first-match).
    """
    patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-MTX-WORST-CASE")
    _set_payer_review(
        db_session,
        tenant.id,
        patient.id,
        contracted_status="NO",
        authorization_required_status="YES",
    )
    # no consent doc, no authorization evidence

    result = check_patient_billing_readiness(
        db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE
    )

    assert result.ready is False
    assert len(result.blockers) >= 1  # authorization required, no evidence
    assert len(result.warnings) >= 2  # not contracted + consent missing
