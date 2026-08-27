from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_order import PatientOrder
from app.models.rnica_assessment import RnicaAssessment


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"RNICA-ORD-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()

    return patient, admission


def _make_rnica_assessment(db_session, patient, tenant_id, form_data):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data,
    )
    db_session.add(record)
    db_session.commit()
    return record


@pytest.mark.integration
def test_suggested_orders_detects_skin_finding(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(
        db_session,
        patient,
        tenant_id,
        {
            "skin": {"wound_present": True, "notes": "Stage 2 pressure injury, sacrum, draining."},
        },
    )

    resp = client.get(f"/visits/rnica/{record.id}/suggested-orders", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["generator"]["mode"] == "suggest_only"
    assert body["generator"]["auto_applied"] is False
    rule_keys = {s["rule_key"] for s in body["suggestions"]}
    assert "SKIN_INTEGRITY" in rule_keys

    # Nothing should be persisted just from viewing suggestions.
    assert (
        db_session.query(PatientOrder)
        .filter(PatientOrder.patient_id == patient.id)
        .count()
        == 0
    )


@pytest.mark.integration
def test_apply_suggested_orders_creates_real_orders(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(
        db_session,
        patient,
        tenant_id,
        {
            "skin": {"wound_present": True, "notes": "Stage 2 pressure injury, sacrum, draining."},
        },
    )

    suggestions_resp = client.get(f"/visits/rnica/{record.id}/suggested-orders", headers=rn_headers)
    assert suggestions_resp.status_code == 200
    suggestion_keys = [s["suggestion_key"] for s in suggestions_resp.json()["suggestions"]]
    assert suggestion_keys

    apply_resp = client.post(
        f"/visits/rnica/{record.id}/suggested-orders/apply",
        json={"suggestion_keys": suggestion_keys},
        headers=rn_headers,
    )
    assert apply_resp.status_code == 201, apply_resp.text
    created = apply_resp.json()["created"]
    assert len(created) == len(suggestion_keys)

    orders = db_session.query(PatientOrder).filter(PatientOrder.patient_id == patient.id).all()
    assert len(orders) == len(suggestion_keys)
    for order in orders:
        assert order.source_kind == "RULE_SUGGESTED"
        assert order.source_rnica_assessment_id == record.id
        assert order.status == "active"

    # Re-fetching suggestions after applying must no longer offer the
    # already-created orders (dedup against existing active orders).
    resuggest_resp = client.get(f"/visits/rnica/{record.id}/suggested-orders", headers=rn_headers)
    assert resuggest_resp.status_code == 200
    remaining_keys = {s["suggestion_key"] for s in resuggest_resp.json()["suggestions"]}
    assert remaining_keys.isdisjoint(set(suggestion_keys))


@pytest.mark.integration
def test_apply_suggested_orders_rejects_unknown_key(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {})

    resp = client.post(
        f"/visits/rnica/{record.id}/suggested-orders/apply",
        json={"suggestion_keys": ["NOT_A_REAL_KEY"]},
        headers=rn_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["created"] == []
    assert body["notFound"] == ["NOT_A_REAL_KEY"]
