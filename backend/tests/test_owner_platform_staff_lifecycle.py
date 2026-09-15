from __future__ import annotations

"""
Phase UM-2A (SNS Staff & Access -- Frontend Foundation backend
prerequisites) regression tests.

Covers:
  - account_type on create/serialize (POST /api/owner/users, GET
    /api/owner/users/{id}, and the stats block of GET /api/owner/users).
  - the Final-Active-Owner safeguard on PATCH /api/owner/users/{id}
    (cannot disable the last active OWNER).
  - the new PATCH /api/owner/users/{id}/role endpoint: role-assignment
    ceiling reuse, self-role-change prevention, OWNER-assignment ceiling,
    and the Final-Active-Owner safeguard on demotion.
"""

import uuid

import pytest

from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User

# See test_owner_platform_staff_profile.py for why this cleanup pattern
# is required: platform-tenant users/audit rows are not swept by the
# shared db_session fixture's per-test-tenant cleanup.
_created_platform_user_ids: list[uuid.UUID] = []


@pytest.fixture(autouse=True)
def _cleanup_created_platform_users(db_session):
    _created_platform_user_ids.clear()
    yield
    if _created_platform_user_ids:
        db_session.query(AuditLog).filter(
            AuditLog.tenant_id == PLATFORM_TENANT_ID
        ).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_(_created_platform_user_ids)).delete(
            synchronize_session=False
        )
        db_session.commit()
    _created_platform_user_ids.clear()


def _ensure_platform_tenant(db_session) -> None:
    if db_session.get(Tenant, PLATFORM_TENANT_ID) is None:
        db_session.add(
            Tenant(
                id=PLATFORM_TENANT_ID,
                legal_name="SNS Hospice Solutions",
                display_name="SNS Hospice Solutions",
                npi="9999999999",
                tenant_type="PRODUCTION",
                status="ACTIVE",
            )
        )
        db_session.commit()


