"""
Sprint 2 -- seed a small, self-contained demo dataset for the Billing
Readiness Operational Workflow (dashboard/queue/history at
/billing/readiness in the frontend).

Creates (or refreshes, safe to re-run) one dedicated DEV tenant with a
handful of synthetic patients spanning the full readiness spectrum --
READY, AT_RISK, NOT_READY, and NOT_READY+BLOCKED -- then:

  1. Runs the real build_tenant_readiness_dashboard() evaluation so each
     patient gets a genuine, persisted BillingReadinessVerdict (Sprint 1)
     and a synced BillingBlockerRecord lifecycle (Sprint 2 Deliverable 3)
     -- exactly the same side effect the live dashboard/queue endpoints
     already trigger. Nothing here writes verdicts/blockers directly.
  2. Assigns a couple of patients to a synthetic staff user (Deliverable
     4) and opens/blocks a couple of follow-ups (Deliverable 5), so the
     Operational Queue's assignment/due-date filters have something to
     filter on.

This is purely development/test fixture data: the tenant is tagged
tenant_type="DEV" and every patient MRN is prefixed "READINESS-DEMO-" so
it is unambiguously distinguishable from any other record. No real
tenant, patient, biller, or agency data is created or assumed.

Usage (PowerShell, from backend/):

    python scripts/seed_readiness_workflow_demo.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

import app.main  # noqa: E402,F401  -- imports every router/model so SQLAlchemy's
# mapper registry has every class (e.g. POCProblem) available when it
# configures cross-module relationship() string references below.
from app.core.database import SessionLocal  # noqa: E402
from app.models.admission import Admission  # noqa: E402
from app.models.benefit_period import BenefitPeriod  # noqa: E402
from app.models.certification import Certification  # noqa: E402
from app.models.f2f_encounter import F2FEncounter  # noqa: E402
from app.models.patient import Patient  # noqa: E402
from app.models.patient_payer import PatientPayer  # noqa: E402
from app.models.plan_of_care import PlanOfCare  # noqa: E402
from app.models.plan_of_care_version import PlanOfCareVersion  # noqa: E402
from app.models.poc_physician_approval import PocPhysicianApproval  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.billing.services.readiness_dashboard_service import (  # noqa: E402
    build_tenant_readiness_dashboard,
)
from app.billing.services.readiness_workflow_service import (  # noqa: E402
    upsert_assignment,
    upsert_follow_up,
)

# Fixed, deterministic tenant id (not read from the environment) so this
# script is trivially re-runnable in any local/dev database without
# requiring extra setup -- this tenant only ever exists for this demo
# dataset and is never a real agency.
DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-00000000d0d0")
DEMO_TENANT_NAME = "Billing Readiness Workflow Demo Agency (DEV)"
SERVICE_DATE = date(2026, 3, 15)
MRN_PREFIX = "READINESS-DEMO-"


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


def _make_patient(db, *, mrn_suffix: str, created_by: uuid.UUID) -> Patient:
    mrn = f"{MRN_PREFIX}{mrn_suffix}"
    patient = db.query(Patient).filter(Patient.tenant_id == DEMO_TENANT_ID, Patient.mrn == mrn).one_or_none()
    if patient is not None:
        return patient
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=DEMO_TENANT_ID,
        mrn=mrn,
        date_of_birth=date(1945, 6, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        patient_type="TRAINING",
        training_label="SYNTHETIC READINESS WORKFLOW DEMO PATIENT -- no PHI.",
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_by=created_by,
    )
    db.add(patient)
    db.commit()
    return patient


def _make_benefit_period(db, patient: Patient, *, noe_submitted_date: date = date(2026, 1, 3)) -> BenefitPeriod:
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


def _make_f2f(db, patient: Patient, bp: BenefitPeriod) -> None:
    existing = (
        db.query(F2FEncounter)
        .filter(F2FEncounter.patient_id == patient.id, F2FEncounter.benefit_period_id == bp.id)
        .one_or_none()
    )
    if existing is not None:
        return
    db.add(
        F2FEncounter(
            id=uuid.uuid4(),
            tenant_id=DEMO_TENANT_ID,
            patient_id=patient.id,
            benefit_period_id=bp.id,
            encounter_date=bp.start_date,
            performed_by_role="MD",
            attested_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )
    db.commit()


def _make_approved_poc(db, patient: Patient, created_by: uuid.UUID) -> None:
    existing = db.query(PlanOfCare).filter(PlanOfCare.patient_id == patient.id).one_or_none()
    if existing is not None:
        return
    admission = Admission(
        id=uuid.uuid4(), tenant_id=DEMO_TENANT_ID, patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_by=created_by,
    )
    db.add(admission)
    db.commit()

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


def main() -> int:
    db = SessionLocal()
    try:
        _ensure_tenant(db)
        staff_user = _ensure_staff_user(db)

        # READY -- fully documented, no blockers/warnings.
        ready_patient = _make_patient(db, mrn_suffix="READY-1", created_by=staff_user.id)
        bp1 = _make_benefit_period(db, ready_patient)
        _make_certification(db, ready_patient, bp1)
        _make_f2f(db, ready_patient, bp1)
        _make_approved_poc(db, ready_patient, staff_user.id)
        _make_payer(db, ready_patient)

        # AT_RISK -- fully documented (no blockers), but the NOE was
        # filed more than 5 days after election -- the real evaluator's
        # sole warning-level (non-blocking) gap, per
        # build_patient_readiness_result's NOE-late-filing check.
        at_risk_patient = _make_patient(db, mrn_suffix="ATRISK-1", created_by=staff_user.id)
        bp2 = _make_benefit_period(db, at_risk_patient, noe_submitted_date=date(2026, 1, 12))
        _make_certification(db, at_risk_patient, bp2)
        _make_approved_poc(db, at_risk_patient, staff_user.id)
        _make_payer(db, at_risk_patient)

        # NOT_READY -- no benefit period paperwork at all.
        not_ready_patient = _make_patient(db, mrn_suffix="NOTREADY-1", created_by=staff_user.id)
        _make_benefit_period(db, not_ready_patient)

        # NOT_READY, to be manually marked BLOCKED via a follow-up below.
        blocked_patient = _make_patient(db, mrn_suffix="BLOCKED-1", created_by=staff_user.id)
        _make_benefit_period(db, blocked_patient)

        # Run the real evaluation once so every patient has a persisted
        # BillingReadinessVerdict / synced blocker lifecycle before we
        # attach assignments and follow-ups to them below (assignment/
        # follow-up rows reference real verdicts and patients, not the
        # other way around, but attaching a BLOCKED follow-up before any
        # verdict exists would just be attaching it to nothing yet).
        build_tenant_readiness_dashboard(db, tenant_id=str(DEMO_TENANT_ID), service_date=SERVICE_DATE)

        # Deliverable 4 -- assign the NOT_READY patient to the demo staff
        # user so the queue has a real "Assigned" row to filter on.
        upsert_assignment(
            db,
            tenant_id=str(DEMO_TENANT_ID),
            patient_id=str(not_ready_patient.id),
            actor_user_id=str(staff_user.id),
            assigned_user_id=str(staff_user.id),
            assigned_role="BILLING_SPECIALIST",
            assignment_status="ASSIGNED",
        )

        # Deliverable 5 -- an open follow-up due soon on the NOT_READY
        # patient, and a BLOCKED follow-up on the dedicated blocked
        # patient (the sole trigger for the dashboard's Blocked bucket).
        upsert_follow_up(
            db,
            tenant_id=str(DEMO_TENANT_ID),
            patient_id=str(not_ready_patient.id),
            actor_user_id=str(staff_user.id),
            status="OPEN",
            due_date=date.today() + timedelta(days=2),
            notes="Follow up on outstanding NOE filing.",
        )
        upsert_follow_up(
            db,
            tenant_id=str(DEMO_TENANT_ID),
            patient_id=str(blocked_patient.id),
            actor_user_id=str(staff_user.id),
            status="BLOCKED",
            due_date=date.today() - timedelta(days=3),
            notes="Awaiting physician signature on certification -- escalated.",
        )

        # Re-run the evaluation once more now that the BLOCKED follow-up
        # exists, so the printed summary (and the persisted verdicts)
        # reflect the final, real 4-bucket rollup -- matching exactly
        # what GET /billing/readiness-dashboard will return on next call.
        dashboard = build_tenant_readiness_dashboard(db, tenant_id=str(DEMO_TENANT_ID), service_date=SERVICE_DATE)

        print("Seeded Billing Readiness Operational Workflow demo data.")
        print(f"  tenant_id: {DEMO_TENANT_ID}")
        print(f"  counts:    {dashboard['counts']}")
        print(f"  patients:  {ready_patient.mrn}, {at_risk_patient.mrn}, {not_ready_patient.mrn}, {blocked_patient.mrn}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
