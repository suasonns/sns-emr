from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.models.admission import Admission
from app.models.enums import TaskDiscipline, TaskOrigin, TaskStatus, TaskType
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.task import Task

ADMIN_EMAIL = "rsuason@loveandfaithhospice.com"
MIN_PASSWORD_LENGTH = 12

TEST_PATIENTS = (
    ("TEST-0001", "Test", "Patient Alpha", date(1942, 4, 12), "Congestive heart failure"),
    ("TEST-0002", "Test", "Patient Bravo", date(1948, 9, 3), "Chronic obstructive pulmonary disease"),
    ("TEST-0003", "Test", "Patient Charlie", date(1939, 1, 27), "Metastatic lung cancer"),
    ("TEST-0004", "Test", "Patient Delta", date(1951, 7, 19), "Alzheimer disease"),
    ("TEST-0005", "Test", "Patient Echo", date(1945, 11, 8), "End-stage renal disease"),
)


def _test_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"sns-hospice-solutions-test:{kind}:{key}")


def _insert_test_records(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    for index, (mrn, first_name, last_name, dob, diagnosis) in enumerate(TEST_PATIENTS):
        patient = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id, Patient.mrn == mrn)
            .one_or_none()
        )
        if patient is None:
            patient = Patient(
                id=_test_id("patient", mrn),
                tenant_id=tenant_id,
                mrn=mrn,
                date_of_birth=dob,
                primary_diagnosis=diagnosis,
                status="ACTIVE",
                patient_type="TRAINING",
                training_label="SYNTHETIC TEST DATA",
                admission_status="ADMITTED",
                acuity_state="ROUTINE",
                hospice_election_date=(now - timedelta(days=30 + index * 4)).date(),
                created_by=user_id,
            )
            db.add(patient)

        facesheet = (
            db.query(PatientFaceSheet)
            .filter(PatientFaceSheet.tenant_id == tenant_id, PatientFaceSheet.patient_id == patient.id)
            .first()
        )
        if facesheet is None:
            db.add(
                PatientFaceSheet(
                    id=_test_id("facesheet", mrn),
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    first_name=first_name,
                    last_name=last_name,
                    dob=dob,
                    primary_payer="Medicare",
                    created_by=user_id,
                )
            )

        admission = (
            db.query(Admission)
            .filter(Admission.tenant_id == tenant_id, Admission.patient_id == patient.id)
            .first()
        )
        if admission is None:
            admission_at = now - timedelta(days=30 + index * 4)
            db.add(
                Admission(
                    id=_test_id("admission", mrn),
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    admission_date=admission_at,
                    soc_date=admission_at,
                    status="ADMITTED",
                    referral_source="SYNTHETIC TEST DATA",
                    reason_for_admission=diagnosis,
                    created_by=user_id,
                )
            )

        task_id = _test_id("task", mrn)
        if db.get(Task, task_id) is None:
            db.add(
                Task(
                    id=task_id,
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    created_by=user_id,
                    assigned_user_id=user_id,
                    task_type=TaskType.POC_REVIEW_REQUIRED if index % 2 == 0 else TaskType.IDG_REVIEW,
                    origin=TaskOrigin.MANUAL,
                    discipline=TaskDiscipline.RN,
                    status=TaskStatus.PENDING,
                    priority="HIGH" if index == 0 else "MEDIUM",
                    alert_reason="Synthetic test task",
                    due_date=(now + timedelta(days=index - 1)).date(),
                )
            )


def bootstrap_production_admin(db: Session) -> bool:
    password = os.getenv("ADMIN_PASSWORD")
    system_tenant_id_raw = os.getenv("SYSTEM_TENANT_ID") or os.getenv("OWNER_TENANT_ID")

    if not password:
        return False
    if not system_tenant_id_raw:
        raise RuntimeError(
            "SYSTEM_TENANT_ID is required for global owner/billing dashboard access. "
            "This is not an agency tenant."
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise RuntimeError(f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters")

    system_tenant_id = uuid.UUID(system_tenant_id_raw)
    system_tenant = db.get(Tenant, system_tenant_id)
    if system_tenant is None:
        system_tenant = Tenant(
            id=system_tenant_id,
            legal_name="SNS Platform",
            display_name="SNS Platform",
            npi="0000000000",
            ein=None,
            ptan=None,
            tenant_type="PRODUCTION",
            environment_tag="PERMANENT",
            status="ACTIVE",
            ai_enabled=True,
            billing_enabled=False,
        )
        db.add(system_tenant)

    agency_tenant_id_raw = os.getenv("DEV_TENANT_REAL_ID")
    agency_tenant_id = uuid.UUID(agency_tenant_id_raw) if agency_tenant_id_raw else system_tenant_id

    user = db.query(User).filter(User.email == ADMIN_EMAIL).one_or_none()
    if user is None:
        user = User(id=uuid.uuid4(), tenant_id=agency_tenant_id, email=ADMIN_EMAIL)
        db.add(user)

    user.tenant_id = agency_tenant_id
    user.first_name = "Romel"
    user.middle_name = None
    user.last_name = "Suason"
    user.full_name = "Romel Suason"
    # This is the Love & Faith Hospice agency account (DPCS + Administrator),
    # distinct from the SNS Hospice Solutions platform/vendor OWNER account.
    user.role = "DPCS_ADMINISTRATOR"
    user.access_level = "FULL_ACCESS"
    user.active = True
    user.password_hash = hash_password(password)

    db.flush()
    db.commit()
    return True