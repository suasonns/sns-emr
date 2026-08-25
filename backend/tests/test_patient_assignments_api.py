from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.enums import Discipline
from app.models.patient import Patient
from app.models.user import User
from tests.conftest import TEST_USER_ID


def _headers(role: str, tenant_id: str, *, user_id: uuid.UUID = TEST_USER_ID) -> dict:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _make_patient(db_session, tenant_id: str) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=f"PA-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1946, 6, 6),
        primary_diagnosis="Hospice verification diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_user(
    db_session,
    tenant_id: str,
    *,
    role: str,
    full_name: str,
    discipline: str | None = None,
    active: bool = True,
) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{full_name.replace(' ', '.').lower()}.{uuid.uuid4().hex[:8]}@example.com",
        full_name=full_name,
        role=role,
        discipline=discipline,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.integration
def test_assignment_post_reassigns_same_discipline_and_preserves_history(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    first_chha = _make_user(db_session, tenant_id, role="CHHA", discipline="HA", full_name="Helpful Aide One")
    second_chha = _make_user(db_session, tenant_id, role="CHHA", discipline="HA", full_name="Helpful Aide Two")

    legacy_response = client.post(
        "/patient-assignments/",
        headers=_headers("ADMINISTRATOR", tenant_id),
        json={
            "patient_id": str(patient.id),
            "discipline": "CHHA",
            "staff_user_id": str(first_chha.id),
            "note": "Initial aide assignment",
        },
    )
    assert legacy_response.status_code == 201, legacy_response.text
    assert legacy_response.json()["user_id"] == str(first_chha.id)
    assert legacy_response.json()["assigned_by_user_id"] == str(TEST_USER_ID)

    current_response = client.post(
        "/patient-assignments/",
        headers=_headers("ADMINISTRATOR", tenant_id),
        json={
            "patient_id": str(patient.id),
            "discipline": "CHHA",
            "user_id": str(second_chha.id),
            "note": "Reassigned aide",
        },
    )
    assert current_response.status_code == 201, current_response.text
    assert current_response.json()["user_id"] == str(second_chha.id)
    assert current_response.json()["active"] is True
    assert current_response.json()["status"] == "ASSIGNED"

    active_list = client.get(
        f"/patient-assignments/patient/{patient.id}",
        headers=_headers("ADMINISTRATOR", tenant_id),
    )
    assert active_list.status_code == 200, active_list.text
    active_assignments = active_list.json()["assignments"]
    assert len(active_assignments) == 1
    assert active_assignments[0]["user_id"] == str(second_chha.id)

    history_list = client.get(
        f"/patient-assignments/patient/{patient.id}?include_inactive=true",
        headers=_headers("ADMINISTRATOR", tenant_id),
    )
    assert history_list.status_code == 200, history_list.text
    history_assignments = history_list.json()["assignments"]
    assert len(history_assignments) == 2
    assert history_assignments[0]["user_id"] == str(second_chha.id)
    assert history_assignments[0]["status"] == "ASSIGNED"
    assert history_assignments[0]["active"] is True
    assert history_assignments[1]["user_id"] == str(first_chha.id)
    assert history_assignments[1]["status"] == "REASSIGNED"
    assert history_assignments[1]["active"] is False


@pytest.mark.integration
def test_assignment_post_rejects_non_matching_staff_role(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admin_staff = _make_user(db_session, tenant_id, role="ADMINISTRATOR", discipline="ADMN", full_name="Roster Administrator")

    response = client.post(
        "/patient-assignments/",
        headers=_headers("ADMINISTRATOR", tenant_id),
        json={
            "patient_id": str(patient.id),
            "discipline": "CHHA",
            "user_id": str(admin_staff.id),
        },
    )
    assert response.status_code == 400, response.text
    assert "assignable clinical discipline" in response.json()["detail"]


@pytest.mark.integration
def test_assignment_deactivate_endpoint_marks_assignment_inactive(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    lvn_user = _make_user(db_session, tenant_id, role="LVN", discipline="LVN", full_name="Assigned LVN")

    create_response = client.post(
        "/patient-assignments/",
        headers=_headers("ADMINISTRATOR", tenant_id),
        json={
            "patient_id": str(patient.id),
            "discipline": Discipline.LVN.value,
            "user_id": str(lvn_user.id),
            "service_area": "South",
        },
    )
    assert create_response.status_code == 201, create_response.text
    assignment_id = create_response.json()["id"]

    deactivate_response = client.patch(
        f"/patient-assignments/{assignment_id}/deactivate",
        headers=_headers("ADMINISTRATOR", tenant_id),
        json={"note": "Coverage ended"},
    )
    assert deactivate_response.status_code == 200, deactivate_response.text
    payload = deactivate_response.json()
    assert payload["id"] == assignment_id
    assert payload["active"] is False
    assert payload["status"] == "INACTIVE"
    assert payload["note"] == "Coverage ended"

    active_list = client.get(
        f"/patient-assignments/patient/{patient.id}",
        headers=_headers("ADMINISTRATOR", tenant_id),
    )
    assert active_list.status_code == 200, active_list.text
    assert active_list.json()["assignments"] == []

    history_list = client.get(
        f"/patient-assignments/patient/{patient.id}?include_inactive=true",
        headers=_headers("ADMINISTRATOR", tenant_id),
    )
    assert history_list.status_code == 200, history_list.text
    history_assignments = history_list.json()["assignments"]
    assert len(history_assignments) == 1
    assert history_assignments[0]["id"] == assignment_id
    assert history_assignments[0]["status"] == "INACTIVE"
    assert history_assignments[0]["active"] is False
