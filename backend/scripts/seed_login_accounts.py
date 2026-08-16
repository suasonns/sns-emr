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

ACCOUNTS = [
    {
        "env_var": "ADMIN_PASSWORD",
        "email": "rsuason@loveandfaithhospice.com",
        "full_name": "Romel Suason",
        "role": "ADMINISTRATOR",
        "access_level": "FULL_ACCESS",
    },
]


def main() -> int:
    tenant_id_raw = os.getenv("TENANT_ID") or os.getenv("DEV_TENANT_REAL_ID")
    if not tenant_id_raw:
        print("ERROR: set TENANT_ID to the tenant these accounts belong to.")
        return 1

    tenant_id = uuid.UUID(tenant_id_raw)

    db = SessionLocal()
    try:
        if db.get(Tenant, tenant_id) is None:
            print(f"ERROR: tenant {tenant_id} does not exist. Seed the tenant first.")
            return 1

        created = 0
        updated = 0
        skipped = []

        for account in ACCOUNTS:
            password = os.getenv(account["env_var"])
            email = account["email"]

            user = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.email == email)
                .one_or_none()
            )

            if password is None and user is None:
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
