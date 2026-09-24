from __future__ import annotations

import uuid

from app.models.tenant import Tenant
from app.models.user import User
from app.services.admin_bootstrap_service import provision_development_logins

# SUPERADMIN (the SNS Tech Solutions OWNER account) disabled-account
# rejection. This is the one focused gap identified in
# docs/phase2/SUPERADMIN_OWNER_ACCOUNT_VALIDATION.md's test matrix: login
# already filters on User.active (see app/api/auth.py::login), but no test
# exercised that specifically for the OWNER role before this addition.

TEST_ROLES = {"OWNER"}


def test_disabled_owner_account_cannot_log_in(client, db_session, monkeypatch):
    suffix = uuid.uuid4().hex
    platform_tenant_id = uuid.uuid4()
    email = f"owner-disabled-{suffix}@example.test"
    password = f"Owner-Disabled-{suffix}!"

    monkeypatch.setenv("DEV_PLATFORM_TENANT_ID", str(platform_tenant_id))
    monkeypatch.setenv("DEV_PLATFORM_OWNER_EMAIL", email)
    monkeypatch.setenv("DEV_PLATFORM_OWNER_PASSWORD", password)

    assert provision_development_logins(db_session, roles=TEST_ROLES) == 1

    user = db_session.query(User).filter(User.email == email).one()
    assert user.role == "OWNER"

    # Sanity check: the account works while enabled.
    ok_response = client.post("/auth/login", json={"email": email, "password": password})
    assert ok_response.status_code == 200

    user.active = False
    db_session.commit()

    disabled_response = client.post("/auth/login", json={"email": email, "password": password})
    assert disabled_response.status_code == 401
    assert disabled_response.json()["detail"] == "Invalid credentials"

    # Cleanup: this test provisions a throwaway platform tenant/user pair
    # (see test_auth_hardening.py's cleanup note for why this matters).
    from sqlalchemy import text as _text

    db_session.execute(
        _text("DELETE FROM audit_logs WHERE created_by = :id"), {"id": user.id}
    )
    db_session.delete(user)
    db_session.flush()
    tenant = db_session.get(Tenant, platform_tenant_id)
    if tenant is not None:
        db_session.delete(tenant)
    db_session.commit()
