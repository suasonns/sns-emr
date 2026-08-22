from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"AAC-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_rnica_assessment(db_session, patient, tenant_id, form_data=None):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data or {},
    )
    db_session.add(record)
    db_session.commit()
    return record


@pytest.mark.integration
def test_create_list_and_update_status_via_action_center_routes(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id is not None

    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id)

    # --- Create ---------------------------------------------------------
    create_resp = client.post(
        f"/visits/rnica/{record.id}/action-center",
        json={
            "request_type": "dme_order",
            "details": "Hospital bed and bedside commode for safety.",
            "source_section": "functional_status",
        },
        headers=rn_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["requestType"] == "DME_ORDER"
    assert created["status"] == "REQUESTED"
    assert created["sourceSection"] == "functional_status"
    assert created["rnicaAssessmentId"] == str(record.id)
    assert len(created["statusHistory"]) == 1
    assert created["statusHistory"][0]["status"] == "REQUESTED"
    request_id = created["id"]

    # --- List: request is visible from the action center drawer ---------
    list_resp = client.get(f"/visits/rnica/{record.id}/action-center", headers=rn_headers)
    assert list_resp.status_code == 200, list_resp.text
    requests = list_resp.json()["requests"]
    assert any(r["id"] == request_id for r in requests)

    # --- Update status ----------------------------------------------------
    update_resp = client.patch(
        f"/visits/rnica/{record.id}/action-center/{request_id}/status",
        json={"status": "sent", "note": "Faxed to DME vendor"},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["status"] == "SENT"
    assert len(updated["statusHistory"]) == 2
    assert updated["statusHistory"][-1]["status"] == "SENT"
    assert updated["statusHistory"][-1]["note"] == "Faxed to DME vendor"


@pytest.mark.integration
def test_action_center_is_global_across_sections_and_available_on_locked_assessment(
    client, db_session, rn_headers
):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id)

    # Raise requests from two different sections of the same assessment.
    for section, request_type, details in (
        ("nutrition", "medication_request", "Request appetite stimulant."),
        ("skin_wound", "supply_order", "Wound dressing supplies needed."),
    ):
        resp = client.post(
            f"/visits/rnica/{record.id}/action-center",
            json={"request_type": request_type, "details": details, "source_section": section},
            headers=rn_headers,
        )
        assert resp.status_code == 201, resp.text

    list_resp = client.get(f"/visits/rnica/{record.id}/action-center", headers=rn_headers)
    requests = list_resp.json()["requests"]
    assert {r["sourceSection"] for r in requests} == {"nutrition", "skin_wound"}

    # Lock the assessment directly (bypassing the finalization workflow,
    # which is out of scope here) to confirm Action Center still works on
    # a locked chart -- it is explicitly NOT lock-gated (Phase A spec).
    record.locked = True
    db_session.add(record)
    db_session.commit()

    resp = client.post(
        f"/visits/rnica/{record.id}/action-center",
        json={"request_type": "referral", "details": "Chaplain referral requested."},
        headers=rn_headers,
    )
    assert resp.status_code == 201, resp.text


@pytest.mark.integration
def test_action_center_validates_request_type_and_status_values(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id)

    bad_type_resp = client.post(
        f"/visits/rnica/{record.id}/action-center",
        json={"request_type": "LAB_ORDER", "details": "Not a supported Phase A type."},
        headers=rn_headers,
    )
    assert bad_type_resp.status_code == 400, bad_type_resp.text

    blank_details_resp = client.post(
        f"/visits/rnica/{record.id}/action-center",
        json={"request_type": "REFERRAL", "details": "   "},
        headers=rn_headers,
    )
    assert blank_details_resp.status_code == 400, blank_details_resp.text

    create_resp = client.post(
        f"/visits/rnica/{record.id}/action-center",
        json={"request_type": "physician_order", "details": "Order for wound care ointment."},
        headers=rn_headers,
    )
    request_id = create_resp.json()["id"]

    bad_status_resp = client.patch(
        f"/visits/rnica/{record.id}/action-center/{request_id}/status",
        json={"status": "APPROVED"},
        headers=rn_headers,
    )
    assert bad_status_resp.status_code == 400, bad_status_resp.text

    missing_resp = client.patch(
        f"/visits/rnica/{record.id}/action-center/{uuid.uuid4()}/status",
        json={"status": "ORDERED"},
        headers=rn_headers,
    )
    assert missing_resp.status_code == 404, missing_resp.text
