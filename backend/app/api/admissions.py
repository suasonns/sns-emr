from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditLog
from app.services.admission.guardrail_assessment_service import (
    AdmissionGuardrailAssessmentService,
)


router = APIRouter(prefix="/api/patients", tags=["Admissions"])


class AdmitPatientRequest(BaseModel):
    acknowledged: bool = Field(
        default=False,
        description="Acknowledges HIGH/CRITICAL documentation guidance.",
    )


def enforce_admission_requirements(db: Session, patient_id: str, tenant_id: str) -> None:

    row = (
        db.execute(
            text(
                """
                SELECT
                    allergy_state,
                    dx_discrepancy_open
                FROM patient_face_sheet_view
                WHERE patient_id = :pid
                  AND tenant_id = :tenant_id
                """
            ),
            {"pid": patient_id, "tenant_id": tenant_id},
        )
        .mappings()
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")

    if row["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        raise HTTPException(
            status_code=409,
            detail="Allergy status must be documented before admission.",
        )

    if row["dx_discrepancy_open"] is True:
        raise HTTPException(
            status_code=409,
            detail="Diagnosis discrepancy must be resolved before admission.",
        )

    rn_dx_exists = db.execute(
        text(
            """
            SELECT 1
            FROM diagnosis_sources
            WHERE patient_id = :pid
              AND tenant_id = :tenant_id
              AND source = 'RN_IA'
              AND dx_type = 'PRIMARY'
              AND is_active = true
            LIMIT 1
            """
        ),
        {"pid": patient_id, "tenant_id": tenant_id},
    ).scalar()

    if not rn_dx_exists:
        raise HTTPException(
            status_code=409,
            detail="RN Initial Assessment primary diagnosis is required.",
        )


@router.post("/{patient_id}/admit", status_code=status.HTTP_200_OK)
def admit_patient(
    patient_id: str,
    payload: Optional[AdmitPatientRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:

    payload = payload or AdmitPatientRequest()
    acknowledged = bool(payload.acknowledged)

    tenant_id = current_user.tenant_id
    user_id = current_user.id

    try:
        with db.begin():

            enforce_admission_requirements(db, patient_id, tenant_id)

            # --------------------------------------------------
            # ✅ LOAD PATIENT
            # --------------------------------------------------
            patient_row = (
                db.execute(
                    text(
                        """
                        SELECT patient_type
                        FROM patients
                        WHERE id = :pid
                          AND tenant_id = :tenant_id
                        """
                    ),
                    {"pid": patient_id, "tenant_id": tenant_id},
                )
                .mappings()
                .first()
            )

            if not patient_row:
                raise HTTPException(status_code=404, detail="Patient not found")

            if patient_row["patient_type"] in ("TRAINING", "DEMO", "TEST"):
                raise HTTPException(
                    status_code=403,
                    detail="Training/demo patients cannot be admitted.",
                )

            # --------------------------------------------------
            # ✅ LOAD LATEST ADMISSION (AUTHORITATIVE)
            # --------------------------------------------------
            admission_ctx = (
                db.execute(
                    text(
                        """
                        SELECT id, soc_date, status, admission_authorized_at
                        FROM admissions
                        WHERE patient_id = :pid
                          AND tenant_id = :tenant_id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"pid": patient_id, "tenant_id": tenant_id},
                )
                .mappings()
                .first()
            )

            if not admission_ctx:
                raise HTTPException(
                    status_code=409,
                    detail="Admission authorization required before admit.",
                )

            # --------------------------------------------------
            # ✅ ENFORCE AUTHORIZATION
            # --------------------------------------------------
            if admission_ctx["admission_authorized_at"] is None:
                raise HTTPException(
                    status_code=409,
                    detail="Admission must be authorized before activation.",
                )
            
            # ✅ SOC ENFORCEMENT (EDGE CASE)
            if admission_ctx["status"] == "AUTHORIZED" and admission_ctx["soc_date"] is None:
                raise HTTPException(
                status_code=409,
                detail="SOC must be set before admission activation.",
            )
            
            if admission_ctx["status"] not in ("AUTHORIZED", "PENDING"):
                raise HTTPException(
                    status_code=409,
                    detail="Admission is not in a valid state for activation.",
                )

            # --------------------------------------------------
            # ✅ SOC VALIDATION
            # --------------------------------------------------
            soc_datetime = admission_ctx["soc_date"]

            if soc_datetime is None:
                raise HTTPException(
                    status_code=400,
                    detail="SOC date/time must be entered before admission.",
                )

            now = datetime.utcnow()

            if soc_datetime > now:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot admit before SOC date/time.",
                )
            
            # ✅ GUARDRAILS CHECK (MUST RUN BEFORE ACTIVATION)
            guardrail_result = AdmissionGuardrailAssessmentService.assess_admission(
                db=db,
                admission={"id": admission_ctx["id"], "patient_id": patient_id},
                user_id=user_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
            )

            severity = (guardrail_result.get("severity") or "INFO").upper()

            if severity in {"HIGH", "CRITICAL"} and not acknowledged:
                return {
                    "blocked": True,
                    "reason": "ACK_REQUIRED",
                    "guardrail": guardrail_result,
                }
            
            # --------------------------------------------------
            # ✅ BLOCK DUPLICATE ACTIVE ADMISSION
            # --------------------------------------------------
            existing_active = (
                db.execute(
                    text(
                        """
                        SELECT id
                        FROM admissions
                        WHERE patient_id = :pid
                          AND tenant_id = :tenant_id
                          AND status = 'ACTIVE'
                        LIMIT 1
                        """
                    ),
                    {"pid": patient_id, "tenant_id": tenant_id},
                )
                .mappings()
                .first()
            )

            if existing_active:
                raise HTTPException(
                    status_code=409,
                    detail="Active admission already exists.",
                )

            # --------------------------------------------------
            # ✅ ACTIVATE ADMISSION (SAFE SCOPE)
            # --------------------------------------------------
            updated = db.execute(
                text(
                    """
                    UPDATE admissions
                    SET status = 'ACTIVE',
                        admission_date = :now,
                        admitted_by = :user_id
                    WHERE id = :admission_id
                      AND patient_id = :pid
                      AND tenant_id = :tenant_id
                    """
                ),
                {
                    "now": now,
                    "user_id": user_id,
                    "admission_id": admission_ctx["id"],
                    "pid": patient_id,
                    "tenant_id": tenant_id,
                },
            ).rowcount

            if updated == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to activate admission.",
                )

            # --------------------------------------------------
            # ✅ UPDATE PATIENT STATE
            # --------------------------------------------------
            db.execute(
                text(
                    """
                    UPDATE patients
                    SET status = 'ACTIVE'
                    WHERE id = :pid
                      AND tenant_id = :tenant_id
                    """
                ),
                {"pid": patient_id, "tenant_id": tenant_id},
            )

            # --------------------------------------------------
            # ✅ AUDIT LOG (ENTERPRISE)
            # --------------------------------------------------
            audit = AuditLog()
            audit.tenant_id = tenant_id
            audit.user_id = user_id
            audit.action = "PATIENT_ADMITTED"
            audit.entity_type = "PATIENT"
            audit.entity_id = patient_id
            audit.created_at = now

            audit.details = {
                "admission_id": str(admission_ctx["id"]),
                "previous_status": admission_ctx["status"],
                "new_status": "ACTIVE",
                "soc_date": soc_datetime.isoformat(),
            }

            audit.changes = audit.details

            db.add(audit)

        return {
            "patient_id": patient_id,
            "admission_id": str(admission_ctx["id"]),
            "status": "ACTIVE",
            "soc_date": soc_datetime.isoformat(),
        }

    except HTTPException:
        raise
    except Exception:
        raise