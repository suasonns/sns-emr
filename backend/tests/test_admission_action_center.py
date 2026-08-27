from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from tests.conftest import TEST_USER_ID


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
            "type_details": {"item_description": "Hospital bed and bedside commode"},
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
    for section, request_type, details, extra in (
        ("nutrition", "medication_request", "Request appetite stimulant.", {}),
        (
            "skin_wound",
            "supply_order",
            "Wound dressing supplies needed.",
            {"type_details": {"item_description": "Foam dressing, 4x4"}},
        ),
    ):
        resp = client.post(
            f"/visits/rnica/{record.id}/action-center",
            json={
                "request_type": request_type,
                "details": details,
                "source_section": section,
                **extra,
            },
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
        json={
            "request_type": "referral",
            "details": "Chaplain referral requested.",
            "type_details": {"destination": "Chaplaincy services", "reason": "Spiritual support"},
        },
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


class TestDmeSupplyReferralPhysicianContactWorkflow:
    """Item 4: DME, supplies, referrals, and physician-contact workflow.

    Covers completion-evidence gating, cancellation-reason gating,
    mutation-after-finalization, tenant isolation, and authenticated-user
    enforcement at the service layer (the service is the single point of
    authorization/audit enforcement; the route layer only forwards the
    request-scoped tenant/user).
    """

    def test_dme_order_requires_item_description_in_type_details(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.create_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                user_id=TEST_USER_ID,
                request_type="DME_ORDER",
                details="Wheelchair needed.",
            )

    def test_physician_contact_requires_physician_method_and_reason(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.create_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                user_id=user_id,
                request_type="PHYSICIAN_CONTACT",
                details="Called MD about new symptom.",
            )

        result = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="PHYSICIAN_CONTACT",
            details="Called MD about new symptom.",
            type_details={
                "physician_name": "Dr. Smith",
                "contact_method": "PHONE",
                "reason": "New unmanaged symptom",
            },
        )
        assert result["typeDetails"]["physician_name"] == "Dr. Smith"

    def test_create_requires_authenticated_user(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.create_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                user_id=None,
                request_type="REFERRAL",
                details="Chaplain referral.",
                type_details={"destination": "Chaplaincy", "reason": "Spiritual support"},
            )

    def test_complete_requires_timestamped_evidence(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID
        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="SUPPLY_ORDER",
            details="Wound dressing supplies.",
            type_details={"item_description": "Foam dressing"},
        )

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.complete_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                completion_evidence="   ",
            )

        completed = svc.complete_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            request_id=uuid.UUID(created["id"]),
            user_id=user_id,
            completion_evidence="Delivered and signed for by caregiver on 2026-08-30.",
        )
        assert completed["status"] == "COMPLETED"
        assert completed["completedAt"] is not None
        assert completed["completionEvidence"]

    def test_cancel_requires_reason(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID
        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="REFERRAL",
            details="Home health referral.",
            type_details={"destination": "Home health agency", "reason": "Skilled need"},
        )

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.cancel_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                cancellation_reason="",
            )

        canceled = svc.cancel_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            request_id=uuid.UUID(created["id"]),
            user_id=user_id,
            cancellation_reason="Patient declined referral",
        )
        assert canceled["status"] == "CANCELED"
        assert canceled["cancellationReason"] == "Patient declined referral"

    def test_finalized_request_cannot_be_mutated(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID
        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="SUPPLY_ORDER",
            details="Incontinence supplies.",
            type_details={"item_description": "Briefs, size M"},
        )
        svc.complete_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            request_id=uuid.UUID(created["id"]),
            user_id=user_id,
            completion_evidence="Delivered 2026-08-30, signed by patient.",
        )

        with pytest.raises(svc.AdmissionActionCenterError):
            svc.update_status(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                new_status="ACKNOWLEDGED",
            )
        with pytest.raises(svc.AdmissionActionCenterError):
            svc.cancel_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                cancellation_reason="Trying to cancel a completed request",
            )

    def test_cross_tenant_read_and_write_denied(self, db_session):
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        other_tenant_id = uuid.uuid4()
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID
        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="REFERRAL",
            details="PT referral.",
            type_details={"destination": "Physical therapy", "reason": "Mobility decline"},
        )

        # Cross-tenant read: request is invisible to another tenant's scope.
        assert svc.list_requests(db_session, tenant_id=other_tenant_id, patient_id=patient.id) == []

        # Cross-tenant write: status/complete/cancel all report not-found
        # rather than leaking existence or mutating another tenant's record.
        with pytest.raises(svc.AdmissionActionCenterError, match="not found"):
            svc.update_status(
                db_session,
                tenant_id=other_tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                new_status="IN_PROGRESS",
            )
        with pytest.raises(svc.AdmissionActionCenterError, match="not found"):
            svc.complete_request(
                db_session,
                tenant_id=other_tenant_id,
                patient_id=patient.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                completion_evidence="Attempted cross-tenant completion",
            )

    def test_same_tenant_cross_patient_mutation_denied(self, db_session):
        """Item 3 / P0-3: a same-tenant user authorized for one patient's
        assessment must not be able to mutate a *different* patient's
        request just by supplying that request's id -- the service must
        verify the loaded request actually belongs to the patient resolved
        from the route, not just the tenant."""
        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient_a = _make_patient(db_session, tenant_id)
        patient_b = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID

        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient_a.id,
            user_id=user_id,
            request_type="REFERRAL",
            details="PT referral for patient A.",
            type_details={"destination": "Physical therapy", "reason": "Mobility decline"},
        )

        # Same tenant, but the request belongs to patient A -- mutating it
        # while "authorized" only for patient B must be denied as not found.
        with pytest.raises(svc.AdmissionActionCenterError, match="not found"):
            svc.update_status(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient_b.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                new_status="SENT",
            )
        with pytest.raises(svc.AdmissionActionCenterError, match="not found"):
            svc.complete_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient_b.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                completion_evidence="Attempted cross-patient completion",
            )
        with pytest.raises(svc.AdmissionActionCenterError, match="not found"):
            svc.cancel_request(
                db_session,
                tenant_id=tenant_id,
                patient_id=patient_b.id,
                request_id=uuid.UUID(created["id"]),
                user_id=user_id,
                cancellation_reason="Attempted cross-patient cancellation",
            )

        # Sanity check: the same mutation succeeds with the correct patient.
        updated = svc.update_status(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient_a.id,
            request_id=uuid.UUID(created["id"]),
            user_id=user_id,
            new_status="SENT",
        )
        assert updated["status"] == "SENT"

    def test_same_tenant_cross_patient_mutation_denied_via_route(self, client, db_session, rn_headers):
        """Route-level regression: authorizing via patient B's assessment
        must not allow mutating patient A's Action Center request."""
        tenant_id = db_session.info.get("tenant_id")
        patient_a = _make_patient(db_session, tenant_id)
        patient_b = _make_patient(db_session, tenant_id)
        assessment_a = _make_rnica_assessment(db_session, patient_a, tenant_id)
        assessment_b = _make_rnica_assessment(db_session, patient_b, tenant_id)

        create_resp = client.post(
            f"/visits/rnica/{assessment_a.id}/action-center",
            json={
                "request_type": "supply_order",
                "details": "Wound care supplies for patient A.",
                "type_details": {"item_description": "Foam dressing, box"},
            },
            headers=rn_headers,
        )
        assert create_resp.status_code == 201, create_resp.text
        request_id = create_resp.json()["id"]

        # Authorized via patient B's assessment, but targeting patient A's
        # request id -- must be rejected (404), not mutated.
        complete_resp = client.post(
            f"/visits/rnica/{assessment_b.id}/action-center/{request_id}/complete",
            json={"completion_evidence": "Attempted cross-patient completion via route"},
            headers=rn_headers,
        )
        assert complete_resp.status_code == 404, complete_resp.text

        cancel_resp = client.post(
            f"/visits/rnica/{assessment_b.id}/action-center/{request_id}/cancel",
            json={"cancellation_reason": "Attempted cross-patient cancellation via route"},
            headers=rn_headers,
        )
        assert cancel_resp.status_code == 404, cancel_resp.text

        status_resp = client.patch(
            f"/visits/rnica/{assessment_b.id}/action-center/{request_id}/status",
            json={"status": "sent"},
            headers=rn_headers,
        )
        assert status_resp.status_code == 404, status_resp.text

    def test_audit_events_recorded_for_create_complete_and_cancel(self, db_session):
        from sqlalchemy import text

        from app.services import admission_action_center_service as svc

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        user_id = TEST_USER_ID
        created = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="DME_ORDER",
            details="Hospital bed.",
            type_details={"item_description": "Hospital bed, full electric"},
        )
        svc.complete_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            request_id=uuid.UUID(created["id"]),
            user_id=user_id,
            completion_evidence="Delivered and set up 2026-08-30.",
        )

        cancel_target = svc.create_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            user_id=user_id,
            request_type="SUPPLY_ORDER",
            details="Gloves.",
            type_details={"item_description": "Nitrile gloves, box"},
        )
        svc.cancel_request(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            request_id=uuid.UUID(cancel_target["id"]),
            user_id=user_id,
            cancellation_reason="Duplicate request",
        )

        rows = db_session.execute(
            text(
                "SELECT entity_id, action, metadata FROM audit_logs WHERE entity_id IN (:a, :b) "
                "AND action IN ("
                "'ADMISSION_ACTION_REQUEST_CREATED', "
                "'ADMISSION_ACTION_REQUEST_COMPLETED', "
                "'ADMISSION_ACTION_REQUEST_CANCELED'"
                ")"
            ),
            {"a": created["id"], "b": cancel_target["id"]},
        ).fetchall()
        actions_by_entity: dict[str, set[str]] = {}
        metadata_by_action: dict[str, dict] = {}
        for entity_id, action, metadata in rows:
            actions_by_entity.setdefault(str(entity_id), set()).add(action)
            metadata_by_action[f"{entity_id}:{action}"] = metadata

        assert actions_by_entity[created["id"]] == {
            "ADMISSION_ACTION_REQUEST_CREATED",
            "ADMISSION_ACTION_REQUEST_COMPLETED",
        }
        assert actions_by_entity[cancel_target["id"]] == {
            "ADMISSION_ACTION_REQUEST_CREATED",
            "ADMISSION_ACTION_REQUEST_CANCELED",
        }

        # P1-1: audit_event(meta=...) must actually persist to the
        # `metadata` DB column (mapped attribute `event_metadata`), not be
        # silently dropped by a stale "meta" column-name check.
        created_meta = metadata_by_action[f"{created['id']}:ADMISSION_ACTION_REQUEST_CREATED"]
        assert created_meta is not None
        assert created_meta["requestType"] == "DME_ORDER"

        completed_meta = metadata_by_action[f"{created['id']}:ADMISSION_ACTION_REQUEST_COMPLETED"]
        assert completed_meta is not None
        assert completed_meta["completionEvidence"] == "Delivered and set up 2026-08-30."

        canceled_meta = metadata_by_action[f"{cancel_target['id']}:ADMISSION_ACTION_REQUEST_CANCELED"]
        assert canceled_meta is not None
        assert canceled_meta["cancellationReason"] == "Duplicate request"
