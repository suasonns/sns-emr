import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.models.patient import Patient
from app.models.admission import Admission
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.enums import DiagnosisType, DiagnosisStatus, DiagnosisSource
from app.services.admission_cloning_service import clone_previous_admission
from app.services.admission_dx_validation_engine import AdmissionDxValidationEngine


def _get_patient(db):
    tenant_id = uuid.UUID(db.info["tenant_id"])
    user_id = _get_existing_user_id(db)
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=f"MRN-{patient_id.hex[:8]}",
        date_of_birth=datetime(1950, 1, 1).date(),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
        created_by=user_id,
    )
    db.add(patient)
    db.flush()

    prior_admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="AUTHORIZED",
        admission_date=datetime.now(timezone.utc),
        created_by=user_id,
    )
    db.add(prior_admission)
    db.add(
        PatientDiagnosis(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            diagnosis_type=DiagnosisType.PRIMARY,
            status=DiagnosisStatus.ACTIVE,
            source=DiagnosisSource.REFERRAL,
            icd10_code="C25.9",
            diagnosis_description="Malignant neoplasm of pancreas",
            display_name="Pancreatic cancer",
        )
    )
    db.flush()
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


def test_dx_decision_same_primary(db_session):
    db = db_session
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


def test_dx_decision_changed_primary(db_session):
    db = db_session
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
