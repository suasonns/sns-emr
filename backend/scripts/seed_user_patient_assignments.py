"""
Seed PatientAssignment rows for a given user across every active patient
in their own tenant. Generic, tenant-scoped — not hardcoded to a single
patient. Usage: pass the user's email as sys.argv[1].
"""
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.enums import Discipline

email = sys.argv[1]
db = SessionLocal()

user = db.query(User).filter(User.email == email).first()
if not user:
    print(f"No user found for {email}")
    sys.exit(1)

# Map role -> Discipline enum; fall back to ADMIN for non-clinical roles
# (e.g. OWNER) so an assignment can still be recorded for care-team display.
role_to_discipline = {
    "MD": Discipline.MD, "DO": Discipline.DO, "NP": Discipline.NP, "PA": Discipline.PA,
    "RN": Discipline.RN, "LVN": Discipline.LVN, "LPN": Discipline.LPN,
    "CHHA": Discipline.CHHA, "AIDE": Discipline.AIDE,
    "SW": Discipline.SW, "MSW": Discipline.MSW, "BSW": Discipline.BSW, "LCSW": Discipline.LCSW,
    "SC": Discipline.SC, "CHAPLAIN": Discipline.CHAPLAIN,
}
discipline = role_to_discipline.get(user.role, Discipline.ADMIN)

patients = db.query(Patient).filter(Patient.tenant_id == user.tenant_id).all()
created, existing = 0, 0
for patient in patients:
    row = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.tenant_id == user.tenant_id,
            PatientAssignment.patient_id == patient.id,
            PatientAssignment.user_id == user.id,
        )
        .first()
    )
    if row:
        if not row.active:
            row.active = True
            row.status = "ASSIGNED"
        existing += 1
        continue
    db.add(PatientAssignment(
        tenant_id=user.tenant_id,
        patient_id=patient.id,
        user_id=user.id,
        discipline=discipline,
        is_primary=True,
        active=True,
        status="ASSIGNED",
        assigned_by=user.id,
    ))
    created += 1

db.commit()
print(f"{email}: {created} assignments created, {existing} already existed, across {len(patients)} patients in tenant {user.tenant_id}")
