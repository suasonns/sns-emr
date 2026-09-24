from __future__ import annotations

from typing import Iterable, Optional

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user, CurrentUser
from app.core.security import get_current_access
from app.core.roles import role_matches


# =========================================================
# SYSTEM ACCESS (INFRA / ADMIN ONLY)
# =========================================================

def require_system_access():
    """
    System-level access ONLY.

    Use ONLY for:
    - /admin/*
    - /debug/*
    - /system/*

    NEVER use this in clinical endpoints.
    """

    def dependency(access=Depends(get_current_access)):
        return access

    return dependency


# =========================================================
# ROLE-BASED ACCESS (CLINICAL)
# =========================================================

def require_roles(
    allowed_roles: Optional[Iterable[str]] = None,
    *,
    allow_clinical_admin: bool = True,
):
    """
    Enforces role-based access using JWT user context.

    Use this for ALL clinical endpoints:
    - visits
    - notes
    - F2F
    - certifications
    - tasks

    `allow_clinical_admin` controls whether ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR
    implicitly satisfy this gate (see `role_matches`). Set it to False for
    endpoints that grant an actual clinical/legal signing authority (e.g.
    physician order approval, batch signature) — administrative rank must
    never itself confer the ability to sign as a prescriber. Leave it True
    (default) for viewing/monitoring endpoints, where oversight roles are
    intentionally allowed to satisfy the gate.
    """

    def dependency(user: CurrentUser = Depends(get_current_user)):
        if not role_matches(
            user.role, allowed_roles, allow_clinical_admin=allow_clinical_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not allowed",
            )
        return user

    return dependency


# =========================================================
# PERMISSION-BASED ACCESS (FUTURE)
# =========================================================

def require_permission(permission: str = ""):
    """
    Placeholder for fine-grained permissions.
    Currently acts as authenticated user gate.
    """

    def dependency(user: CurrentUser = Depends(get_current_user)):
        return user

    return dependency


# =========================================================
# PERMISSION CHECK (UTILITY)
# =========================================================

# Survey Mode actions (regulator-facing chart PDF download, compliance
# views, bulk export) are all tenant-wide oversight actions. Reuse the
# existing VIEW_ALL_TENANT_PATIENTS capability (app.core.capabilities)
# instead of introducing a second permission system -- that capability
# already carries the correct role set (clinical-admin group, QA roles,
# physician tenant-wide-oversight roles, clinical supervisor).
_SURVEY_MODE_ACTIONS = {"download_chart_pdf", "view_compliance", "export_data"}


def has_permission(user, action: str = "", *args, **kwargs) -> bool:
    """
    Survey Mode permission check (AC-001 remediation).

    Deny-by-default: an unrecognized action is always denied. Reuses
    app.core.capabilities.has_capability() -- the repository's existing
    tenant/clinical capability mechanism -- rather than a bespoke rule.
    """
    from app.core.capabilities import VIEW_ALL_TENANT_PATIENTS, has_capability

    if action not in _SURVEY_MODE_ACTIONS:
        return False

    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    return has_capability(role, VIEW_ALL_TENANT_PATIENTS)
