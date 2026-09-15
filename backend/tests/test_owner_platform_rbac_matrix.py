from __future__ import annotations

"""
Unit tests for the SNS Staff & Access RBAC foundation (Phase UM-1):
app.core.roles.role_can() / ACCESS_LEVEL_FOR_ROLE / PLATFORM_PERMISSION_MATRIX,
and the app.core.role_guards.require_platform_permission() dependency.

These are pure-function/dependency tests (no DB access needed), but still
run through the isolated test runner like every other backend test in this
repo, per backend/scripts/run_isolated_tests.py.
"""

import pytest
from fastapi import HTTPException

from app.core.role_guards import require_platform_permission
from app.core.roles import (
    ACCESS_LEVEL_FOR_ROLE,
    PLATFORM_ROLES,
    access_level_for_role,
    role_can,
)
from app.core.security import CurrentUser
import uuid


def _user(role: str) -> CurrentUser:
    return CurrentUser(user_id=uuid.uuid4(), role=role, tenant_id=None, email=f"{role.lower()}@sns.internal")


# ---------------------------------------------------------------------
# OWNER: unconditional access to every staff.* capability
# ---------------------------------------------------------------------

def test_owner_has_every_staff_capability():
    for capability in [
        "staff.view",
        "staff.create",
        "staff.invite",
        "staff.edit_profile",
        "staff.assign_role",
        "staff.assign_owner_role",
        "staff.activate",
        "staff.suspend",
        "staff.disable",
        "staff.revoke_access",
        "staff.remove",
        "staff.reset_password",
        "staff.view_audit",
        "staff.manage_service_accounts",
        "staff.manage_api_clients",
    ]:
        assert role_can("OWNER", capability) is True


# ---------------------------------------------------------------------
# PLATFORM_ADMIN: delegated admin, capped below OWNER
# ---------------------------------------------------------------------

def test_platform_admin_is_limited_by_assignment_ceiling():
    assert role_can("PLATFORM_ADMIN", "staff.suspend") is True
    # Cannot assign or act on OWNER.
    assert role_can("PLATFORM_ADMIN", "staff.assign_owner_role") is False
    assert role_can("PLATFORM_ADMIN", "staff.suspend", target_role="OWNER") is False
    # Cannot act on another PLATFORM_ADMIN (no lateral admin-on-admin action).
    assert role_can("PLATFORM_ADMIN", "staff.suspend", target_role="PLATFORM_ADMIN") is False


def test_platform_admin_cannot_manage_non_human_identities():
    assert role_can("PLATFORM_ADMIN", "staff.manage_service_accounts") is False
    assert role_can("PLATFORM_ADMIN", "staff.manage_api_clients") is False


# ---------------------------------------------------------------------
# Specialized administrators are limited to their delegated permissions
# ---------------------------------------------------------------------

def test_security_administrator_limited_scope():
    assert role_can("PLATFORM_SECURITY", "staff.view") is True
    assert role_can("PLATFORM_SECURITY", "staff.suspend") is True
    assert role_can("PLATFORM_SECURITY", "staff.revoke_access") is True
    assert role_can("PLATFORM_SECURITY", "staff.reset_password") is False
    assert role_can("PLATFORM_SECURITY", "staff.assign_role") is False


def test_compliance_administrator_read_only_plus_audit():
    assert role_can("PLATFORM_COMPLIANCE", "staff.view") is True
    assert role_can("PLATFORM_COMPLIANCE", "staff.view_audit") is True
    assert role_can("PLATFORM_COMPLIANCE", "staff.suspend") is False
    assert role_can("PLATFORM_COMPLIANCE", "staff.remove") is False


# ---------------------------------------------------------------------
# Customer Service / Technical Support / Software Development cannot
# administer staff.
# ---------------------------------------------------------------------

def test_customer_service_cannot_administer_staff():
    for capability in ["staff.view", "staff.create", "staff.suspend", "staff.assign_role"]:
        assert role_can("PLATFORM_CUSTOMER_SERVICE", capability) is False


def test_technical_support_cannot_assign_privileged_roles():
    assert role_can("PLATFORM_SUPPORT", "staff.view") is True
    assert role_can("PLATFORM_SUPPORT", "staff.assign_role") is False
    assert role_can("PLATFORM_SUPPORT", "staff.assign_owner_role") is False


def test_software_development_cannot_administer_staff_unless_explicitly_granted():
    assert role_can("PLATFORM_DEVELOPER", "staff.view") is True
    assert role_can("PLATFORM_DEVELOPER", "staff.suspend") is False
    assert role_can("PLATFORM_DEVELOPER", "staff.assign_role") is False


