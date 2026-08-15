import uuid
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.patient import Patient
from app.models.admission import Admission
from app.services.admission_cloning_service import clone_previous_admission


def test_clone_engine():

    db = SessionLocal()

    # ✅ REAL PATIENT ID
    patient_id = uuid.UUID("22acc303-cd29-42d6-8083-18b2541d1c6b")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    assert patient is not None, "Patient not found"

    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()

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

    # ✅ ASSERT EXPECTED RESULT
    assert "status" in result
