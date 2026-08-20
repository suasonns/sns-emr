from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

MIN_PASSWORD_LENGTH = 12

DEV_TENANT_ID_ENV = "DEV_TENANT_ID"
DEV_PLATFORM_TENANT_ID_ENV = "DEV_PLATFORM_TENANT_ID"


@dataclass(frozen=True)
class DevelopmentIdentity:
    email_env: str
    password_env: str
    tenant_env: str
    full_name: str
    role: str


DEVELOPMENT_IDENTITIES = (
    DevelopmentIdentity(
        email_env="DEV_DPCS_ADMIN_EMAIL",
        password_env="DEV_DPCS_ADMIN_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development DPCS Administrator",
        role="DPCS_ADMINISTRATOR",
    ),
    DevelopmentIdentity(
        email_env="DEV_PLATFORM_OWNER_EMAIL",
        password_env="DEV_PLATFORM_OWNER_PASSWORD",
        tenant_env=DEV_PLATFORM_TENANT_ID_ENV,
        full_name="Development Platform Owner",
        role="OWNER",
    ),
    DevelopmentIdentity(
        email_env="DEV_BILLING_EMAIL",
        password_env="DEV_BILLING_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development Billing",
        role="BILLING",
    ),
)


def _configured_uuid(env_name: str) -> uuid.UUID:
    value = os.getenv(env_name)
    if not value:
        raise RuntimeError(f"{env_name} is required when a related development identity is configured")
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise RuntimeError(f"{env_name} must be a valid UUID") from exc


def _ensure_tenant(db: Session, tenant_id: uuid.UUID, *, platform: bool) -> None:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            legal_name="SNS Development Platform" if platform else "SNS Development Agency",
            display_name="Development Platform" if platform else "Development Agency",
            npi="0000000000",
            ein=None if platform else "000000000",
            ptan=None if platform else "DEVELOPMENT",
            tenant_type="DEV",
            environment_tag="DEVELOPMENT",
            status="ACTIVE",
            ai_enabled=True,
            billing_enabled=not platform,
        )
        db.add(tenant)
        db.flush()
        return

    tenant.status = "ACTIVE"
    tenant.ai_enabled = True
    if platform:
        tenant.billing_enabled = False


def provision_development_logins(db: Session) -> int:
    """Create/update configured development identities without implicit secrets."""
    provisioned = 0

    for identity in DEVELOPMENT_IDENTITIES:
        email = (os.getenv(identity.email_env) or "").strip().lower()
        password = os.getenv(identity.password_env)

        if not email and not password:
            continue
        if not email:
            raise RuntimeError(f"{identity.email_env} is required when {identity.password_env} is configured")
        if password is not None and len(password) < MIN_PASSWORD_LENGTH:
            raise RuntimeError(
                f"{identity.password_env} must be at least {MIN_PASSWORD_LENGTH} characters"
            )

        tenant_id = _configured_uuid(identity.tenant_env)
        user = (
            db.query(User)
            .filter(func.lower(User.email) == email)
            .one_or_none()
        )
        if user is None and password is None:
            continue

        _ensure_tenant(
            db,
            tenant_id,
            platform=identity.tenant_env == DEV_PLATFORM_TENANT_ID_ENV,
        )

        if user is None:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=email,
                full_name=identity.full_name,
                role=identity.role,
                access_level="FULL_ACCESS",
                active=True,
            )
            db.add(user)
        else:
            user.tenant_id = tenant_id
            user.email = email
            user.full_name = identity.full_name
            user.role = identity.role
            user.access_level = "FULL_ACCESS"
            user.active = True

        if password is not None:
            user.password_hash = hash_password(password)

        provisioned += 1

    if provisioned:
        db.commit()
    return provisioned
