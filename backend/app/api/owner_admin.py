# api/owner_admin.py
#
# Platform-owner-only tenant onboarding. Lets the OWNER (platform/vendor
# super-user) add new hospice agency tenants and their initial
# administrator account, without ever touching an existing tenant's
# clinical/patient data.

from __future__ import annotations

import time
import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.staff import _generate_temp_password, _issue_password_reset_link
from app.core.database import get_db
from app.core.role_guards import require_owner
from app.core.security import CurrentUser, get_current_user, hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit_logger import log_event
from app.services.dashboard_service import _safe_scalar

router = APIRouter(prefix="/api/owner", tags=["Owner"])

MIN_PASSWORD_LENGTH = 12

# Recorded once, the moment this module is imported at process startup --
# a real (if approximate) backend process-uptime clock. Resets whenever
# the server process restarts, same as any real uptime counter would.
_PROCESS_STARTED_AT = time.monotonic()
_PROCESS_STARTED_AT_WALL = time.time()

# Roles that may be assigned as the initial admin for a newly onboarded
# tenant. Never OWNER (platform-only) or BILLING (assigned separately).
INITIAL_ADMIN_ROLES = {"DPCS_ADMINISTRATOR", "ADMINISTRATOR", "DPCS"}

# ---------------------------------------------------------------------
# AUDIT LOG CATEGORIZATION
#
# audit_logs.action is a flat, free-form string written by ~30 different
# call sites across the app (see app/services/audit_logger.py callers).
# There is no "category" column in the schema, so this map buckets every
# action string that is actually written today into the same five
# categories the owner-portal UI groups by. Keep this in sync when a new
# log_event(action=...) call site is added elsewhere in the backend --
# an unmapped action falls into "DATA" (safe default: clinical/business
# data mutation) rather than being silently dropped.
# ---------------------------------------------------------------------
AUDIT_CATEGORY_ACTIONS: dict[str, set[str]] = {
    "AUTH": {
        "LOGIN_SUCCESS",
        "LOGIN_FAILED",
        "CHANGE_PASSWORD",
        "PASSWORD_SET_VIA_RESET_LINK",
        "SWITCH_AGENCY",
        "PROVIDER_SIGNATURE_ACCESS_GRANTED",
        "PROVIDER_SIGNATURE_ACCESS_DENIED",
    },
    "BILLING": {
        "BILLING_GENERATED",
        "BILLING_GENERATION_FAILED",
        "PAYER_VALIDATION_FAILED",
        "COVERAGE_INTENT_SET",
    },
    "COMPLIANCE": {
        "VIEW_AUDIT_DASHBOARD",
        "SIGN_CTI",
        "SUBMIT_CTI_FOR_SIGNATURE",
        "CREATE_CTI_DRAFT",
        "UPDATE_CTI_NARRATIVE",
        "CERTIFICATION_STATUS_TRANSITION",
        "REG_REPORT_CERTIFIED",
        "SURVEY_PDF_ACCESS",
        "SURVEY_EXPORT_BUNDLE",
        "ADMISSION_RISK_ASSESSMENT",
        "RNICA_HOPE_CLOSED",
        "RNICA_HOPE_READY_TO_EXPORT",
        "RNICA_HOPE_EXPORTED_TO_BATCH",
        "RNICA_HOPE_SUBMISSION_UPDATED",
        "RNICA_HOPE_INACTIVATION_UPDATED",
        "RNICA_HOPE_UNLOCKED",
        "RNICA_ASSESSMENT_LOCKED",
        "RNICA_AMENDMENT_SUBMITTED",
        "RNICA_AMENDMENT_APPROVED",
        "RNICA_AMENDMENT_DENIED",
        "AUTHORIZE_ADMISSION",
        "RECORDS_RELEASE_SIGNED",
    },
    "ADMIN": {
        "TENANT_ONBOARDED",
        "ADMIT_PATIENT",
        "ADMISSION_ACTION_REQUEST_CREATED",
        "ADMISSION_ACTION_REQUEST_STATUS_CHANGED",
        "ADMISSION_ACTION_REQUEST_COMPLETED",
        "ADMISSION_ACTION_REQUEST_CANCELED",
        "PROVIDER_LINK_REMOVED",
        "PROVIDER_ACCESS_BLOCKED_UNLINKED",
        "IMPORT_ORDER_TEMPLATE",
        "GENERATE_IDG_REMINDERS",
        "OWNER_DISABLED_USER",
        "OWNER_ENABLED_USER",
        "OWNER_RESET_USER_PASSWORD",
        "OWNER_SET_TENANT_STATUS",
        "OWNER_SET_TENANT_FINANCIALS",
    },
}

