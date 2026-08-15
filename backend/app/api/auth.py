from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# =========================================================
# REQUEST MODEL
# =========================================================

class LoginRequest(BaseModel):
    email: str
    role: Optional[str] = None


# =========================================================
# HELPERS
# =========================================================

def _get_active_user(
    db: Session,
    *,
    email: str,
):
    row = db.execute(
        text(
            """
            SELECT
                id,
                tenant_id,
                email,
                role,
                active
            FROM public.users
            WHERE lower(email) = lower(:email)
            LIMIT 1
            """
        ),
        {"email": email},
    ).mappings().first()

    if not row:
        return None
    if not row["active"]:
        return None

    return row


def _is_active_tenant(
    db: Session,
    *,
    tenant_id: uuid.UUID,
) -> bool:
    result = db.execute(
        text(
            """
            SELECT 1
            FROM public.tenants
            WHERE id = :tenant_id
              AND status = 'ACTIVE'
            LIMIT 1
            """
        ),
        {"tenant_id": str(tenant_id)},
    ).scalar()

    return bool(result)


def _write_auth_audit_log(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    email: str,
    role: str,
    success: bool,
    request: Request,
    failure_reason: str | None = None,
) -> None:
    try:
        db.execute(
            text(
                """
                INSERT INTO public.audit_logs (
                    id,
                    tenant_id,
                    user_id,
                    role,
                    action,
                    entity_type,
                    entity_id,
                    description,
                    metadata,
                    ip_address,
                    request_id,
                    created_by,
                    created_at
                )
                VALUES (
                    :id,
                    :tenant_id,
                    :user_id,
                    :role,
                    'LOGIN',
                    'auth',
                    NULL,
                    :description,
                    CAST(:metadata AS jsonb),
                    :ip_address,
                    :request_id,
                    :created_by,
                    NOW()
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "role": role,
                "description": "User login success" if success else "User login failed",
                "metadata": json.dumps(
                    {
                        "email": email,
                        "role": role,
                        "success": success,
                        "failure_reason": failure_reason,
                    }
                ),
                "ip_address": request.client.host if request.client else None,
                "request_id": str(uuid.uuid4()),
                "created_by": str(user_id),
            },
        )
    except Exception:
        logger.exception("auth audit log write failed")


# =========================================================
# ENDPOINTS
# =========================================================

@router.post("/login")
def login(
    request: Request,
    payload: LoginRequest = Body(...),
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email is required",
        )

    try:
        db.rollback()

        user = _get_active_user(
            db,
            email=email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = uuid.UUID(str(user["id"]))
        tenant_id = uuid.UUID(str(user["tenant_id"]))
        db_role = str(user["role"]).strip().upper()

        if payload.role:
            requested_role = payload.role.strip().upper()

            if requested_role != db_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="role mismatch",
                )

        if not _is_active_tenant(
            db,
            tenant_id=tenant_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="inactive tenant",
            )

        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role=db_role,
            email=email,
        )

        _write_auth_audit_log(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            role=db_role,
            success=True,
            request=request,
        )

        db.commit()

        logger.info(
            "LOGIN success tenant_id=%s user_id=%s email=%s role=%s",
            tenant_id,
            user_id,
            email,
            db_role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "role": db_role,
            "email": email,
        }

    except HTTPException as exc:
        db.rollback()

        try:
            user = _get_active_user(
                db,
                email=email,
            )

            if user:
                _write_auth_audit_log(
                    db,
                    tenant_id=uuid.UUID(str(user["tenant_id"])),
                    user_id=uuid.UUID(str(user["id"])),
                    email=email,
                    role=str(user["role"]).strip().upper(),
                    success=False,
                    failure_reason=exc.detail if isinstance(exc.detail, str) else "auth failure",
                    request=request,
                )
                db.commit()

        except Exception:
            db.rollback()

        raise

    except Exception:
        db.rollback()
        logger.exception("login failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="authentication failed",
        )