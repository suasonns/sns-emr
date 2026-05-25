import os
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.security import get_current_user
from app.services.audit_logger import log_event
from app.tenancy.registry import (
    assert_known_tenant,
    assert_training_or_legacy_tenant,
    TENANT_REAL,
)


router = APIRouter(prefix="/internal/training", tags=["internal-training"])


def _ensure_dev_env():
    env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    if env not in {"development", "dev", "local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Training endpoints are disabled outside development environments",
        )


def _require_admin(user):
    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    role = str(role or "").upper()
    if role not in {"ADMIN", "SUPER_USER"}:
        raise HTTPException(status_code=403, detail="Forbidden")


def _tenant_id_from_user(user) -> str:
    tid = user.get("tenant_id") if isinstance(user, dict) else getattr(user, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=401, detail="Missing tenant context")
    return str(tid)


class DeletePatientRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Why this patient is being removed")


class ResetPatientsRequest(BaseModel):
    tenant_id: UUID
    reason: str = Field(..., min_length=3)
    confirm: str = Field(..., description="Must equal RESET_ALL_TRAINING_DATA")


@router.post("/patients/{patient_id}/delete", status_code=status.HTTP_200_OK)
def delete_patient_dev(
    patient_id: UUID,
    payload: DeletePatientRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    DEV ONLY: Delete a single patient (hard delete) with explicit reason + audit log.
    Allowed for all known tenants in DEV.
    """
    _ensure_dev_env()
    _require_admin(user)

    tenant_id = _tenant_id_from_user(user)
    assert_known_tenant(tenant_id)

    # Hard delete patient scoped to tenant_id (prevents cross-tenant deletion)
    result = db.execute(
        text("DELETE FROM public.patients WHERE id = :pid AND tenant_id = :tid"),
        {"pid": str(patient_id), "tid": tenant_id},
    )
    db.commit()

    deleted_count = result.rowcount or 0

    log_event(
        user_id=str(user.get("id") if isinstance(user, dict) else getattr(user, "id", None)),
        role=str(user.get("role") if isinstance(user, dict) else getattr(user, "role", "")).upper(),
        action="DEV_PATIENT_DELETE",
        entity_type="PATIENT",
        entity_id=str(patient_id),
        db=db,
    )

    return {
        "deleted": deleted_count,
        "patient_id": str(patient_id),
        "tenant_id": tenant_id,
        "reason": payload.reason,
        "at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/reset-patients", status_code=status.HTTP_200_OK)
def reset_patients_training_tenant(
    payload: ResetPatientsRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    DEV ONLY: Bulk reset patients for TRAINING + LEGACY tenants only.
    Requires explicit confirmation phrase and audit log.
    """
    _ensure_dev_env()
    _require_admin(user)

    # Guard: target tenant must be known and training/legacy
    target_tenant = str(payload.tenant_id)
    assert_known_tenant(target_tenant)
    assert_training_or_legacy_tenant(target_tenant)

    # Prevent bulk reset for Love & Faith (reduces catastrophic wipe risk)
    if target_tenant == TENANT_REAL:
        raise HTTPException(
            status_code=403,
            detail="Bulk reset is not allowed for the real tenant",
        )

    if payload.confirm != "RESET_ALL_TRAINING_DATA":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation phrase",
        )

    # Count before
    before = db.execute(
        text("SELECT COUNT(*) FROM public.patients WHERE tenant_id = :tid"),
        {"tid": target_tenant},
    ).scalar() or 0

    # Delete scoped to tenant
    db.execute(
        text("DELETE FROM public.patients WHERE tenant_id = :tid"),
        {"tid": target_tenant},
    )
    db.commit()

    log_event(
        user_id=str(user.get("id") if isinstance(user, dict) else getattr(user, "id", None)),
        role=str(user.get("role") if isinstance(user, dict) else getattr(user, "role", "")).upper(),
        action="DEV_TENANT_PATIENT_RESET",
        entity_type="TENANT",
        entity_id=target_tenant,
        db=db,
    )

    return {
        "tenant_id": target_tenant,
        "deleted_patients": int(before),
        "reason": payload.reason,
        "at": datetime.now(timezone.utc).isoformat(),
    }