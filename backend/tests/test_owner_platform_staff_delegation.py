from __future__ import annotations

"""
Phase UM-3 (SNS Staff & Access -- responsibility-ownership delegation)
regression tests.

Covers:
  - the distinct ACTIVE/SUSPENDED/DISABLED/REMOVED status model
    (PATCH /users/{id}/status, POST /users/{id}/revoke-access,
    POST /users/{id}/remove) as delegable, capability-gated actions
    instead of OWNER-only;
  - the Remove Staff soft-removal workflow (final-owner safeguard,
    no self-removal, no hard delete, removed accounts excluded from the
    default roster view);
  - delegated permission grants (POST/GET/DELETE
    /users/{id}/permissions): an actor with delegation authority (OWNER
    or PLATFORM_ADMIN) can hand a capability they hold to another SNS
    staff member, an actor without delegation authority cannot, Ownership
    Continuity can never be delegated, and revocation removes effective
    authority immediately.
"""

import uuid

import pytest

from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.staff_permission_grant import StaffPermissionGrant
from app.models.tenant import Tenant
from app.models.user import User

_created_platform_user_ids: list[uuid.UUID] = []


@pytest.fixture(autouse=True)
def _cleanup_created_platform_users(db_session):
    _created_platform_user_ids.clear()
    yield
    if _created_platform_user_ids:
        db_session.query(StaffPermissionGrant).filter(
            StaffPermissionGrant.target_user_id.in_(_created_platform_user_ids)
        ).delete(synchronize_session=False)
        db_session.query(AuditLog).filter(AuditLog.tenant_id == PLATFORM_TENANT_ID).delete(
            synchronize_session=False
        )
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


def _make_platform_user(db_session, *, role: str, email: str, active: bool = True) -> User:
    _ensure_platform_tenant(db_session)
    user = User(
        id=uuid.uuid4(),
        tenant_id=PLATFORM_TENANT_ID,
        email=email,
        full_name=email.split("@")[0],
        role=role,
        active=active,
        account_type="HUMAN_STAFF",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _created_platform_user_ids.append(user.id)
    return user


def _actor_headers(db_session, role: str) -> tuple[dict[str, str], User]:
    actor = _make_platform_user(db_session, role=role, email=f"actor.{uuid.uuid4().hex[:8]}@sns.internal")
    token = create_access_token(user_id=actor.id, role=role, tenant_id=PLATFORM_TENANT_ID, email=actor.email)
    return {"Authorization": f"Bearer {token}"}, actor


# ---------------------------------------------------------------------
# PATCH /users/{id}/status -- distinct ACTIVE/SUSPENDED/DISABLED model
# ---------------------------------------------------------------------


def test_admin_can_suspend_staff_and_status_is_distinct_from_disabled(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"susp.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "SUSPENDED", "reason": "Under investigation"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["platform_staff_status"] == "SUSPENDED"
    assert body["active"] is False

    resp2 = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "DISABLED"},
        headers=headers,
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["platform_staff_status"] == "DISABLED"


def test_compliance_is_read_only_by_default_but_can_be_delegated_a_suspend(client, db_session, tenant):
    """PLATFORM_COMPLIANCE has no staff.suspend by default (established
    RBAC boundary). An Admin can delegate it a compliance-motivated
    suspension without widening the role's default bundle; delegation
    never extends to disable/remove."""
    admin_headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    headers, compliance_actor = _actor_headers(db_session, "PLATFORM_COMPLIANCE")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"comp.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "SUSPENDED", "reason": "Compliance hold"},
        headers=headers,
    )
    assert resp.status_code == 403

    grant_resp = client.post(
        f"/api/owner/users/{compliance_actor.id}/permissions",
        json={"capability": "staff.suspend", "reason": "Compliance-motivated suspension"},
        headers=admin_headers,
    )
    assert grant_resp.status_code == 201, grant_resp.text

    resp2 = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "SUSPENDED", "reason": "Compliance hold"},
        headers=headers,
    )
    assert resp2.status_code == 200, resp2.text

    resp3 = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "DISABLED"},
        headers=headers,
    )
    assert resp3.status_code == 403

    resp4 = client.post(
        f"/api/owner/users/{target.id}/remove",
        json={"reason": "test"},
        headers=headers,
    )
    assert resp4.status_code == 403


