# api/owner_admin.py
#
# Platform-owner-only tenant onboarding. Lets the OWNER (platform/vendor
# super-user) add new hospice agency tenants and their initial
# administrator account, without ever touching an existing tenant's
# clinical/patient data.

from __future__ import annotations

from datetime import datetime, timezone
import time
import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.api.staff import _generate_temp_password, _issue_password_reset_link
from app.billing.models.billing_provider_agency_assignment import (
    BillingProviderAgencyAssignment,
    BillingProviderAgencyServiceScope,
    normalize_billing_provider_permission_level,
    normalize_billing_provider_service_scope,
)
from app.billing.models.billing_provider_organization import BillingProviderOrganization
from app.billing.services.billing_provider_access_service import (
    assert_no_conflicting_active_assignment,
    compute_tenant_financials_enabled,
    compute_tenant_financials_enabled_map,
)
from app.core.account_types import ACCOUNT_TYPES, normalize_account_type
from app.core.database import get_db
from app.core.departments import PLATFORM_DEPARTMENTS, normalize_department
from app.core.job_titles import JOB_TITLES_BY_DEPARTMENT, normalize_job_title
from app.core.platforms import AVAILABLE_PLATFORMS, normalize_platform
from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.role_guards import require_owner, require_platform_permission
from app.core.roles import (
    PLATFORM_ROLES,
    PLATFORM_STAFF_STATUSES,
    STAFF_CAPABILITIES,
    NON_DELEGABLE_CAPABILITIES,
    access_level_for_role,
    can_delegate_capability,
    capabilities_for_role,
    is_owner_role,
    is_platform_role,
    normalize_platform_staff_status,
    role_can,
)
from app.core.security import CurrentUser, get_current_user, hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.models.staff_permission_grant import StaffPermissionGrant
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
        "OWNER_CREATED_STAFF",
        "OWNER_UPDATED_STAFF_PROFILE",
        "OWNER_CHANGED_STAFF_ROLE",
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


# ---------------------------------------------------------------------
# AUDIT RISK CLASSIFICATION (owner-approved centralized severity resolver)
#
# The single, centralized, backend-authoritative source of severity for
# every audit event -- app.api.owner_admin._severity_for_event(). The
# frontend never computes or overrides this; it only renders whatever
# `severity` this endpoint returns (see OwnerAuditLogEntry.severity in
# the frontend API client). Most actions resolve via the flat,
# deterministic action -> severity table below; every action name here
# is a real log_event(action=...) call site in this codebase. Unmapped
# actions default to "INFO" (safe default: routine activity), the same
# fallback pattern used by _category_for_action's "DATA" default.
#
# Two actions are context-aware (real blast radius depends on metadata
# already written today, not on the action name alone) and are resolved
# by _severity_for_event() instead of the flat table:
#
#   OWNER_SET_TENANT_STATUS -- suspending/deactivating a tenant cuts off
#   platform access for an entire hospice agency (every clinical/
#   billing/admin user at that tenant) = CRITICAL. Reactivating
#   (new_status == "ACTIVE") is a return to normal operation = INFO.
#
#   OWNER_CHANGED_STAFF_ROLE -- assigning the OWNER role to someone, or
#   demoting/removing an existing OWNER's platform-ownership authority
#   (previous_role == "OWNER" or new_role == "OWNER"), is a Platform
#   Ownership Authority change = CRITICAL, the highest-impact access
#   event in the system (see the Final-Active-Owner safeguards in
#   update_platform_staff_role() above -- this is a real, guarded path,
#   not a hypothetical). Promotion to PLATFORM_ADMIN (broadest non-owner
#   capability bundle, see PLATFORM_PERMISSION_MATRIX in app.core.roles)
#   = HIGH. Every other role change = WARNING (routine, reversible).
# ---------------------------------------------------------------------
AUDIT_SEVERITY_ACTIONS: dict[str, set[str]] = {
    "WARNING": {
        "LOGIN_FAILED",
        "CHANGE_PASSWORD",
        "PASSWORD_SET_VIA_RESET_LINK",
        "OWNER_RESET_USER_PASSWORD",
        "OWNER_DISABLED_USER",
        "OWNER_SUSPENDED_STAFF",
        "OWNER_DELEGATED_STAFF_PERMISSION",
        "OWNER_REVOKED_STAFF_PERMISSION",
        "PAYER_VALIDATION_FAILED",
        "BILLING_GENERATION_FAILED",
        "PROVIDER_SIGNATURE_ACCESS_DENIED",
        "PROVIDER_LINK_REMOVED",
        "PROVIDER_ACCESS_BLOCKED_UNLINKED",
        "RNICA_AMENDMENT_DENIED",
        "ADMISSION_ACTION_REQUEST_CANCELED",
    },
    "HIGH": {
        "OWNER_REVOKED_STAFF_ACCESS",
        "OWNER_REMOVED_STAFF",
        "RNICA_HOPE_UNLOCKED",
    },
    # CRITICAL is intentionally empty in the flat table -- both of its
    # real members (OWNER_SET_TENANT_STATUS, OWNER_CHANGED_STAFF_ROLE)
    # are context-conditional and resolved by _severity_for_event below,
    # not listed here as an unconditional action->severity mapping.
    "CRITICAL": set(),
}

_ACTION_TO_SEVERITY: dict[str, str] = {
    action: severity
    for severity, actions in AUDIT_SEVERITY_ACTIONS.items()
    for action in actions
}

# Tenant-status values that cut off platform access for an entire
# agency -- see the module docstring above.
_TENANT_STATUS_CRITICAL_VALUES = {"SUSPENDED", "INACTIVE"}

# Role-change severity boundary: the broadest non-owner capability
# bundle (see PLATFORM_PERMISSION_MATRIX in app.core.roles) is the
# highest-impact *non-ownership* role assignment that exists today.
_HIGH_IMPACT_ROLE_ASSIGNMENTS = {"PLATFORM_ADMIN"}


def _severity_for_event(action: str, metadata: dict | None) -> str:
    """Single, centralized, authoritative severity resolver. `metadata`
    is the same event_metadata JSON already stored on the audit_logs
    row -- never re-derived, guessed, or computed on the frontend."""
    meta = metadata or {}

    if action == "OWNER_SET_TENANT_STATUS":
        new_status = str(meta.get("new_status") or "").strip().upper()
        if new_status in _TENANT_STATUS_CRITICAL_VALUES:
            return "CRITICAL"
        return "INFO"

    if action == "OWNER_CHANGED_STAFF_ROLE":
        previous_role = str(meta.get("previous_role") or "").strip().upper()
        new_role = str(meta.get("new_role") or "").strip().upper()
        if previous_role == "OWNER" or new_role == "OWNER":
            return "CRITICAL"
        if new_role in _HIGH_IMPACT_ROLE_ASSIGNMENTS:
            return "HIGH"
        return "WARNING"

    return _ACTION_TO_SEVERITY.get(action, "INFO")


