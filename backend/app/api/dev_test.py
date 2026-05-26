from __future__ import annotations

from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db_tenant_dependency import get_db_tenant
from app.models.patient import Patient
from app.services.audit_logger import log_event

router = APIRouter(
    prefix="/dev-test",
    tags=["Dev Test"],
)


# ---------------------------------------------------------------------
# COUNTER (TENANT-SAFE)
# ---------------------------------------------------------------------
@router.get("/patients-count")
def patients_count(db: Session = Depends(get_db_tenant)):
    try:
        tenant_id = str(db.info["tenant_id"])

        count = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .count()
        )

        return {"count": count}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to count patients: {str(e)}",
        )


# ---------------------------------------------------------------------
# CREATE PATIENT (TENANT AUTO-STAMP SAFE)
# ---------------------------------------------------------------------
@router.post("/create-patient")
def create_patient(db: Session = Depends(get_db_tenant)):
    try:
        patient = Patient(
            mrn="TEST-" + str(uuid.uuid4())[:8],
            full_name="Test Patient",
            date_of_birth=date(1970, 1, 1),
            primary_diagnosis="CHF",
            status="ACTIVE",
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        return {
            "status": "created",
            "patient_id": str(patient.id),
            "tenant_id": str(patient.tenant_id),
            "mrn": patient.mrn,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create patient: {str(e)}",
        )


# ---------------------------------------------------------------------
# OWNERSHIP CHECK (DEV-ONLY) + AUDIT EVIDENCE ON VIOLATION
# Requires DB function: admin_patient_owner_tenant(uuid) RETURNS uuid
# ---------------------------------------------------------------------
@router.get("/ownership-check/{patient_id}")
def ownership_check(patient_id: str, request: Request, db: Session = Depends(get_db_tenant)):
    request_tenant = str(getattr(request.state, "tenant_id", None) or db.info.get("tenant_id") or "")

    # Ask DB who owns this patient (no PHI returned)
    owner_tenant = db.execute(
        text("SELECT admin_patient_owner_tenant(:pid)::text"),
        {"pid": patient_id},
    ).scalar()

    if owner_tenant is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    if str(owner_tenant) != str(request_tenant):
        # ✅ Audit evidence of cross-tenant attempt (non-blocking)
        req_id = str(getattr(request.state, "request_id", "") or "")
        user_id = str(getattr(request.state, "user_id", "") or "")

        try:
            log_event(
                request_id=req_id,
                tenant_id=request_tenant,
                user_id=user_id,
                role=None,
                action="CROSS_TENANT_ACCESS_ATTEMPT",
                entity_type="patient",
                entity_id=str(patient_id),
                ip=request.client.host if request.client else None,
                metadata={
                    "request_tenant_id": request_tenant,
                    "owner_tenant_id": str(owner_tenant),
                    "reason": "Ownership mismatch (cross-tenant access blocked)",
                },
                db=db,
                commit=True,
            )
            print("AUDIT LOG WRITTEN ✅")
        except Exception as e:
            # Never block security enforcement if audit write fails
            print(f"AUDIT LOG WRITE FAILED: {e}")

        raise HTTPException(status_code=403, detail="Cross-tenant access blocked")

    return {"status": "ok", "owner_tenant_id": str(owner_tenant)}