# ---------------------------------------------------------------------
# Read-Only Auditor can never mutate accounts.
# ---------------------------------------------------------------------

def test_read_only_auditor_cannot_mutate_accounts():
    assert role_can("PLATFORM_AUDITOR", "staff.view") is True
    assert role_can("PLATFORM_AUDITOR", "staff.view_audit") is True
    for capability in [
        "staff.create",
        "staff.invite",
        "staff.edit_profile",
        "staff.assign_role",
        "staff.activate",
        "staff.suspend",
        "staff.disable",
        "staff.revoke_access",
        "staff.remove",
        "staff.reset_password",
    ]:
        assert role_can("PLATFORM_AUDITOR", capability) is False


# ---------------------------------------------------------------------
# Final-active-OWNER / hierarchy safeguards.
# ---------------------------------------------------------------------

def test_no_non_owner_role_can_ever_assign_owner_role():
    for role in PLATFORM_ROLES - {"OWNER"}:
        assert role_can(role, "staff.assign_owner_role") is False


def test_no_non_owner_role_can_ever_mutate_an_owner_target():
    for role in PLATFORM_ROLES - {"OWNER"}:
        assert role_can(role, "staff.suspend", target_role="OWNER") is False
        assert role_can(role, "staff.disable", target_role="OWNER") is False
        assert role_can(role, "staff.revoke_access", target_role="OWNER") is False
        assert role_can(role, "staff.remove", target_role="OWNER") is False


# ---------------------------------------------------------------------
# Deny-by-default: unknown role / unknown capability / non-platform role.
# ---------------------------------------------------------------------

def test_unknown_capability_denied():
    assert role_can("OWNER", "staff.not_a_real_capability") is False


def test_unknown_role_denied():
    assert role_can("SOMETHING_MADE_UP", "staff.view") is False


def test_tenant_and_biller_roles_never_get_staff_capabilities():
    # Tenant/clinical/financial roles are not platform roles at all --
    # they must get nothing from this matrix, regardless of capability.
    for role in ["ADMINISTRATOR", "DPCS", "RN", "BILLING", "CFO"]:
        assert role_can(role, "staff.view") is False


# ---------------------------------------------------------------------
# Access-level derivation is total (every PLATFORM_ROLES entry has a tier)
# and purely presentational.
# ---------------------------------------------------------------------

def test_every_platform_role_has_a_derived_access_level():
    assert access_level_for_role("OWNER") == "LEVEL_1_OWNER"
    for role in PLATFORM_ROLES:
        assert access_level_for_role(role) in {
            "LEVEL_1_OWNER",
            "LEVEL_2_ADMINISTRATOR",
            "LEVEL_3_SPECIALIZED_ADMINISTRATOR",
            "LEVEL_4_OPERATIONAL_STAFF",
            "LEVEL_5_LIMITED_SUPPORT",
            "LEVEL_6_READ_ONLY",
        }


def test_access_level_matrix_has_no_stray_roles():
    # Every key in ACCESS_LEVEL_FOR_ROLE must be a real PLATFORM_ROLES member
    # -- guards against the derived-tier map drifting from the role SSOT.
    assert set(ACCESS_LEVEL_FOR_ROLE) <= PLATFORM_ROLES


# ---------------------------------------------------------------------
# require_platform_permission() dependency: denies non-platform roles and
# platform roles lacking the specific capability; allows a role that has it.
# ---------------------------------------------------------------------

def test_dependency_denies_non_platform_role():
    dependency = require_platform_permission("staff.view")
    with pytest.raises(HTTPException) as exc_info:
        dependency(user=_user("ADMINISTRATOR"))
    assert exc_info.value.status_code == 403


def test_dependency_denies_platform_role_missing_capability():
    dependency = require_platform_permission("staff.suspend")
    with pytest.raises(HTTPException) as exc_info:
        dependency(user=_user("PLATFORM_CUSTOMER_SERVICE"))
    assert exc_info.value.status_code == 403


def test_dependency_allows_role_with_capability():
    dependency = require_platform_permission("staff.view")
    user = dependency(user=_user("PLATFORM_SUPPORT"))
    assert user.role == "PLATFORM_SUPPORT"


def test_dependency_allows_owner_for_any_capability():
    dependency = require_platform_permission("staff.manage_api_clients")
    user = dependency(user=_user("OWNER"))
    assert user.role == "OWNER"
