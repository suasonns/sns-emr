from __future__ import annotations

from datetime import date, datetime, timezone
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


router = APIRouter(prefix="/patients", tags=["Admissions"])


class AdmitPatientRequest(BaseModel):
    acknowledged: bool = Field(
        default=False,
        description="Acknowledges HIGH/CRITICAL documentation guidance.",
    )


# CMS HOPE A2115 "Reason for Discharge" — official numeric codes.
DISCHARGE_REASON_CODES: Dict[str, str] = {
    "1": "Expired",
    "2": "Revoked",
    "3": "No longer terminally ill",
    "4": "Moved out of hospice service area",
    "5": "Transferred to another hospice",
    "6": "Discharged for cause",
}

# Granular, operational discharge reasons staff actually pick day-to-day, each
# mapped to the CMS HOPE A2115 code it reports as. This is what the finalize
# dropdown shows; DISCHARGE_REASON_CODES remains the source of truth for the
# official CMS code/label recorded on the HOPE Discharge record.
GRANULAR_DISCHARGE_REASONS: Dict[str, Dict[str, str]] = {
    "death": {"label": "Death", "cms_code": "1"},
    "revocation_of_hospice": {"label": "Revocation of Hospice", "cms_code": "2"},
    "patient_refused_service": {"label": "Patient Refused Service", "cms_code": "2"},
    "declined_further_services": {"label": "Declined Further Services", "cms_code": "2"},
    "status_improved": {"label": "Status Improved", "cms_code": "3"},
    "symptoms_managed": {"label": "Symptoms Managed", "cms_code": "3"},
    "prognosis_extended": {"label": "Prognosis Extended", "cms_code": "3"},
    "patient_transfer_to_rehab": {"label": "Patient Transfer to Rehab/Outpatient Rehab Facility", "cms_code": "3"},
    "transferred_to_homehealth_within_agency": {"label": "Transferred to Homehealth within Agency", "cms_code": "3"},
    "transferred_to_palliative_care_within_agency": {"label": "Transferred to Palliative Care within Agency", "cms_code": "3"},
    "moved_out_of_area": {"label": "Moved Out of Area", "cms_code": "4"},
    "transferred_to_another_hospice": {"label": "Transferred to Another Hospice", "cms_code": "5"},
    "administrative_discharge": {"label": "Administrative Discharge", "cms_code": "6"},
    "change_in_payer": {"label": "Change in Payer", "cms_code": "6"},
    "discharged_with_cause": {"label": "Discharged with Cause", "cms_code": "6"},
    "discharged_f2f_not_done_timely": {"label": "Discharged Due to Face to Face Not Done Timely", "cms_code": "6"},
    "hospitalized": {"label": "Hospitalized", "cms_code": "6"},
    "no_longer_able_to_meet_needs": {"label": "No Longer Able to Meet Pt/Family/PCG Needs", "cms_code": "6"},
    "non_compliant_with_treatment": {"label": "Non-Compliant with Treatment/POC", "cms_code": "6"},
    "patient_goals_not_met": {"label": "Patient Goals Not Met", "cms_code": "6"},
    "transfer_to_non_contracted_snf_or_hospital": {"label": "Transfer to Non-Contracted SNF or Hospital", "cms_code": "6"},
    "unsafe_environment_for_staff": {"label": "Unsafe Environment for Staff", "cms_code": "6"},
}


class DischargePlanningUpdate(BaseModel):
    discharge_projected_date: Optional[datetime] = None
    discharge_comments: Optional[str] = None
    discharge_plan_reviewed: Optional[bool] = None
    discharge_notified: Optional[bool] = None
    discharge_explained: Optional[bool] = None
    discharge_readmission_explained: Optional[bool] = None
    discharge_medication_instruction: Optional[bool] = None
    discharge_contact_provided: Optional[bool] = None
    discharge_referral_provided: Optional[bool] = None


