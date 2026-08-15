import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.patient import Patient
from app.models.admission import Admission
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.enums import DiagnosisType, DiagnosisStatus
from app.services.admission_cloning_service import clone_previous_admission
from app.services.admission_dx_validation_engine import AdmissionDxValidationEngine


PATIENT_ID = uuid.UUID("22acc303-cd29-42d6-8083-18b2541d1c6b")


def _get_patient(db):
    patient = db.query(Patient).filter(Patient.id == PATIENT_ID).first()
    assert patient is not None, "Patient not found"
    return patient


def _get_existing_user_id(db):
    row = db.execute(
        text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    ).fetchone()
    assert row is not None, "No users found in users table"
    return row[0]


def _get_latest_active_primary(db, patient):
    query = (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == patient.tenant_id,
            PatientDiagnosis.patient_id == patient.id,
            PatientDiagnosis.diagnosis_type == DiagnosisType.PRIMARY,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
        )
        .order_by(PatientDiagnosis.created_at.desc())
    )

    return query.first()


def _get_matching_secondary_on_new_admission(db, patient, new_admission_id, icd10_code):
    query = (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == patient.tenant_id,
            PatientDiagnosis.patient_id == patient.id,
            PatientDiagnosis.diagnosis_type == DiagnosisType.SECONDARY,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.icd10_code == icd10_code,
        )
        .order_by(PatientDiagnosis.created_at.desc())
    )

    if hasattr(PatientDiagnosis, "admission_id"):
        query = query.filter(PatientDiagnosis.admission_id == new_admission_id)

    return query.first()


def _create_new_admission(db, patient, user_id):
    now = datetime.now(timezone.utc)

    new_admission = Admission(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        status="PENDING",
        admission_date=now,
        created_at=now,
        updated_at=now,
        created_by=user_id,
        updated_by=user_id,
    )

    db.add(new_admission)
    db.flush()
    return new_admission


def test_dx_decision_same_primary():
    db = SessionLocal()

    try:
        patient = _get_patient(db)
        user_id = _get_existing_user_id(db)

        previous_primary = _get_latest_active_primary(db, patient)
        assert previous_primary is not None, "Patient has no active previous primary diagnosis"
        assert previous_primary.icd10_code, "Previous primary diagnosis code is missing"

        new_admission = _create_new_admission(db, patient, user_id)

        clone_result = clone_previous_admission(
            db=db,
            patient_id=patient.id,
            new_admission=new_admission,
            user_id=user_id,
        )

        print("CLONE RESULT (same primary test):", clone_result)

        decision = AdmissionDxValidationEngine.validate_and_apply_primary_decision(
            db=db,
            patient=patient,
            new_admission=new_admission,
            user_id=user_id,
            primary_diagnosis=previous_primary.icd10_code,
            is_same_primary_as_previous=True,
        )

        db.flush()

        print("DX DECISION RESULT (same primary):", decision)

        assert decision.success is True
        assert decision.status == "primary_confirmed_same_as_previous"
        assert "confirmed_previous_primary" in decision.actions

        secondary_row = _get_matching_secondary_on_new_admission(
            db=db,
            patient=patient,
            new_admission_id=new_admission.id,
            icd10_code=previous_primary.icd10_code,
        )
        assert secondary_row is None

    finally:
        db.rollback()
        db.close()


def test_dx_decision_changed_primary():
    db = SessionLocal()

    try:
        patient = _get_patient(db)
        user_id = _get_existing_user_id(db)

        previous_primary = _get_latest_active_primary(db, patient)
        assert previous_primary is not None, "Patient has no active previous primary diagnosis"
        assert previous_primary.icd10_code, "Previous primary diagnosis code is missing"

        new_admission = _create_new_admission(db, patient, user_id)

        clone_result = clone_previous_admission(
            db=db,
            patient_id=patient.id,
            new_admission=new_admission,
            user_id=user_id,
        )

        print("CLONE RESULT (changed primary test):", clone_result)

        # Replace this if your diagnosis master/source rejects this code
        new_primary_code = "C78.7"

        decision = AdmissionDxValidationEngine.validate_and_apply_primary_decision(
            db=db,
            patient=patient,
            new_admission=new_admission,
            user_id=user_id,
            primary_diagnosis=new_primary_code,
            is_same_primary_as_previous=False,
        )

        db.flush()

        print("DX DECISION RESULT (changed primary):", decision)

        assert decision.success is True
        assert decision.status == "primary_changed"
        assert "created_new_primary" in decision.actions
        assert "previous_primary_moved_to_secondary" in decision.actions

        secondary_row = _get_matching_secondary_on_new_admission(
            db=db,
            patient=patient,
            new_admission_id=new_admission.id,
            icd10_code=previous_primary.icd10_code,
        )
        assert secondary_row is not None, "Previous primary was not moved to secondary"

    finally:
        db.rollback()
        db.close()