_ACTION_TO_CATEGORY: dict[str, str] = {
    action: category
    for category, actions in AUDIT_CATEGORY_ACTIONS.items()
    for action in actions
}

VALID_AUDIT_CATEGORIES = set(AUDIT_CATEGORY_ACTIONS) | {"DATA"}


def _category_for_action(action: str) -> str:
    return _ACTION_TO_CATEGORY.get(action, "DATA")


class CreateTenantRequest(BaseModel):
    legal_name: str = Field(min_length=2, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    npi: str = Field(min_length=10, max_length=10)
    ein: str | None = Field(default=None, min_length=9, max_length=9)
    ptan: str | None = Field(default=None, max_length=32)
    tenant_type: str = Field(default="TRAINING")

    admin_email: EmailStr
    admin_full_name: str = Field(min_length=2, max_length=200)
    admin_password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    admin_role: str = Field(default="DPCS_ADMINISTRATOR")

    @field_validator("npi")
    @classmethod
    def _npi_digits(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("NPI must be exactly 10 digits")
        return value

    @field_validator("ein")
    @classmethod
    def _ein_digits(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("EIN must be exactly 9 digits")
        return value

    @field_validator("tenant_type")
    @classmethod
    def _tenant_type_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"PRODUCTION", "TRAINING", "DEV"}:
            raise ValueError("tenant_type must be PRODUCTION, TRAINING, or DEV")
        return value

    @field_validator("admin_role")
    @classmethod
    def _admin_role_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in INITIAL_ADMIN_ROLES:
            raise ValueError(f"admin_role must be one of {sorted(INITIAL_ADMIN_ROLES)}")
        return value


def _require_platform_owner(user: CurrentUser) -> None:
    """Explicit platform-owner check; do not rely on clinical-admin fallback."""
    require_owner(user)


@router.get("/tenants")
def list_tenants(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)

    rows = (
        db.execute(
            text(
                """
                SELECT
                    t.id::text AS tenant_id,
                    t.legal_name,
                    COALESCE(t.display_name, t.legal_name) AS display_name,
                    t.tenant_type,
                    t.status,
                    t.ai_enabled,
                    t.billing_enabled,
                    t.financials_enabled,
                    t.created_at,
                    (SELECT COUNT(*) FROM users u WHERE u.tenant_id = t.id) AS user_count,
                    (SELECT COUNT(*) FROM patients p WHERE p.tenant_id = t.id) AS patient_count
                FROM tenants t
                ORDER BY t.created_at DESC
                """
            )
        )
        .mappings()
        .all()
    )

    return {"tenants": [dict(row) for row in rows]}


@router.post("/tenants", status_code=201)
def create_tenant(
    payload: CreateTenantRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)

    existing = db.query(Tenant).filter(Tenant.legal_name == payload.legal_name).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A tenant with this legal name already exists")

    existing_user = db.query(User).filter(User.email == payload.admin_email).one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    tenant = Tenant(
        id=uuid.uuid4(),
        legal_name=payload.legal_name,
        display_name=payload.display_name or payload.legal_name,
        npi=payload.npi,
        ein=payload.ein,
        ptan=payload.ptan,
        tenant_type=payload.tenant_type,
        status="ACTIVE",
        ai_enabled=True,
        # Billing requires ein+ptan on file (see Tenant CHECK constraint);
        # only turn it on automatically when both were actually supplied.
        billing_enabled=bool(payload.ein and payload.ptan),
        financials_enabled=False,
        created_by=getattr(user, "user_id", None) or getattr(user, "id", None),
    )
    db.add(tenant)
    db.flush()

    admin_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=payload.admin_email,
        full_name=payload.admin_full_name,
        role=payload.admin_role,
        access_level="FULL_ACCESS",
        active=True,
        password_hash=hash_password(payload.admin_password),
    )
    db.add(admin_user)

    db.commit()
    db.refresh(tenant)
    db.refresh(admin_user)

    log_event(
        user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
        tenant_id=str(tenant.id),
        role=str(getattr(user, "role", None) or "OWNER"),
        action="TENANT_ONBOARDED",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={
            "legal_name": tenant.legal_name,
            "tenant_type": tenant.tenant_type,
            "admin_email": admin_user.email,
        },
        db=db,
    )

    return {
        "tenant_id": str(tenant.id),
        "legal_name": tenant.legal_name,
        "display_name": tenant.display_name,
        "billing_enabled": tenant.billing_enabled,
        "financials_enabled": tenant.financials_enabled,
        "admin_user": {
            "id": str(admin_user.id),
            "email": admin_user.email,
            "role": admin_user.role,
        },
    }


VALID_TENANT_STATUSES = {"ACTIVE", "INACTIVE", "SUSPENDED"}


class SetTenantStatusPayload(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _status_valid(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in VALID_TENANT_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_TENANT_STATUSES)}")
        return value


class SetTenantFinancialsPayload(BaseModel):
    financials_enabled: bool


@router.patch("/tenants/{target_tenant_id}/status")
def set_tenant_status(
    target_tenant_id: UUID,
    payload: SetTenantStatusPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Suspend / reactivate / deactivate a tenant's platform access. This
    does not touch any clinical/business data -- only the tenant.status
    flag that every tenant-scoped auth check gates on."""
    _require_platform_owner(user)

    tenant = db.get(Tenant, target_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    previous_status = tenant.status
    tenant.status = payload.status
    db.commit()
    db.refresh(tenant)

    log_event(
        db=db,
        user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
        tenant_id=str(tenant.id),
        role=str(getattr(user, "role", None) or "OWNER"),
        action="OWNER_SET_TENANT_STATUS",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={
            "legal_name": tenant.legal_name,
            "previous_status": previous_status,
            "new_status": tenant.status,
        },
        commit=True,
    )

    return {"tenant_id": str(tenant.id), "status": tenant.status}


@router.patch("/tenants/{target_tenant_id}/financials")
def set_tenant_financials(
    target_tenant_id: UUID,
    payload: SetTenantFinancialsPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_platform_owner(user)

    tenant = db.get(Tenant, target_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    previous_value = bool(tenant.financials_enabled)
    tenant.financials_enabled = payload.financials_enabled
    db.commit()
    db.refresh(tenant)

    log_event(
        db=db,
        user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
        tenant_id=str(tenant.id),
        role=str(getattr(user, "role", None) or "OWNER"),
        action="OWNER_SET_TENANT_FINANCIALS",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={
            "legal_name": tenant.legal_name,
            "previous_financials_enabled": previous_value,
            "new_financials_enabled": tenant.financials_enabled,
        },
        commit=True,
    )

    return {
        "tenant_id": str(tenant.id),
        "financials_enabled": bool(tenant.financials_enabled),
    }


# =========================================================
# PLATFORM-WIDE AUDIT LOG (cross-tenant, owner-only)
# =========================================================


@router.get("/audit-logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    search: Optional[str] = Query(None, max_length=200),
    category: Optional[str] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    hours: int = Query(24, ge=1, le=8760),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Real, platform-wide activity trail backing the owner-portal Audit
    Logs page. Reads the same `audit_logs` table every clinical/billing/
    admin/auth action in the app already writes to (app.services.audit_logger.
    log_event) -- there is no separate mock data source. `category` is
    derived server-side from `action` via AUDIT_CATEGORY_ACTIONS since the
    table has no category column."""
    _require_platform_owner(user)

    if category is not None:
        category = category.strip().upper()
        if category not in VALID_AUDIT_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"category must be one of {sorted(VALID_AUDIT_CATEGORIES)}",
            )

    normalized_search = (search or "").strip() or None
    search_pattern = f"%{normalized_search}%" if normalized_search else None

    # Only "DATA" needs an explicit NOT-IN filter (it's every action not
    # otherwise mapped, i.e. everything outside the other four buckets).
    category_actions: Optional[list[str]] = None
    category_is_data_bucket = False
    if category == "DATA":
        category_is_data_bucket = True
    elif category:
        category_actions = sorted(AUDIT_CATEGORY_ACTIONS[category])

    all_mapped_actions = sorted(_ACTION_TO_CATEGORY)

    base_filters = """
        al.created_at >= NOW() - (CAST(:hours AS text) || ' hours')::interval
        AND (CAST(:tenant_id AS uuid) IS NULL OR al.tenant_id = CAST(:tenant_id AS uuid))
        AND (
            CAST(:search_pattern AS text) IS NULL
            OR al.action ILIKE :search_pattern
            OR al.entity_type ILIKE :search_pattern
            OR al.description ILIKE :search_pattern
            OR al.ip_address ILIKE :search_pattern
            OR u.email ILIKE :search_pattern
            OR u.full_name ILIKE :search_pattern
            OR t.display_name ILIKE :search_pattern
            OR t.legal_name ILIKE :search_pattern
        )
    """

    category_filter = ""
    if category_actions is not None:
        category_filter = "AND al.action = ANY(:category_actions)"
    elif category_is_data_bucket:
        category_filter = "AND NOT (al.action = ANY(:all_mapped_actions))"

    params: dict[str, object] = {
        "hours": hours,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "search_pattern": search_pattern,
        "category_actions": category_actions,
        "all_mapped_actions": all_mapped_actions,
        "limit": limit,
        "offset": offset,
    }

    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    al.id::text AS log_id,
                    al.created_at,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.ip_address,
                    al.description,
                    al.metadata AS event_metadata,
                    al.user_id::text AS user_id,
                    COALESCE(u.full_name, u.email, 'System') AS user_display,
                    u.email AS user_email,
                    al.role AS user_role,
                    al.tenant_id::text AS tenant_id,
                    COALESCE(t.display_name, t.legal_name, 'Unknown Tenant') AS tenant_name,
                    COUNT(*) OVER() AS total_count
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.user_id
                LEFT JOIN tenants t ON t.id = al.tenant_id
                WHERE {base_filters}
                {category_filter}
                ORDER BY al.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    total_count = rows[0]["total_count"] if rows else 0
    logs = []
    for row in rows:
        data = dict(row)
        data.pop("total_count", None)
        data["category"] = _category_for_action(data["action"])
        logs.append(data)

    # Category pill counts over the same date/tenant/search window (ignores
    # the active category filter itself, so switching pills doesn't require
    # a second round trip). GROUP BY action keeps this cheap even on a large
    # table -- distinct action strings are a small, bounded set.
    count_rows = (
        db.execute(
            text(
                f"""
                SELECT al.action, COUNT(*) AS action_count
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.user_id
                LEFT JOIN tenants t ON t.id = al.tenant_id
                WHERE {base_filters}
                GROUP BY al.action
                """
            ),
            {k: v for k, v in params.items() if k not in ("limit", "offset", "category_actions", "all_mapped_actions")},
        )
        .mappings()
        .all()
    )

    category_counts = {c: 0 for c in VALID_AUDIT_CATEGORIES}
    for row in count_rows:
        category_counts[_category_for_action(row["action"])] += row["action_count"]

    return {
        "logs": logs,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "category_counts": category_counts,
        "window_hours": hours,
    }


# =========================================================
# PLATFORM-WIDE USER MANAGEMENT (cross-tenant, owner-only)
# =========================================================

# Roles that carry agency-level administrative authority, for the
# "Agency Admins" stat. Reuses the same set the tenant-onboarding flow
# treats as an initial-admin role -- these are the only roles that can
# ever be the sole administrator of a tenant.
AGENCY_ADMIN_ROLES = INITIAL_ADMIN_ROLES


@router.get("/users")
def list_platform_users(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    search: Optional[str] = Query(None, max_length=200),
    role: Optional[str] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Real, platform-wide user roster backing the owner-portal User
    Management page. Reads the same `users` table every tenant's staff
    roster already lives in (app/api/staff.py is tenant-scoped only --
    this is the cross-tenant analog for the platform owner). `last_login`
    is derived from the real `LOGIN_SUCCESS` audit events written by
    app/api/auth.py (there is no last_login column on `users`)."""
    _require_platform_owner(user)

    if status is not None:
        status = status.strip().upper()
        if status not in {"ACTIVE", "DISABLED"}:
            raise HTTPException(
                status_code=400,
                detail="status must be one of ['ACTIVE', 'DISABLED']",
            )

    normalized_search = (search or "").strip() or None
    search_pattern = f"%{normalized_search}%" if normalized_search else None
    normalized_role = (role or "").strip().upper() or None

    base_filters = """
        (CAST(:tenant_id AS uuid) IS NULL OR u.tenant_id = CAST(:tenant_id AS uuid))
        AND (CAST(:role AS text) IS NULL OR u.role = :role)
        AND (
            CAST(:status AS text) IS NULL
            OR (:status = 'ACTIVE' AND u.active = true)
            OR (:status = 'DISABLED' AND u.active = false)
        )
        AND (
            CAST(:search_pattern AS text) IS NULL
            OR u.full_name ILIKE :search_pattern
            OR u.email ILIKE :search_pattern
            OR t.display_name ILIKE :search_pattern
            OR t.legal_name ILIKE :search_pattern
        )
    """

    params = {
        "tenant_id": str(tenant_id) if tenant_id else None,
        "role": normalized_role,
        "status": status,
        "search_pattern": search_pattern,
        "limit": limit,
        "offset": offset,
    }

    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    u.id::text AS user_id,
                    u.full_name,
                    u.email,
                    u.role,
                    u.active,
                    u.tenant_id::text AS tenant_id,
                    COALESCE(t.display_name, t.legal_name, 'Unknown Tenant') AS tenant_name,
                    (
                        SELECT MAX(al.created_at)
                        FROM audit_logs al
                        WHERE al.user_id = u.id AND al.action = 'LOGIN_SUCCESS'
                    ) AS last_login,
                    COUNT(*) OVER() AS total_count
                FROM users u
                LEFT JOIN tenants t ON t.id = u.tenant_id
                WHERE {base_filters}
                ORDER BY u.full_name ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    total_count = rows[0]["total_count"] if rows else 0
    users = []
    for row in rows:
        data = dict(row)
        data.pop("total_count", None)
        users.append(data)

    # Platform-wide stats, independent of the active filter/pagination so
    # the stat cards always reflect the whole roster, not the current page.
    stats_row = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_users,
                COUNT(*) FILTER (WHERE u.active = true) AS active_users,
                COUNT(*) FILTER (
                    WHERE u.active = true AND EXISTS (
                        SELECT 1 FROM audit_logs al
                        WHERE al.user_id = u.id
                          AND al.action = 'LOGIN_SUCCESS'
                          AND al.created_at >= NOW() - INTERVAL '24 hours'
                    )
                ) AS active_now,
                COUNT(*) FILTER (WHERE u.role = ANY(:agency_admin_roles)) AS agency_admins,
                COUNT(*) FILTER (WHERE u.active = false) AS disabled_users
            FROM users u
            """
        ),
        {"agency_admin_roles": sorted(AGENCY_ADMIN_ROLES)},
    ).mappings().one()

    # Distinct roles actually in use, to populate the Role filter dropdown
    # with real values instead of a hardcoded/guessed list.
    role_rows = db.execute(text("SELECT DISTINCT role FROM users ORDER BY role")).all()
    available_roles = [r[0] for r in role_rows]

    return {
        "users": users,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "stats": dict(stats_row),
        "available_roles": available_roles,
    }


