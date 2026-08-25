"""
Tests for the Phase 1 billing read-only aggregation endpoints:
- app.billing.api.visits_notes_router (visits/notes documentation status)
- app.billing.api.poc_certification_router (POC/CTI/F2F billing-readiness view)
- app.billing.api.noe_tracking_router (NOE filing timeliness tracker)

These call the router functions directly (bypassing FastAPI's HTTP layer)
against the real test Postgres DB (db_session fixture), passing a minimal
fake "current user" object exposing tenant_id -- the same tenant-scoping
shape every other billing endpoint in this codebase relies on.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest

from app.billing.api.noe_tracking_router import list_noe_tracking
from app.billing.api.poc_certification_router import list_poc_certification_status
from app.billing.api.visits_notes_router import list_visits_notes
from app.models.admission import Admission
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.clinical_note import ClinicalNote
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc_physician_approval import PocPhysicianApproval
from app.models.user import User
from app.models.visit import Visit
from tests.conftest import TEST_USER_ID


@dataclass(frozen=True)
class _FakeUser:
    tenant_id: uuid.UUID


_MRN_SUFFIX = uuid.uuid4().hex[:8]


def _unique_mrn(label: str) -> str:
    return f"PHASE1-{label}-{_MRN_SUFFIX}"


def _make_patient(db_session, tenant_id: str, *, mrn: str) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=_unique_mrn(mrn),
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="J44.9",
        status="ACTIVE",
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_facesheet(db_session, tenant_id: str, patient: Patient, *, first_name: str, last_name: str) -> None:
    fs = PatientFaceSheet(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        first_name=first_name,
        last_name=last_name,
        created_by=TEST_USER_ID,
    )
    db_session.add(fs)
    db_session.commit()


def _make_user(db_session, tenant_id: str, *, full_name: str = "Dr. Test Author") -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{uuid.uuid4().hex[:10]}@example.com",
        full_name=full_name,
        role="RN",
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_admission(db_session, tenant_id: str, patient: Patient) -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status="ADMITTED",
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_visit_and_note(
    db_session,
    tenant_id: str,
    patient: Patient,
    admission: Admission,
    author: User,
    *,
    finalized: bool,
    encounter_date: date = date(2026, 3, 1),
):
    visit_dt = datetime(encounter_date.year, encounter_date.month, encounter_date.day, 9, 0, tzinfo=timezone.utc)
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=author.id,
        visit_type="RN",
        visit_discipline="RN",
        visit_mode="IN_PERSON",
        status="FINALIZED" if finalized else "DRAFT",
        visit_datetime=visit_dt,
        form_type="ASSESS",
        finalized_by=author.id if finalized else None,
        finalized_at=visit_dt if finalized else None,
    )
    db_session.add(visit)
    db_session.flush()

    note = ClinicalNote(
        id=uuid.uuid4(),
        visit_id=visit.id,
        author_id=author.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        note_type="RN_VISIT_NOTE",
        discipline="RN",
        form_key="RN_VISIT_NOTE",
        status="FINALIZED" if finalized else "DRAFT",
        encounter_date=encounter_date,
        content={"narrative": "test"},
        signed_by=author.id if finalized else None,
        signed_at=visit_dt if finalized else None,
        finalized_at=visit_dt if finalized else None,
        finalized_by=author.id if finalized else None,
    )
    db_session.add(note)
    db_session.commit()
    return visit, note


def _make_benefit_period(
    db_session,
    tenant_id: str,
    patient: Patient,
    *,
    benefit_type: str = "INITIAL",
    period_number: int = 1,
    election_date: date = date(2026, 1, 1),
    noe_submitted_date: date | None = date(2026, 1, 2),
    noe_exception_reason: str | None = None,
) -> BenefitPeriod:
    bp = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        benefit_type=benefit_type,
        period_number=period_number,
        election_date=election_date,
        start_date=election_date,
        end_date=date(2026, 4, 30),
        is_current=True,
        noe_submitted_date=noe_submitted_date,
        noe_exception_reason=noe_exception_reason,
    )
    db_session.add(bp)
    db_session.commit()
    return bp


def _make_certification(db_session, tenant_id: str, patient: Patient, bp: BenefitPeriod, *, status: str = "FINALIZED") -> Certification:
    cert = Certification(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        benefit_period_id=bp.id,
        cert_type="INITIAL",
        signed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        effective_date=bp.start_date,
        signed_by_role="MEDICAL_DIRECTOR",
        status=status,
    )
    db_session.add(cert)
    db_session.commit()
    return cert


def _make_approved_poc(db_session, tenant_id: str, patient: Patient) -> None:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(admission)
    db_session.commit()

    poc = PlanOfCare(
        id=uuid.uuid4(),
        admission_id=admission.id,
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        status="ACTIVE",
    )
    db_session.add(poc)
    db_session.commit()

    version = PlanOfCareVersion(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        plan_of_care_id=poc.id,
        version_number=1,
        status="ACTIVE",
        source_kind="ICA",
    )
    db_session.add(version)
    db_session.commit()

    poc.current_version_id = version.id
    db_session.commit()

    approval = PocPhysicianApproval(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        poc_version_id=version.id,
        physician_name="Dr. Test Physician",
        physician_role="HOSPICE_MEDICAL_DIRECTOR",
        approval_method="UPLOADED_SIGNED_APPROVAL_DOCUMENT",
        approval_status="PHYSICIAN_APPROVED",
        approval_date=date(2026, 1, 2),
    )
    db_session.add(approval)
    db_session.commit()


# ---------------------------------------------------------------------
# visits-notes
# ---------------------------------------------------------------------


def test_list_visits_notes_returns_finalized_and_draft(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="VN1")
    _make_facesheet(db_session, tenant.id, patient, first_name="Ann", last_name="Vance")
    author = _make_user(db_session, tenant.id)
    admission = _make_admission(db_session, tenant.id, patient)

    _make_visit_and_note(db_session, tenant.id, patient, admission, author, finalized=True, encounter_date=date(2026, 3, 1))
    _make_visit_and_note(db_session, tenant.id, patient, admission, author, finalized=False, encounter_date=date(2026, 3, 5))

    result = list_visits_notes(
        patient_id=str(patient.id),
        unsigned_only=False,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    assert result["count"] == 2
    statuses = {row["status"] for row in result["visits_notes"]}
    assert statuses == {"FINALIZED", "DRAFT"}
    finalized_row = next(r for r in result["visits_notes"] if r["status"] == "FINALIZED")
    assert finalized_row["documentation_complete"] is True
    assert finalized_row["patient_name"] == "Ann Vance"
    draft_row = next(r for r in result["visits_notes"] if r["status"] == "DRAFT")
    assert draft_row["documentation_complete"] is False


def test_list_visits_notes_unsigned_only_filter(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="VN2")
    author = _make_user(db_session, tenant.id)
    admission = _make_admission(db_session, tenant.id, patient)

    _make_visit_and_note(db_session, tenant.id, patient, admission, author, finalized=True, encounter_date=date(2026, 3, 1))
    _make_visit_and_note(db_session, tenant.id, patient, admission, author, finalized=False, encounter_date=date(2026, 3, 5))

    result = list_visits_notes(
        patient_id=str(patient.id),
        unsigned_only=True,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    assert result["count"] == 1
    assert result["visits_notes"][0]["status"] == "DRAFT"


# ---------------------------------------------------------------------
# poc-certification-status
# ---------------------------------------------------------------------


def test_poc_certification_status_billing_ready_initial_period(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="POC1")
    _make_facesheet(db_session, tenant.id, patient, first_name="Ben", last_name="Certo")
    bp = _make_benefit_period(db_session, tenant.id, patient, benefit_type="INITIAL", period_number=1)
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)

    result = list_poc_certification_status(
        patient_id=str(patient.id),
        current_period_only=True,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    assert result["count"] == 1
    row = result["poc_certification_status"][0]
    assert row["patient_name"] == "Ben Certo"
    assert row["certification"]["status"] == "FINALIZED"
    assert row["plan_of_care"]["physician_approval_status"] == "PHYSICIAN_APPROVED"
    assert row["billing_ready"] is True


def test_poc_certification_status_recert_requires_f2f(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="POC2")
    bp = _make_benefit_period(db_session, tenant.id, patient, benefit_type="RECERT", period_number=2)
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    # deliberately no F2F encounter created

    result = list_poc_certification_status(
        patient_id=str(patient.id),
        current_period_only=True,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    row = result["poc_certification_status"][0]
    assert row["f2f_encounter"] is None
    assert row["billing_ready"] is False

    # Now add the F2F encounter and confirm it flips to ready
    f2f = F2FEncounter(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant.id)),
        patient_id=patient.id,
        benefit_period_id=bp.id,
        encounter_date=bp.start_date,
        performed_by_role="MD",
        status="FINALIZED",
    )
    db_session.add(f2f)
    db_session.commit()

    result2 = list_poc_certification_status(
        patient_id=str(patient.id),
        current_period_only=True,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )
    row2 = result2["poc_certification_status"][0]
    assert row2["f2f_encounter"]["status"] == "FINALIZED"
    assert row2["billing_ready"] is True


# ---------------------------------------------------------------------
# noe-tracking
# ---------------------------------------------------------------------


def test_noe_tracking_flags_late_filing(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="NOE1")
    _make_facesheet(db_session, tenant.id, patient, first_name="Cara", last_name="Notice")
    # Election 2026-01-01, deadline 2026-01-06 (5-day window); filed 2026-01-10 -- late.
    _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 1, 1),
        noe_submitted_date=date(2026, 1, 10),
    )

    result = list_noe_tracking(
        late_only=False,
        unfiled_only=False,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    row = next(r for r in result["noe_tracking"] if r["patient_id"] == str(patient.id))
    assert row["is_late"] is True
    assert row["non_covered_days"] == 9
    assert row["patient_name"] == "Cara Notice"
    assert result["late_count"] >= 1


def test_noe_tracking_exempt_when_exception_reason_present(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="NOE2")
    _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 1, 1),
        noe_submitted_date=date(2026, 1, 10),
        noe_exception_reason="CMS transmittal 2551 MAC outage exception",
    )

    result = list_noe_tracking(
        late_only=False,
        unfiled_only=False,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    row = next(r for r in result["noe_tracking"] if r["patient_id"] == str(patient.id))
    assert row["is_exempt"] is True
    assert row["is_late"] is False


def test_noe_tracking_unfiled_only_filter(db_session, tenant):
    patient_filed = _make_patient(db_session, tenant.id, mrn="NOE3")
    _make_benefit_period(
        db_session, tenant.id, patient_filed, election_date=date(2026, 1, 1), noe_submitted_date=date(2026, 1, 2)
    )
    patient_unfiled = _make_patient(db_session, tenant.id, mrn="NOE4")
    _make_benefit_period(
        db_session, tenant.id, patient_unfiled, election_date=date(2026, 1, 1), noe_submitted_date=None
    )

    result = list_noe_tracking(
        late_only=False,
        unfiled_only=True,
        limit=1000,
        db=db_session,
        user=_FakeUser(tenant_id=uuid.UUID(str(tenant.id))),
    )

    patient_ids = {r["patient_id"] for r in result["noe_tracking"]}
    assert str(patient_unfiled.id) in patient_ids
    assert str(patient_filed.id) not in patient_ids
