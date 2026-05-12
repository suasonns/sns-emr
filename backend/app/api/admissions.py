from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Admissions"])


def enforce_admission_requirements(db: Session, patient_id: str):
    # -------------------------------------------
    # 1) Read face sheet for allergy + discrepancy
    # -------------------------------------------
    row = db.execute(
        text("""
            SELECT
                allergy_state,
                dx_discrepancy_open
            FROM patient_face_sheet_view
            WHERE patient_id = :pid
        """),
        {"pid": patient_id},
    ).mappings().first()

    if not row:
        raise HTTPException(404, "Patient not found")

    # Allergy gate
    if row["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        raise HTTPException(
            status_code=409,
            detail="Admission cannot be finalized until allergy status is documented (NKDA or allergy list)."
        )

    # Dx discrepancy gate
    if row["dx_discrepancy_open"] is True:
        raise HTTPException(
            status_code=409,
            detail="Admission cannot be finalized until diagnosis discrepancy is reconciled."
        )

    # -------------------------------------------
    # 2) RN Initial Assessment PRIMARY Dx gate
    #    (query diagnosis_sources directly)
    # -------------------------------------------
    rn_dx_exists = db.execute(
        text("""
            SELECT 1
            FROM diagnosis_sources
            WHERE patient_id = :pid
              AND source = 'RN_IA'
              AND dx_type = 'PRIMARY'
              AND is_active = true
            LIMIT 1
        """),
        {"pid": patient_id},
    ).scalar()

    if not rn_dx_exists:
        raise HTTPException(
            status_code=409,
            detail="Admission cannot be finalized until RN Initial Assessment primary diagnosis is documented."
        )


@router.post("/{patient_id}/admit", status_code=status.HTTP_200_OK)
def admit_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Enforce all admission gates
    enforce_admission_requirements(db, patient_id)

    # Transition patient to ACTIVE
    updated = db.execute(
        text("""
            UPDATE patients
            SET status = 'ACTIVE'
            WHERE id = :pid
        """),
        {"pid": patient_id},
    ).rowcount

    if updated == 0:
        raise HTTPException(404, "Patient not found")

    db.commit()

    return {"patient_id": patient_id, "status": "ACTIVE"}

@router.get("/{patient_id}/noe-readiness", status_code=status.HTTP_200_OK)
def noe_readiness(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Determine whether the patient is ready for NOE submission.
    This endpoint NEVER mutates data. It only reports readiness + reasons.
    """

    # ------------------------------------------------
    # 1) Pull state-aware data from face sheet
    # ------------------------------------------------
    row = db.execute(
        text("""
            SELECT
                patient_status,
                allergy_state,
                dx_discrepancy_open
            FROM patient_face_sheet_view
            WHERE patient_id = :pid
        """),
        {"pid": patient_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")

    reasons = []

    # Must be admitted
    if row["patient_status"] != "ACTIVE":
        reasons.append("Patient is not admitted (status is not ACTIVE)")

    # Allergy must be documented
    if row["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        reasons.append("Allergy status not documented (NKDA or allergy list required)")

    # Dx discrepancy must be resolved
    if row["dx_discrepancy_open"] is True:
        reasons.append("Diagnosis discrepancy is still open")

    # ------------------------------------------------
    # 2) RN IA Primary Dx check (source-of-truth table)
    # ------------------------------------------------
    rn_dx_exists = db.execute(
        text("""
            SELECT 1
            FROM diagnosis_sources
            WHERE patient_id = :pid
              AND source = 'RN_IA'
              AND dx_type = 'PRIMARY'
              AND is_active = true
            LIMIT 1
        """),
        {"pid": patient_id},
    ).scalar()

    if not rn_dx_exists:
        reasons.append("RN Initial Assessment primary diagnosis is missing")

    # ------------------------------------------------
    # 3) Final readiness result
    # ------------------------------------------------
    return {
        "patient_id": patient_id,
        "ready": len(reasons) == 0,
        "reasons": reasons
    }