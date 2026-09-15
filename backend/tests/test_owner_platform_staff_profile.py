from __future__ import annotations

"""
Phase UM-2 (SNS Staff Profile) regression tests for
POST /api/owner/users, GET /api/owner/users/{id}, and
PATCH /api/owner/users/{id}/profile in app/api/owner_admin.py.

Covers: creation scoped to the platform tenant, role-assignment ceiling
on create (only OWNER may create another OWNER), profile view/edit
scoping to PLATFORM_ROLES only, and the RBAC target-hierarchy ceiling
on profile edits (PLATFORM_ADMIN may not edit another PLATFORM_ADMIN or
OWNER; a limited role may not edit anyone).
"""

import uuid

import pytest

from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User

# The shared conftest db_session fixture deliberately RETAINS the "users"
# table across tests (only rows matching the per-test tenant fixture are
# swept). Because every user this file creates lives under the fixed
# PLATFORM_TENANT_ID -- not the per-test tenant -- those rows would
# otherwise persist forever in the test database and leak into unrelated
# tests (e.g. the platform-role allowlist assertion in
# test_owner_platform_staff_scope.py). Track every id we create here and
# delete them ourselves at the end of each test.
_created_platform_user_ids: list[uuid.UUID] = []


@pytest.fixture(autouse=True)
def _cleanup_created_platform_users(db_session):
    _created_platform_user_ids.clear()
    yield
    if _created_platform_user_ids:
        # Audit rows (also PLATFORM_TENANT_ID-scoped, so also outside the
        # fixture's own-tenant sweep) FK-reference these users as
        # created_by -- clear them first or the user delete below fails.
        db_session.query(AuditLog).filter(
            AuditLog.tenant_id == PLATFORM_TENANT_ID
        ).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_(_created_platform_user_ids)).delete(
            synchronize_session=False
        )
        db_session.commit()
    _created_platform_user_ids.clear()



def _actor_headers(db_session, role: str) -> dict[str, str]:
    """Create a real, persisted platform-staff row for the acting user and
    return auth headers for it. created_by/updated_by on the target row
    are FK-constrained to users.id, so the actor must exist in the DB --
    unlike a bare JWT with a throwaway random user_id."""
    actor = _make_platform_user(db_session, role=role, email=f"actor.{uuid.uuid4().hex[:8]}@sns.internal")
    token = create_access_token(
        user_id=actor.id,
        role=role,
        tenant_id=PLATFORM_TENANT_ID,
        email=actor.email,
    )
    auth_scheme = "Bearer"
    return {"Authorization": f"{auth_scheme} {token}"}


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


def _make_platform_user(db_session, *, role: str, email: str) -> User:
    _ensure_platform_tenant(db_session)
    user = User(
        id=uuid.uuid4(),
        tenant_id=PLATFORM_TENANT_ID,
        email=email,
        full_name=email.split("@")[0],
        role=role,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _created_platform_user_ids.append(user.id)
    return user


def test_owner_can_create_sns_staff(client, db_session, tenant):
    _ensure_platform_tenant(db_session)
    headers = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"newstaff.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "New",
            "last_name": "Staffer",
            "role": "PLATFORM_SUPPORT",
            "department": "CUSTOMER_SUPPORT",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["role"] == "PLATFORM_SUPPORT"
    assert body["department"] == "CUSTOMER_SUPPORT"
    assert body["access_level"] == "LEVEL_5_LIMITED_SUPPORT"
    assert "temporary_password" in body
    _created_platform_user_ids.append(uuid.UUID(body["user_id"]))


def test_platform_admin_cannot_create_another_owner(client, db_session, tenant):
    _ensure_platform_tenant(db_session)
    headers = _actor_headers(db_session, "PLATFORM_ADMIN")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"wannabeowner.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Would",
            "last_name": "BeOwner",
            "role": "OWNER",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_platform_admin_can_create_support_staff(client, db_session, tenant):
    _ensure_platform_tenant(db_session)
    headers = _actor_headers(db_session, "PLATFORM_ADMIN")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"opsstaff.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Ops",
            "last_name": "Staffer",
            "role": "PLATFORM_OPERATIONS",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    _created_platform_user_ids.append(uuid.UUID(resp.json()["user_id"]))


def test_read_only_auditor_cannot_create_staff(client, db_session, tenant):
    _ensure_platform_tenant(db_session)
    headers = _actor_headers(db_session, "PLATFORM_AUDITOR")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": f"blocked.{uuid.uuid4().hex[:8]}@sns.internal",
            "first_name": "Should",
            "last_name": "Fail",
            "role": "PLATFORM_SUPPORT",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_create_rejects_invalid_role(client, db_session, tenant):
    _ensure_platform_tenant(db_session)
    headers = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": "invalid@sns.internal",
            "first_name": "Bad",
            "last_name": "Role",
            "role": "ADMINISTRATOR",  # tenant role, not a platform role
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_rejects_duplicate_email(client, db_session, tenant):
    existing = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email="dupe@sns.internal")
    headers = _actor_headers(db_session, "OWNER")

    resp = client.post(
        "/api/owner/users",
        json={
            "email": existing.email,
            "first_name": "Dup",
            "last_name": "Licate",
            "role": "PLATFORM_SUPPORT",
        },
        headers=headers,
    )
    assert resp.status_code == 409