class DischargeFinalizeRequest(BaseModel):
    discharge_date: date
    reason_code: str = Field(
        ...,
        description="Granular discharge reason key (see GRANULAR_DISCHARGE_REASONS); mapped internally to a CMS A2115 code (1-6)",
    )
    notes: Optional[str] = None


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


def _serialize_discharge_state(patient_row, admission_row) -> Dict[str, Any]:
    return {
        "patient_status": patient_row["status"],
        "admission_id": str(admission_row["id"]) if admission_row else None,
        "admission_status": admission_row["status"] if admission_row else None,
        "discharged": patient_row["status"] == "DISCHARGED",
        "discharge_date": patient_row["discharge_date"].isoformat() if patient_row["discharge_date"] else None,
        "discharge_reason": patient_row["discharge_reason"],
        "discharge_initiated_by": patient_row["discharge_initiated_by"],
        "discharge_projected_date": patient_row["discharge_projected_date"].isoformat() if patient_row["discharge_projected_date"] else None,
        "discharge_comments": patient_row["discharge_comments"],
        "checklist": {
            "plan_reviewed": patient_row["discharge_plan_reviewed"],
            "notified": patient_row["discharge_notified"],
            "explained": patient_row["discharge_explained"],
            "readmission_explained": patient_row["discharge_readmission_explained"],
            "medication_instruction": patient_row["discharge_medication_instruction"],
            "contact_provided": patient_row["discharge_contact_provided"],
            "referral_provided": patient_row["discharge_referral_provided"],
        },
        "reason_codes": {key: v["label"] for key, v in GRANULAR_DISCHARGE_REASONS.items()},
    }


