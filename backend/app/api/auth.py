from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ✅ ✅ ✅ PLACE IT RIGHT HERE (TOP-LEVEL CONSTANT)
# =========================================================
# TENANT REGISTRY (CONTROL LAYER)
# =========================================================

TENANT_REGISTRY = {
    "01271980-0000-0000-0000-000005101977": {
        "legal_name": "LOVE AND FAITH HOSPICE",
        "display_name": "Love and Faith Hospice",
        "npi": "1275143653",
        "ein": "851033525",
        "ccn": "B51771",
        "entity_id": "4583772",
    },
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": {
        "legal_name": "Angela Hospice",
        "display_name": "Angela Hospice",
        "npi": "1111111111",
    },
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": {
        "legal_name": "Silva Hospice",
        "display_name": "Silva Hospice",
        "npi": "2222222222",
    },
}

# =========================================================
# REQUEST MODEL
# =========================================================

class DevLoginRequest(BaseModel):
    user_id: str
    role: str
    tenant_id: Optional[uuid.UUID] = None


# =========================================================
# HELPERS
# =========================================================

def _ensure_dev_only() -> None:
    env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    if env not in {"development", "dev", "local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="dev-login is disabled outside development environments",
        )


def _is_truthy(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _dev_email(user_id: str, tenant_id: Optional[uuid.UUID]) -> str:
    suffix = str(tenant_id)[:8] if tenant_id else "system"
    return f"{user_id}+{suffix}@sns.dev".lower()


def _safe_ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return f'"{name}"'


def _deterministic_dev_npi(tenant_id: uuid.UUID) -> str:
    return str(tenant_id.int % 10**10).zfill(10)


# =========================================================
# TENANT CHECK (SINGLE SOURCE OF TRUTH)
# =========================================================

def _public_tenant_exists(db: Session, tenant_id: uuid.UUID) -> bool:
    try:
        result = db.execute(
            text("""
                SELECT 1 FROM public.tenants
                WHERE id = :tid
                LIMIT 1
            """),
            {"tid": tenant_id},
        ).scalar()

        return bool(result)

    except Exception:
        db.rollback()
        logger.exception("public.tenants lookup failed")
        raise


def _ensure_public_tenant_for_dev(db: Session, tenant_id: uuid.UUID) -> None:
    if _public_tenant_exists(db, tenant_id):
        return

    tenant_key = str(tenant_id)

    if tenant_key not in TENANT_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant {tenant_key} not registered",
        )

    t = TENANT_REGISTRY[tenant_key]

    db.execute(
        text("""
            INSERT INTO public.tenants (
                id,
                legal_name,
                display_name,
                npi,
                status
            )
            VALUES (
                :id,
                :legal_name,
                :display_name,
                :npi,
                'ACTIVE'
            )
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": tenant_key,
            "legal_name": t["legal_name"],
            "display_name": t["display_name"],
            "npi": t["npi"],
        },
    )

    db.commit()   # temporary debug-proof commit

# =========================================================
# ENDPOINT
# =========================================================

@router.post("/dev-login")
def dev_login(
    payload: DevLoginRequest = Body(...),
    db: Session = Depends(get_db),
):
    _ensure_dev_only()

    # ✅ ALWAYS CLEAN START
    db.rollback()

    role = payload.role.strip().upper()

    if not role:
        raise HTTPException(status_code=422, detail="role is required")

    is_system = role in {"OWNER", "BILLING"}

    if not is_system and not payload.tenant_id:
        raise HTTPException(status_code=422, detail="tenant_id required")

    # =====================================================
    # TENANT VALIDATION
    # =====================================================

    if payload.tenant_id:
        try:
            db.rollback()

            exists = _public_tenant_exists(db, payload.tenant_id)

            logger.info(
                "Tenant check tenant_id=%s exists=%s",
                payload.tenant_id,
                exists,
            )

            if not exists:
                db.rollback()
                _ensure_public_tenant_for_dev(db, payload.tenant_id)

        except Exception as exc:
            db.rollback()
            logger.exception("Tenant validation failed")
            raise HTTPException(
                status_code=500,
                detail=f"Tenant validation failed: {exc}",
            )

    # =====================================================
    # USER UPSERT
    # =====================================================

    user_uuid = uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{payload.tenant_id}:{payload.user_id}:{role}",
    )

    email = _dev_email(payload.user_id, payload.tenant_id)

    try:
        db.execute(
            text("""
                INSERT INTO public.users (
                    id,
                    tenant_id,
                    full_name,
                    email,
                    role,
                    access_level,
                    active,
                    created_at,
                    updated_at
                )
                VALUES (
                :uid,
                :tid,
                :name,
                :email,
                :role,
                'FULL_ACCESS',
                true,
                NOW(),
                NOW()
            )
            ON CONFLICT (tenant_id, email) DO UPDATE
            SET
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                updated_at = NOW()
        """),
        {
            "uid": user_uuid,
            "tid": payload.tenant_id,
            "name": payload.user_id,
            "email": email,
            "role": role,
        },
    )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("User upsert failed")
        raise

    token = create_access_token(
        user_id=user_uuid,
        role=role,
        tenant_id=payload.tenant_id,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
    }