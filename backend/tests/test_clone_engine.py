import uuid
from datetime import datetime, timezone

from app.models.patient import Patient
from app.models.admission import Admission
from app.services.admission_cloning_service import clone_previous_admission


def test_clone_engine(db_session):
    db = db_session
    tenant_id = uuid.UUID(db.info["tenant_id"])
    user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
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

    now = datetime.now(timezone.utc)
    previous_admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        status="AUTHORIZED",
        admission_date=now,
        created_at=now,
        created_by=user_id,
    )
    db.add(previous_admission)
    db.flush()

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

    result = clone_previous_admission(
        db=db,
        patient_id=patient.id,
        new_admission=new_admission,
        user_id=user_id,
    )

    db.commit()

    print("✅ CLONING RESULT:", result)

    assert "status" in result
