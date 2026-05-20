# app/api/admissions.py

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
from app.services.admission_guardrails_service import AdmissionGuardrailsService


router = APIRouter(prefix="/api/patients", tags=["Admissions"])


# ==========================================================
# Request model: supports ACK_REQUIRED workflow
# ==========================================================

class AdmitPatientRequest(BaseModel):
    acknowledged: bool = Field(
        default=False,
        description="Acknowledges HIGH/CRITICAL documentation guidance (clinical decision remains with staff).",
    )


# ==========================================================
# Hard validation: objective gates only (your policy)
# - allergy must be documented
# - dx discrepancy must be resolved (NOE/CTI/RN Primary Dx mismatch)
# - RN IA primary dx must exist
# NOTE: tenant-safe reads
# ==========================================================

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
        # Do not leak existence across tenants
        raise HTTPException(status_code=404, detail="Patient not found")

    # Allergy gate (objective requirement)
    if row["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        raise HTTPException(
            status_code=409,
            detail="Admission cannot be finalized until allergy status is documented (NKDA or allergy list).",
        )

    # Dx discrepancy gate (your ONLY hard-block clinical integrity rule)
    if row["dx_discrepancy_open"] is True:
        raise HTTPException(
            status_code=409,
            detail="Admission cannot be finalized until diagnosis discrepancy is reconciled.",
        )

    # RN IA PRIMARY Dx required (objective requirement)
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
            detail="Admission cannot be finalized until RN Initial Assessment primary diagnosis is documented.",
        )


# ==========================================================
# Admit endpoint
# - Applies hard validation (objective blocks only)
# - Runs guardrails (decision support only)
# - Surfaces rn_explanation
# - ACK_REQUIRED for HIGH/CRITICAL guidance (workflow pause only)
# - Tenant-safe update + audit
# ==========================================================

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
            # 1) Hard validation (objective requirements only)
            enforce_admission_requirements(db, patient_id, tenant_id)

            # 2) Guardrails (decision support only)
            admission_context = {"id": patient_id, "patient_id": patient_id}
            result = AdmissionGuardrailsService.assess_admission(
                db=db,
                admission=admission_context,
                user_id=user_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
            )

            severity = (result.get("severity") or "INFO").upper()
            flags: List[Any] = result.get("flags", []) or []
            mode = (result.get("guardrail_mode") or "GUIDANCE").upper()
            rn_explanation = result.get("rn_explanation")  # centralized, compliance-approved wording

            # 3) ACK_REQUIRED workflow pause (NOT a denial, NOT a clinical block)
            if severity in {"HIGH", "CRITICAL"} and not acknowledged:
                return {
                    "blocked": True,
                    "reason": "ACK_REQUIRED",
                    "guardrail_mode": mode,
                    "guardrail": {"severity": severity, "flags": flags},
                    "rn_explanation": rn_explanation,
                }

            # 4) Tenant-safe status transition
            updated = db.execute(
                text(
                    """
                    UPDATE patients
                    SET status = 'ACTIVE'
                    WHERE id = :pid
                      AND tenant_id = :tenant_id
                    """
                ),
                {"pid": patient_id, "tenant_id": tenant_id},
            ).rowcount

            if updated == 0:
                # Do not leak cross-tenant existence
                raise HTTPException(status_code=404, detail="Patient not found")

            # 5) Audit the admission event (survey-defensible)
            now = datetime.utcnow()
            audit = AuditLog()

            if hasattr(audit, "tenant_id"):
                audit.tenant_id = tenant_id
            if hasattr(audit, "user_id"):
                audit.user_id = user_id
            if hasattr(audit, "actor_user_id"):
                audit.actor_user_id = user_id
            if hasattr(audit, "action"):
                audit.action = "PATIENT_ADMITTED"
            if hasattr(audit, "entity_type"):
                audit.entity_type = "PATIENT"
            if hasattr(audit, "entity"):
                audit.entity = "PATIENT"
            if hasattr(audit, "entity_id"):
                audit.entity_id = patient_id
            if hasattr(audit, "timestamp"):
                audit.timestamp = now
            if hasattr(audit, "created_at"):
                audit.created_at = now
            if hasattr(audit, "details"):
                audit.details = {
                    "guardrail_mode": mode,
                    "severity": severity,
                    "flags": flags,
                    "rn_explanation": rn_explanation,
                    "acknowledged": acknowledged,
                }
            if hasattr(audit, "changes"):
                audit.changes = {
                    "guardrail_mode": mode,
                    "severity": severity,
                    "flags": flags,
                    "rn_explanation": rn_explanation,
                    "acknowledged": acknowledged,
                }

            db.add(audit)

        # success response (include rn_explanation)
        return {
            "patient_id": patient_id,
            "status": "ACTIVE",
            "guardrail_mode": mode,
            "guardrail": {
                "severity": severity,
                "flags": flags,
                "requires_md_review": bool(result.get("requires_md_review", False)),
            },
            "rn_explanation": rn_explanation,
        }

    except HTTPException:
        raise
    except Exception:
        raise


# ==========================================================
# NOE readiness endpoint (tenant-safe)
# ==========================================================

@router.get("/{patient_id}/noe-readiness", status_code=status.HTTP_200_OK)
def noe_readiness(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Determine whether the patient is ready for NOE submission.
    This endpoint NEVER mutates data. It only reports readiness + reasons.
    """
    tenant_id = current_user.tenant_id

    row = (
        db.execute(
            text(
                """
                SELECT
                    patient_status,
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

    reasons: List[str] = []

    if row["patient_status"] != "ACTIVE":
        reasons.append("Patient is not admitted (status is not ACTIVE)")

    if row["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        reasons.append("Allergy status not documented (NKDA or allergy list required)")

    if row["dx_discrepancy_open"] is True:
        reasons.append("Diagnosis discrepancy is still open")

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
        reasons.append("RN Initial Assessment primary diagnosis is missing")

    return {
        "patient_id": patient_id,
        "ready": len(reasons) == 0,
        "reasons": reasons,
    }