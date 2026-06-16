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
from app.core.user_session_reference import generate_user_session_reference
from app.core.user_session_reference_store import put_user_session_reference

logger = logging.getLogger(__name__)

# This router already owns the /auth prefix
router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------
# Request model
# ---------------------------
class DevLoginRequest(BaseModel):
    user_id: str = Field(..., description="Developer user identifier")
    role: str = Field(..., description="Role (TENANT staff roles, OWNER, BILLING)")
    tenant_id: Optional[uuid.UUID] = Field(
        None,
        description="Tenant UUID (required for tenant staff only)",
    )


# ---------------------------
# Guards / small helpers
# ---------------------------
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
    """
    Deterministic + unique per (tenant, user) in dev.
    """
    suffix = str(tenant_id)[:8] if tenant_id else "system"
    return f"{user_id}+{suffix}@sns.dev".lower()


def _safe_ident(name: str) -> str:
    """
    Minimal SQL identifier safety for dynamic column names read from information_schema.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return f'"{name}"'


def _deterministic_dev_npi(tenant_id: uuid.UUID) -> str:
    """
    Dev-only deterministic 10-digit numeric string.
    This is NOT a real NPI and must never be used in production.
    """
    return str(tenant_id.int % 10**10).zfill(10)


# ---------------------------
# Tenant existence / provisioning
# ---------------------------
def _public_tenant_exists(db: Session, tenant_id: uuid.UUID) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM public.tenants
            WHERE id::text = :tid
            LIMIT 1
            """
        ),
        {"tid": str(tenant_id)},
    ).scalar()
    return bool(row)


def _core_tenant_exists(db: Session, tenant_id: uuid.UUID) -> bool:
    try:
        row = db.execute(
            text(
                """
                SELECT 1
                FROM core.tenants
                WHERE id::text = :tid
                LIMIT 1
                """
            ),
            {"tid": str(tenant_id)},
        ).scalar()
        return bool(row)
    except Exception:
        # Some dev DBs may not have core.tenants or may differ in shape.
        logger.debug("core.tenants lookup skipped/unavailable", exc_info=True)
        return False


