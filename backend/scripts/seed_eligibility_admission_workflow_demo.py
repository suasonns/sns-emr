"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Phase 10 synthetic data.

Rebuilds the disposable dev data for the corrected workflow into the five
scenarios the directive specifies, each following the real
eligibility -> benefit-period -> admission -> billing chain (never a
fabricated/impossible state):

  A. REFERRAL       -- a patient row only. No Admission record at all
                       (admission_status stays at its PRE_REFERRAL
                       default). No EligibilityVerification, no
                       BenefitPeriodDetermination. Must never appear on
                       the Billing Readiness dashboard/queue (Directive
                       item 10's population correction excludes it by
                       construction -- there is no ADMITTED admission
                       row to join against).

  B. ADMISSION HOLD -- an Admission row exists but status='PENDING' (not
                       yet ADMITTED), and the eligibility evidence is
                       incomplete (EligibilityVerification.status=
                       "PENDING") AND the benefit period is unresolved
                       (BenefitPeriodDetermination.status=
                       "INFORMATION_INCOMPLETE") -- exactly the Phase 4
                       admission-gate rule ("eligibility evidence
                       incomplete OR benefit period unresolved ->
                       admission blocked"). Also excluded from billing
                       readiness because the admission is not ADMITTED.

  C. READY          -- ADMITTED, CONFIRMED eligibility
                       (VERIFIED_ACTIVE), CONFIRMED benefit-period
                       (BENEFIT_PERIOD_CONFIRMED), and every billing
                       readiness prerequisite (election, on-time NOE,
                       finalized certification, approved Plan of Care,
                       unambiguous payer) satisfied -- admission gate
                       CLEAR, billing readiness READY.

  D. AT RISK        -- same ADMITTED / CONFIRMED eligibility /
                       CONFIRMED benefit-period baseline as (C), but the
                       NOE was filed more than 5 days after election --
                       the readiness evaluator's sole warning-level
                       (non-blocking) gap. Admission gate CLEAR, billing
                       readiness AT_RISK.

  E. NOT READY      -- same ADMITTED / CONFIRMED eligibility /
                       CONFIRMED benefit-period baseline as (C), but no
                       finalized Certification of Terminal Illness on
                       file -- a real blocking gap. Admission gate
                       CLEAR, billing readiness NOT_READY.

This intentionally reuses the same fixed DEV demo tenant
(00000000-0000-0000-0000-00000000d0d0,
seed_readiness_workflow_demo.py's "Billing Readiness Workflow Demo
Agency (DEV)") so there is exactly one synthetic dev tenant in the app,
not two competing ones -- these five patients get their own
"ELIGWF-DEMO-" MRN prefix so they never collide with the pre-existing
READINESS-DEMO- patients from that older script (which predate the
eligibility/admission-gate rebuild and remain untouched/valid billing-
readiness-only fixtures).

Purely development/test fixture data: no real tenant, patient, biller,
or agency is created or assumed.

Usage (PowerShell, from backend/):

    python scripts/seed_eligibility_admission_workflow_demo.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

import app.main  # noqa: E402,F401  -- see seed_readiness_workflow_demo.py for why.
from app.core.database import SessionLocal  # noqa: E402
from app.models.admission import Admission  # noqa: E402
from app.models.benefit_period import BenefitPeriod  # noqa: E402
from app.models.certification import Certification  # noqa: E402
from app.models.document_record import DocumentRecord  # noqa: E402
from app.models.patient import Patient  # noqa: E402
from app.models.patient_payer import PatientPayer  # noqa: E402
from app.models.plan_of_care import PlanOfCare  # noqa: E402
from app.models.plan_of_care_version import PlanOfCareVersion  # noqa: E402
from app.models.poc_physician_approval import PocPhysicianApproval  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.billing.models.eligibility_source_document import EligibilitySourceDocument  # noqa: E402
from app.billing.services.billing_readiness_service import (  # noqa: E402
    build_tenant_billing_readiness_report,
)
from app.billing.services.eligibility_workflow_service import (  # noqa: E402
    evaluate_admission_gate,
    record_benefit_period_determination,
    record_eligibility_source_document,
    record_eligibility_verification,
)
from app.billing.services.readiness_workflow_service import (  # noqa: E402
    derive_readiness_status,
)

# Same fixed demo tenant seed_readiness_workflow_demo.py uses -- see that
# script's docstring for why the id is hardcoded rather than env-read.
DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-00000000d0d0")
DEMO_TENANT_NAME = "Billing Readiness Workflow Demo Agency (DEV)"
SERVICE_DATE = date(2026, 3, 15)
MRN_PREFIX = "ELIGWF-DEMO-"


def _ensure_tenant(db) -> Tenant:
    tenant = db.get(Tenant, DEMO_TENANT_ID)
    if tenant is None:
        tenant = Tenant(id=DEMO_TENANT_ID, legal_name=DEMO_TENANT_NAME, display_name=DEMO_TENANT_NAME)
        db.add(tenant)
    tenant.legal_name = DEMO_TENANT_NAME
    tenant.display_name = DEMO_TENANT_NAME
    tenant.tenant_type = "DEV"
    tenant.status = "ACTIVE"
    tenant.billing_enabled = True
    tenant.npi = "0000000099"
    tenant.ein = "999999999"
    tenant.ptan = "P9999999"
    db.commit()
    return tenant


def _ensure_staff_user(db) -> User:
    email = "readiness-demo-staff@example.com"
    user = db.query(User).filter(User.tenant_id == DEMO_TENANT_ID, User.email == email).one_or_none()
    if user is None:
        user = User(
            id=uuid.uuid4(),
            tenant_id=DEMO_TENANT_ID,
            email=email,
            full_name="Readiness Demo Staff",
            role="BILLING",
        )
        db.add(user)
        db.commit()
    return user


def _make_patient(db, *, mrn_suffix: str, created_by: uuid.UUID, admission_status: str) -> Patient:
    mrn = f"{MRN_PREFIX}{mrn_suffix}"
    patient = db.query(Patient).filter(Patient.tenant_id == DEMO_TENANT_ID, Patient.mrn == mrn).one_or_none()
    if patient is not None:
        patient.admission_status = admission_status
        db.commit()
        return patient
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=DEMO_TENANT_ID,
        mrn=mrn,
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        patient_type="TRAINING",
        training_label="SYNTHETIC ELIGIBILITY/ADMISSION WORKFLOW DEMO PATIENT -- no PHI.",
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        admission_status=admission_status,
        created_by=created_by,
    )
    db.add(patient)
    db.commit()
    return patient


def _make_admission(db, patient: Patient, *, status: str, created_by: uuid.UUID) -> Admission:
    existing = (
        db.query(Admission)
        .filter(Admission.tenant_id == DEMO_TENANT_ID, Admission.patient_id == patient.id)
        .one_or_none()
    )
    if existing is not None:
        existing.status = status
        db.commit()
        return existing
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=DEMO_TENANT_ID,
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status=status,
        created_by=created_by,
    )
    db.add(admission)
    db.commit()
    return admission


