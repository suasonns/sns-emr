from __future__ import annotations

"""
Audit Logs (owner-portal standalone page) backend regression tests.

Covers:
  - the centralized severity resolver (_severity_for_event), table-driven
    over every explicitly mapped action, the two context-aware actions
    (OWNER_SET_TENANT_STATUS, OWNER_CHANGED_STAFF_ROLE), and the default
    unknown-action fallback;
  - the role-derived Affected Permissions diff
    (_affected_permissions_for_role_change), reusing the same
    authoritative RBAC source as SNS Staff & Access
    (app.core.roles.capabilities_for_role) -- no second permission
    catalog;
  - the `entity_id` query parameter on GET /api/owner/audit-logs (full
    Related Events history, not just the current page), including that
    it composes correctly with existing filters/count parity;
  - that `severity` and `affected_permissions` are present end-to-end on
    a real role-change event returned by the live endpoint.
"""

import uuid

import pytest

from app.api.owner_admin import (
    _affected_permissions_for_role_change,
    _severity_for_event,
)
from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.roles import capabilities_for_role
from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User

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
    token = create_access_token(
        user_id=actor.id,
        role=role,
        tenant_id=PLATFORM_TENANT_ID,
        email=actor.email,
    )
    return {"Authorization": f"Bearer {token}"}, actor


# ---------------------------------------------------------------------
# _severity_for_event -- table-driven unit tests, no DB required.
# ---------------------------------------------------------------------

_FLAT_TABLE_CASES = [
    ("LOGIN_SUCCESS", "INFO"),  # unmapped -> safe default
    ("LOGIN_FAILED", "WARNING"),
    ("CHANGE_PASSWORD", "WARNING"),
    ("PASSWORD_SET_VIA_RESET_LINK", "WARNING"),
    ("OWNER_RESET_USER_PASSWORD", "WARNING"),
    ("OWNER_DISABLED_USER", "WARNING"),
    ("OWNER_SUSPENDED_STAFF", "WARNING"),
    ("OWNER_DELEGATED_STAFF_PERMISSION", "WARNING"),
    ("OWNER_REVOKED_STAFF_PERMISSION", "WARNING"),
    ("OWNER_REVOKED_STAFF_ACCESS", "HIGH"),
    ("OWNER_REMOVED_STAFF", "HIGH"),
    ("RNICA_HOPE_UNLOCKED", "HIGH"),
    ("TENANT_ONBOARDED", "INFO"),
    ("SOME_TOTALLY_UNKNOWN_ACTION_NOBODY_LOGS", "INFO"),
]


@pytest.mark.parametrize("action,expected", _FLAT_TABLE_CASES)
def test_severity_for_event_flat_table(action, expected):
    assert _severity_for_event(action, None) == expected


@pytest.mark.parametrize(
    "new_status,expected",
    [
        ("SUSPENDED", "CRITICAL"),
        ("INACTIVE", "CRITICAL"),
        ("ACTIVE", "INFO"),
        ("active", "INFO"),  # case-insensitive
        ("suspended", "CRITICAL"),  # case-insensitive
    ],
)
def test_severity_for_event_tenant_status_is_context_aware(new_status, expected):
    assert (
        _severity_for_event("OWNER_SET_TENANT_STATUS", {"new_status": new_status})
        == expected
    )


def test_severity_for_event_tenant_status_missing_metadata_defaults_info():
    assert _severity_for_event("OWNER_SET_TENANT_STATUS", None) == "INFO"
    assert _severity_for_event("OWNER_SET_TENANT_STATUS", {}) == "INFO"


@pytest.mark.parametrize(
    "previous_role,new_role,expected",
    [
        ("PLATFORM_SUPPORT", "PLATFORM_OPERATIONS", "WARNING"),
        ("PLATFORM_SUPPORT", "PLATFORM_ADMIN", "HIGH"),
        ("PLATFORM_ADMIN", "PLATFORM_SUPPORT", "WARNING"),  # demotion FROM admin is routine
        ("PLATFORM_SUPPORT", "OWNER", "CRITICAL"),  # assigning ownership authority
        ("OWNER", "PLATFORM_ADMIN", "CRITICAL"),  # removing ownership authority
        ("owner", "platform_admin", "CRITICAL"),  # case-insensitive
    ],
)
def test_severity_for_event_role_change_is_context_aware(previous_role, new_role, expected):
    metadata = {"previous_role": previous_role, "new_role": new_role}
    assert _severity_for_event("OWNER_CHANGED_STAFF_ROLE", metadata) == expected