class SetUserActivePayload(BaseModel):
    active: bool


@router.patch("/users/{target_user_id}")
def set_platform_user_active(
    target_user_id: UUID,
    payload: SetUserActivePayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Enable/disable any user across any tenant. Owner-only, cross-tenant
    analog of the tenant-scoped PATCH /staff/{staff_id} toggle."""
    _require_platform_owner(user)

    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target.active = payload.active
    db.commit()

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_ENABLED_USER" if payload.active else "OWNER_DISABLED_USER",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "target_tenant_id": str(target.tenant_id)},
        commit=True,
    )

    return {"user_id": str(target.id), "active": target.active}


@router.post("/users/{target_user_id}/reset-password")
def reset_platform_user_password(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Owner-issued password reset for any user in any tenant. Same
    temp-password + must-change-password + reset-link mechanics as the
    tenant-scoped POST /staff/{staff_id}/reset-password."""
    _require_platform_owner(user)

    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    temp_password = _generate_temp_password()
    target.password_hash = hash_password(temp_password)
    target.must_change_password = True
    reset_link = _issue_password_reset_link(target)
    db.commit()

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_RESET_USER_PASSWORD",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "target_tenant_id": str(target.tenant_id)},
        commit=True,
    )

    return {
        "user_id": str(target.id),
        "email": target.email,
        "temporary_password": temp_password,
        "reset_link": reset_link,
    }