def _make_benefit_period(db, patient: Patient, *, noe_submitted_date: date) -> BenefitPeriod:
    existing = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.tenant_id == DEMO_TENANT_ID, BenefitPeriod.patient_id == patient.id)
        .one_or_none()
    )
    if existing is not None:
        return existing
    bp = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=DEMO_TENANT_ID,
        patient_id=patient.id,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 30),
        is_current=True,
        noe_submitted_date=noe_submitted_date,
    )
    db.add(bp)
    db.commit()
    return bp


def _make_certification(db, patient: Patient, bp: BenefitPeriod) -> None:
    existing = (
        db.query(Certification)
        .filter(Certification.patient_id == patient.id, Certification.benefit_period_id == bp.id)
        .one_or_none()
    )
    if existing is not None:
        return
    db.add(
        Certification(
            id=uuid.uuid4(),
            tenant_id=DEMO_TENANT_ID,
            patient_id=patient.id,
            benefit_period_id=bp.id,
            cert_type="INITIAL",
            signed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            effective_date=bp.start_date,
            signed_by_role="MEDICAL_DIRECTOR",
            status="FINALIZED",
        )
    )
    db.commit()


def _make_approved_poc(db, patient: Patient, admission: Admission) -> None:
    existing = db.query(PlanOfCare).filter(PlanOfCare.patient_id == patient.id).one_or_none()
    if existing is not None:
        return
    poc = PlanOfCare(id=uuid.uuid4(), admission_id=admission.id, patient_id=patient.id, tenant_id=DEMO_TENANT_ID, status="ACTIVE")
    db.add(poc)
    db.commit()

    version = PlanOfCareVersion(
        id=uuid.uuid4(), tenant_id=DEMO_TENANT_ID, plan_of_care_id=poc.id,
        version_number=1, status="ACTIVE", source_kind="ICA",
    )
    db.add(version)
    db.commit()

    poc.current_version_id = version.id
    db.commit()

    db.add(
        PocPhysicianApproval(
            id=uuid.uuid4(),
            tenant_id=DEMO_TENANT_ID,
            patient_id=patient.id,
            poc_version_id=version.id,
            physician_name="Dr. Demo Physician",
            physician_role="HOSPICE_MEDICAL_DIRECTOR",
            approval_method="UPLOADED_SIGNED_APPROVAL_DOCUMENT",
            approval_status="PHYSICIAN_APPROVED",
            approval_date=date(2026, 1, 2),
        )
    )
    db.commit()