def test_get_platform_staff_detail(client, db_session, tenant):
    target = _make_platform_user(db_session, role="PLATFORM_QA", email=f"qa.{uuid.uuid4().hex[:8]}@sns.internal")
    headers = _actor_headers(db_session, "OWNER")

    resp = client.get(f"/api/owner/users/{target.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == target.email


def test_get_platform_staff_detail_404_for_tenant_user(client, db_session, tenant):
    tenant_user_id = uuid.uuid4()
    db_session.add(
        User(
            id=tenant_user_id,
            tenant_id=uuid.UUID(str(tenant.id)),
            email=f"agency.{uuid.uuid4().hex[:8]}@example.com",
            full_name="Agency User",
            role="ADMINISTRATOR",
            active=True,
        )
    )
    db_session.commit()
    headers = _actor_headers(db_session, "OWNER")

    resp = client.get(f"/api/owner/users/{tenant_user_id}", headers=headers)
    assert resp.status_code == 404


def test_owner_can_edit_any_staff_profile(client, db_session, tenant):
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"editme.{uuid.uuid4().hex[:8]}@sns.internal")
    headers = _actor_headers(db_session, "OWNER")

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={
            "first_name": "Updated",
            "last_name": "Name",
            "department": "CUSTOMER_SUPPORT",
            "notes": "Promoted to lead",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["first_name"] == "Updated"
    assert body["department"] == "CUSTOMER_SUPPORT"
    assert body["notes"] == "Promoted to lead"
    assert body["updated_by"] is not None


def test_platform_admin_cannot_edit_another_platform_admin(client, db_session, tenant):
    target = _make_platform_user(db_session, role="PLATFORM_ADMIN", email=f"otheradmin.{uuid.uuid4().hex[:8]}@sns.internal")
    headers = _actor_headers(db_session, "PLATFORM_ADMIN")

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={"first_name": "Hacked", "last_name": "Admin"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_platform_admin_cannot_edit_owner_profile(client, db_session, tenant):
    target = _make_platform_user(db_session, role="OWNER", email=f"owner.{uuid.uuid4().hex[:8]}@sns.internal")
    headers = _actor_headers(db_session, "PLATFORM_ADMIN")

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={"first_name": "Hacked", "last_name": "Owner"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_read_only_auditor_cannot_edit_any_profile(client, db_session, tenant):
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"target.{uuid.uuid4().hex[:8]}@sns.internal")
    headers = _actor_headers(db_session, "PLATFORM_AUDITOR")

    resp = client.patch(
        f"/api/owner/users/{target.id}/profile",
        json={"first_name": "Should", "last_name": "Fail"},
        headers=headers,
    )
    assert resp.status_code == 403
