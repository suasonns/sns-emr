from __future__ import annotations

import os
import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

ADMIN_EMAIL = "rsuason@loveandfaithhospice.com"
MIN_PASSWORD_LENGTH = 12


def bootstrap_production_admin(db: Session) -> bool:
    password = os.getenv("ADMIN_PASSWORD")
    tenant_id_raw = os.getenv("DEV_TENANT_REAL_ID")

    if not password:
        return False
    if not tenant_id_raw:
        raise RuntimeError("DEV_TENANT_REAL_ID is required when ADMIN_PASSWORD is set")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise RuntimeError(f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters")

    tenant_id = uuid.UUID(tenant_id_raw)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(id=tenant_id)
        db.add(tenant)

    tenant.legal_name = "Love & Faith Hospice"
    tenant.display_name = "Love & Faith"
    tenant.npi = "1275143653"
    tenant.ein = "851033525"
    tenant.ptan = "B51771"
    tenant.tenant_type = "PRODUCTION"
    tenant.environment_tag = "PERMANENT"
    tenant.status = "ACTIVE"
    tenant.ai_enabled = True
    tenant.billing_enabled = True

    user = (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.email == ADMIN_EMAIL)
        .one_or_none()
    )
    if user is None:
        user = User(id=uuid.uuid4(), tenant_id=tenant_id, email=ADMIN_EMAIL)
        db.add(user)

    user.full_name = "Romel Suason"
    user.role = "ADMINISTRATOR"
    user.access_level = "FULL_ACCESS"
    user.active = True
    user.password_hash = hash_password(password)

    db.commit()
    return True