def _make_source_document(db, patient: Patient, staff_user: User) -> EligibilitySourceDocument:
    """
    Every EligibilityVerification traces to a real source document
    (Directive item 4 -- no structured finding without a traceable
    document). Reuses the existing document-management DocumentRecord
    table, exactly as record_eligibility_source_document requires.
    """
    existing = (
        db.query(EligibilitySourceDocument)
        .filter(
            EligibilitySourceDocument.tenant_id == DEMO_TENANT_ID,
            EligibilitySourceDocument.patient_id == patient.id,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing

    doc_record = DocumentRecord(
        id=uuid.uuid4(),
        tenant_id=DEMO_TENANT_ID,
        patient_id=patient.id,
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        source="EXTERNAL",
        uploaded_by=staff_user.id,
    )
    db.add(doc_record)
    db.commit()

    return record_eligibility_source_document(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(patient.id),
        document_record_id=str(doc_record.id),
        document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
        uploaded_by_user_id=str(staff_user.id),
        verification_date=date(2026, 1, 1),
    )


def _make_consent_document(db, patient: Patient, staff_user: User) -> None:
    """
    Priority 6 -- Election/Consent Documentation. An ACTIVE DocumentRecord
    of any recognized election/consent type satisfies this (see
    app.billing.services.election_consent_workflow_service). Only used
    for the "fully documented" READY scenario -- missing it is AT_RISK,
    not a regression, but this scenario is meant to demonstrate a
    patient with nothing outstanding.
    """
    existing = (
        db.query(DocumentRecord)
        .filter(
            DocumentRecord.tenant_id == DEMO_TENANT_ID,
            DocumentRecord.patient_id == patient.id,
            DocumentRecord.document_type == "CONSENT_FORM",
        )
        .one_or_none()
    )
    if existing is not None:
        return
    db.add(
        DocumentRecord(
            id=uuid.uuid4(),
            tenant_id=DEMO_TENANT_ID,
            patient_id=patient.id,
            document_type="CONSENT_FORM",
            source="EXTERNAL",
            uploaded_by=staff_user.id,
        )
    )
    db.commit()


def _make_payer(db, patient: Patient) -> None:
    existing = db.query(PatientPayer).filter(PatientPayer.patient_id == patient.id).one_or_none()
    if existing is not None:
        return
    db.add(
        PatientPayer(
            id=uuid.uuid4(),
            patient_id=patient.id,
            payer_name="MEDICARE",
            payer_type="MEDICARE",
            subscriber_id="1EG4TE5MK73",
            subscriber_id_type="MBI",
            is_primary=True,
            effective_start_date=date(2020, 1, 1),
        )
    )
    db.commit()


def run(db) -> dict:
    """
    Idempotent seed body, split out from main() so it is directly
    unit-testable against the pytest db_session fixture (see
    tests/test_seed_eligibility_admission_workflow_demo.py) without
    opening/closing its own session.
    """
    _ensure_tenant(db)
    staff_user = _ensure_staff_user(db)

    # ----- A. REFERRAL -- patient only, nothing else. -----
    referral_patient = _make_patient(
        db, mrn_suffix="REFERRAL-A", created_by=staff_user.id, admission_status="PRE_REFERRAL"
    )

    # ----- B. ADMISSION HOLD -- Admission PENDING + incomplete/unresolved evidence. -----
    hold_patient = _make_patient(
        db, mrn_suffix="ADMITHOLD-B", created_by=staff_user.id, admission_status="CONSENT_SIGNED"
    )
    hold_admission = _make_admission(db, hold_patient, status="PENDING", created_by=staff_user.id)
    hold_source_doc = _make_source_document(db, hold_patient, staff_user)
    record_eligibility_verification(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(hold_patient.id),
        source_document_id=str(hold_source_doc.id),
        verified_by_user_id=str(staff_user.id),
        status="PENDING",
    )
    record_benefit_period_determination(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(hold_patient.id),
        admission_id=str(hold_admission.id),
        determination_status="INFORMATION_INCOMPLETE",
    )

    # ----- C. READY -- ADMITTED, CONFIRMED eligibility + benefit period, full documentation. -----
    ready_patient = _make_patient(
        db, mrn_suffix="READY-C", created_by=staff_user.id, admission_status="ADMITTED"
    )
    ready_admission = _make_admission(db, ready_patient, status="ADMITTED", created_by=staff_user.id)
    ready_source_doc = _make_source_document(db, ready_patient, staff_user)
    record_eligibility_verification(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(ready_patient.id),
        source_document_id=str(ready_source_doc.id),
        verified_by_user_id=str(staff_user.id),
        status="VERIFIED_ACTIVE",
    )
    record_benefit_period_determination(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(ready_patient.id),
        admission_id=str(ready_admission.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
    )
    bp_ready = _make_benefit_period(db, ready_patient, noe_submitted_date=date(2026, 1, 3))
    _make_certification(db, ready_patient, bp_ready)
    _make_approved_poc(db, ready_patient, ready_admission)
    _make_payer(db, ready_patient)
    _make_consent_document(db, ready_patient, staff_user)

    # ----- D. AT RISK -- same baseline as (C), but NOE filed late (warning only). -----
    at_risk_patient = _make_patient(
        db, mrn_suffix="ATRISK-D", created_by=staff_user.id, admission_status="ADMITTED"
    )
    at_risk_admission = _make_admission(db, at_risk_patient, status="ADMITTED", created_by=staff_user.id)
    at_risk_source_doc = _make_source_document(db, at_risk_patient, staff_user)
    record_eligibility_verification(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(at_risk_patient.id),
        source_document_id=str(at_risk_source_doc.id),
        verified_by_user_id=str(staff_user.id),
        status="VERIFIED_ACTIVE",
    )
    record_benefit_period_determination(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(at_risk_patient.id),
        admission_id=str(at_risk_admission.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
    )
    bp_at_risk = _make_benefit_period(db, at_risk_patient, noe_submitted_date=date(2026, 1, 12))
    _make_certification(db, at_risk_patient, bp_at_risk)
    _make_approved_poc(db, at_risk_patient, at_risk_admission)
    _make_payer(db, at_risk_patient)

    # ----- E. NOT READY -- same baseline as (C), but no finalized certification. -----
    not_ready_patient = _make_patient(
        db, mrn_suffix="NOTREADY-E", created_by=staff_user.id, admission_status="ADMITTED"
    )
    not_ready_admission = _make_admission(db, not_ready_patient, status="ADMITTED", created_by=staff_user.id)
    not_ready_source_doc = _make_source_document(db, not_ready_patient, staff_user)
    record_eligibility_verification(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(not_ready_patient.id),
        source_document_id=str(not_ready_source_doc.id),
        verified_by_user_id=str(staff_user.id),
        status="VERIFIED_ACTIVE",
    )
    record_benefit_period_determination(
        db,
        tenant_id=str(DEMO_TENANT_ID),
        patient_id=str(not_ready_patient.id),
        admission_id=str(not_ready_admission.id),
        determination_status="BENEFIT_PERIOD_CONFIRMED",
        anticipated_benefit_period_number=1,
    )
    _make_benefit_period(db, not_ready_patient, noe_submitted_date=date(2026, 1, 3))
    _make_approved_poc(db, not_ready_patient, not_ready_admission)
    _make_payer(db, not_ready_patient)
    # Deliberately no _make_certification() call -- this is the blocker.

    report = build_tenant_billing_readiness_report(db, tenant_id=str(DEMO_TENANT_ID), service_date=SERVICE_DATE)
    by_patient = {p["patient_id"]: p for p in report["patients"]}

    return {
        "referral_patient": referral_patient,
        "hold_patient": hold_patient,
        "ready_patient": ready_patient,
        "at_risk_patient": at_risk_patient,
        "not_ready_patient": not_ready_patient,
        "report": report,
        "by_patient": by_patient,
        "referral_admission_gate": evaluate_admission_gate(
            db, tenant_id=str(DEMO_TENANT_ID), patient_id=str(referral_patient.id)
        ),
        "hold_admission_gate": evaluate_admission_gate(
            db, tenant_id=str(DEMO_TENANT_ID), patient_id=str(hold_patient.id)
        ),
        "ready_admission_gate": evaluate_admission_gate(
            db, tenant_id=str(DEMO_TENANT_ID), patient_id=str(ready_patient.id)
        ),
    }


def main() -> int:
    db = SessionLocal()
    try:
        result = run(db)
        report = result["report"]
        by_patient = result["by_patient"]

        print("Seeded Eligibility/Admission/Benefit-Period/Billing-Readiness workflow demo data.")
        print(f"  tenant_id: {DEMO_TENANT_ID}")
        print(f"  A. Referral    : {result['referral_patient'].mrn} -- admission gate {result['referral_admission_gate'].gate_status} (expected CLEAR; no rows yet, non-regression rule), NOT in billing readiness report ({result['referral_patient'].mrn not in {p['mrn'] for p in report['patients']}})")
        print(f"  B. Admission Hold: {result['hold_patient'].mrn} -- admission gate {result['hold_admission_gate'].gate_status} (expected ADMISSION_REVIEW_REQUIRED), NOT in billing readiness report")
        for label, patient in (
            ("C. Ready", result["ready_patient"]),
            ("D. At Risk", result["at_risk_patient"]),
            ("E. Not Ready", result["not_ready_patient"]),
        ):
            row = by_patient.get(str(patient.id))
            status = derive_readiness_status(blockers=row["blockers"], warnings=row["warnings"]) if row else "MISSING FROM REPORT"
            print(f"  {label}: {patient.mrn} -- readiness_status={status}")
        print(f"  billing readiness report counts: total={report['total_patients']} ready={report['ready_count']} not_ready={report['not_ready_count']}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
