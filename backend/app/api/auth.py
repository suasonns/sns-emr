# app/api/auth.py

from __future__ import annotations

import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# ROUTER (MUST COME BEFORE DECORATORS)
# ---------------------------------------------------------
router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------
# DEV LOGIN SCHEMA
# ---------------------------------------------------------
class DevLoginRequest(BaseModel):
    user_id: str = Field(..., description="Developer user identifier")
    role: str = Field(..., description="Role (ADMIN, RN, MD, etc)")
    tenant_id: uuid.UUID = Field(..., description="Tenant UUID (required)")


# ---------------------------------------------------------
# DEV‑ONLY GUARD
# ---------------------------------------------------------
def _ensure_dev_only() -> None:
    env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    if env not in {"development", "dev", "local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="dev-login is disabled outside development environments",
        )


# ---------------------------------------------------------
# DEV LOGIN ENDPOINT
# ---------------------------------------------------------
@router.post("/dev-login", summary="Dev Login (tenant required)")
def dev_login(
    db: Session = Depends(get_db),
    payload: DevLoginRequest = Body(...),
):
    """
    DEV LOGIN — stable, explicit, enterprise-safe

    Solves ONLY identity + tenant context.
    """

    _ensure_dev_only()

    # 1) Verify tenant exists (SQL-only)
    try:
        tenant_exists = db.execute(
            text("SELECT 1 FROM public.tenants WHERE id = :tid"),
            {"tid": str(payload.tenant_id)},
        ).scalar()
    except Exception as e:
        logger.exception("Tenant lookup failed")
        raise HTTPException(status_code=500, detail=f"Tenant lookup failed: {e}")

    if not tenant_exists:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 2) Normalize role
    role_norm = payload.role.strip().upper()
    if not role_norm:
        raise HTTPException(status_code=400, detail="role is required")

    # 3) Deterministic dev subject UUID
    dev_user_uuid = uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{payload.tenant_id}:{payload.user_id}",
    )

    # 4) Create token (MATCHES create_access_token SIGNATURE)
    try:
        access_token = create_access_token(
            subject=str(dev_user_uuid),
            role=role_norm,
            tenant_id=str(payload.tenant_id),
        )
    except Exception as e:
        logger.exception("Token creation failed")
        raise HTTPException(status_code=500, detail=f"Token creation failed: {e}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": str(payload.tenant_id),
        "user_id": payload.user_id,
        "role": role_norm,
    }