# =========================================================
# SYSTEM HEALTH
# =========================================================

# Security-relevant AUTH/ADMIN actions surfaced on the Security Health
# panel. Sourced from the same AUDIT_CATEGORY_ACTIONS map above -- no
# separate/duplicated action list.
_SECURITY_LOGIN_FAILURE_ACTIONS = ["LOGIN_FAILED"]
_SECURITY_PASSWORD_RESET_ACTIONS = [
    "CHANGE_PASSWORD",
    "PASSWORD_SET_VIA_RESET_LINK",
    "OWNER_RESET_USER_PASSWORD",
]
_SECURITY_PERMISSION_CHANGE_ACTIONS = [
    "OWNER_ENABLED_USER",
    "OWNER_DISABLED_USER",
    "OWNER_SET_TENANT_STATUS",
    "OWNER_SET_TENANT_FINANCIALS",
    "PROVIDER_LINK_REMOVED",
    "PROVIDER_ACCESS_BLOCKED_UNLINKED",
]
_SECURITY_EVENT_ACTIONS = (
    _SECURITY_LOGIN_FAILURE_ACTIONS
    + _SECURITY_PASSWORD_RESET_ACTIONS
    + _SECURITY_PERMISSION_CHANGE_ACTIONS
)


def _safe_scalar_text(db: Session, statement) -> Optional[str]:
    """Like _safe_scalar but for a text-valued scalar (e.g. pg_size_pretty)
    where a failed/unsupported query should surface as None, not 0."""
    try:
        result = db.execute(statement)
        value = result.scalar()
        return str(value) if value is not None else None
    except Exception:
        db.rollback()
        return None