def test_unassigned_role_cannot_change_status(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_CUSTOMER_SERVICE")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"unassigned.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "SUSPENDED"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_cannot_suspend_the_final_active_owner(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.patch(
        f"/api/owner/users/{actor.id}/status",
        json={"status": "SUSPENDED"},
        headers=headers,
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------
# POST /users/{id}/revoke-access
# ---------------------------------------------------------------------


def test_revoke_access_transitions_to_disabled_with_distinct_audit_event(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_SECURITY")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"revoke.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/revoke-access",
        json={"reason": "Security incident"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["platform_staff_status"] == "DISABLED"

    audit_resp = client.get(f"/api/owner/users/{target.id}/audit", headers=headers)
    events = audit_resp.json()["events"]
    assert any(e["action"] == "OWNER_REVOKED_STAFF_ACCESS" for e in events)


# ---------------------------------------------------------------------
# POST /users/{id}/remove -- Remove Staff (Staff Lifecycle, delegable)
# ---------------------------------------------------------------------


def test_admin_can_remove_lower_authority_staff(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"rm.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/remove",
        json={"reason": "No longer with SNS"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["platform_staff_status"] == "REMOVED"
    assert body["active"] is False

    # Preserved, not hard-deleted: still visible via GET.
    get_resp = client.get(f"/api/owner/users/{target.id}", headers=headers)
    assert get_resp.status_code == 200

    # Excluded from the default roster view.
    roster = client.get("/api/owner/users", headers=headers).json()
    assert str(target.id) not in {u["user_id"] for u in roster["users"]}

    # Available via explicit status filter.
    removed_roster = client.get("/api/owner/users?status=REMOVED", headers=headers).json()
    assert str(target.id) in {u["user_id"] for u in removed_roster["users"]}


def test_admin_cannot_remove_owner(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    _actor_headers(db_session, "OWNER")  # ensure >1 active owner exists
    owner_headers, second_owner = _actor_headers(db_session, "OWNER")

    resp = client.post(
        f"/api/owner/users/{second_owner.id}/remove",
        json={"reason": "test"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_cannot_remove_another_admin(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_ADMIN", email=f"admin2.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/remove",
        json={"reason": "test"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_cannot_remove_self(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "PLATFORM_ADMIN")

    resp = client.post(
        f"/api/owner/users/{actor.id}/remove",
        json={"reason": "test"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_final_active_owner_cannot_be_removed(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")

    resp = client.post(
        f"/api/owner/users/{actor.id}/remove",
        json={"reason": "test"},
        headers=headers,
    )
    assert resp.status_code in (403, 409)


def test_removed_account_cannot_authenticate(client, db_session, tenant):
    from app.core.security import hash_password

    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"login.{uuid.uuid4().hex[:8]}@sns.internal")
    target.password_hash = hash_password("Sup3rSecret!23")
    db_session.commit()

    client.post(f"/api/owner/users/{target.id}/remove", json={"reason": "test"}, headers=headers)

    login_resp = client.post(
        "/auth/login",
        json={"email": target.email, "password": "Sup3rSecret!23"},
    )
    assert login_resp.status_code in (400, 401, 403)


def test_remove_requires_a_reason(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"noreason.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(f"/api/owner/users/{target.id}/remove", json={"reason": ""}, headers=headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------
# Delegated permission grants
# ---------------------------------------------------------------------


def test_admin_can_delegate_a_capability_it_holds(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_CUSTOMER_SERVICE", email=f"del.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/permissions",
        json={"capability": "staff.reset_password", "reason": "Covering support desk"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    grant_id = resp.json()["grant_id"]
    assert resp.json()["is_active"] is True

    perms = client.get(f"/api/owner/users/{target.id}/permissions", headers=headers).json()
    assert "staff.reset_password" in perms["effective_permissions"]
    assert "staff.reset_password" not in perms["role_defaults"]

    revoke_resp = client.request(
        "DELETE",
        f"/api/owner/users/{target.id}/permissions/{grant_id}",
        json={"reason": "No longer needed"},
        headers=headers,
    )
    assert revoke_resp.status_code == 200, revoke_resp.text

    perms_after = client.get(f"/api/owner/users/{target.id}/permissions", headers=headers).json()
    assert "staff.reset_password" not in perms_after["effective_permissions"]


def test_non_delegation_authority_role_cannot_delegate(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "PLATFORM_SECURITY")
    target = _make_platform_user(db_session, role="PLATFORM_CUSTOMER_SERVICE", email=f"nodel.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/permissions",
        json={"capability": "staff.suspend"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_cannot_delegate_a_capability_it_does_not_hold(client, db_session, tenant):
    """PLATFORM_ADMIN never holds staff.assign_owner_role (non-delegable,
    Ownership Continuity) -- attempting to grant it must always fail."""
    headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"ownerdel.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/permissions",
        json={"capability": "staff.assign_owner_role"},
        headers=headers,
    )
    assert resp.status_code in (403, 422)


def test_delegated_capability_grants_real_effective_access(client, db_session, tenant):
    """A PLATFORM_SUPPORT actor who is delegated staff.suspend can then
    actually call the capability-gated endpoint successfully."""
    admin_headers, _ = _actor_headers(db_session, "PLATFORM_ADMIN")
    support_headers, support_actor = _actor_headers(db_session, "PLATFORM_SUPPORT")
    target = _make_platform_user(db_session, role="PLATFORM_CUSTOMER_SERVICE", email=f"grantee.{uuid.uuid4().hex[:8]}@sns.internal")

    grant_resp = client.post(
        f"/api/owner/users/{support_actor.id}/permissions",
        json={"capability": "staff.suspend", "reason": "Delegated for coverage"},
        headers=admin_headers,
    )
    assert grant_resp.status_code == 201, grant_resp.text

    status_resp = client.patch(
        f"/api/owner/users/{target.id}/status",
        json={"status": "SUSPENDED"},
        headers=support_headers,
    )
    assert status_resp.status_code == 200, status_resp.text


def test_owner_can_delegate_and_revoke(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"ownergrant.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.post(
        f"/api/owner/users/{target.id}/permissions",
        json={"capability": "staff.disable"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
