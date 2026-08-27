"""
End-to-end HTTP-level coverage for the "all disciplines need a staff+date
picker" feature added to make sure every visit is tracked against a real
chosen clinician instead of always silently defaulting to whoever clicked
the button:

  GET /visits/patient/{patient_id}/assignable-staff?discipline=...
      -- lists the staff assigned to a patient for a given discipline, used
         by the "Create Visit" staff+date picker (RN/LVN/SC/MSW/CHHA).
  GET /visits/{visit_id}/edit-history
      -- read-only edit/audit trail for a visit, backing "CHHA Notes
         History" (who edited a visit, what action, and when).

Also covers that POST /visits/ (create_visit) honors the new optional
assigned_staff_id / visit_datetime fields instead of always defaulting to
the creating user and now().
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.audit_log import AuditLog
from app.models.enums import Discipline
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.models.visit import Visit
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id() -> uuid.UUID:
    return uuid.UUID(_test_tenant_id())


def _qa_headers() -> dict:
    token = create_access_token(
        user_id=TEST_USER_ID,
        role="QA_REVIEWER",
        tenant_id=_tenant_id(),
        email="qa.reviewer@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-User-Id": str(TEST_USER_ID)}


def _make_patient(db_session) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        mrn=f"PICK-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Test Diagnosis",
        status="ACTIVE",
        admission_status="ACTIVE",
        hospice_election_date=date.today(),
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient_id, *, status: str = "ACTIVE") -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        effective_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        soc_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status=status,
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_user(db_session, *, role: str, full_name: str) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        email=f"{uuid.uuid4().hex[:10]}@example.com",
        full_name=full_name,
        role=role,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _assign(db_session, patient_id, user_id, discipline: Discipline, *, is_primary: bool = False):
    assignment = PatientAssignment(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        user_id=user_id,
        discipline=discipline,
        active=True,
        status="ASSIGNED",
        is_primary=is_primary,
        assigned_by=TEST_USER_ID,
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


class TestAssignableStaffEndpoint:
    def test_lists_only_staff_matching_discipline(self, client, db_session):
        patient = _make_patient(db_session)
        aide = _make_user(db_session, role="CHHA", full_name="Aide One")
        rn = _make_user(db_session, role="RN", full_name="Nurse One")
        _assign(db_session, patient.id, aide.id, Discipline.CHHA, is_primary=True)
        _assign(db_session, patient.id, rn.id, Discipline.RN, is_primary=True)

        resp = client.get(
            f"/visits/patient/{patient.id}/assignable-staff",
            params={"discipline": "CHHA"},
            headers=_qa_headers(),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["discipline"] == "CHHA"
        staff_ids = [row["user_id"] for row in body["staff"]]
        assert str(aide.id) in staff_ids
        assert str(rn.id) not in staff_ids

    def test_unknown_discipline_is_rejected(self, client, db_session):
        patient = _make_patient(db_session)
        resp = client.get(
            f"/visits/patient/{patient.id}/assignable-staff",
            params={"discipline": "NOT_A_DISCIPLINE"},
            headers=_qa_headers(),
        )
        assert resp.status_code == 422, resp.text


class TestCreateVisitStaffAndDatetime:
    def test_create_visit_honors_assigned_staff_and_datetime(self, client, db_session):
        patient = _make_patient(db_session)
        _make_admission(db_session, patient.id, status="ADMITTED")
        aide = _make_user(db_session, role="CHHA", full_name="Aide Two")
        _assign(db_session, patient.id, aide.id, Discipline.CHHA, is_primary=True)

        chosen_datetime = datetime(2026, 3, 1, 9, 30, tzinfo=timezone.utc)
        resp = client.post(
            "/visits/",
            json={
                "patient_id": str(patient.id),
                "visit_type": "CHHA",
                "level_of_care": "CC",
                "form_type": "ROUTINE_VISIT",
                "visit_schedule_type": "SCHEDULED",
                "assigned_staff_id": str(aide.id),
                "visit_datetime": chosen_datetime.isoformat(),
            },
            headers=_qa_headers(),
        )
        assert resp.status_code == 201, resp.text
        visit_id = resp.json()["visit_id"]

        visit = db_session.query(Visit).filter(Visit.id == uuid.UUID(visit_id)).first()
        assert visit is not None
        assert str(visit.provider_id) == str(aide.id)
        assert visit.visit_datetime.replace(tzinfo=timezone.utc) == chosen_datetime

    def test_create_visit_rejects_staff_from_other_tenant(self, client, db_session):
        from app.models.tenant import Tenant

        other_tenant_id = uuid.uuid4()
        db_session.add(Tenant(
            id=other_tenant_id, legal_name="Other Tenant", display_name="Other",
            npi="9876543211", tenant_type="DEV", status="ACTIVE",
        ))
        db_session.commit()

        patient = _make_patient(db_session)
        _make_admission(db_session, patient.id, status="ADMITTED")
        other_tenant_user = User(
            id=uuid.uuid4(),
            tenant_id=other_tenant_id,
            email=f"{uuid.uuid4().hex[:10]}@example.com",
            full_name="Outsider",
            role="CHHA",
            active=True,
        )
        db_session.add(other_tenant_user)
        db_session.commit()

        resp = client.post(
            "/visits/",
            json={
                "patient_id": str(patient.id),
                "visit_type": "CHHA",
                "level_of_care": "RC",
                "form_type": "ROUTINE_VISIT",
                "assigned_staff_id": str(other_tenant_user.id),
            },
            headers=_qa_headers(),
        )
        assert resp.status_code == 422, resp.text


class TestVisitEditHistoryEndpoint:
    def test_returns_audit_log_rows_for_visit(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        visit = Visit(
            id=uuid.uuid4(),
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            admission_id=admission.id,
            provider_id=TEST_USER_ID,
            visit_type="ROUTINE",
            visit_discipline="AIDE",
            visit_datetime=datetime.now(timezone.utc),
            status="DRAFT",
            created_by=TEST_USER_ID,
        )
        db_session.add(visit)
        db_session.commit()

        log = AuditLog(
            id=uuid.uuid4(),
            tenant_id=_tenant_id(),
            user_id=TEST_USER_ID,
            role="RN",
            action="visit.status_updated",
            entity_type="visit",
            entity_id=str(visit.id),
        )
        db_session.add(log)
        db_session.commit()

        resp = client.get(f"/visits/{visit.id}/edit-history", headers=_qa_headers())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) == 1
        assert body[0]["action"] == "visit.status_updated"
        assert body[0]["user_id"] == str(TEST_USER_ID)

    def test_returns_empty_list_when_no_history(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        visit = Visit(
            id=uuid.uuid4(),
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            admission_id=admission.id,
            provider_id=TEST_USER_ID,
            visit_type="ROUTINE",
            visit_discipline="AIDE",
            visit_datetime=datetime.now(timezone.utc),
            status="DRAFT",
            created_by=TEST_USER_ID,
        )
        db_session.add(visit)
        db_session.commit()

        resp = client.get(f"/visits/{visit.id}/edit-history", headers=_qa_headers())
        assert resp.status_code == 200, resp.text
        assert resp.json() == []

    def test_returns_404_for_unknown_visit(self, client, db_session):
        resp = client.get(f"/visits/{uuid.uuid4()}/edit-history", headers=_qa_headers())
        assert resp.status_code == 404