def _affected_permissions_for_role_change(metadata: dict | None) -> dict | None:
    """Affected Permissions for an OWNER_CHANGED_STAFF_ROLE event -- reuses
    the SAME authoritative RBAC source SNS Staff & Access already uses
    (app.core.roles.capabilities_for_role / PLATFORM_PERMISSION_MATRIX),
    with no direct_grants (this is the role-default baseline diff only;
    a target's individually delegated grants are a separate, unrelated
    concept and are intentionally not folded in here, per the approved
    scope). Returns None when there isn't a real previous/new role pair
    to diff -- never a fabricated or guessed permission name."""
    meta = metadata or {}
    previous_role = str(meta.get("previous_role") or "").strip().upper()
    new_role = str(meta.get("new_role") or "").strip().upper()
    if not previous_role or not new_role or previous_role == new_role:
        return None
    if previous_role not in PLATFORM_ROLES or new_role not in PLATFORM_ROLES:
        return None
    before = set(capabilities_for_role(previous_role))
    after = set(capabilities_for_role(new_role))
    return {
        "previous_role": previous_role,
        "new_role": new_role,
        "added": sorted(after - before),
        "removed": sorted(before - after),
    }


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


def _is_platform_staff_account(target: Optional[User]) -> bool:
    """True for a genuine SNS platform-staff account: role membership in
    PLATFORM_ROLES (app.core.roles) is the authoritative, already-tested
    isolation boundary for the SNS Staff & Access surface (see
    tests/test_owner_platform_staff_scope.py) -- deliberately independent
    of which tenant row the account happens to be parented under."""
    return target is not None and is_platform_role(target.role)


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
    financials_map = compute_tenant_financials_enabled_map(
        db,
        [UUID(row["tenant_id"]) for row in rows],
    )
    tenants = []
    for row in rows:
        payload = dict(row)
        payload["financials_enabled"] = financials_map.get(UUID(payload["tenant_id"]), False)
        tenants.append(payload)
    return {"tenants": tenants}


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
        "financials_enabled": compute_tenant_financials_enabled(db, tenant.id),
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
    class ServiceScopeEntry(BaseModel):
        scope: str
        permission_level: str = Field(default="VIEW")

        @field_validator("scope")
        @classmethod
        def _scope_valid(cls, value: str) -> str:
            return normalize_billing_provider_service_scope(value)

        @field_validator("permission_level")
        @classmethod
        def _permission_level_valid(cls, value: str) -> str:
            return normalize_billing_provider_permission_level(value)

    financials_enabled: bool
    billing_provider_organization_id: UUID | None = None
    effective_start_at: datetime | None = None
    effective_end_at: datetime | None = None
    service_scopes: list[ServiceScopeEntry] = Field(default_factory=list)
    change_reason: str | None = Field(default=None, max_length=1000)

    @field_validator("service_scopes", mode="before")
    @classmethod
    def _service_scope_valid(cls, values) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for value in values:
            if isinstance(value, str):
                value = {"scope": value, "permission_level": "VIEW"}
            elif isinstance(value, cls.ServiceScopeEntry):
                value = value.model_dump()
            elif not isinstance(value, dict):
                raise ValueError("service_scopes entries must be strings or {scope, permission_level} objects")
            scope = normalize_billing_provider_service_scope(value.get("scope", ""))
            permission_level = normalize_billing_provider_permission_level(
                value.get("permission_level")
            )
            if scope not in seen:
                normalized.append(
                    {
                        "scope": scope,
                        "permission_level": permission_level,
                    }
                )
                seen.add(scope)
        return normalized

    @field_validator("change_reason")
    @classmethod
    def _change_reason_trimmed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @model_validator(mode="after")
    def _validate_financials_transition(self):
        if self.financials_enabled:
            if self.billing_provider_organization_id is None:
                raise ValueError("billing_provider_organization_id is required when turning Financials on")
            if self.effective_start_at is None:
                raise ValueError("effective_start_at is required when turning Financials on")
            if not self.service_scopes:
                raise ValueError("service_scopes must contain at least one value when turning Financials on")
            if (
                self.effective_end_at is not None
                and self.effective_start_at is not None
                and self.effective_end_at < self.effective_start_at
            ):
                raise ValueError("effective_end_at must be on or after effective_start_at")
        return self


def _current_financials_assignment(db: Session, tenant_id: UUID):
    now = datetime.now(timezone.utc)
    return (
        db.query(BillingProviderAgencyAssignment)
        .join(
            BillingProviderOrganization,
            BillingProviderOrganization.id
            == BillingProviderAgencyAssignment.billing_provider_organization_id,
        )
        .join(
            BillingProviderAgencyServiceScope,
            BillingProviderAgencyServiceScope.assignment_id == BillingProviderAgencyAssignment.id,
        )
        .filter(
            BillingProviderAgencyAssignment.tenant_id == tenant_id,
            BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
            BillingProviderOrganization.status == "ACTIVE",
            BillingProviderAgencyAssignment.effective_start_at <= now,
            or_(
                BillingProviderAgencyAssignment.effective_end_at.is_(None),
                BillingProviderAgencyAssignment.effective_end_at >= now,
            ),
        )
        .order_by(BillingProviderAgencyAssignment.effective_start_at.desc())
        .first()
    )


