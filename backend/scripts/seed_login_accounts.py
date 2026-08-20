"""
Seed or update login accounts.

Passwords are read from environment variables so they never appear in source
control or shell history files. Safe to re-run: existing users are updated in
place, and a password is only changed when its variable is provided.

Usage (PowerShell):

    $env:TENANT_ID = "01271980-0000-0000-0000-000005101977"
    $env:ADMIN_PASSWORD = Read-Host "Admin password"
    python scripts/seed_login_accounts.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402

MIN_PASSWORD_LENGTH = 12

SYSTEM_TENANT_ID = "SYSTEM_TENANT_ID"

ACCOUNTS = [
    {
        "env_var": "ADMIN_PASSWORD",
        "tenant_env_var": "DEV_TENANT_REAL_ID",
        "email": "rsuason@loveandfaithhospice.com",
        "full_name": "Romel Suason",
        "role": "OWNER",
        "access_level": "FULL_ACCESS",
    },
    {
        "env_var": "BILLING_PASSWORD",
        "tenant_env_var": "SYSTEM_TENANT_ID",
        "email": "billing@sns.local",
        "full_name": "Billing Team",
        "role": "BILLING",
        "access_level": "FULL_ACCESS",
    },
]


def _ensure_platform_tenant(db) -> uuid.UUID:
    tenant_id_raw = os.getenv(SYSTEM_TENANT_ID) or os.getenv("OWNER_TENANT_ID")
    if not tenant_id_raw:
        raise RuntimeError(
            "SYSTEM_TENANT_ID is required for global owner/billing dashboard access. "
            "This tenant is not an agency tenant."
        )

    tenant_id = uuid.UUID(tenant_id_raw)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            legal_name="SNS Platform",
            display_name="SNS Platform",
            npi="0000000000",
            ein=None,
            ptan=None,
            tenant_type="PRODUCTION",
            environment_tag="PERMANENT",
            status="ACTIVE",
            ai_enabled=True,
            billing_enabled=False,
        )
        db.add(tenant)
    else:
        tenant.legal_name = tenant.legal_name or "SNS Platform"
        tenant.display_name = tenant.display_name or "SNS Platform"
        tenant.tenant_type = tenant.tenant_type or "PRODUCTION"
        tenant.environment_tag = tenant.environment_tag or "PERMANENT"
        tenant.status = tenant.status or "ACTIVE"
        tenant.ai_enabled = True
        tenant.billing_enabled = False

    return tenant_id


def main() -> int:
    db = SessionLocal()
    try:
        created = 0
        updated = 0
        skipped = []

        for account in ACCOUNTS:
            tenant_env_var = account.get("tenant_env_var") or SYSTEM_TENANT_ID
            tenant_id_raw = os.getenv(tenant_env_var)
            if not tenant_id_raw:
                if tenant_env_var == SYSTEM_TENANT_ID:
                    tenant_id = _ensure_platform_tenant(db)
                else:
                    skipped.append(f"{account['email']} (missing {tenant_env_var})")
                    continue
            else:
                tenant_id = uuid.UUID(tenant_id_raw)

            password = os.getenv(account["env_var"])
            email = account["email"]

            user = db.query(User).filter(User.email == email).one_or_none()
            if user is None:
                user = db.query(User).filter(User.email == email).first()

            if user is None and password is None:
                skipped.append(f"{email} (no {account['env_var']}, user does not exist)")
                continue

            if password is not None and len(password) < MIN_PASSWORD_LENGTH:
                print(
                    f"ERROR: {account['env_var']} is shorter than "
                    f"{MIN_PASSWORD_LENGTH} characters."
                )
                return 1

            if user is None:
                user = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    email=email,
                    full_name=account["full_name"],
                    role=account["role"],
                    access_level=account["access_level"],
                    active=True,
                )
                db.add(user)
                created += 1
            else:
                user.tenant_id = tenant_id
                user.full_name = account["full_name"]
                user.role = account["role"]
                user.access_level = account["access_level"]
                user.active = True
                updated += 1

            if password is not None:
                user.password_hash = hash_password(password)

        db.commit()

        print(f"created: {created}, updated: {updated}")
        for entry in skipped:
            print(f"skipped: {entry}")
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