def _make_platform_user(db_session, *, role: str, email: str, active: bool = True, account_type: str = "HUMAN_STAFF") -> User:
    _ensure_platform_tenant(db_session)
    user = User(
        id=uuid.uuid4(),
        tenant_id=PLATFORM_TENANT_ID,
        email=email,
        full_name=email.split("@")[0],
        role=role,
        active=active,
        account_type=account_type,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _created_platform_user_ids.append(user.id)
    return user


def _actor_headers(db_session, role: str) -> dict[str, str]:
    actor = _make_platform_user(db_session, role=role, email=f"actor.{uuid.uuid4().hex[:8]}@sns.internal")
    token = create_access_token(
        user_id=actor.id,
        role=role,
        tenant_id=PLATFORM_TENANT_ID,
        email=actor.email,
    )
    auth_scheme = "Bearer"
    return {"Authorization": f"{auth_scheme} {token}"}, actor


# ---------------------------------------------------------------------
# account_type
# ---------------------------------------------------------------------


def test_create_staff_defaults_account_type_to_human_staff(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"human.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Human",
            "last_name": "Staffer",
            "role": "PLATFORM_SUPPORT",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["account_type"] == "HUMAN_STAFF"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_create_staff_with_explicit_account_type(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"svc.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Service",
            "last_name": "Account",
            "role": "PLATFORM_OPERATIONS",
            "account_type": "SERVICE_ACCOUNT",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["account_type"] == "SERVICE_ACCOUNT"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_create_staff_rejects_invalid_account_type(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"bad.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Bad",
            "last_name": "Type",
            "role": "PLATFORM_SUPPORT",
            "account_type": "NOT_A_REAL_TYPE",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_list_stats_include_account_type_and_owner_counts(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")
    _make_platform_user(
        db_session, role="PLATFORM_OPERATIONS", email=f"api.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="API_CLIENT",
    )

    resp = client.get("/api/owner/users", headers=headers)
    assert resp.status_code == 200, resp.text
    stats = resp.json()["stats"]
    assert "active_owners" in stats
    assert "service_accounts" in stats
    assert "automation_accounts" in stats
    assert "api_clients" in stats
    assert stats["api_clients"] >= 1
    assert stats["active_owners"] >= 1
    assert "SERVICE_ACCOUNT" in resp.json()["available_account_types"]


def test_list_can_filter_by_account_type(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    svc = _make_platform_user(
        db_session, role="PLATFORM_OPERATIONS", email=f"svcfilter.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="SERVICE_ACCOUNT",
    )
    _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"human.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get("/api/owner/users?account_type=SERVICE_ACCOUNT", headers=headers)
    assert resp.status_code == 200, resp.text
    returned_ids = {u["user_id"] for u in resp.json()["users"]}
    assert str(svc.id) in returned_ids
    assert all(u["account_type"] == "SERVICE_ACCOUNT" for u in resp.json()["users"])


def test_list_can_filter_by_department(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"deptfilter.{uuid.uuid4().hex[:8]}@sns.internal")
    target.department = "SECURITY"
    db_session.commit()

    resp = client.get("/api/owner/users?department=SECURITY", headers=headers)
    assert resp.status_code == 200, resp.text
    returned_ids = {u["user_id"] for u in resp.json()["users"]}
    assert str(target.id) in returned_ids


def test_list_rejects_invalid_account_type_filter(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    resp = client.get("/api/owner/users?account_type=NOT_REAL", headers=headers)
    assert resp.status_code == 400


def test_list_rows_include_allowed_actions_and_actor_capabilities(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"row.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get("/api/owner/users", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "actor_capabilities" in body
    assert "staff.create" in body["actor_capabilities"]
    row = body["users"][0]
    assert "allowed_actions" in row
    assert set(row["allowed_actions"].keys()) == {
        "edit_profile", "assign_role", "activate", "suspend", "disable", "revoke_access",
        "reset_password", "remove",
    }


def test_platform_support_row_actions_reflect_delegable_default_bundle(client, db_session, tenant):
    """PLATFORM_SUPPORT now holds staff.view + staff.reset_password by
    default (Phase UM-3 responsibility-ownership model) -- the roster is
    delegable, not OWNER-only, and row actions reflect exactly the
    capability matrix via role_can(), not an OWNER-only shortcut."""
    headers, _ = _actor_headers(db_session, "PLATFORM_SUPPORT")
    _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"row2.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get("/api/owner/users", headers=headers)
    assert resp.status_code == 200, resp.text
    row = next(u for u in resp.json()["users"] if u["email"].startswith("row2."))
    assert row["allowed_actions"]["reset_password"] is True
    assert row["allowed_actions"]["suspend"] is False
    assert row["allowed_actions"]["disable"] is False
    assert row["allowed_actions"]["remove"] is False
    assert row["allowed_actions"]["assign_role"] is False


# ---------------------------------------------------------------------
# GET /users/{id}/audit
# ---------------------------------------------------------------------


def test_staff_audit_history_reflects_real_lifecycle_events(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"audited.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    audit_resp = client.get(f"/api/owner/users/{target.id}/audit", headers=headers)
    assert audit_resp.status_code == 200, audit_resp.text
    events = audit_resp.json()["events"]
    assert any(e["action"] == "OWNER_CHANGED_STAFF_ROLE" for e in events)


# ---------------------------------------------------------------------
# Final-Active-Owner safeguard on PATCH /users/{id} (active toggle)
# ---------------------------------------------------------------------


def test_cannot_disable_the_last_active_owner(client, db_session, tenant):
    """When the acting OWNER is the only active OWNER, disabling their own
    (or any other sole remaining) OWNER account must be blocked."""
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.patch(
        f"/api/owner/users/{actor.id}",
        json={"active": False},
        headers=headers,
    )
    assert resp.status_code == 409, resp.text
    assert "final active platform owner" in resp.json()["detail"].lower()


def test_can_disable_an_owner_when_another_active_owner_remains(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    other_owner = _make_platform_user(db_session, role="OWNER", email=f"owner2.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{other_owner.id}",
        json={"active": False},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["active"] is False


# ---------------------------------------------------------------------
# PATCH /users/{id}/role
# ---------------------------------------------------------------------


def test_owner_can_change_another_staff_members_role(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"target.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_OPERATIONS"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "PLATFORM_OPERATIONS"


def test_only_owner_may_assign_owner_role(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"target.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "OWNER"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_actor_cannot_change_own_role(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.patch(
        f"/api/owner/users/{actor.id}/role",
        json={"role": "PLATFORM_ADMIN"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_platform_admin_cannot_change_another_platform_admins_role(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    other_admin = _make_platform_user(db_session, role="PLATFORM_ADMIN", email=f"admin2.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{other_admin.id}/role",
        json={"role": "PLATFORM_SUPPORT"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_owner_can_demote_another_owner_when_a_third_remains(client, db_session, tenant):
    """Demoting an OWNER target requires an OWNER actor (target-hierarchy
    ceiling), and the actor themself always counts as an active OWNER --
    so the Final-Active-Owner safeguard can only ever fire when the
    *target* is the sole other active owner and the actor's own count is
    excluded, which the endpoint checks via exclude_user_id=target.id.
    With three active owners, demoting one still leaves two -- succeeds."""
    headers, _ = _actor_headers(db_session, "OWNER")
    other_owner = _make_platform_user(db_session, role="OWNER", email=f"owner2.{uuid.uuid4().hex[:8]}@sns.internal")
    _make_platform_user(db_session, role="OWNER", email=f"owner3.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{other_owner.id}/role",
        json={"role": "PLATFORM_ADMIN"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "PLATFORM_ADMIN"


def test_role_change_is_audited(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"target.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "OWNER_CHANGED_STAFF_ROLE", AuditLog.entity_id == str(target.id))
        .first()
    )
    assert entry is not None
    assert entry.event_metadata["previous_role"] == "PLATFORM_SUPPORT"
    assert entry.event_metadata["new_role"] == "PLATFORM_QA"


# ---------------------------------------------------------------------
# UM-2A IAM correction: account_types (plural) scope filter, and
# is_final_active_owner succession signal.
# ---------------------------------------------------------------------


def test_list_can_filter_by_multiple_account_types(client, db_session, tenant):
    """The SNS Staff & Access page's Service Accounts tab must be able to
    scope to both SERVICE_ACCOUNT and AUTOMATION_ACCOUNT in one request
    (account_types, plural, comma-separated) -- distinct from the
    single-value account_type filter."""
    headers, _ = _actor_headers(db_session, "OWNER")
    svc = _make_platform_user(
        db_session, role="PLATFORM_OPERATIONS", email=f"svc2.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="SERVICE_ACCOUNT",
    )
    auto = _make_platform_user(
        db_session, role="PLATFORM_OPERATIONS", email=f"auto2.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="AUTOMATION_ACCOUNT",
    )
    _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"human2.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get(
        "/api/owner/users?account_types=SERVICE_ACCOUNT,AUTOMATION_ACCOUNT",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    returned_ids = {u["user_id"] for u in resp.json()["users"]}
    assert str(svc.id) in returned_ids
    assert str(auto.id) in returned_ids
    assert all(u["account_type"] in {"SERVICE_ACCOUNT", "AUTOMATION_ACCOUNT"} for u in resp.json()["users"])


def test_list_rejects_invalid_account_types_filter(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    resp = client.get("/api/owner/users?account_types=SERVICE_ACCOUNT,NOT_REAL", headers=headers)
    assert resp.status_code == 400


def test_staff_detail_flags_the_sole_active_owner_as_final(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.get(f"/api/owner/users/{actor.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_final_active_owner"] is True


def test_staff_detail_does_not_flag_owner_as_final_when_another_owner_is_active(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")
    _make_platform_user(db_session, role="OWNER", email=f"owner3.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get(f"/api/owner/users/{actor.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_final_active_owner"] is False


def test_staff_detail_does_not_flag_non_owner_as_final(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"nonowner.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.get(f"/api/owner/users/{target.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_final_active_owner"] is False


def test_audit_logs_can_scope_to_entity_type_user(client, db_session, tenant):
    """The SNS Staff & Access page's Audit tab scopes the platform-wide
    audit trail to entity_type='user' so it never shows unrelated
    tenant/billing/clinical events."""
    headers, actor = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"scoped.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    audit_resp = client.get("/api/owner/audit-logs?entity_type=user&hours=8760", headers=headers)
    assert audit_resp.status_code == 200, audit_resp.text
    logs = audit_resp.json()["logs"]
    assert any(log["entity_id"] == str(target.id) and log["action"] == "OWNER_CHANGED_STAFF_ROLE" for log in logs)
    assert all(log["entity_id"] is not None for log in logs)


# ---------------------------------------------------------------------
# job_title (Human Staff) / responsible_owner, purpose, scope (Platform
# Identities) -- final SNS Staff & Access IAM direction.
# ---------------------------------------------------------------------


def test_create_human_staff_persists_job_title(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"titled.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Titled",
            "last_name": "Staffer",
            "role": "PLATFORM_SECURITY",
            "job_title": "Director of Platform Security",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["job_title"] == "Director of Platform Security"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_create_service_account_persists_responsible_owner_purpose_and_scope(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"svcid.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Nightly",
            "last_name": "ReconciliationJob",
            "role": "PLATFORM_OPERATIONS",
            "account_type": "SERVICE_ACCOUNT",
            "responsible_owner_id": str(actor.id),
            "purpose": "Runs the nightly reconciliation batch job.",
            "scope": "claims:read, claims:reconcile",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["responsible_owner_id"] == str(actor.id)
    assert body["responsible_owner_name"] == actor.full_name
    assert body["purpose"] == "Runs the nightly reconciliation batch job."
    assert body["scope"] == "claims:read, claims:reconcile"
    _created_platform_user_ids.append(uuid.UUID(body["user_id"]))


def test_create_rejects_responsible_owner_that_does_not_exist(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"badowner.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Bad",
            "last_name": "Owner",
            "role": "PLATFORM_OPERATIONS",
            "account_type": "SERVICE_ACCOUNT",
            "responsible_owner_id": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert resp.status_code == 400, resp.text


def test_update_profile_can_change_job_title_and_identity_fields(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(
        db_session,
        role="PLATFORM_AI_MANAGEMENT",
        email=f"apiclient.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="API_CLIENT",
    )

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={
            "first_name": target.full_name,
            "last_name": "Client",
            "job_title": "Integration Client",
            "responsible_owner_id": str(actor.id),
            "purpose": "Integration client for the tenant claims export API.",
            "scope": "read:claims",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job_title"] == "Integration Client"
    assert body["responsible_owner_id"] == str(actor.id)
    assert body["responsible_owner_name"] == actor.full_name
    assert body["purpose"] == "Integration client for the tenant claims export API."
    assert body["scope"] == "read:claims"


def test_list_platform_users_includes_job_title_and_responsible_owner_name(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(
        db_session,
        role="PLATFORM_OPERATIONS",
        email=f"listed.{uuid.uuid4().hex[:8]}@sns.internal",
        account_type="SERVICE_ACCOUNT",
    )
    target.responsible_owner_id = actor.id
    target.identity_purpose = "Backup automation account."
    db_session.commit()

    resp = client.get("/api/owner/users?account_type=SERVICE_ACCOUNT", headers=headers)
    assert resp.status_code == 200, resp.text
    row = next(u for u in resp.json()["users"] if u["user_id"] == str(target.id))
    assert row["responsible_owner_name"] == actor.full_name
    assert row["purpose"] == "Backup automation account."


def test_create_defaults_platform_to_sns_hospice_solutions(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"noplatform.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "No",
            "last_name": "PlatformField",
            "role": "PLATFORM_SECURITY",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["platform"] == "SNS Hospice Solutions"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_create_persists_explicit_platform(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"withplatform.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "With",
            "last_name": "PlatformField",
            "role": "PLATFORM_DEVELOPER",
            "platform": "SNS Home Health Solutions",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["platform"] == "SNS Home Health Solutions"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_create_rejects_unknown_platform(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"badplatform.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Bad",
            "last_name": "PlatformField",
            "role": "PLATFORM_DEVELOPMENT",
            "platform": "Not A Real Platform",
        },
        headers=headers,
    )
    assert resp.status_code == 422, resp.text


def test_update_profile_can_change_platform(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(
        db_session,
        role="PLATFORM_QA",
        email=f"platformupdate.{uuid.uuid4().hex[:8]}@sns.internal",
    )

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={
            "first_name": target.full_name,
            "last_name": "Staffer",
            "platform": "SNS Scribe",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["platform"] == "SNS Scribe"


def test_list_platform_users_includes_platform_and_filters_by_it(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(
        db_session,
        role="PLATFORM_OPERATIONS",
        email=f"platformlisted.{uuid.uuid4().hex[:8]}@sns.internal",
    )
    target.platform = "SNS Home Health Solutions"
    db_session.commit()

    resp = client.get("/api/owner/users?platform=SNS Home Health Solutions", headers=headers)
    assert resp.status_code == 200, resp.text
    rows = resp.json()["users"]
    assert any(u["user_id"] == str(target.id) for u in rows)
    assert all(u["platform"] == "SNS Home Health Solutions" for u in rows)

    resp2 = client.get("/api/owner/users", headers=headers)
    assert resp2.status_code == 200, resp2.text
    assert "available_platforms" in resp2.json()
    assert resp2.json()["available_platforms"] == [
        "SNS Hospice Solutions",
        "SNS Home Health Solutions",
        "SNS Scribe",
    ]


def test_create_persists_catalog_job_title_matched_case_insensitively(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"devtitle.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Dev",
            "last_name": "Staffer",
            "role": "PLATFORM_DEVELOPER",
            "department": "DEVELOPMENT",
            "job_title": "senior software developer",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Canonical catalog casing is returned regardless of input casing.
    assert body["job_title"] == "Senior Software Developer"
    _created_platform_user_ids.append(uuid.UUID(body["user_id"]))


def test_create_rejects_job_title_not_in_department_catalog(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"badtitle.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Bad",
            "last_name": "Title",
            "role": "PLATFORM_DEVELOPER",
            "department": "DEVELOPMENT",
            "job_title": "Chief Astronaut",
        },
        headers=headers,
    )
    assert resp.status_code == 422, resp.text


def test_create_allows_free_text_job_title_for_department_without_catalog(client, db_session, tenant):
    # PLATFORM_ADMINISTRATION has no defined job-title catalog yet, so
    # any non-blank job title is accepted unchanged -- see
    # app/core/job_titles.py module docstring.
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"admintitle.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Admin",
            "last_name": "Staffer",
            "role": "PLATFORM_ADMIN",
            "department": "PLATFORM_ADMINISTRATION",
            "job_title": "Director of Platform Administration",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["job_title"] == "Director of Platform Administration"
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_update_profile_rejects_job_title_not_in_department_catalog(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(
        db_session,
        role="PLATFORM_QA",
        email=f"qatitle.{uuid.uuid4().hex[:8]}@sns.internal",
    )

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={
            "first_name": target.first_name,
            "last_name": target.last_name,
            "department": "QUALITY_ASSURANCE",
            "job_title": "Not A Real QA Title",
        },
        headers=headers,
    )
    assert resp.status_code == 422, resp.text


def test_list_response_includes_job_titles_by_department(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")

    resp = client.get("/api/owner/users", headers=headers)
    assert resp.status_code == 200, resp.text
    catalog = resp.json()["job_titles_by_department"]
    assert catalog["DEVELOPMENT"] == [
        "Development Lead",
        "Senior Software Developer",
        "Software Developer",
    ]
    assert catalog["EXECUTIVE"] == ["CEO", "CFO", "COO", "Founder", "President"]
    # Departments without a defined catalog are simply absent.
    assert "PLATFORM_ADMINISTRATION" not in catalog