def _tenant_financials_response(db: Session, tenant_id: UUID) -> dict:
    assignment = _current_financials_assignment(db, tenant_id)
    return {
        "tenant_id": str(tenant_id),
        "financials_enabled": compute_tenant_financials_enabled(db, tenant_id),
        "current_assignment": None
        if assignment is None
        else {
            "assignment_id": str(assignment.id),
            "billing_provider_organization_id": str(
                assignment.billing_provider_organization_id
            ),
            "relationship_status": assignment.relationship_status,
            "effective_start_at": assignment.effective_start_at.isoformat()
            if assignment.effective_start_at
            else None,
            "effective_end_at": assignment.effective_end_at.isoformat()
            if assignment.effective_end_at
            else None,
            "service_scopes": [
                {
                    "scope": scope.scope,
                    "permission_level": scope.permission_level,
                }
                for scope in assignment.service_scopes
            ],
        },
    }


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
    actor_user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    previous_value = compute_tenant_financials_enabled(db, tenant.id)

    if payload.financials_enabled:
        provider = db.get(BillingProviderOrganization, payload.billing_provider_organization_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Billing provider organization not found")
        if provider.status != "ACTIVE":
            raise HTTPException(
                status_code=409,
                detail="Billing provider organization must be ACTIVE to enable Financials.",
            )

        assert_no_conflicting_active_assignment(
            db,
            tenant_id=tenant.id,
            billing_provider_organization_id=provider.id,
            effective_start_at=payload.effective_start_at,
            effective_end_at=payload.effective_end_at,
        )

        row = (
            db.query(BillingProviderAgencyAssignment)
            .filter(
                BillingProviderAgencyAssignment.tenant_id == tenant.id,
                BillingProviderAgencyAssignment.billing_provider_organization_id == provider.id,
                BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
            )
            .order_by(BillingProviderAgencyAssignment.effective_start_at.desc())
            .first()
        )
        if row is None:
            row = BillingProviderAgencyAssignment(
                billing_provider_organization_id=provider.id,
                tenant_id=tenant.id,
                relationship_status="ACTIVE",
                effective_start_at=payload.effective_start_at,
                effective_end_at=payload.effective_end_at,
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            db.add(row)
        else:
            row.relationship_status = "ACTIVE"
            row.effective_start_at = payload.effective_start_at
            row.effective_end_at = payload.effective_end_at
            row.updated_by = actor_user_id
        row.service_scopes[:] = [
            BillingProviderAgencyServiceScope(
                scope=scope.scope,
                permission_level=scope.permission_level,
            )
            for scope in payload.service_scopes
        ]
    else:
        end_at = payload.effective_end_at or datetime.now(timezone.utc)
        active_rows = (
            db.query(BillingProviderAgencyAssignment)
            .filter(
                BillingProviderAgencyAssignment.tenant_id == tenant.id,
                BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
            )
            .all()
        )
        for row in active_rows:
            if end_at < row.effective_start_at:
                raise HTTPException(
                    status_code=400,
                    detail="effective_end_at cannot be earlier than the active assignment start.",
                )
            row.relationship_status = "TERMINATED"
            row.effective_end_at = end_at
            row.updated_by = actor_user_id

    db.commit()
    db.refresh(tenant)

    log_event(
        db=db,
        user_id=str(actor_user_id),
        tenant_id=str(tenant.id),
        role=str(getattr(user, "role", None) or "OWNER"),
        action="OWNER_SET_TENANT_FINANCIALS",
        entity_type="tenant",
        entity_id=str(tenant.id),
        metadata={
            "legal_name": tenant.legal_name,
            "previous_financials_enabled": previous_value,
            "new_financials_enabled": compute_tenant_financials_enabled(db, tenant.id),
            "billing_provider_organization_id": str(payload.billing_provider_organization_id)
            if payload.billing_provider_organization_id
            else None,
            "effective_start_at": payload.effective_start_at.isoformat()
            if payload.effective_start_at
            else None,
            "effective_end_at": payload.effective_end_at.isoformat()
            if payload.effective_end_at
            else None,
            "service_scopes": [scope.model_dump() for scope in payload.service_scopes],
            "change_reason": payload.change_reason,
        },
        commit=True,
    )
    return _tenant_financials_response(db, tenant.id)


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
    entity_type: Optional[str] = Query(
        None,
        description=(
            "Exact entity_type match (e.g. 'user'). Used by the SNS Staff & "
            "Access page's Audit tab to scope the platform-wide audit trail "
            "to staff/identity lifecycle events only, without duplicating "
            "the standalone Audit Logs page's full feed."
        ),
    ),
    entity_id: Optional[str] = Query(
        None,
        description=(
            "Exact entity_id match. Used by the Audit Logs Event Details "
            "drawer to fetch the full Related Events history for one "
            "record (not just the currently loaded page), mirroring the "
            "same entity_type/entity_id lookup already used internally by "
            "the SNS Staff & Access per-user audit tab."
        ),
    ),
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
    normalized_entity_type = (entity_type or "").strip().lower() or None
    normalized_entity_id = (entity_id or "").strip() or None

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
        AND (CAST(:entity_type AS text) IS NULL OR al.entity_type = :entity_type)
        AND (CAST(:entity_id AS text) IS NULL OR al.entity_id = :entity_id)
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
        "entity_type": normalized_entity_type,
        "entity_id": normalized_entity_id,
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
                    al.request_id::text AS request_id,
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
        data["severity"] = _severity_for_event(data["action"], data["event_metadata"])
        data["affected_permissions"] = (
            _affected_permissions_for_role_change(data["event_metadata"])
            if data["action"] == "OWNER_CHANGED_STAFF_ROLE"
            else None
        )
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
# SNS PLATFORM STAFF & ACCESS (SNS Hospice Solutions personnel only,
# owner-only)
#
# Scope rule (authoritative, per platform-owner design decision): this
# endpoint set manages SNS Hospice Solutions vendor/platform staff
# ONLY -- i.e. accounts whose role is in app.core.roles.PLATFORM_ROLES
# (OWNER, PLATFORM_SUPPORT, PLATFORM_BILLING, PLATFORM_OPERATIONS,
# PLATFORM_AI_MANAGEMENT, PLATFORM_COMPLIANCE). It must never list,
# enable/disable, or reset the password of a tenant-agency or
# billing-organization user -- those accounts are managed inside their
# own tenant's/biller's environment. Any cross-tenant "support access"
# to a tenant account is a separate, explicitly-audited capability and
# is intentionally NOT part of this surface.
# =========================================================

# Platform roles considered to carry elevated/privileged platform authority
# (vs. routine department staff), for the "Privileged Accounts" stat.
PRIVILEGED_PLATFORM_ROLES = {"OWNER", "PLATFORM_OPERATIONS", "PLATFORM_COMPLIANCE"}


@router.get("/users", dependencies=[Depends(require_platform_permission("staff.view"))])
def list_platform_users(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    search: Optional[str] = Query(None, max_length=200),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
    account_types: Optional[str] = Query(
        None,
        description=(
            "Comma-separated list of account types (e.g. "
            "'SERVICE_ACCOUNT,AUTOMATION_ACCOUNT'). Used by the SNS Staff & "
            "Access UI's Human Staff / Service Accounts / API Identities tabs "
            "to scope to more than one account_type at once -- distinct from "
            "the single-value account_type filter above."
        ),
    ),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Real SNS Hospice Solutions staff roster backing the owner-portal
    Staff & Access page. Reads the same `users` table every tenant's
    staff roster already lives in (app/api/staff.py is tenant-scoped
    only -- this is the platform-staff-only analog for the platform
    owner), but is hard-scoped to PLATFORM_ROLES so no tenant-agency or
    biller account is ever returned. `last_login` is derived from the
    real `LOGIN_SUCCESS` audit events written by app/api/auth.py (there
    is no last_login column on `users`). Gated by staff.view (Phase UM-3) --
    every specialized platform role that can see the roster at all needs
    real, delegable view access, not an OWNER-only gate."""

    if status is not None:
        status = status.strip().upper()
        if status not in PLATFORM_STAFF_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"status must be one of {sorted(PLATFORM_STAFF_STATUSES)}",
            )

    normalized_search = (search or "").strip() or None
    search_pattern = f"%{normalized_search}%" if normalized_search else None
    normalized_role = (role or "").strip().upper() or None
    if normalized_role is not None and normalized_role not in PLATFORM_ROLES:
        raise HTTPException(
            status_code=400,
            detail="role must be one of the SNS platform roles.",
        )

    try:
        normalized_department = normalize_department(department)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized_platform: Optional[str] = None
    if platform is not None and platform.strip():
        try:
            normalized_platform = normalize_platform(platform)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized_account_type = (account_type or "").strip().upper() or None
    if normalized_account_type is not None and normalized_account_type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"account_type must be one of {sorted(ACCOUNT_TYPES)}",
        )

    normalized_account_types_list: Optional[list[str]] = None
    if account_types is not None and account_types.strip():
        normalized_account_types_list = [
            part.strip().upper() for part in account_types.split(",") if part.strip()
        ]
        invalid = [t for t in normalized_account_types_list if t not in ACCOUNT_TYPES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"account_types must each be one of {sorted(ACCOUNT_TYPES)}",
            )

    base_filters = """
        u.role = ANY(:platform_roles)
        AND (CAST(:role AS text) IS NULL OR u.role = :role)
        AND (
            CAST(:status AS text) IS NOT NULL AND u.platform_staff_status = :status
            OR CAST(:status AS text) IS NULL AND u.platform_staff_status <> 'REMOVED'
        )
        AND (CAST(:department AS text) IS NULL OR u.department = :department)
        AND (CAST(:platform AS text) IS NULL OR u.platform = :platform)
        AND (CAST(:account_type AS text) IS NULL OR u.account_type = :account_type)
        AND (CAST(:account_types_list AS text[]) IS NULL OR u.account_type = ANY(:account_types_list))
        AND (
            CAST(:search_pattern AS text) IS NULL
            OR u.full_name ILIKE :search_pattern
            OR u.email ILIKE :search_pattern
        )
    """

    params = {
        "platform_roles": sorted(PLATFORM_ROLES),
        "role": normalized_role,
        "status": status,
        "department": normalized_department,
        "platform": normalized_platform,
        "account_type": normalized_account_type,
        "account_types_list": normalized_account_types_list,
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
                    u.platform_staff_status,
                    u.department,
                    u.account_type,
                    u.job_title,
                    u.platform,
                    u.identity_purpose AS purpose,
                    u.identity_scope AS scope,
                    u.responsible_owner_id::text AS responsible_owner_id,
                    ro.full_name AS responsible_owner_name,
                    (
                        SELECT MAX(al.created_at)
                        FROM audit_logs al
                        WHERE al.user_id = u.id AND al.action = 'LOGIN_SUCCESS'
                    ) AS last_login,
                    COUNT(*) OVER() AS total_count
                FROM users u
                LEFT JOIN users ro ON ro.id = u.responsible_owner_id
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
    actor_grants = _active_grant_capabilities(db, user.user_id)
    for row in rows:
        data = dict(row)
        data["access_level"] = access_level_for_role(data["role"])
        data.pop("total_count", None)
        # Per-row, backend-enforced action visibility -- mirrors the exact
        # ceiling role_can() applies on write (including this actor's own
        # delegated grants, Phase UM-3), so the frontend never has to
        # duplicate/guess the RBAC hierarchy for row actions.
        data["allowed_actions"] = {
            "edit_profile": role_can(user.role, "staff.edit_profile", target_role=data["role"], actor_direct_grants=actor_grants),
            "assign_role": role_can(user.role, "staff.assign_role", target_role=data["role"], actor_direct_grants=actor_grants),
            "activate": role_can(user.role, "staff.activate", target_role=data["role"], actor_direct_grants=actor_grants),
            "suspend": role_can(user.role, "staff.suspend", target_role=data["role"], actor_direct_grants=actor_grants),
            "disable": role_can(user.role, "staff.disable", target_role=data["role"], actor_direct_grants=actor_grants),
            "revoke_access": role_can(user.role, "staff.revoke_access", target_role=data["role"], actor_direct_grants=actor_grants),
            "reset_password": role_can(user.role, "staff.reset_password", target_role=data["role"], actor_direct_grants=actor_grants),
            "remove": role_can(user.role, "staff.remove", target_role=data["role"], actor_direct_grants=actor_grants),
        }
        users.append(data)

    # Platform-staff-wide stats, independent of the active filter/pagination
    # so the stat cards always reflect the whole SNS roster, not the
    # current page.
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
                COUNT(*) FILTER (WHERE u.role = ANY(:privileged_roles)) AS privileged_accounts,
                COUNT(*) FILTER (WHERE u.active = false) AS disabled_users,
                COUNT(*) FILTER (WHERE u.platform_staff_status = 'SUSPENDED') AS suspended_users,
                (
                    SELECT COUNT(*) FROM users u2
                    WHERE u2.role = ANY(:platform_roles) AND u2.platform_staff_status = 'REMOVED'
                ) AS removed_users,
                COUNT(*) FILTER (WHERE u.role = 'OWNER' AND u.active = true) AS active_owners,
                COUNT(*) FILTER (WHERE u.account_type = 'SERVICE_ACCOUNT') AS service_accounts,
                COUNT(*) FILTER (WHERE u.account_type = 'AUTOMATION_ACCOUNT') AS automation_accounts,
                COUNT(*) FILTER (WHERE u.account_type = 'API_CLIENT') AS api_clients
            FROM users u
            WHERE u.role = ANY(:platform_roles)
              AND u.platform_staff_status <> 'REMOVED'
            """
        ),
        {
            "privileged_roles": sorted(PRIVILEGED_PLATFORM_ROLES),
            "platform_roles": sorted(PLATFORM_ROLES),
        },
    ).mappings().one()

    # All valid SNS platform roles (not just roles currently assigned to
    # an existing account) -- this populates both the Role filter
    # dropdown and, critically, the Add/Change-Role selectors, which must
    # offer every role a new or existing account could be assigned, not
    # just roles already in use.
    available_roles = sorted(PLATFORM_ROLES)

    return {
        "users": users,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "stats": dict(stats_row),
        "available_roles": available_roles,
        # Derived (never independently editable) Access Level per role,
        # mirroring app.core.roles.ACCESS_LEVEL_FOR_ROLE. Lets the Add
        # Staff form preview "Access Level (derived)" live as a role is
        # selected, without duplicating/hardcoding the tier mapping on
        # the frontend.
        "access_levels_by_role": {role: access_level_for_role(role) for role in available_roles},
        # All 12 approved platform departments (not just ones in use) so
        # the "Add SNS Staff" form always offers the full taxonomy -- see
        # app/core/departments.py. Purely presentational; grants nothing.
        "available_departments": sorted(PLATFORM_DEPARTMENTS),
        # Known SNS platforms (SNS Hospice Solutions is the only staffed
        # one today; SNS Home Health Solutions / SNS Scribe are real,
        # planned future platforms under the same SNS Tech Solutions
        # Owner Platform -- listed now so Platform is selectable without a
        # later redesign). See app/core/platforms.py.
        "available_platforms": AVAILABLE_PLATFORMS,
        # Department-scoped Job Title catalog (Platform > Department >
        # Job Title > Platform Role > Access Level). Frontend keys into
        # this by the selected Department to drive a cascading Job Title
        # selector. Departments absent from this map (e.g. Platform
        # Administration) have no catalog yet and accept free text -- see
        # app/core/job_titles.py.
        "job_titles_by_department": {
            department: sorted(titles) for department, titles in JOB_TITLES_BY_DEPARTMENT.items()
        },
        # All 4 approved account types, for the "Add SNS Staff" form's
        # Account Type selector. Purely presentational; grants nothing.
        "available_account_types": sorted(ACCOUNT_TYPES),
        # The calling actor's own real, backend-derived capability grants --
        # lets the frontend show/hide "+ Add Staff", row actions, etc.
        # without duplicating/hardcoding the permission matrix.
        "actor_capabilities": capabilities_for_role(user.role),
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
    """Enable/disable an SNS platform-staff account.

    Delegable (Phase UM-3): gated by staff.activate / staff.disable via
    role_can() (role default OR this actor's own active delegated grant),
    not OWNER-only -- Platform Administrator holds both by default and may
    delegate either individually. Kept for backward compatibility; prefer
    PATCH /users/{id}/status for the full ACTIVE/SUSPENDED/DISABLED model.

    Scoped to PLATFORM_ROLES only -- this endpoint must never be used to
    enable/disable a tenant-agency or billing-organization user. Those
    accounts are managed inside their own tenant's/biller's environment."""
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not _is_platform_staff_account(target):
        raise HTTPException(
            status_code=403,
            detail="This endpoint only manages SNS platform staff accounts.",
        )

    capability = "staff.activate" if payload.active else "staff.disable"
    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not role_can(user.role, capability, target_role=target.role, actor_direct_grants=actor_grants):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to {'activate' if payload.active else 'disable'} this SNS staff member.",
        )

    # Final-Active-Owner safeguard (approved SNS Staff & Access
    # architecture): the last remaining active Platform Owner can never be
    # disabled -- there must always be at least one to administer the
    # platform.
    if (
        not payload.active
        and target.role == "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=409,
            detail="The final active Platform Owner cannot be disabled.",
        )

    target.active = payload.active
    target.platform_staff_status = "ACTIVE" if payload.active else "DISABLED"
    target.updated_by = user.user_id
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

    return {"user_id": str(target.id), "active": target.active, "platform_staff_status": target.platform_staff_status}


class SetPlatformStaffStatusPayload(BaseModel):
    """Full 4-state lifecycle status change (ACTIVE / SUSPENDED /
    DISABLED). REMOVED is intentionally NOT settable here -- use
    POST /users/{id}/remove, which requires a reason and enforces
    additional no-self-removal / no-hard-delete guarantees."""

    status: str
    reason: Optional[str] = None

    @field_validator("status")
    @classmethod
    def _status_is_settable(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        settable = PLATFORM_STAFF_STATUSES - {"REMOVED"}
        if normalized not in settable:
            raise ValueError(f"status must be one of {sorted(settable)}")
        return normalized


_STATUS_CAPABILITY = {
    "ACTIVE": "staff.activate",
    "SUSPENDED": "staff.suspend",
    "DISABLED": "staff.disable",
}
_STATUS_AUDIT_ACTION = {
    "ACTIVE": "OWNER_ACTIVATED_STAFF",
    "SUSPENDED": "OWNER_SUSPENDED_STAFF",
    "DISABLED": "OWNER_DISABLED_USER",
}


@router.patch("/users/{target_user_id}/status")
def set_platform_staff_status(
    target_user_id: UUID,
    payload: SetPlatformStaffStatusPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Distinct ACTIVE / SUSPENDED / DISABLED lifecycle transition (Phase
    UM-3). SUSPENDED is a temporary, expected-to-be-reversible hold
    (investigation/leave/temporary restriction); DISABLED is an
    administrative block that still allows later reactivation. Each
    transition is gated by its own delegable capability -- Platform
    Compliance may hold staff.suspend for compliance-related restrictions
    without also holding staff.disable or staff.remove."""
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not _is_platform_staff_account(target):
        raise HTTPException(
            status_code=403,
            detail="This endpoint only manages SNS platform staff accounts.",
        )

    capability = _STATUS_CAPABILITY[payload.status]
    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not role_can(user.role, capability, target_role=target.role, actor_direct_grants=actor_grants):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to set this SNS staff member's status to {payload.status}.",
        )

    if (
        payload.status != "ACTIVE"
        and target.role == "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=409,
            detail="The final active Platform Owner cannot be suspended or disabled.",
        )

    previous_status = normalize_platform_staff_status(target.platform_staff_status)
    target.platform_staff_status = payload.status
    target.active = payload.status == "ACTIVE"
    target.updated_by = user.user_id
    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action=_STATUS_AUDIT_ACTION[payload.status],
        entity_type="user",
        entity_id=str(target.id),
        metadata={
            "target_email": target.email,
            "previous_status": previous_status,
            "new_status": payload.status,
            "reason": payload.reason,
        },
        commit=True,
    )

    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


class RevokeAccessPayload(BaseModel):
    reason: Optional[str] = None


@router.post("/users/{target_user_id}/revoke-access")
def revoke_platform_staff_access(
    target_user_id: UUID,
    payload: RevokeAccessPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Revoke Access is an ACTION distinct from Suspend/Disable, with its
    own audit trail entry -- for human staff it resolves to the DISABLED
    status (not a 5th "REVOKED" status; see the approved SNS Staff &
    Access status model). Delegable via staff.revoke_access -- Platform
    Security holds this by default for security-related access actions."""
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not _is_platform_staff_account(target):
        raise HTTPException(
            status_code=403,
            detail="This endpoint only manages SNS platform staff accounts.",
        )

    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not role_can(user.role, "staff.revoke_access", target_role=target.role, actor_direct_grants=actor_grants):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to revoke this SNS staff member's access.",
        )

    if (
        target.role == "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=409,
            detail="The final active Platform Owner's access cannot be revoked.",
        )

    previous_status = normalize_platform_staff_status(target.platform_staff_status)
    target.platform_staff_status = "DISABLED"
    target.active = False
    target.updated_by = user.user_id
    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_REVOKED_STAFF_ACCESS",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "previous_status": previous_status, "reason": payload.reason},
        commit=True,
    )

    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


class RemoveStaffPayload(BaseModel):
    reason: str = Field(min_length=1)


@router.post("/users/{target_user_id}/remove")
def remove_platform_staff(
    target_user_id: UUID,
    payload: RemoveStaffPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Remove Staff -- a Staff Lifecycle action (delegable via
    staff.remove; Platform Administrator holds it by default), NOT
    Ownership Continuity. Soft-removal only: sets platform_staff_status
    to REMOVED and active=false (authentication blocked), but NEVER
    hard-deletes the row -- identity, audit history, ownership/
    responsible-owner references, and historical attribution all survive.
    A required `reason` is captured in the audit event."""
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not _is_platform_staff_account(target):
        raise HTTPException(
            status_code=403,
            detail="This endpoint only manages SNS platform staff accounts.",
        )
    if target.id == user.user_id:
        raise HTTPException(status_code=403, detail="You cannot remove your own SNS staff account.")

    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not role_can(user.role, "staff.remove", target_role=target.role, actor_direct_grants=actor_grants):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to remove this SNS staff member.",
        )

    # Final-Active-Owner safeguard: the last remaining active Platform
    # Owner can never be removed -- there must always be at least one.
    if (
        target.role == "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=409,
            detail="The final active Platform Owner cannot be removed.",
        )

    if normalize_platform_staff_status(target.platform_staff_status) == "REMOVED":
        raise HTTPException(status_code=409, detail="This SNS staff account has already been removed.")

    previous_status = normalize_platform_staff_status(target.platform_staff_status)
    target.platform_staff_status = "REMOVED"
    target.active = False
    target.updated_by = user.user_id
    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_REMOVED_STAFF",
        entity_type="user",
        entity_id=str(target.id),
        metadata={
            "target_email": target.email,
            "previous_status": previous_status,
            "reason": payload.reason,
        },
        commit=True,
    )

    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


# =========================================================
# SNS STAFF & ACCESS -- DELEGATED PERMISSION GRANTS (Phase UM-3)
#
# "Problems escalate upward, work delegates downward": a Platform Owner
# or Platform Administrator may delegate an individual `staff.*`
# capability to an eligible SNS platform identity without changing their
# Platform Role. See app.core.roles.can_delegate_capability for the
# authoritative delegation-eligibility rule (delegable capability + actor
# has delegation authority + actor already effectively holds the
# capability for that target) and NON_DELEGABLE_CAPABILITIES for what can
# never be delegated this way (Ownership Continuity).
# =========================================================


class GrantPermissionPayload(BaseModel):
    capability: str
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("capability")
    @classmethod
    def _capability_is_known(cls, value: str) -> str:
        normalized = (value or "").strip()
        if normalized not in STAFF_CAPABILITIES:
            raise ValueError(f"capability must be one of {sorted(STAFF_CAPABILITIES)}")
        return normalized


def _serialize_grant(grant: StaffPermissionGrant, db: Session) -> dict:
    granted_by = db.get(User, grant.granted_by_user_id)
    revoked_by = db.get(User, grant.revoked_by_user_id) if grant.revoked_by_user_id else None
    return {
        "grant_id": str(grant.id),
        "capability": grant.capability,
        "granted_by_user_id": str(grant.granted_by_user_id),
        "granted_by_name": granted_by.full_name if granted_by else None,
        "granted_at": grant.granted_at or grant.created_at,
        "reason": grant.reason,
        "expires_at": grant.expires_at,
        "revoked_at": grant.revoked_at,
        "revoked_by_user_id": str(grant.revoked_by_user_id) if grant.revoked_by_user_id else None,
        "revoked_by_name": revoked_by.full_name if revoked_by else None,
        "revoke_reason": grant.revoke_reason,
        "is_active": grant.revoked_at is None and (grant.expires_at is None or grant.expires_at > _now()),
    }


@router.get(
    "/users/{target_user_id}/permissions",
    dependencies=[Depends(require_platform_permission("staff.view"))],
)
def get_platform_staff_permissions(
    target_user_id: UUID,
    db: Session = Depends(get_db),
):
    """Effective-permission resolution for the Access tab's "Responsibility
    Assignment" section: role defaults, this account's active delegated
    grants, revoked/expired grant history, the resulting effective set,
    and (for transparency) every capability this account does NOT have,
    with why -- not granted, Owner-only, or blocked by the assignment
    ceiling."""
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    all_grants = (
        db.query(StaffPermissionGrant)
        .filter(StaffPermissionGrant.target_user_id == target.id)
        .order_by(StaffPermissionGrant.created_at.desc())
        .all()
    )
    active_grant_caps = _active_grant_capabilities(db, target.id)
    role_defaults = capabilities_for_role(target.role)
    effective = capabilities_for_role(target.role, active_grant_caps)

    denied = []
    for capability in sorted(STAFF_CAPABILITIES):
        if capability in effective:
            continue
        if capability in NON_DELEGABLE_CAPABILITIES:
            reason = "owner_only"
        elif target.role == "OWNER":
            reason = None  # unreachable -- OWNER effective == all capabilities
        else:
            reason = "not_granted"
        denied.append({"capability": capability, "reason": reason})

    return {
        "user_id": str(target.id),
        "role": target.role,
        "role_defaults": role_defaults,
        "delegated_grants": [_serialize_grant(g, db) for g in all_grants],
        "effective_permissions": effective,
        "denied_permissions": denied,
    }


@router.post("/users/{target_user_id}/permissions", status_code=201)
def grant_platform_staff_permission(
    target_user_id: UUID,
    payload: GrantPermissionPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Delegate one `staff.*` capability to an eligible SNS platform
    identity. The actor must hold delegation authority (OWNER or Platform
    Administrator) AND already effectively hold the capability for this
    target (an actor can never delegate authority they do not themselves
    have, and never above their own assignment ceiling)."""
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not can_delegate_capability(
        user.role, payload.capability, target_role=target.role, actor_direct_grants=actor_grants
    ):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have authority to delegate '{payload.capability}' to this SNS staff member.",
        )

    if payload.expires_at is not None and payload.expires_at <= _now():
        raise HTTPException(status_code=400, detail="expires_at must be in the future.")

    grant = StaffPermissionGrant(
        target_user_id=target.id,
        capability=payload.capability,
        granted_by_user_id=user.user_id,
        granted_at=_now(),
        reason=payload.reason,
        expires_at=payload.expires_at,
        created_by=user.user_id,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_DELEGATED_STAFF_PERMISSION",
        entity_type="user",
        entity_id=str(target.id),
        metadata={
            "target_email": target.email,
            "capability": payload.capability,
            "reason": payload.reason,
            "expires_at": payload.expires_at.isoformat() if payload.expires_at else None,
        },
        commit=True,
    )

    return _serialize_grant(grant, db)


class RevokePermissionPayload(BaseModel):
    reason: Optional[str] = None


@router.delete("/users/{target_user_id}/permissions/{grant_id}")
def revoke_platform_staff_permission(
    target_user_id: UUID,
    grant_id: UUID,
    payload: RevokePermissionPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Revoke a previously delegated capability. Recalculates effective
    permissions immediately (the grant row is kept, marked revoked, for
    its own audit trail -- never hard-deleted)."""
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    grant = db.get(StaffPermissionGrant, grant_id)
    if grant is None or grant.target_user_id != target.id:
        raise HTTPException(status_code=404, detail="Permission grant not found")
    if grant.revoked_at is not None:
        raise HTTPException(status_code=409, detail="This permission grant has already been revoked.")

    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not can_delegate_capability(
        user.role, grant.capability, target_role=target.role, actor_direct_grants=actor_grants
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have authority to revoke this delegated permission.",
        )

    grant.revoked_at = _now()
    grant.revoked_by_user_id = user.user_id
    grant.revoke_reason = payload.reason
    db.commit()
    db.refresh(grant)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_REVOKED_STAFF_PERMISSION",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "capability": grant.capability, "reason": payload.reason},
        commit=True,
    )

    return _serialize_grant(grant, db)


@router.post("/users/{target_user_id}/reset-password")
def reset_platform_user_password(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Password reset for an SNS platform-staff account -- delegable via
    staff.reset_password (Platform Administrator by default; Platform
    Support may hold it as a routine account-recovery function). Same
    temp-password + must-change-password + reset-link mechanics as the
    tenant-scoped POST /staff/{staff_id}/reset-password.

    Scoped to PLATFORM_ROLES only -- see set_platform_user_active above."""
    target = db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not _is_platform_staff_account(target):
        raise HTTPException(
            status_code=403,
            detail="This endpoint only manages SNS platform staff accounts.",
        )

    actor_grants = _active_grant_capabilities(db, user.user_id)
    if not role_can(user.role, "staff.reset_password", target_role=target.role, actor_direct_grants=actor_grants):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to reset this SNS staff member's password.",
        )

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
# SNS STAFF & ACCESS — STAFF PROFILE (Phase UM-2)
#
# Create/view/edit an SNS platform-staff profile. All three endpoints are
# scoped to PLATFORM_ROLES and app.core.protected_tenants.PLATFORM_TENANT_ID
# only -- same guarantee as list_platform_users/set_platform_user_active
# above: never touches a tenant-agency or billing-organization account.
#
# Gated by app.core.role_guards.require_platform_permission() (Phase UM-1)
# instead of _require_platform_owner -- this is the first surface where the
# non-OWNER platform roles (PLATFORM_ADMIN, PLATFORM_SECURITY, etc.) get
# real, enforced access rather than being merely defined-but-unused.
# =========================================================


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _active_grants_query(db: Session, target_user_id: UUID):
    """Active (not revoked, not expired) StaffPermissionGrant rows for one
    target account -- the delegated-capability half of "effective
    permissions" (Phase UM-3)."""
    now = _now()
    return db.query(StaffPermissionGrant).filter(
        StaffPermissionGrant.target_user_id == target_user_id,
        StaffPermissionGrant.revoked_at.is_(None),
        or_(
            StaffPermissionGrant.expires_at.is_(None),
            StaffPermissionGrant.expires_at > now,
        ),
    )


def _active_grant_capabilities(db: Session, target_user_id: UUID) -> set[str]:
    return {row.capability for row in _active_grants_query(db, target_user_id).all()}


def _serialize_platform_staff(target: User, db: Session, *, last_login: Optional[datetime] = None) -> dict:
    is_final_active_owner = bool(
        target.role == "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    )
    responsible_owner_name = None
    if target.responsible_owner_id:
        owner = db.get(User, target.responsible_owner_id)
        responsible_owner_name = owner.full_name if owner is not None else None
    direct_grants = _active_grant_capabilities(db, target.id)
    return {
        "user_id": str(target.id),
        "email": target.email,
        "full_name": target.full_name,
        "first_name": target.first_name,
        "middle_name": target.middle_name,
        "last_name": target.last_name,
        "role": target.role,
        "access_level": access_level_for_role(target.role),
        "department": target.department,
        "account_type": target.account_type,
        # Highest organizational assignment level (Platform > Department >
        # Job Title > Platform Role > Access Level).
        "platform": target.platform,
        "active": target.active,
        # Distinct 4-state lifecycle (ACTIVE/SUSPENDED/DISABLED/REMOVED) --
        # see app.core.roles.PLATFORM_STAFF_STATUSES. `active` above stays
        # for app-wide auth-gate compatibility; this is the authoritative
        # status for SNS Staff & Access UI/workflows.
        "platform_staff_status": normalize_platform_staff_status(target.platform_staff_status),
        "phone": target.phone,
        "address_street": target.address_street,
        "address_city": target.address_city,
        "address_state": target.address_state,
        "address_zip": target.address_zip,
        "start_date": target.employment_date,
        "notes": target.notes,
        # Human Staff job title (blank/None for Platform Identities).
        "job_title": target.job_title,
        # Platform Identities only (Service Account / Automation Account /
        # API Client) -- never fabricated: null until an actor sets them.
        "responsible_owner_id": str(target.responsible_owner_id) if target.responsible_owner_id else None,
        "responsible_owner_name": responsible_owner_name,
        "purpose": target.identity_purpose,
        "scope": target.identity_scope,
        "must_change_password": bool(target.must_change_password),
        "created_by": str(target.created_by) if target.created_by else None,
        "created_at": target.created_at,
        "updated_by": str(target.updated_by) if target.updated_by else None,
        "updated_at": target.updated_at,
        "last_login": last_login,
        # Platform Owner succession/continuity signal (approved SNS Staff &
        # Access requirement): true only when this account is the single
        # remaining active OWNER -- the frontend uses this to render an
        # explicit "Final Platform Owner -- protected" safeguard notice in
        # the Access tab, independent of/in addition to the hard 409s the
        # role-change/disable endpoints already enforce server-side.
        "is_final_active_owner": is_final_active_owner,
        # Real, backend-derived EFFECTIVE capability grants for this
        # specific account -- role defaults UNIONED with this account's
        # own active delegated grants (Phase UM-3). Never hardcoded in the
        # frontend; this is the same source of truth role_can() enforces.
        # See GET /users/{id}/permissions for the full role-default vs.
        # delegated vs. revoked breakdown used by the Access tab.
        "capabilities": capabilities_for_role(target.role, direct_grants),
    }


def _get_last_login(db: Session, user_id: UUID) -> Optional[datetime]:
    return db.execute(
        text(
            "SELECT MAX(created_at) FROM audit_logs WHERE user_id = :user_id AND action = 'LOGIN_SUCCESS'"
        ),
        {"user_id": str(user_id)},
    ).scalar()


def _count_active_platform_owners(db: Session, *, exclude_user_id: Optional[UUID] = None) -> int:
    """The Final-Active-Owner safeguard (per approved SNS Staff & Access
    architecture): there must always be at least one active OWNER
    account. Used to block disabling/demoting the last one. Excludes a
    given user id so callers can ask "how many WOULD remain if this user
    were removed/changed" in one query."""
    query = db.query(User).filter(User.role == "OWNER", User.active.is_(True))
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.count()


class PlatformStaffWrite(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    role: str
    department: Optional[str] = None
    account_type: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    address_street: Optional[str] = Field(default=None, max_length=255)
    address_city: Optional[str] = Field(default=None, max_length=100)
    address_state: Optional[str] = Field(default=None, max_length=2)
    address_zip: Optional[str] = Field(default=None, max_length=10)
    start_date: Optional[datetime] = None
    notes: Optional[str] = None
    # Human Staff: SNS job title (e.g. "Director of Platform Security").
    job_title: Optional[str] = Field(default=None, max_length=150)
    # Highest organizational assignment level (Platform > Department >
    # Job Title > Platform Role > Access Level). Defaults to SNS Hospice
    # Solutions when omitted -- see app/core/platforms.py.
    platform: Optional[str] = Field(default=None, max_length=120)
    # Platform Identities only (Service Account / Automation Account /
    # API Client) -- an accountable SNS human staff member, why the
    # identity exists, and (API Clients) what it is authorized to touch.
    # Never displayed as ordinary Human Staff fields.
    responsible_owner_id: Optional[UUID] = None
    purpose: Optional[str] = None
    scope: Optional[str] = Field(default=None, max_length=255)

    @field_validator("role")
    @classmethod
    def _role_is_platform_role(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in PLATFORM_ROLES:
            raise ValueError(f"role must be one of the SNS platform roles: {sorted(PLATFORM_ROLES)}")
        return normalized

    @field_validator("department")
    @classmethod
    def _department_is_valid(cls, value: Optional[str]) -> Optional[str]:
        try:
            return normalize_department(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("account_type")
    @classmethod
    def _account_type_is_valid(cls, value: Optional[str]) -> str:
        try:
            return normalize_account_type(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("platform")
    @classmethod
    def _platform_is_valid(cls, value: Optional[str]) -> str:
        try:
            return normalize_platform(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def _job_title_matches_department(self) -> "PlatformStaffWrite":
        # Runs after the individual field validators above, so
        # self.department is already the normalized uppercase code by
        # this point. See app/core/job_titles.py for the department ->
        # catalog rules (departments without a catalog accept free text).
        try:
            self.job_title = normalize_job_title(self.department, self.job_title)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self


class PlatformStaffProfileUpdate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    address_street: Optional[str] = Field(default=None, max_length=255)
    address_city: Optional[str] = Field(default=None, max_length=100)
    address_state: Optional[str] = Field(default=None, max_length=2)
    address_zip: Optional[str] = Field(default=None, max_length=10)
    start_date: Optional[datetime] = None
    notes: Optional[str] = None
    job_title: Optional[str] = Field(default=None, max_length=150)
    platform: Optional[str] = Field(default=None, max_length=120)
    responsible_owner_id: Optional[UUID] = None
    purpose: Optional[str] = None
    scope: Optional[str] = Field(default=None, max_length=255)

    @field_validator("department")
    @classmethod
    def _department_is_valid(cls, value: Optional[str]) -> Optional[str]:
        try:
            return normalize_department(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("platform")
    @classmethod
    def _platform_is_valid(cls, value: Optional[str]) -> str:
        try:
            return normalize_platform(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def _job_title_matches_department(self) -> "PlatformStaffProfileUpdate":
        try:
            self.job_title = normalize_job_title(self.department, self.job_title)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self


def _validate_responsible_owner(db: Session, responsible_owner_id: Optional[UUID]) -> Optional[UUID]:
    """Platform Identities (Service Account / Automation Account / API
    Client) must be accountable to a real, existing SNS human staff
    member -- never a fabricated/free-text name. Returns None unchanged;
    raises 400 if the id does not resolve to a platform staff account."""
    if responsible_owner_id is None:
        return None
    owner = db.get(User, responsible_owner_id)
    if owner is None or not is_platform_role(owner.role):
        raise HTTPException(status_code=400, detail="responsible_owner_id must reference an existing SNS staff account")
    return responsible_owner_id


@router.post("/users", status_code=201, dependencies=[Depends(require_platform_permission("staff.create"))])
def create_platform_staff(
    payload: PlatformStaffWrite,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new SNS platform-staff account. Role-assignment ceiling:
    only an actor with `staff.assign_owner_role` (OWNER only, see
    app.core.roles.role_can) may create another OWNER."""
    if payload.role == "OWNER" and not role_can(user.role, "staff.assign_owner_role"):
        raise HTTPException(
            status_code=403,
            detail="Only a Platform Owner may create another Platform Owner account.",
        )

    normalized_email = payload.email.strip().lower()
    existing = (
        db.query(User)
        .filter(User.tenant_id == PLATFORM_TENANT_ID, User.email == normalized_email)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="An SNS staff account with this email already exists")

    full_name = " ".join(
        part for part in [payload.first_name.strip(), (payload.middle_name or "").strip(), payload.last_name.strip()]
        if part
    )
    responsible_owner_id = _validate_responsible_owner(db, payload.responsible_owner_id)

    target = User(
        tenant_id=PLATFORM_TENANT_ID,
        created_by=user.user_id,
        must_change_password=True,
        email=normalized_email,
        first_name=payload.first_name.strip(),
        middle_name=(payload.middle_name or "").strip() or None,
        last_name=payload.last_name.strip(),
        full_name=full_name,
        role=payload.role,
        department=payload.department,
        account_type=payload.account_type or "HUMAN_STAFF",
        phone=payload.phone,
        address_street=payload.address_street,
        address_city=payload.address_city,
        address_state=payload.address_state,
        address_zip=payload.address_zip,
        employment_date=payload.start_date,
        notes=payload.notes,
        job_title=payload.job_title,
        platform=normalize_platform(payload.platform),
        responsible_owner_id=responsible_owner_id,
        identity_purpose=payload.purpose,
        identity_scope=payload.scope,
    )
    temp_password = _generate_temp_password()
    target.password_hash = hash_password(temp_password)
    reset_link = _issue_password_reset_link(target)
    db.add(target)
    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_CREATED_STAFF",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "target_role": target.role},
        commit=True,
    )

    result = _serialize_platform_staff(target, db)
    # Only returned once, at creation -- same one-time-reveal pattern as
    # the tenant-scoped POST /staff (app/api/staff.py::create_staff).
    result["temporary_password"] = temp_password
    result["reset_link"] = reset_link
    return result


@router.get("/users/{target_user_id}", dependencies=[Depends(require_platform_permission("staff.view"))])
def get_platform_staff(
    target_user_id: UUID,
    db: Session = Depends(get_db),
):
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")
    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


@router.get(
    "/users/{target_user_id}/audit",
    dependencies=[Depends(require_platform_permission("staff.view_audit"))],
)
def get_platform_staff_audit_history(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """Real audit history for one SNS staff member -- every lifecycle
    event already written via app.services.audit_logger.log_event with
    entity_type='user'/entity_id=<this user> (OWNER_CREATED_STAFF,
    OWNER_UPDATED_STAFF_PROFILE, OWNER_CHANGED_STAFF_ROLE,
    OWNER_ENABLED_USER, OWNER_DISABLED_USER, OWNER_RESET_USER_PASSWORD).
    No separate/mocked audit source -- this is the same audit_logs table
    the platform-wide GET /api/owner/audit-logs reads."""
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    rows = (
        db.execute(
            text(
                """
                SELECT
                    al.id::text AS log_id,
                    al.created_at,
                    al.action,
                    al.description,
                    al.metadata AS event_metadata,
                    al.user_id::text AS actor_user_id,
                    u.full_name AS actor_full_name,
                    u.email AS actor_email
                FROM audit_logs al
                LEFT JOIN users u ON u.id = al.user_id
                WHERE al.entity_type = 'user' AND al.entity_id = :target_id
                ORDER BY al.created_at DESC
                LIMIT :limit
                """
            ),
            {"target_id": str(target_user_id), "limit": limit},
        )
        .mappings()
        .all()
    )
    return {"events": [dict(row) for row in rows]}


@router.patch(
    "/users/{target_user_id}/profile",
    dependencies=[Depends(require_platform_permission("staff.edit_profile"))],
)
def update_platform_staff_profile(
    target_user_id: UUID,
    payload: PlatformStaffProfileUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Edit an SNS staff member's profile fields (name/department/contact/
    notes). Does NOT change role or active status -- see
    set_platform_user_active above (lifecycle) and the future Phase UM-4
    role-assignment endpoint (role changes)."""
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    if not role_can(user.role, "staff.edit_profile", target_role=target.role):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to edit this SNS staff member's profile.",
        )

    responsible_owner_id = _validate_responsible_owner(db, payload.responsible_owner_id)
    if responsible_owner_id == target.id:
        raise HTTPException(status_code=400, detail="An identity cannot be its own responsible owner.")

    target.first_name = payload.first_name.strip()
    target.last_name = payload.last_name.strip()
    target.middle_name = (payload.middle_name or "").strip() or None
    target.full_name = " ".join(
        part for part in [target.first_name, target.middle_name, target.last_name] if part
    )
    target.job_title = payload.job_title
    target.platform = normalize_platform(payload.platform)
    target.responsible_owner_id = responsible_owner_id
    target.identity_purpose = payload.purpose
    target.identity_scope = payload.scope
    target.department = payload.department
    target.phone = payload.phone
    target.address_street = payload.address_street
    target.address_city = payload.address_city
    target.address_state = payload.address_state
    target.address_zip = payload.address_zip
    target.employment_date = payload.start_date
    target.notes = payload.notes
    target.updated_by = user.user_id

    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_UPDATED_STAFF_PROFILE",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email},
        commit=True,
    )

    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


class PlatformStaffRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def _role_is_platform_role(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in PLATFORM_ROLES:
            raise ValueError(f"role must be one of the SNS platform roles: {sorted(PLATFORM_ROLES)}")
        return normalized


@router.patch(
    "/users/{target_user_id}/role",
    dependencies=[Depends(require_platform_permission("staff.assign_role"))],
)
def update_platform_staff_role(
    target_user_id: UUID,
    payload: PlatformStaffRoleUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Change an SNS staff member's platform role.

    Enforces (all required by the approved SNS Staff & Access
    architecture, not optional):
      - the target-hierarchy/assignment-ceiling rule (role_can with
        target_role -- e.g. a non-owner may never touch an OWNER target
        or assign the OWNER role);
      - self-elevation prevention (an actor may never change their own
        role through this endpoint, even to a role they could otherwise
        assign to someone else);
      - the Final-Active-Owner safeguard (the last remaining active
        Platform Owner can never be demoted away from OWNER).
    """
    target = db.get(User, target_user_id)
    if not _is_platform_staff_account(target):
        raise HTTPException(status_code=404, detail="SNS staff account not found")

    if target.id == user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot change your own platform role.",
        )

    if not role_can(user.role, "staff.assign_role", target_role=target.role):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to change this SNS staff member's role.",
        )

    if payload.role == "OWNER" and not role_can(user.role, "staff.assign_owner_role"):
        raise HTTPException(
            status_code=403,
            detail="Only a Platform Owner may assign the Platform Owner role.",
        )

    if (
        target.role == "OWNER"
        and payload.role != "OWNER"
        and target.active
        and _count_active_platform_owners(db, exclude_user_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=409,
            detail="The final active Platform Owner cannot be demoted.",
        )

    previous_role = target.role
    target.role = payload.role
    target.updated_by = user.user_id
    db.commit()
    db.refresh(target)

    log_event(
        db=db,
        user_id=user.user_id,
        tenant_id=target.tenant_id,
        role=user.role,
        action="OWNER_CHANGED_STAFF_ROLE",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"target_email": target.email, "previous_role": previous_role, "new_role": target.role},
        commit=True,
    )

    return _serialize_platform_staff(target, db, last_login=_get_last_login(db, target.id))


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