@router.get("/system-health")
def system_health(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Real platform reliability + security signals for the owner-portal
    System Health page. Every field here is measured live against the
    actual database and audit trail -- there is no synthetic per-service
    latency/uptime grid or fabricated AI-engine telemetry, because no
    such infrastructure (microservice mesh, APM, or AI inference service)
    exists in this system today."""
    _require_platform_owner(user)

    # --- Reliability: DB connectivity + measured query latency ---
    db_connected = True
    db_latency_ms: Optional[float] = None
    try:
        started = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - started) * 1000, 2)
    except Exception:
        db_connected = False

    db_size_pretty = _safe_scalar_text(
        db, text("SELECT pg_size_pretty(pg_database_size(current_database()))")
    )

    system_incidents_total = _safe_scalar(db, text("SELECT COUNT(*) FROM incident_reports")) or 0

    recent_incident_rows = (
        db.execute(
            text(
                """
                SELECT
                    ir.id::text AS incident_id,
                    ir.incident_type,
                    ir.incident_severity,
                    ir.incident_date,
                    ir.created_at,
                    COALESCE(t.display_name, t.legal_name, 'Unknown Tenant') AS tenant_name
                FROM incident_reports ir
                LEFT JOIN tenants t ON t.id = ir.tenant_id
                ORDER BY ir.created_at DESC
                LIMIT 10
                """
            )
        )
        .mappings()
        .all()
    )

    backend_uptime_seconds = round(time.monotonic() - _PROCESS_STARTED_AT, 1)

    # --- Security: real failed-login/reset/permission-change counts ---
    def _security_action_count(actions: list[str], hours: int) -> int:
        return (
            _safe_scalar(
                db,
                text(
                    """
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = ANY(:actions)
                      AND created_at >= NOW() - (CAST(:hours AS text) || ' hours')::interval
                    """
                ),
                {"actions": actions, "hours": hours},
            )
            or 0
        )

    failed_logins_24h = _security_action_count(_SECURITY_LOGIN_FAILURE_ACTIONS, 24)
    failed_logins_7d = _security_action_count(_SECURITY_LOGIN_FAILURE_ACTIONS, 24 * 7)
    password_resets_7d = _security_action_count(_SECURITY_PASSWORD_RESET_ACTIONS, 24 * 7)
    permission_changes_7d = _security_action_count(_SECURITY_PERMISSION_CHANGE_ACTIONS, 24 * 7)

    recent_security_rows = (
        db.execute(
            text(
                """
                SELECT
                    al.id::text AS log_id,
                    al.created_at,
                    al.action,
                    al.ip_address,
                    COALESCE(u.full_name, u.email, 'System') AS user_display,
                    COALESCE(t.display_name, t.legal_name, 'Unknown Tenant') AS tenant_name
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.user_id
                LEFT JOIN tenants t ON t.id = al.tenant_id
                WHERE al.action = ANY(:actions)
                ORDER BY al.created_at DESC
                LIMIT 10
                """
            ),
            {"actions": _SECURITY_EVENT_ACTIONS},
        )
        .mappings()
        .all()
    )

    return {
        "reliability": {
            "db_connected": db_connected,
            "db_latency_ms": db_latency_ms,
            "db_size_pretty": db_size_pretty,
            "backend_uptime_seconds": backend_uptime_seconds,
            "system_incidents_total": system_incidents_total,
            "recent_incidents": [dict(row) for row in recent_incident_rows],
        },
        "security": {
            "failed_logins_24h": failed_logins_24h,
            "failed_logins_7d": failed_logins_7d,
            "password_resets_7d": password_resets_7d,
            "permission_changes_7d": permission_changes_7d,
            "recent_events": [dict(row) for row in recent_security_rows],
        },
    }


# =========================================================
# ADOPTION HEALTH ("is anyone actually using the platform")
# =========================================================


@router.get("/adoption-health")
def adoption_health(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Real DAU/WAU/MAU + a 14-day daily-active-user trend, derived
    entirely from the real LOGIN_SUCCESS audit trail (app.api.auth writes
    one of these on every successful login). No feature-level adoption
    percentages are included here -- per-module usage instrumentation
    (e.g. "Notes Module: 94%") does not exist yet in this codebase and
    is intentionally left out rather than fabricated."""
    _require_platform_owner(user)

    def _distinct_active_users(hours: int) -> int:
        return (
            _safe_scalar(
                db,
                text(
                    """
                    SELECT COUNT(DISTINCT user_id)
                    FROM audit_logs
                    WHERE action = 'LOGIN_SUCCESS'
                      AND created_at >= NOW() - (CAST(:hours AS text) || ' hours')::interval
                    """
                ),
                {"hours": hours},
            )
            or 0
        )

    dau = _distinct_active_users(24)
    wau = _distinct_active_users(24 * 7)
    mau = _distinct_active_users(24 * 30)

    trend_rows = (
        db.execute(
            text(
                """
                SELECT
                    date_trunc('day', created_at)::date AS day,
                    COUNT(DISTINCT user_id) AS active_users
                FROM audit_logs
                WHERE action = 'LOGIN_SUCCESS'
                  AND created_at >= NOW() - INTERVAL '14 days'
                GROUP BY 1
                ORDER BY 1
                """
            )
        )
        .mappings()
        .all()
    )

    total_tenants = _safe_scalar(db, text("SELECT COUNT(*) FROM tenants")) or 0
    total_logins_30d = _distinct_active_users(24 * 30)

    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "total_tenants": total_tenants,
        "daily_active_trend": [
            {"date": str(row["day"]), "active_users": row["active_users"]}
            for row in trend_rows
        ],
    }

