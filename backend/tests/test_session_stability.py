"""Backend regression tests for the session-stability release blocker
(users being signed out mid-navigation on billing pages).

These tests lock in the auth-lifecycle contract the frontend fix in
sns-emr-frontend/src/api/{client,dashboard,census,ownerAdmin}.ts relies
on:

  - An expired (or malformed) access token is rejected with 401 on a
    protected route -- this is the trigger the frontend must react to
    by attempting a refresh, not by immediately clearing the session.
  - POST /auth/refresh, given a still-valid refresh token, returns a
    fresh access token that itself reaches protected routes.
  - An invalid or expired refresh token is rejected with 401 -- this is
    the case where the frontend must clear the session and redirect to
    login (the refresh credential itself is no longer usable).
  - A suspended tenant is rejected with 403, not 401, both on ordinary
    protected routes and on /auth/refresh -- this is what lets the
    frontend distinguish "your session is fine but this tenant is
    denied" from "your session expired", so a 403 must never destroy a
    valid session client-side.
  - A deactivated user cannot use /auth/refresh to keep renewing.
  - An access token cannot be used in place of a refresh token (and
    vice versa is already covered by decode_refresh_token's typ check).

Known gap (documented, not fixed here -- see PR notes): the backend has
no server-side refresh-token store, so rotation/reuse-detection ("a
previously-rotated-away refresh token is rejected") cannot be tested or
enforced without adding a new persistence layer, which is out of scope
for this fix. Every valid, unexpired, correctly-typed refresh token is
currently accepted even after a newer one has been issued.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import (
    ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.services.admin_bootstrap_service import provision_development_logins

TEST_ROLES = {"DPCS_ADMINISTRATOR"}


def _configured_identity(monkeypatch):
    """Provisions a single synthetic tenant/user pair local to the
    isolated test database -- never a real tenant or credential. Mirrors
    the pattern already used by test_auth_hardening.py."""
    suffix = uuid.uuid4().hex
    tenant_id = uuid.uuid4()
    platform_tenant_id = uuid.uuid4()
    email = f"session-stability-{suffix}@example.test"
    password = f"Stability-{suffix}!"

    monkeypatch.setenv("DEV_TENANT_ID", str(tenant_id))
    monkeypatch.setenv("DEV_PLATFORM_TENANT_ID", str(platform_tenant_id))
    monkeypatch.setenv("DEV_DPCS_ADMIN_EMAIL", email)
    monkeypatch.setenv("DEV_DPCS_ADMIN_PASSWORD", password)

    return tenant_id, platform_tenant_id, email, password


def _forge_token(*, sub: str, tenant_id: str, role: str, typ: str, expires_delta: timedelta) -> str:
    """Builds a JWT with the same shape create_access_token/
    create_refresh_token produce, but with an arbitrary (e.g. already
    expired) exp claim -- used to test expiry handling deterministically
    without sleeping in the test."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "role": role,
        "typ": typ,
        "jti": str(uuid.uuid4()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture()
def stability_identity(db_session, monkeypatch):
    tenant_id, platform_tenant_id, email, password = _configured_identity(monkeypatch)
    assert provision_development_logins(db_session, roles=TEST_ROLES) == 1
    user = db_session.query(User).filter(User.email == email).one()
    yield {
        "tenant_id": tenant_id,
        "platform_tenant_id": platform_tenant_id,
        "email": email,
        "password": password,
        "user_id": user.id,
    }

    from sqlalchemy import text as _text

    user_ids = [
        row.id
        for row in db_session.query(User.id).filter(
            User.tenant_id.in_([tenant_id, platform_tenant_id])
        )
    ]
    if user_ids:
        db_session.execute(
            _text("DELETE FROM audit_logs WHERE created_by = ANY(:ids)"),
            {"ids": user_ids},
        )
    db_session.query(User).filter(
        User.tenant_id.in_([tenant_id, platform_tenant_id])
    ).delete(synchronize_session=False)
    db_session.query(Tenant).filter(
        Tenant.id.in_([tenant_id, platform_tenant_id])
    ).delete(synchronize_session=False)
    db_session.commit()


def test_login_returns_access_and_refresh_tokens(client, stability_identity):
    response = client.post(
        "/auth/login",
        json={"email": stability_identity["email"], "password": stability_identity["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_valid_access_token_reaches_protected_route(client, stability_identity):
    token = create_access_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == stability_identity["email"]


def test_expired_access_token_is_rejected(client, stability_identity):
    expired_token = _forge_token(
        sub=str(stability_identity["user_id"]),
        tenant_id=str(stability_identity["tenant_id"]),
        role="DPCS_ADMINISTRATOR",
        typ="access",
        expires_delta=timedelta(minutes=-5),
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_valid_refresh_token_produces_new_working_access_token(client, stability_identity):
    refresh_token = create_refresh_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    new_access_token = body["access_token"]
    assert new_access_token

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_response.status_code == 200


def test_invalid_refresh_token_is_rejected(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_expired_refresh_token_is_rejected(client, stability_identity):
    expired_refresh_token = _forge_token(
        sub=str(stability_identity["user_id"]),
        tenant_id=str(stability_identity["tenant_id"]),
        role="DPCS_ADMINISTRATOR",
        typ="refresh",
        expires_delta=timedelta(minutes=-1),
    )
    response = client.post("/auth/refresh", json={"refresh_token": expired_refresh_token})
    assert response.status_code == 401


def test_access_token_cannot_be_used_as_refresh_token(client, stability_identity):
    access_token = create_access_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_disabled_account_cannot_refresh(client, db_session, stability_identity):
    user = db_session.get(User, stability_identity["user_id"])
    user.active = False
    db_session.commit()

    refresh_token = create_refresh_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401


def test_tenant_suspension_is_403_not_401_and_survives_a_valid_session(
    client, db_session, stability_identity
):
    """A suspended tenant must never look like an expired session: the
    frontend relies on this exact status-code distinction (401 -> try to
    refresh, 403 -> tenant/authorization denial, never clear the
    session)."""
    tenant = db_session.get(Tenant, stability_identity["tenant_id"])
    tenant.status = "SUSPENDED"
    db_session.commit()

    access_token = create_access_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 403

    refresh_token = create_refresh_token(
        user_id=stability_identity["user_id"],
        role="DPCS_ADMINISTRATOR",
        tenant_id=stability_identity["tenant_id"],
        email=stability_identity["email"],
    )
    refresh_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 403
