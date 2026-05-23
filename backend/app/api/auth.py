from __future__ import annotations

import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class DevLoginRequest(BaseModel):
    user_id: str = Field(..., description="Developer user identifier")
    role: str = Field(..., description="Role (ADMIN, RN, MD, etc)")
    tenant_id: uuid.UUID = Field(..., description="Tenant UUID (required)")


def _ensure_dev_only() -> None:
    env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    if env not in {"development", "dev", "local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="dev-login is disabled outside development environments",
        )


@router.post("/dev-login", summary="Dev Login (tenant required)")
def dev_login(
    db: Session = Depends(get_db),
    payload: DevLoginRequest = Body(...),
):
    """
    DEV LOGIN — enterprise-safe identity provisioning

    Guarantees:
    - No tenant table mutation
    - Valid users row exists for FK(created_by) integrity
    - Deterministic UUID per tenant + user_id
    """

    _ensure_dev_only()

    # 1) Verify tenant exists (read-only)
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
    role_norm = (payload.role or "").strip().upper()
    if not role_norm:
        raise HTTPException(status_code=400, detail="role is required")

    # 3) Deterministic dev user UUID
    dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{payload.tenant_id}:{payload.user_id}")

    # 4) Ensure users row exists (satisfy NOT NULL constraints)
    #    Based on observed DB errors, users requires: email (NOT NULL), role (NOT NULL), created_at (NOT NULL).
    #    We also set updated_at to avoid the next likely NOT NULL failure.
    try:
        db.execute(
            text(
                """
                INSERT INTO public.users (
                    id,
                    tenant_id,
                    full_name,
                    email,
                    role,
                    created_at,
                    updated_at
                )
                VALUES (
                    :uid,
                    :tid,
                    :full_name,
                    :email,
                    :role,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (id) DO UPDATE
                SET
                    tenant_id = EXCLUDED.tenant_id,
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    role = EXCLUDED.role,
                    updated_at = NOW()
                """
            ),
            {
                "uid": str(dev_user_uuid),
                "tid": str(payload.tenant_id),
                "full_name": f"{payload.user_id} (DEV)",
                "email": "rsuason@sns.com",
                "role": role_norm,
            },
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("Dev user upsert failed")
        raise HTTPException(status_code=500, detail=f"Dev user upsert failed: {e}")

    # 5) Issue access token
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