from sqlalchemy.orm import Session
from datetime import datetime

from app.models.patient import Patient
from app.services.idg_meeting_scheduler import generate_idg_meetings


def generate_for_all_active_patients(
    db: Session,
    *,
    tenant_id,
    start_date: datetime,
    created_by=None,
):

    patients = (
        db.query(Patient)
        .filter(
            Patient.tenant_id == tenant_id,
            Patient.status == "active",
        )
        .all()
    )

    for patient in patients:
        generate_idg_meetings(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            benefit_period_id=None,
            start_date=start_date,
            created_by=created_by,
        )