def _required_public_tenant_columns(db: Session) -> list[str]:
    """
    Returns required public.tenants columns that do not have a DB default,
    excluding identity/default-populated columns.
    """
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'tenants'
              AND is_nullable = 'NO'
              AND COALESCE(column_default, '') = ''
              AND COALESCE(is_identity, 'NO') = 'NO'
            ORDER BY ordinal_position
            """
        )
    ).fetchall()

    return [str(row[0]) for row in rows]


def _build_public_tenant_seed_values(tenant_id: uuid.UUID) -> Dict[str, Any]:
    """
    Common dev seed values for public.tenants.
    Any required column can also be supplied with:
      DEV_PUBLIC_TENANT__<COLUMN_NAME_UPPER>

    Examples:
      DEV_PUBLIC_TENANT__NPI=1234567890
      DEV_PUBLIC_TENANT__CCN=055555
      DEV_PUBLIC_TENANT__TIN=999999999
    """
    defaults: Dict[str, Any] = {
        "id": str(tenant_id),
        "legal_name": os.getenv("DEV_TENANT_LEGAL_NAME", "DEV TENANT"),
        "display_name": os.getenv("DEV_TENANT_DISPLAY_NAME", "DEV TENANT"),
        "status": os.getenv("DEV_TENANT_STATUS", "ACTIVE"),
        "npi": os.getenv("DEV_TENANT_NPI") or _deterministic_dev_npi(tenant_id),
    }

    # Allow arbitrary schema-specific overrides through env vars
    # Pattern: DEV_PUBLIC_TENANT__<COLUMN_NAME_UPPER>
    for env_name, env_value in os.environ.items():
        prefix = "DEV_PUBLIC_TENANT__"
        if env_name.startswith(prefix):
            column_name = env_name[len(prefix):].strip().lower()
            if column_name:
                defaults[column_name] = env_value

    return defaults


def _ensure_public_tenant_for_dev(db: Session, tenant_id: uuid.UUID) -> None:
    """
    Ensures the tenant row exists in public.tenants, which is the actual FK target
    for public.users.tenant_id.

    Strategy:
    - If public.tenants row exists: do nothing
    - Else, if DEV_AUTO_CREATE_PUBLIC_TENANT is false: return 404
    - Else, introspect required DB columns and insert a dev row safely
    - If required columns are missing from defaults/env, fail clearly
    """
    if _public_tenant_exists(db, tenant_id):
        return

    auto_create = _is_truthy(
        os.getenv("DEV_AUTO_CREATE_PUBLIC_TENANT"),
        default=True,
    )
    if not auto_create:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found in public.tenants",
        )

    required_columns = _required_public_tenant_columns(db)
    seed_values = _build_public_tenant_seed_values(tenant_id)

    # created_at / updated_at can be handled inline with NOW()
    sql_values: list[str] = []
    sql_columns: list[str] = []
    bind_params: Dict[str, Any] = {}
    missing_required: list[str] = []

    for column in required_columns:
        if column in {"created_at", "updated_at"}:
            sql_columns.append(_safe_ident(column))
            sql_values.append("NOW()")
            continue

        if column in seed_values:
            sql_columns.append(_safe_ident(column))
            sql_values.append(f":{column}")
            bind_params[column] = seed_values[column]
            continue

        missing_required.append(column)

    if missing_required:
        missing_env_names = [f"DEV_PUBLIC_TENANT__{col.upper()}" for col in missing_required]
        logger.error(
            "Cannot auto-create public.tenants row; missing required columns: %s",
            ", ".join(missing_required),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Cannot auto-create public.tenants row. "
                f"Missing required columns: {missing_required}. "
                f"Provide env vars such as: {missing_env_names}"
            ),
        )

    # If the schema has no required columns (unlikely), still insert id explicitly
    if not sql_columns:
        sql_columns = ['"id"']
        sql_values = [":id"]
        bind_params = {"id": str(tenant_id)}

    insert_sql = f"""
        INSERT INTO public.tenants (
            {", ".join(sql_columns)}
        )
        VALUES (
            {", ".join(sql_values)}
        )
        ON CONFLICT ("id") DO NOTHING
    """

    logger.info(
        "Auto-creating missing public.tenants row for dev tenant_id=%s",
        str(tenant_id),
    )
    db.execute(text(insert_sql), bind_params)


# ---------------------------
# Endpoint
# ---------------------------
@router.post("/dev-login", summary="Dev Login")
def dev_login(
    payload: DevLoginRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    DEV LOGIN — enterprise-safe identity provisioning.

    Identity classes:
    - TENANT staff -> tenant_id REQUIRED
    - OWNER / BILLING -> tenant_id NOT required
    """
    _ensure_dev_only()

    role_norm = (payload.role or "").strip().upper()
    if not role_norm:
        raise HTTPException(status_code=422, detail="role is required")

    is_system_role = role_norm in {"OWNER", "BILLING"}

    if not is_system_role and not payload.tenant_id:
        raise HTTPException(
            status_code=422,
            detail="tenant_id is required for tenant staff",
        )

    # Tenant staff must be backed by public.tenants because public.users.tenant_id
    # references public.tenants.id.
    if payload.tenant_id:
        try:
            core_exists = _core_tenant_exists(db, payload.tenant_id)
            public_exists = _public_tenant_exists(db, payload.tenant_id)

            logger.info(
                "Dev login tenant check tenant_id=%s core_exists=%s public_exists=%s",
                str(payload.tenant_id),
                core_exists,
                public_exists,
            )

            if not public_exists:
                _ensure_public_tenant_for_dev(db, payload.tenant_id)

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Tenant verification/provisioning failed")
            raise HTTPException(
                status_code=500,
                detail=f"Tenant verification/provisioning failed: {exc}",
            ) from exc

    tenant_part = str(payload.tenant_id) if payload.tenant_id else "SYSTEM"
    dev_user_uuid = uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{tenant_part}:{payload.user_id}:{role_norm}",
    )

    email = _dev_email(payload.user_id, payload.tenant_id)

    try:
        row = db.execute(
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
                ON CONFLICT (email) DO UPDATE
                SET
                    tenant_id = EXCLUDED.tenant_id,
                    full_name = EXCLUDED.full_name,
                    role = EXCLUDED.role,
                    updated_at = NOW()
                RETURNING id
                """
            ),
            {
                "uid": str(dev_user_uuid),
                "tid": str(payload.tenant_id) if payload.tenant_id else None,
                "full_name": f"{payload.user_id} (DEV)",
                "email": email,
                "role": role_norm,
            },
        ).fetchone()

        if row and row[0]:
            dev_user_uuid = uuid.UUID(str(row[0]))

        db.commit()

        logger.info(
            "Dev login user upsert succeeded user_id=%s email=%s role=%s tenant_id=%s",
            str(dev_user_uuid),
            email,
            role_norm,
            str(payload.tenant_id) if payload.tenant_id else None,
        )

    except Exception as exc:
        db.rollback()
        logger.exception("Dev user upsert failed")
        raise HTTPException(
            status_code=500,
            detail=f"Dev user upsert failed: {exc}",
        ) from exc

    user_session_reference = None
    if not is_system_role and payload.tenant_id:
        user_session_reference = generate_user_session_reference()
        put_user_session_reference(
            ref=user_session_reference,
            user_id=str(dev_user_uuid),
            role=role_norm,
            tenant_id=str(payload.tenant_id),
            ui_context={
                "purpose": "training_troubleshooting",
                "entrypoint": "dev-login",
            },
        )

    try:
        access_token = create_access_token(
            subject=str(dev_user_uuid),
            role=role_norm,
            tenant_id=str(payload.tenant_id) if payload.tenant_id else None,
        )
    except Exception as exc:
        logger.exception("Token creation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Token creation failed: {exc}",
        ) from exc

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": str(payload.tenant_id) if payload.tenant_id else None,
        "user_id": payload.user_id,
        "role": role_norm,
        "email": email,
        "user_session_reference": user_session_reference,
    }