def test_severity_for_event_role_change_missing_metadata_defaults_warning():
    # Malformed/missing role metadata must never raise and must never
    # silently escalate to CRITICAL/HIGH -- falls back to the safest
    # non-owner-adjacent tier.
    assert _severity_for_event("OWNER_CHANGED_STAFF_ROLE", None) == "WARNING"
    assert _severity_for_event("OWNER_CHANGED_STAFF_ROLE", {}) == "WARNING"


# ---------------------------------------------------------------------
# _affected_permissions_for_role_change -- reuses the SAME authoritative
# RBAC source as SNS Staff & Access (app.core.roles.capabilities_for_role).
# ---------------------------------------------------------------------


def test_affected_permissions_computes_real_capability_diff():
    before = set(capabilities_for_role("PLATFORM_SUPPORT"))
    after = set(capabilities_for_role("PLATFORM_ADMIN"))
    result = _affected_permissions_for_role_change(
        {"previous_role": "PLATFORM_SUPPORT", "new_role": "PLATFORM_ADMIN"}
    )
    assert result is not None
    assert result["previous_role"] == "PLATFORM_SUPPORT"
    assert result["new_role"] == "PLATFORM_ADMIN"
    assert set(result["added"]) == after - before
    assert set(result["removed"]) == before - after
    # Every listed capability must be a real one from the authoritative
    # matrix -- never an invented permission name.
    for cap in result["added"] + result["removed"]:
        assert cap in capabilities_for_role("OWNER")


def test_affected_permissions_none_for_missing_or_equal_roles():
    assert _affected_permissions_for_role_change(None) is None
    assert _affected_permissions_for_role_change({}) is None
    assert _affected_permissions_for_role_change(
        {"previous_role": "PLATFORM_SUPPORT", "new_role": "PLATFORM_SUPPORT"}
    ) is None


def test_affected_permissions_none_for_unrecognized_role_value():
    # Defensive: never guess/invent a permission set for a role string
    # that isn't a real platform role.
    assert _affected_permissions_for_role_change(
        {"previous_role": "PLATFORM_SUPPORT", "new_role": "NOT_A_REAL_ROLE"}
    ) is None


# ---------------------------------------------------------------------
# GET /api/owner/audit-logs -- entity_id filter (full Related Events
# history) + end-to-end severity/affected_permissions on a real event.
# ---------------------------------------------------------------------


