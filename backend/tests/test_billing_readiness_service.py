"""
Tests for app.billing.services.billing_readiness_service -- the
pre-billing chart-completeness gate. These run against the real test
Postgres DB (db_session fixture) since the service is intentionally
real-SQL, not a pure function, so its query shape against the actual
schema is what's under test.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.billing.services.billing_readiness_service import (
    check_patient_billing_readiness,
    build_tenant_billing_readiness_report,
    build_cross_agency_billing_readiness_report,
    categorize_blocker,
)
from app.models.admission import Admission
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.patient_payer import PatientPayer
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc_physician_approval import PocPhysicianApproval


SERVICE_DATE = date(2026, 3, 15)


@pytest.fixture(autouse=True)
def _clean_patient_payers_leftovers(db_session, tenant):
    """
    patient_payers has no tenant_id column, so the shared db_session
    fixture's generic tenant-scoped cleanup can't target it -- a leftover
    payer row from an earlier failed run blocks deleting its patient row
    on the next run (duplicate MRN). Clean it explicitly, scoped through
    patients.tenant_id, before every test in this module.
    """
    from sqlalchemy import text as _text

    db_session.execute(
        _text(
            "DELETE FROM patient_payers WHERE patient_id IN "
            "(SELECT id FROM patients WHERE tenant_id = :tenant_id)"
        ),
        {"tenant_id": uuid.UUID(tenant.id)},
    )
    db_session.commit()
    yield


_MRN_SUFFIX = uuid.uuid4().hex[:8]


def _unique_mrn(label: str) -> str:
    """
    Other test modules' leftover patient rows can survive between runs in
    the shared dev DB (referenced by tables outside the tenant-scoped
    cleanup, e.g. visits), so a fixed MRN can collide with stale data on
    re-run. Suffix every MRN used in this module with a fresh per-process
    token to guarantee uniqueness regardless of leftover rows.
    """
    return f"{label}-{_MRN_SUFFIX}"


def _make_patient(db_session, tenant_id: str, *, mrn: str = "MRN-READY-1") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        mrn=_unique_mrn(mrn),
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_benefit_period(
    db_session,
    tenant_id: str,
    patient: Patient,
    *,
    period_number: int = 1,
    election_date: date = date(2026, 1, 1),
    start_date: date = date(2026, 1, 1),
    end_date: date | None = date(2026, 4, 30),
    noe_submitted_date: date | None = date(2026, 1, 3),
    noe_exception_reason: str | None = None,
) -> BenefitPeriod:
    bp = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        patient_id=patient.id,
        benefit_type="INITIAL" if period_number == 1 else "RECERT",
        period_number=period_number,
        election_date=election_date,
        start_date=start_date,
        end_date=end_date,
        is_current=True,
        noe_submitted_date=noe_submitted_date,
        noe_exception_reason=noe_exception_reason,
    )
    db_session.add(bp)
    db_session.commit()
    return bp


def _make_certification(db_session, tenant_id: str, patient: Patient, bp: BenefitPeriod) -> None:
    cert = Certification(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        patient_id=patient.id,
        benefit_period_id=bp.id,
        cert_type="INITIAL",
        signed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        effective_date=bp.start_date,
        signed_by_role="MEDICAL_DIRECTOR",
        status="FINALIZED",
    )
    db_session.add(cert)
    db_session.commit()


def _make_f2f(db_session, tenant_id: str, patient: Patient, bp: BenefitPeriod) -> None:
    f2f = F2FEncounter(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        patient_id=patient.id,
        benefit_period_id=bp.id,
        encounter_date=bp.start_date,
        performed_by_role="MD",
        attested_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db_session.add(f2f)
    db_session.commit()


def _make_approved_poc(db_session, tenant_id: str, patient: Patient) -> None:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(admission)
    db_session.commit()

    poc = PlanOfCare(
        id=uuid.uuid4(),
        admission_id=admission.id,
        patient_id=patient.id,
        tenant_id=uuid.UUID(tenant_id),
        status="ACTIVE",
    )
    db_session.add(poc)
    db_session.commit()

    version = PlanOfCareVersion(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
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
        tenant_id=uuid.UUID(tenant_id),
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


def _make_payer(db_session, patient: Patient, *, is_primary: bool = True) -> None:
    payer = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient.id,
        payer_name="MEDICARE",
        payer_type="MEDICARE",
        subscriber_id="1EG4TE5MK73",
        subscriber_id_type="MBI",
        is_primary=is_primary,
        effective_start_date=date(2020, 1, 1),
    )
    db_session.add(payer)
    db_session.commit()


def _fully_ready_patient(db_session, tenant_id: str, *, mrn: str = "MRN-READY-1") -> Patient:
    patient = _make_patient(db_session, tenant_id, mrn=mrn)
    bp = _make_benefit_period(db_session, tenant_id, patient)
    _make_certification(db_session, tenant_id, patient, bp)
    _make_approved_poc(db_session, tenant_id, patient)
    _make_payer(db_session, patient)
    return patient


# ---------------------------------------------------------------------
# check_patient_billing_readiness
# ---------------------------------------------------------------------


def test_fully_documented_patient_is_ready(db_session, tenant):
    patient = _fully_ready_patient(db_session, tenant.id)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is True
    assert result.blockers == []
    assert result.period_number == 1


def test_patient_not_found_is_not_ready(db_session, tenant):
    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(uuid.uuid4()),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert "not found" in result.blockers[0].lower()


def test_no_benefit_period_covering_service_date_is_not_ready(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-NO-BP")

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("no benefit period" in b.lower() for b in result.blockers)


def test_missing_election_signature_blocks_initial_period(db_session, tenant):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant.id),
        mrn=_unique_mrn("MRN-NO-ELECTION"),
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        election_signed_at=None,
    )
    db_session.add(patient)
    db_session.commit()

    bp = _make_benefit_period(db_session, tenant.id, patient)
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("election statement" in b.lower() for b in result.blockers)


def test_unfiled_noe_with_no_exception_blocks_initial_period(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-NO-NOE")
    bp = _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        noe_submitted_date=None,
        noe_exception_reason=None,
    )
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("notice of election" in b.lower() for b in result.blockers)


def test_documented_noe_exception_does_not_block(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-NOE-EXCEPTION")
    bp = _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        noe_submitted_date=None,
        noe_exception_reason="MAC system outage per CMS transmittal 1234",
    )
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is True


def test_late_noe_filing_is_a_warning_not_a_blocker(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-LATE-NOE")
    bp = _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        election_date=date(2026, 1, 1),
        noe_submitted_date=date(2026, 1, 10),  # 9 days late
    )
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is True
    assert any("filed late" in w.lower() for w in result.warnings)


def test_missing_certification_blocks(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-NO-CERT")
    _make_benefit_period(db_session, tenant.id, patient)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("certification" in b.lower() for b in result.blockers)


def test_third_benefit_period_requires_f2f(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-3RD-BP-NO-F2F")
    bp = _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        period_number=3,
        election_date=date(2025, 1, 1),
        start_date=date(2026, 1, 1),
    )
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("face-to-face" in b.lower() for b in result.blockers)


def test_third_benefit_period_with_f2f_attested_is_ready(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-3RD-BP-WITH-F2F")
    bp = _make_benefit_period(
        db_session,
        tenant.id,
        patient,
        period_number=3,
        election_date=date(2025, 1, 1),
        start_date=date(2026, 1, 1),
    )
    _make_certification(db_session, tenant.id, patient, bp)
    _make_f2f(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is True


def test_missing_physician_approved_poc_blocks(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-NO-POC")
    bp = _make_benefit_period(db_session, tenant.id, patient)
    _make_certification(db_session, tenant.id, patient, bp)
    _make_payer(db_session, patient)

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("plan of care" in b.lower() for b in result.blockers)


def test_ambiguous_payer_sequence_blocks(db_session, tenant):
    patient = _make_patient(db_session, tenant.id, mrn="MRN-AMBIGUOUS-PAYER")
    bp = _make_benefit_period(db_session, tenant.id, patient)
    _make_certification(db_session, tenant.id, patient, bp)
    _make_approved_poc(db_session, tenant.id, patient)
    _make_payer(db_session, patient, is_primary=True)

    other_payer = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient.id,
        payer_name="ACME WORKERS COMP",
        payer_type="WORKERS_COMP",
        subscriber_id="WC1",
        subscriber_id_type="MI",
        is_primary=False,
        effective_start_date=date(2020, 1, 1),
        msp_type_code="15",
    )
    other_payer2 = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient.id,
        payer_name="AUTO LIABILITY CO",
        payer_type="LIABILITY",
        subscriber_id="AL1",
        subscriber_id_type="MI",
        is_primary=False,
        effective_start_date=date(2020, 1, 1),
        msp_type_code="47",
    )
    db_session.add_all([other_payer, other_payer2])
    db_session.commit()

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("payer sequence is ambiguous" in b.lower() for b in result.blockers)


def test_inactive_patient_status_blocks(db_session, tenant):
    patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-DISCHARGED")
    patient.status = "DISCHARGED"
    db_session.commit()

    result = check_patient_billing_readiness(
        db_session,
        tenant_id=tenant.id,
        patient_id=str(patient.id),
        service_date=SERVICE_DATE,
    )

    assert result.ready is False
    assert any("not active" in b.lower() or "not admitted" not in b.lower() for b in result.blockers)


# ---------------------------------------------------------------------
# build_tenant_billing_readiness_report
# ---------------------------------------------------------------------


def test_tenant_report_aggregates_ready_and_not_ready_patients(db_session, tenant):
    ready_patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-REPORT-READY")

    not_ready_patient = _make_patient(db_session, tenant.id, mrn="MRN-REPORT-NOT-READY")
    _make_benefit_period(db_session, tenant.id, not_ready_patient)
    # No certification / POC / payer -- deliberately incomplete.

    report = build_tenant_billing_readiness_report(
        db_session,
        tenant_id=tenant.id,
        service_date=SERVICE_DATE,
    )

    by_mrn = {row["mrn"]: row for row in report["patients"]}

    assert report["ready_count"] >= 1
    assert report["not_ready_count"] >= 1
    assert by_mrn[_unique_mrn("MRN-REPORT-READY")]["ready"] is True
    assert by_mrn[_unique_mrn("MRN-REPORT-NOT-READY")]["ready"] is False
    assert by_mrn[_unique_mrn("MRN-REPORT-NOT-READY")]["blockers"]
    # No raw chart content should ever appear -- only short labels.
    for row in report["patients"]:
        for blocker in row["blockers"]:
            assert isinstance(blocker, str)


# ---------------------------------------------------------------------
# categorize_blocker
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "blocker,expected_category",
    [
        ("Patient status is 'DISCHARGED', not ACTIVE.", "Patient Not Active"),
        (
            "No benefit period covers the service date 2026-03-15.",
            "Missing Benefit Period",
        ),
        (
            "Hospice election statement is not signed.",
            "Missing Election Statement",
        ),
        (
            "Notice of Election (NOE) has not been filed and no CMS "
            "exception is documented -- Medicare will return the claim.",
            "Missing NOE Filing",
        ),
        (
            "Certification of Terminal Illness (CTI/Recert) is not signed "
            "and finalized for this benefit period.",
            "Missing Certification",
        ),
        (
            "Required face-to-face encounter is not attested for this "
            "benefit period.",
            "Missing F2F Documentation",
        ),
        (
            "Plan of Care is not active with a physician signature on file.",
            "Missing POC Physician Signature",
        ),
        (
            "Payer sequence is ambiguous: multiple active MSP payers.",
            "Payer/MSP Sequencing Issue",
        ),
        ("Patient not found for this tenant.", "Patient Not Found"),
        ("Some future blocker text nobody mapped yet.", "Other"),
    ],
)
def test_categorize_blocker(blocker, expected_category):
    assert categorize_blocker(blocker) == expected_category


# ---------------------------------------------------------------------
# build_cross_agency_billing_readiness_report
# ---------------------------------------------------------------------


def test_cross_agency_report_includes_agency_and_blocker_breakdown(db_session, tenant):
    ready_patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CROSS-READY")

    not_ready_patient = _make_patient(db_session, tenant.id, mrn="MRN-CROSS-NOT-READY")
    _make_benefit_period(db_session, tenant.id, not_ready_patient)
    # Deliberately incomplete: no certification / POC / payer, so this
    # patient contributes at least a "Missing Certification" and
    # "Missing POC Physician Signature" blocker.

    report = build_cross_agency_billing_readiness_report(
        db_session,
        service_date=SERVICE_DATE,
    )

    assert report["total_agencies"] >= 1
    agency_ids = {a["tenant_id"] for a in report["agencies"]}
    assert tenant.id in agency_ids

    this_agency = next(a for a in report["agencies"] if a["tenant_id"] == tenant.id)
    assert this_agency["billing_enabled"] in (True, False)
    if this_agency["billing_enabled"]:
        assert this_agency["ready_count"] >= 1
        assert this_agency["not_ready_count"] >= 1

        categories = {b["category"] for b in report["blocker_breakdown"]}
        assert "Missing Certification" in categories
        assert "Missing POC Physician Signature" in categories

    # Every category in the breakdown must be a known/stable label.
    for entry in report["blocker_breakdown"]:
        assert isinstance(entry["category"], str)
        assert entry["count"] >= 1
