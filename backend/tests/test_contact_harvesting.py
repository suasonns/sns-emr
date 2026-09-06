from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.models.document_record import DocumentRecord
from app.models.patient import Patient
from app.models.patient_contact import PatientContact
from app.models.patient_contact_suggestion import PatientContactSuggestion
from app.services.contact_harvest_service import (
    _parse_contact_value,
    _role_for_label,
    harvest_patient_contacts_from_document,
)
from app.services.contact_sync_service import (
    ALLOWED_CONTACT_ROLES,
    CONSERVATOR,
    GUARDIAN,
    get_patient_contacts,
    set_patient_contact,
)
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"CONTACT-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1935, 6, 1),
        primary_diagnosis="Contact harvesting test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_document(
    db_session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    key_findings: list[dict],
) -> DocumentRecord:
    doc = DocumentRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        document_type="H_AND_P",
        source="EXTERNAL",
        file_name="hnp.txt",
        file_path=None,
        extracted_values={"ai_key_findings": key_findings},
        document_text="synthetic test document",
        uploaded_by=TEST_USER_ID,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


# ---------------------------------------------------------------------
# Role/value parsing
# ---------------------------------------------------------------------


def test_role_for_label_matches_all_new_and_existing_roles():
    assert _role_for_label("Emergency Contact") == "EMERGENCY_CONTACT"
    assert _role_for_label("Responsible Party") == "RESPONSIBLE_PARTY"
    assert _role_for_label("Durable Power of Attorney") == "DPOA"
    assert _role_for_label("Healthcare Proxy") == "HEALTHCARE_AGENT"
    assert _role_for_label("Advance Directive Agent") == "HEALTHCARE_AGENT"
    assert _role_for_label("Guardian") == "GUARDIAN"
    assert _role_for_label("Conservator") == "CONSERVATOR"
    assert _role_for_label("Sodium") is None


def test_guardian_and_conservator_are_allowed_contact_roles():
    assert GUARDIAN in ALLOWED_CONTACT_ROLES
    assert CONSERVATOR in ALLOWED_CONTACT_ROLES


def test_parse_contact_value_extracts_name_relationship_phone():
    parsed = _parse_contact_value("Jane Doe (Daughter) 555-123-4567")
    assert parsed["name"] == "Jane Doe"
    assert parsed["relationship_to_patient"] == "Daughter"
    assert parsed["phone"] == "555-123-4567"


def test_parse_contact_value_extracts_email():
    parsed = _parse_contact_value("John Smith john.smith@example.com")
    assert parsed["email"] == "john.smith@example.com"
    assert parsed["name"] == "John Smith"


# ---------------------------------------------------------------------
# Harvest -> apply when empty
# ---------------------------------------------------------------------