@router.get("/{patient_id}/discharge")
def get_discharge_planning(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    tenant_id = current_user.tenant_id

    patient_row = (
        db.execute(
            text(
                """
                SELECT status, discharge_date, discharge_reason, discharge_initiated_by,
                       discharge_projected_date, discharge_comments, discharge_plan_reviewed,
                       discharge_notified, discharge_explained, discharge_readmission_explained,
                       discharge_medication_instruction, discharge_contact_provided,
                       discharge_referral_provided
                FROM patients
                WHERE id = :pid AND tenant_id = :tenant_id
                """
            ),
            {"pid": patient_id, "tenant_id": tenant_id},
        )
        .mappings()
        .first()
    )

    if not patient_row:
        raise HTTPException(status_code=404, detail="Patient not found")

    admission_row = (
        db.execute(
            text(
                """
                SELECT id, status
                FROM admissions
                WHERE patient_id = :pid AND tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"pid": patient_id, "tenant_id": tenant_id},
        )
        .mappings()
        .first()
    )

    return {
        "patient_id": patient_id,
        **_serialize_discharge_state(patient_row, admission_row),
    }


@router.put("/{patient_id}/discharge")
def update_discharge_planning(
    patient_id: str,
    payload: DischargePlanningUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    tenant_id = current_user.tenant_id

    patient_row = (
        db.execute(
            text("SELECT status FROM patients WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": patient_id, "tenant_id": tenant_id},
        )
        .mappings()
        .first()
    )

    if not patient_row:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient_row["status"] == "DISCHARGED":
        raise HTTPException(
            status_code=409,
            detail="Patient is already discharged; discharge planning checklist is locked.",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail="No discharge planning fields supplied.")

    set_clauses = ", ".join(f"{field} = :{field}" for field in data)
    params = {**data, "pid": patient_id, "tenant_id": tenant_id}

    db.execute(
        text(f"UPDATE patients SET {set_clauses} WHERE id = :pid AND tenant_id = :tenant_id"),
        params,
    )

    audit = AuditLog()
    audit.tenant_id = tenant_id
    audit.user_id = current_user.id
    audit.action = "DISCHARGE_PLANNING_UPDATED"
    audit.entity_type = "PATIENT"
    audit.entity_id = patient_id
    audit.created_at = datetime.now(timezone.utc)
    audit.details = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in data.items()}
    audit.changes = audit.details
    db.add(audit)
    db.commit()

    return get_discharge_planning(patient_id, db, current_user)


@router.post("/{patient_id}/discharge/finalize", status_code=status.HTTP_200_OK)
def finalize_patient_discharge(
    patient_id: str,
    payload: DischargeFinalizeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    granular_reason = GRANULAR_DISCHARGE_REASONS.get(payload.reason_code)
    if granular_reason is None:
        raise HTTPException(
            status_code=422,
            detail=f"reason_code must be one of {sorted(GRANULAR_DISCHARGE_REASONS.keys())}",
        )
    cms_code = granular_reason["cms_code"]

    tenant_id = current_user.tenant_id
    user_id = current_user.id

    try:
        with db.begin():
            patient_row = (
                db.execute(
                    text("SELECT status FROM patients WHERE id = :pid AND tenant_id = :tenant_id"),
                    {"pid": patient_id, "tenant_id": tenant_id},
                )
                .mappings()
                .first()
            )

            if not patient_row:
                raise HTTPException(status_code=404, detail="Patient not found")

            if patient_row["status"] == "DISCHARGED":
                raise HTTPException(status_code=409, detail="Patient is already discharged.")

            admission_row = (
                db.execute(
                    text(
                        """
                        SELECT id, status
                        FROM admissions
                        WHERE patient_id = :pid AND tenant_id = :tenant_id
                          AND status = 'ACTIVE'
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"pid": patient_id, "tenant_id": tenant_id},
                )
                .mappings()
                .first()
            )

            if not admission_row:
                raise HTTPException(
                    status_code=409,
                    detail="No active admission found to discharge.",
                )

            reason_label = f"{cms_code} - {DISCHARGE_REASON_CODES[cms_code]} — {granular_reason['label']}"
            discharged_at = datetime.combine(payload.discharge_date, datetime.min.time()).replace(tzinfo=timezone.utc)

            db.execute(
                text(
                    """
                    UPDATE admissions
                    SET status = 'DISCHARGED',
                        discharged_at = :discharged_at,
                        discharge_reason = :reason
                    WHERE id = :admission_id
                      AND patient_id = :pid
                      AND tenant_id = :tenant_id
                    """
                ),
                {
                    "discharged_at": discharged_at,
                    "reason": reason_label,
                    "admission_id": admission_row["id"],
                    "pid": patient_id,
                    "tenant_id": tenant_id,
                },
            )

            db.execute(
                text(
                    """
                    UPDATE patients
                    SET status = 'DISCHARGED',
                        discharge_date = :discharge_date,
                        discharge_reason = :reason,
                        discharge_initiated_by = :user_id,
                        discharge_comments = COALESCE(:notes, discharge_comments)
                    WHERE id = :pid
                      AND tenant_id = :tenant_id
                    """
                ),
                {
                    "discharge_date": payload.discharge_date,
                    "reason": reason_label,
                    "user_id": str(user_id),
                    "notes": payload.notes,
                    "pid": patient_id,
                    "tenant_id": tenant_id,
                },
            )

            audit = AuditLog()
            audit.tenant_id = tenant_id
            audit.user_id = user_id
            audit.action = "PATIENT_DISCHARGED"
            audit.entity_type = "PATIENT"
            audit.entity_id = patient_id
            audit.created_at = datetime.now(timezone.utc)
            audit.details = {
                "admission_id": str(admission_row["id"]),
                "discharge_date": payload.discharge_date.isoformat(),
                "reason_code": payload.reason_code,
                "cms_a2115_code": cms_code,
                "reason_label": reason_label,
            }
            audit.changes = audit.details
            db.add(audit)

        return {
            "patient_id": patient_id,
            "admission_id": str(admission_row["id"]),
            "status": "DISCHARGED",
            "discharge_date": payload.discharge_date.isoformat(),
            "discharge_reason": reason_label,
        }

    except HTTPException:
        raise
    except Exception:
        raise