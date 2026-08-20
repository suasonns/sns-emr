from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.names import format_person_name
from app.core.roles import access_scope_for_role
from app.core.security import create_access_token, hash_password, verify_password_hash
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


def _user_payload(user: User, tenant: Tenant | None = None) -> dict[str, object]:
    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": str(user.role),
        "email": user.email,
        "full_name": format_person_name(user, user.email),
        "tenant_name": getattr(tenant, "display_name", None) or getattr(tenant, "legal_name", None),
        "ai_enabled": bool(getattr(tenant, "ai_enabled", False)),
        "billing_enabled": bool(getattr(tenant, "billing_enabled", False)),
        "access_scope": access_scope_for_role(user.role),
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(func.lower(User.email) == payload.email.lower())
        .first()
    )

    if user is None or not getattr(user, "active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tenant = db.get(Tenant, user.tenant_id)

    password_hash = getattr(user, "password_hash", None)
    if not password_hash or not verify_password_hash(payload.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        user_id=user.id,
        role=str(user.role),
        tenant_id=user.tenant_id,
        email=user.email,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_payload(user, tenant),
    }


@router.get("/me")
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, current_user.id)
    if user is None or not getattr(user, "active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    tenant = db.get(Tenant, user.tenant_id)
    return _user_payload(user, tenant)


@router.post("/reset-password")
def reset_password():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Public password reset is disabled. Contact an administrator; "
            "authenticated users may use /auth/change-password."
        ),
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.password_hash or not verify_password_hash(
        payload.current_password, user.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.password_hash = hash_password(payload.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "ok"}
