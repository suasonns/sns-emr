from __future__ import annotations

import uuid

from app.core.security import verify_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.services.admin_bootstrap_service import provision_development_logins


# Roles this test is actually responsible for. Passing this set to
# provision_development_logins(..., roles=...) guarantees the call only
# touches these three synthetic identities -- it can never reconcile
# unrelated globally configured identities (e.g. the real acceptance
# Medical Director) onto this test's throwaway tenant, because the function
# skips every DEVELOPMENT_IDENTITIES entry whose role isn't in this set.
TEST_ROLES = {"DPCS_ADMINISTRATOR", "OWNER", "BILLING"}


def _configured_identities(monkeypatch):
    # Unique synthetic identities/tenants per test invocation (not the real
    # DEV_TENANT_ID / DEV_PLATFORM_TENANT_ID env vars, and not the canonical
    # Love & Faith Medical Director account). A fresh uuid4 tenant is used
    # purely as an ephemeral container for these 3 synthetic users; because
    # provisioning is now scoped to TEST_ROLES, no other identity (and no
    # unrelated tenant) is ever touched by this call.
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
    monkeypatch.setenv("DEV_BILLING_TENANT_ID", str(tenant_id))
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
    assert provision_development_logins(db_session, roles=TEST_ROLES) == 3

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
        assert me_payload["access_scope"] == {
            "OWNER": "platform",
            "BILLING": "billing",
            "DPCS_ADMINISTRATOR": "tenant",
        }[role]

    for env_name in (
        "DEV_DPCS_ADMIN_PASSWORD",
        "DEV_PLATFORM_OWNER_PASSWORD",
        "DEV_BILLING_PASSWORD",
    ):
        monkeypatch.delenv(env_name)
    assert provision_development_logins(db_session, roles=TEST_ROLES) == 3
    for role, (email, _) in credentials.items():
        user = db_session.query(User).filter(User.email == email).one()
        assert user.password_hash == original_hashes[role]

    owner_headers = {"Authorization": f"Bearer {tokens['OWNER']}"}
    assert client.get("/api/owner/tenants", headers=owner_headers).status_code == 200
    assert client.get("/patients/", headers=owner_headers).status_code == 403
    assert client.get("/api/dashboard/tenant", headers=owner_headers).status_code == 403
    assert client.get("/api/dashboard/billing", headers=owner_headers).status_code == 403
    assert client.get("/api/dashboard/claim-lifecycle", headers=owner_headers).status_code == 403

    billing_headers = {"Authorization": f"Bearer {tokens['BILLING']}"}
    assert client.get("/api/dashboard/tenant", headers=billing_headers).status_code == 403
    assert client.get("/api/owner/tenants", headers=billing_headers).status_code == 403
    assert client.get("/api/dashboard/claim-lifecycle", headers=billing_headers).status_code == 200
    assert client.get(
        f"/patient-charts/{uuid.uuid4()}/summary",
        headers=billing_headers,
    ).status_code == 403

    tenant_headers = {"Authorization": f"Bearer {tokens['DPCS_ADMINISTRATOR']}"}
    assert client.get("/api/owner/tenants", headers=tenant_headers).status_code == 403

    tenant = db_session.get(Tenant, tenant_id)
    tenant.billing_enabled = False
    db_session.commit()
    assert client.get("/api/dashboard/billing", headers=tenant_headers).status_code == 403
    assert client.get("/api/dashboard/claim-lifecycle", headers=tenant_headers).status_code == 403

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

    # This test provisions two throwaway "SNS Development Agency"/"SNS
    # Development Platform" tenants at fresh uuid4 ids via
    # provision_development_logins(). Nothing else in the suite (or the
    # app) ever cleans those up, so every run of this test permanently
    # leaked a tenant pair (traced 2026-08-25 after a dev-DB audit found
    # 200+ accumulated junk tenants). Delete what this test created. The
    # login/change-password flow above also writes audit_logs rows that
    # reference these users, so those must go first.
    from sqlalchemy import text as _text

    test_user_ids = [
        row.id
        for row in db_session.query(User.id).filter(
            User.tenant_id.in_([tenant_id, platform_tenant_id])
        )
    ]
    if test_user_ids:
        # audit_logs.created_by has a DB-level FK to users.id that isn't
        # mapped on the AuditLog model, so delete via raw SQL.
        db_session.execute(
            _text("DELETE FROM audit_logs WHERE created_by = ANY(:ids)"),
            {"ids": test_user_ids},
        )
    db_session.query(User).filter(
        User.tenant_id.in_([tenant_id, platform_tenant_id])
    ).delete(synchronize_session=False)
    db_session.query(Tenant).filter(
        Tenant.id.in_([tenant_id, platform_tenant_id])
    ).delete(synchronize_session=False)
    db_session.commit()
