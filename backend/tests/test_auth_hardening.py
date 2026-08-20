from __future__ import annotations

import uuid

from app.core.security import verify_password_hash
from app.models.user import User
from app.services.admin_bootstrap_service import provision_development_logins


def _configured_identities(monkeypatch):
    suffix = uuid.uuid4().hex
    tenant_id = uuid.uuid4()
    platform_tenant_id = uuid.uuid4()
    credentials = {
        "DPCS_ADMINISTRATOR": (f"dpcs-{suffix}@example.test", f"Dpcs-{suffix}!"),
        "OWNER": (f"owner-{suffix}@example.test", f"Owner-{suffix}!"),
        "BILLING": (f"billing-{suffix}@example.test", f"Billing-{suffix}!"),
    }
    monkeypatch.setenv("DEV_TENANT_ID", str(tenant_id))
    monkeypatch.setenv("DEV_PLATFORM_TENANT_ID", str(platform_tenant_id))
    monkeypatch.setenv("DEV_DPCS_ADMIN_EMAIL", credentials["DPCS_ADMINISTRATOR"][0])
    monkeypatch.setenv("DEV_DPCS_ADMIN_PASSWORD", credentials["DPCS_ADMINISTRATOR"][1])
    monkeypatch.setenv("DEV_PLATFORM_OWNER_EMAIL", credentials["OWNER"][0])
    monkeypatch.setenv("DEV_PLATFORM_OWNER_PASSWORD", credentials["OWNER"][1])
    monkeypatch.setenv("DEV_BILLING_EMAIL", credentials["BILLING"][0])
    monkeypatch.setenv("DEV_BILLING_PASSWORD", credentials["BILLING"][1])
    return tenant_id, platform_tenant_id, credentials


def test_provisioning_authentication_authorization_and_password_flows(
    client, db_session, monkeypatch
):
    tenant_id, platform_tenant_id, credentials = _configured_identities(monkeypatch)
    assert provision_development_logins(db_session) == 3

    original_hashes = {}
    tokens = {}
    for role, (email, password) in credentials.items():
        user = db_session.query(User).filter(User.email == email).one()
        expected_tenant = platform_tenant_id if role == "OWNER" else tenant_id
        assert user.role == role
        assert user.tenant_id == expected_tenant
        assert verify_password_hash(password, user.password_hash)
        original_hashes[role] = user.password_hash

        login_response = client.post("/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200
        login_payload = login_response.json()
        assert login_payload["user"]["role"] == role
        tokens[role] = login_payload["access_token"]

        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens[role]}"},
        )
        assert me_response.status_code == 200
        me_payload = me_response.json()
        assert me_payload["role"] == role
        assert me_payload["tenant_id"] == str(expected_tenant)
        assert me_payload["ai_enabled"] is True
        assert me_payload["billing_enabled"] is (role != "OWNER")

    for env_name in (
        "DEV_DPCS_ADMIN_PASSWORD",
        "DEV_PLATFORM_OWNER_PASSWORD",
        "DEV_BILLING_PASSWORD",
    ):
        monkeypatch.delenv(env_name)
    assert provision_development_logins(db_session) == 3
    for role, (email, _) in credentials.items():
        user = db_session.query(User).filter(User.email == email).one()
        assert user.password_hash == original_hashes[role]

    owner_headers = {"Authorization": f"Bearer {tokens['OWNER']}"}
    assert client.get("/api/owner/tenants", headers=owner_headers).status_code == 200
    assert client.get("/patients/", headers=owner_headers).status_code == 403
    assert client.get("/api/dashboard/tenant", headers=owner_headers).status_code == 403

    dpcs_email, dpcs_password = credentials["DPCS_ADMINISTRATOR"]
    reset_response = client.post(
        "/auth/reset-password",
        json={"email": dpcs_email, "new_password": "Attacker-password-123!"},
    )
    assert reset_response.status_code == 501
    assert client.post(
        "/auth/login",
        json={"email": dpcs_email, "password": dpcs_password},
    ).status_code == 200

    new_password = f"Changed-{uuid.uuid4().hex}!"
    change_response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['DPCS_ADMINISTRATOR']}"},
        json={"current_password": dpcs_password, "new_password": new_password},
    )
    assert change_response.status_code == 200
    assert client.post(
        "/auth/login",
        json={"email": dpcs_email, "password": new_password},
    ).status_code == 200
