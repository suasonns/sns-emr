# api/owner_admin.py
#
# Platform-owner-only tenant onboarding. Lets the OWNER (platform/vendor
# super-user) add new hospice agency tenants and their initial
# administrator account, without ever touching an existing tenant's
# clinical/patient data.

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_guards import require_owner
from app.core.security import CurrentUser, get_current_user, hash_password
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/api/owner", tags=["Owner"])

MIN_PASSWORD_LENGTH = 12

# Roles that may be assigned as the initial admin for a newly onboarded
# tenant. Never OWNER (platform-only) or BILLING (assigned separately).
INITIAL_ADMIN_ROLES = {"DPCS_ADMINISTRATOR", "ADMINISTRATOR", "DPCS"}


class CreateTenantRequest(BaseModel):
    legal_name: str = Field(min_length=2, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    npi: str = Field(min_length=10, max_length=10)
    ein: str | None = Field(default=None, min_length=9, max_length=9)
    ptan: str | None = Field(default=None, max_length=32)
    tenant_type: str = Field(default="TRAINING")

    admin_email: EmailStr
    admin_full_name: str = Field(min_length=2, max_length=200)
    admin_password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    admin_role: str = Field(default="DPCS_ADMINISTRATOR")

    @field_validator("npi")
    @classmethod
    def _npi_digits(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("NPI must be exactly 10 digits")
        return value

    @field_validator("ein")
    @classmethod
    def _ein_digits(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("EIN must be exactly 9 digits")
        return value

    @field_validator("tenant_type")
    @classmethod
    def _tenant_type_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"PRODUCTION", "TRAINING", "DEV"}:
            raise ValueError("tenant_type must be PRODUCTION, TRAINING, or DEV")
        return value

    @field_validator("admin_role")
    @classmethod
    def _admin_role_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in INITIAL_ADMIN_ROLES:
            raise ValueError(f"admin_role must be one of {sorted(INITIAL_ADMIN_ROLES)}")
        return value


def _require_platform_owner(user: CurrentUser) -> None:
    """Explicit platform-owner check; do not rely on clinical-admin fallback."""
    require_owner(user)


@router.get("/tenants")
def list_tenants(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)

    rows = (
        db.execute(
            text(
                """
                SELECT
                    t.id::text AS tenant_id,
                    t.legal_name,
                    COALESCE(t.display_name, t.legal_name) AS display_name,
                    t.tenant_type,
                    t.status,
                    t.ai_enabled,
                    t.billing_enabled,
                    t.created_at,
                    (SELECT COUNT(*) FROM users u WHERE u.tenant_id = t.id) AS user_count,
                    (SELECT COUNT(*) FROM patients p WHERE p.tenant_id = t.id) AS patient_count
                FROM tenants t
                ORDER BY t.created_at DESC
                """
            )
        )
        .mappings()
        .all()
    )

    return {"tenants": [dict(row) for row in rows]}


@router.post("/tenants", status_code=201)
def create_tenant(
    payload: CreateTenantRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)

    existing = db.query(Tenant).filter(Tenant.legal_name == payload.legal_name).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A tenant with this legal name already exists")

    existing_user = db.query(User).filter(User.email == payload.admin_email).one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    tenant = Tenant(
        id=uuid.uuid4(),
        legal_name=payload.legal_name,
        display_name=payload.display_name or payload.legal_name,
        npi=payload.npi,
        ein=payload.ein,
        ptan=payload.ptan,
        tenant_type=payload.tenant_type,
        status="ACTIVE",
        ai_enabled=True,
        # Billing requires ein+ptan on file (see Tenant CHECK constraint);
        # only turn it on automatically when both were actually supplied.
        billing_enabled=bool(payload.ein and payload.ptan),
        created_by=getattr(user, "user_id", None) or getattr(user, "id", None),
    )
    db.add(tenant)
    db.flush()

    admin_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=payload.admin_email,
        full_name=payload.admin_full_name,
        role=payload.admin_role,
        access_level="FULL_ACCESS",
        active=True,
        password_hash=hash_password(payload.admin_password),
    )
    db.add(admin_user)

    db.commit()
    db.refresh(tenant)
    db.refresh(admin_user)

    return {
        "tenant_id": str(tenant.id),
        "legal_name": tenant.legal_name,
        "display_name": tenant.display_name,
        "billing_enabled": tenant.billing_enabled,
        "admin_user": {
            "id": str(admin_user.id),
            "email": admin_user.email,
            "role": admin_user.role,
        },
    }
