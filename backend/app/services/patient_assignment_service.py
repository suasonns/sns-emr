from sqlalchemy.orm import Session

from app.models.patient_assignment import PatientAssignment
from app.models.enums import Discipline


def set_primary_rn(
    db: Session,
    *,
    tenant_id,
    patient_id,
    user_id,
    assigned_by=None,
):
    """
    Ensures ONLY ONE active primary RN per patient

    Behavior:
    - Deactivates existing primary RN
    - Assigns new primary RN
    """

    # =====================================================
    # STEP 1: Remove existing primary RN
    # =====================================================
    existing_primary = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.discipline == Discipline.RN,
            PatientAssignment.active == True,
            PatientAssignment.is_primary == True,
        )
        .all()
    )

    for assignment in existing_primary:
        assignment.is_primary = False

    # =====================================================
    # STEP 2: Check if assignment already exists
    # =====================================================
    existing_assignment = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.user_id == user_id,
            PatientAssignment.discipline == Discipline.RN,
        )
        .first()
    )

    if existing_assignment:
        existing_assignment.is_primary = True
        existing_assignment.active = True
        existing_assignment.status = "ASSIGNED"
    else:
        # =====================================================
        # STEP 3: Create new assignment
        # =====================================================
        new_assignment = PatientAssignment(
            tenant_id=tenant_id,
            patient_id=patient_id,
            user_id=user_id,
            discipline=Discipline.RN,
            is_primary=True,
            active=True,
            status="ASSIGNED",
            assigned_by=assigned_by,
        )

        db.add(new_assignment)

    db.commit()