def test_audit_logs_entity_id_filters_to_exact_entity(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target_a = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"a.{uuid.uuid4().hex[:8]}@sns.internal")
    target_b = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"b.{uuid.uuid4().hex[:8]}@sns.internal")

    for target in (target_a, target_b):
        resp = client.patch(
            f"/api/owner/users/{target.id}/role",
            json={"role": "PLATFORM_QA"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    resp = client.get(
        f"/api/owner/audit-logs?entity_id={target_a.id}&hours=8760",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    logs = resp.json()["logs"]
    assert len(logs) >= 1
    assert all(log["entity_id"] == str(target_a.id) for log in logs)
    assert not any(log["entity_id"] == str(target_b.id) for log in logs)
    # total_count must reflect the same entity_id-filtered set (count
    # parity), not the full unfiltered table.
    assert resp.json()["total_count"] == len(logs)


def test_audit_logs_entity_id_composes_with_category_filter(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"c.{uuid.uuid4().hex[:8]}@sns.internal")
    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    matching = client.get(
        f"/api/owner/audit-logs?entity_id={target.id}&category=ADMIN&hours=8760",
        headers=headers,
    )
    assert matching.status_code == 200, matching.text
    assert any(log["action"] == "OWNER_CHANGED_STAFF_ROLE" for log in matching.json()["logs"])

    non_matching = client.get(
        f"/api/owner/audit-logs?entity_id={target.id}&category=BILLING&hours=8760",
        headers=headers,
    )
    assert non_matching.status_code == 200, non_matching.text
    assert non_matching.json()["logs"] == []
    assert non_matching.json()["total_count"] == 0


def test_audit_logs_role_change_event_carries_severity_and_affected_permissions(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"d.{uuid.uuid4().hex[:8]}@sns.internal")

    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_ADMIN"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    audit_resp = client.get(f"/api/owner/audit-logs?entity_id={target.id}&hours=8760", headers=headers)
    assert audit_resp.status_code == 200, audit_resp.text
    logs = audit_resp.json()["logs"]
    role_change = next(log for log in logs if log["action"] == "OWNER_CHANGED_STAFF_ROLE")

    assert role_change["severity"] == "HIGH"  # promotion to PLATFORM_ADMIN
    assert role_change["affected_permissions"] is not None
    assert role_change["affected_permissions"]["previous_role"] == "PLATFORM_SUPPORT"
    assert role_change["affected_permissions"]["new_role"] == "PLATFORM_ADMIN"
    assert isinstance(role_change["affected_permissions"]["added"], list)
    assert isinstance(role_change["affected_permissions"]["removed"], list)


def test_audit_logs_non_role_change_event_has_no_affected_permissions(client, db_session, tenant):
    headers, actor = _actor_headers(db_session, "OWNER")
    audit_resp = client.get(f"/api/owner/audit-logs?entity_id={actor.id}&hours=8760", headers=headers)
    assert audit_resp.status_code == 200, audit_resp.text
    # Actor's own LOGIN_SUCCESS (from create_access_token bypass, none
    # expected here) is irrelevant -- assert the invariant on whatever is
    # returned rather than requiring a specific row.
    for log in audit_resp.json()["logs"]:
        if log["action"] != "OWNER_CHANGED_STAFF_ROLE":
            assert log["affected_permissions"] is None


# ---------------------------------------------------------------------
# Free-text search (`search` query param) -- previously had no dedicated
# test isolating this behavior from the entity_id/category filters above.
# ---------------------------------------------------------------------

def test_audit_logs_search_matches_actor_email(client, db_session, tenant):
    # The search join is on the ACTING user (al.user_id -> u.email), i.e.
    # who performed the action, not the target of the action -- so search
    # here against the actor's own email.
    headers, actor = _actor_headers(db_session, "OWNER")
    unique_slug = actor.email.split("@")[0]
    target = _make_platform_user(
        db_session, role="PLATFORM_SUPPORT", email=f"searchable.{uuid.uuid4().hex[:8]}@sns.internal"
    )
    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    matching = client.get(
        f"/api/owner/audit-logs?search={unique_slug}&hours=8760",
        headers=headers,
    )
    assert matching.status_code == 200, matching.text
    logs = matching.json()["logs"]
    assert len(logs) >= 1
    assert any(log["entity_id"] == str(target.id) for log in logs)


def test_audit_logs_search_matches_action_name(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"act.{uuid.uuid4().hex[:8]}@sns.internal")
    resp = client.patch(
        f"/api/owner/users/{target.id}/role",
        json={"role": "PLATFORM_QA"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    matching = client.get(
        "/api/owner/audit-logs?search=OWNER_CHANGED_STAFF_ROLE&hours=8760",
        headers=headers,
    )
    assert matching.status_code == 200, matching.text
    assert any(log["action"] == "OWNER_CHANGED_STAFF_ROLE" for log in matching.json()["logs"])


def test_audit_logs_search_returns_empty_for_no_match(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    resp = client.get(
        "/api/owner/audit-logs?search=definitely-not-a-real-audit-term-xyz&hours=8760",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["logs"] == []
    assert resp.json()["total_count"] == 0


def test_audit_logs_search_composes_with_entity_id_filter(client, db_session, tenant):
    headers, _ = _actor_headers(db_session, "OWNER")
    target_a = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"sa.{uuid.uuid4().hex[:8]}@sns.internal")
    target_b = _make_platform_user(db_session, role="PLATFORM_SUPPORT", email=f"sb.{uuid.uuid4().hex[:8]}@sns.internal")
    for target in (target_a, target_b):
        resp = client.patch(
            f"/api/owner/users/{target.id}/role",
            json={"role": "PLATFORM_QA"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    # Search term matches both accounts' role-change events, but entity_id
    # narrows it to target_a only -- search and entity_id must AND together.
    resp = client.get(
        f"/api/owner/audit-logs?search=OWNER_CHANGED_STAFF_ROLE&entity_id={target_a.id}&hours=8760",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    logs = resp.json()["logs"]
    assert len(logs) >= 1
    assert all(log["entity_id"] == str(target_a.id) for log in logs)