def test_harvest_applies_directly_when_no_existing_contact(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    doc = _make_document(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        key_findings=[
            {
                "label": "Emergency Contact",
                "value": "Jane Doe (Daughter) 555-123-4567",
                "category": "administrative",
                "original_text_excerpt": "Emergency Contact: Jane Doe (Daughter) 555-123-4567",
            }
        ],
    )

    result = harvest_patient_contacts_from_document(db_session, document=doc)
    db_session.commit()

    assert "EMERGENCY_CONTACT" in result["applied"]
    assert result["queued"] == []

    contacts = get_patient_contacts(db_session, patient_id=patient.id, tenant_id=tenant_id)
    row = contacts["EMERGENCY_CONTACT"]
    assert row.name == "Jane Doe"
    assert row.relationship_to_patient == "Daughter"
    assert row.phone == "555-123-4567"
    assert row.attribution_source == "HARVESTED"
    assert row.source_document_id == doc.id
    assert row.manual_override is False


# ---------------------------------------------------------------------
# Harvest -> conflict queues a suggestion, never overwrites
# ---------------------------------------------------------------------


def test_harvest_queues_suggestion_on_conflict_with_existing_value(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    # Existing manually-entered contact.
    set_patient_contact(
        db_session,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role="EMERGENCY_CONTACT",
        source="FACESHEET",
        name="Existing Name",
        phone="111-111-1111",
        updated_by=TEST_USER_ID,
        is_manual_entry=True,
    )
    db_session.commit()

    doc = _make_document(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        key_findings=[
            {
                "label": "Emergency Contact",
                "value": "Different Name 222-222-2222",
                "category": "administrative",
                "original_text_excerpt": "Emergency Contact: Different Name 222-222-2222",
            }
        ],
    )

    result = harvest_patient_contacts_from_document(db_session, document=doc)
    db_session.commit()

    assert result["applied"] == []
    assert "EMERGENCY_CONTACT" in result["queued"]

    # Original value untouched.
    contacts = get_patient_contacts(db_session, patient_id=patient.id, tenant_id=tenant_id)
    row = contacts["EMERGENCY_CONTACT"]
    assert row.name == "Existing Name"
    assert row.phone == "111-111-1111"
    assert row.manual_override is True

    suggestions = (
        db_session.query(PatientContactSuggestion)
        .filter(PatientContactSuggestion.patient_id == patient.id)
        .all()
    )
    assert len(suggestions) == 2  # name + phone both differ
    fields = {s.field_name for s in suggestions}
    assert fields == {"name", "phone"}
    assert all(s.status == "pending" for s in suggestions)


def test_harvest_does_not_duplicate_pending_suggestion_on_repeat_upload(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    set_patient_contact(
        db_session,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role="RESPONSIBLE_PARTY",
        source="FACESHEET",
        name="Existing RP",
        updated_by=TEST_USER_ID,
        is_manual_entry=True,
    )
    db_session.commit()

    findings = [
        {
            "label": "Responsible Party",
            "value": "Conflicting RP",
            "category": "administrative",
            "original_text_excerpt": "Responsible Party: Conflicting RP",
        }
    ]

    doc1 = _make_document(db_session, tenant_id=tenant_id, patient_id=patient.id, key_findings=findings)
    harvest_patient_contacts_from_document(db_session, document=doc1)
    db_session.commit()

    doc2 = _make_document(db_session, tenant_id=tenant_id, patient_id=patient.id, key_findings=findings)
    harvest_patient_contacts_from_document(db_session, document=doc2)
    db_session.commit()

    suggestions = (
        db_session.query(PatientContactSuggestion)
        .filter(
            PatientContactSuggestion.patient_id == patient.id,
            PatientContactSuggestion.role == "RESPONSIBLE_PARTY",
            PatientContactSuggestion.status == "pending",
        )
        .all()
    )
    assert len(suggestions) == 1


# ---------------------------------------------------------------------
# API: manual entry stamps manual_override; suggestion accept/reject
# ---------------------------------------------------------------------


def test_manual_contact_endpoint_stamps_manual_override(db_session, client, rn_headers):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    resp = client.post(
        f"/patients/{patient.id}/contacts",
        params={
            "role": "GUARDIAN",
            "name": "Guardian Name",
            "phone": "333-333-3333",
        },
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["role"] == "GUARDIAN"
    assert body["manual_override"] is True
    assert body["attribution_source"] == "MANUAL"


def test_accept_contact_suggestion_applies_value_and_resolves(db_session, client, rn_headers):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    set_patient_contact(
        db_session,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role="HEALTHCARE_AGENT",
        source="FACESHEET",
        name="Old Agent",
        updated_by=TEST_USER_ID,
        is_manual_entry=True,
    )
    db_session.commit()

    doc = _make_document(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        key_findings=[
            {
                "label": "Healthcare Agent",
                "value": "New Agent",
                "category": "administrative",
                "original_text_excerpt": "Healthcare Agent: New Agent",
            }
        ],
    )
    harvest_patient_contacts_from_document(db_session, document=doc)
    db_session.commit()

    suggestion = (
        db_session.query(PatientContactSuggestion)
        .filter(
            PatientContactSuggestion.patient_id == patient.id,
            PatientContactSuggestion.role == "HEALTHCARE_AGENT",
        )
        .first()
    )
    assert suggestion is not None

    resp = client.post(
        f"/patients/{patient.id}/contacts/suggestions/{suggestion.id}/accept",
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["suggestion"]["status"] == "accepted"
    assert body["contact"]["name"] == "New Agent"

    db_session.expire_all()
    contacts = get_patient_contacts(db_session, patient_id=patient.id, tenant_id=tenant_id)
    assert contacts["HEALTHCARE_AGENT"].name == "New Agent"


def test_reject_contact_suggestion_leaves_existing_value_untouched(db_session, client, rn_headers):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    set_patient_contact(
        db_session,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role="DPOA",
        source="FACESHEET",
        name="Original DPOA",
        updated_by=TEST_USER_ID,
        is_manual_entry=True,
    )
    db_session.commit()

    doc = _make_document(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        key_findings=[
            {
                "label": "Power of Attorney",
                "value": "Conflicting DPOA",
                "category": "administrative",
                "original_text_excerpt": "POA: Conflicting DPOA",
            }
        ],
    )
    harvest_patient_contacts_from_document(db_session, document=doc)
    db_session.commit()

    suggestion = (
        db_session.query(PatientContactSuggestion)
        .filter(PatientContactSuggestion.patient_id == patient.id, PatientContactSuggestion.role == "DPOA")
        .first()
    )
    assert suggestion is not None

    resp = client.post(
        f"/patients/{patient.id}/contacts/suggestions/{suggestion.id}/reject",
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "rejected"

    db_session.expire_all()
    contacts = get_patient_contacts(db_session, patient_id=patient.id, tenant_id=tenant_id)
    assert contacts["DPOA"].name == "Original DPOA"
