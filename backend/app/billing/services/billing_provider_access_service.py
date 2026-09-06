from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.billing.models.billing_provider_agency_assignment import (
    BILLING_PROVIDER_PERMISSION_LEVELS,
    BILLING_PROVIDER_SERVICE_SCOPES,
    BillingProviderAgencyAssignment,
    BillingProviderAgencyServiceScope,
    normalize_billing_provider_permission_level,
)
from app.billing.models.billing_provider_organization import BillingProviderOrganization
from app.billing.models.billing_provider_organization_membership import (
    BillingProviderOrganizationMembership,
)
from app.core.roles import access_scope_for_role, is_owner_role, normalize_role
from app.core.tenant_scope import NON_AGENCY_TENANT_TYPES, list_billable_agency_tenants
from app.models.tenant import Tenant


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _effective_now_filter(start_column, end_column, *, at_time: datetime):
    return (
        start_column <= at_time,
        or_(
            end_column.is_(None),
            end_column >= at_time,
        ),
    )


def _user_tenant_row(db: Session, user):
    return (
        db.query(Tenant.id, Tenant.tenant_type)
        .filter(Tenant.id == getattr(user, "tenant_id", None))
        .one_or_none()
    )


def _active_billing_provider_org_ids_for_user(
    db: Session,
    user,
    *,
    at_time: datetime | None = None,
) -> list[UUID]:
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    if user_id is None:
        return []

    rows = (
        db.query(BillingProviderOrganizationMembership.billing_provider_organization_id)
        .join(
            BillingProviderOrganization,
            BillingProviderOrganization.id
            == BillingProviderOrganizationMembership.billing_provider_organization_id,
        )
        .filter(
            BillingProviderOrganizationMembership.user_id == user_id,
            BillingProviderOrganizationMembership.status == "ACTIVE",
            BillingProviderOrganization.status == "ACTIVE",
            *_effective_now_filter(
                BillingProviderOrganizationMembership.effective_start_at,
                BillingProviderOrganizationMembership.effective_end_at,
                at_time=at_time or _now_utc(),
            ),
        )
        .distinct()
        .all()
    )
    return [UUID(str(row[0])) for row in rows]


def _normalize_requested_ids(
    *,
    requested_tenant_id: UUID | str | None,
    requested_tenant_ids: list[UUID | str] | tuple[UUID | str, ...] | None,
) -> list[UUID]:
    values: list[UUID] = []
    if requested_tenant_id is not None:
        values.append(UUID(str(requested_tenant_id)))
    if requested_tenant_ids:
        values.extend(UUID(str(value)) for value in requested_tenant_ids)
    deduped: list[UUID] = []
    seen: set[UUID] = set()
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped


def _resolve_owner_tenant_ids(
    db: Session,
    *,
    requested_tenant_id: UUID | str | None,
    requested_tenant_ids: list[UUID | str] | tuple[UUID | str, ...] | None,
    all_agencies: bool,
) -> list[UUID]:
    billable = [UUID(row["tenant_id"]) for row in list_billable_agency_tenants(db)]
    allowed = set(billable)
    if all_agencies:
        return billable
    requested = _normalize_requested_ids(
        requested_tenant_id=requested_tenant_id,
        requested_tenant_ids=requested_tenant_ids,
    )
    if requested:
        unauthorized = [tenant_id for tenant_id in requested if tenant_id not in allowed]
        if unauthorized:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        return requested
    raise HTTPException(status_code=400, detail="Select a tenant to view billing data.")


def _resolve_plain_tenant_user_tenant_ids(
    user,
    *,
    requested_tenant_id: UUID | str | None,
    requested_tenant_ids: list[UUID | str] | tuple[UUID | str, ...] | None,
    all_agencies: bool,
) -> list[UUID]:
    own_tenant_id = UUID(str(getattr(user, "tenant_id")))
    requested = _normalize_requested_ids(
        requested_tenant_id=requested_tenant_id,
        requested_tenant_ids=requested_tenant_ids,
    )
    if requested:
        unauthorized = [tenant_id for tenant_id in requested if tenant_id != own_tenant_id]
        if unauthorized:
            raise HTTPException(
                status_code=403,
                detail="You may only view your own tenant's billing data.",
            )
    if all_agencies:
        return [own_tenant_id]
    return [own_tenant_id]


def _resolve_effective_managed_billing_tenant_ids(
    db: Session,
    *,
    requested_scope: str | None = None,
    required_permission_level: str = "VIEW",
    provider_org_ids: list[UUID] | None = None,
    tenant_ids: list[UUID] | None = None,
    at_time: datetime | None = None,
) -> list[UUID]:
    current_time = at_time or _now_utc()
    normalized_permission_level = normalize_billing_provider_permission_level(
        required_permission_level
    )
    query = (
        db.query(BillingProviderAgencyAssignment.tenant_id)
        .join(
            BillingProviderOrganization,
            BillingProviderOrganization.id
            == BillingProviderAgencyAssignment.billing_provider_organization_id,
        )
        .join(
            BillingProviderAgencyServiceScope,
            BillingProviderAgencyServiceScope.assignment_id
            == BillingProviderAgencyAssignment.id,
        )
        .filter(
            BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
            BillingProviderOrganization.status == "ACTIVE",
            *_effective_now_filter(
                BillingProviderAgencyAssignment.effective_start_at,
                BillingProviderAgencyAssignment.effective_end_at,
                at_time=current_time,
            ),
        )
    )
    if requested_scope is not None:
        query = query.filter(BillingProviderAgencyServiceScope.scope == requested_scope)
    if normalized_permission_level == "EDIT":
        query = query.filter(BillingProviderAgencyServiceScope.permission_level == "EDIT")
    if provider_org_ids is not None:
        if not provider_org_ids:
            return []
        query = query.filter(
            BillingProviderAgencyAssignment.billing_provider_organization_id.in_(provider_org_ids)
        )
    if tenant_ids is not None:
        if not tenant_ids:
            return []
        query = query.filter(BillingProviderAgencyAssignment.tenant_id.in_(tenant_ids))
    return [UUID(str(row[0])) for row in query.distinct().all()]


def compute_tenant_financials_enabled_map(
    db: Session,
    tenant_ids: list[UUID | str] | tuple[UUID | str, ...],
    *,
    at_time: datetime | None = None,
) -> dict[UUID, bool]:
    normalized = [UUID(str(tenant_id)) for tenant_id in tenant_ids]
    if not normalized:
        return {}
    enabled = set(
        _resolve_effective_managed_billing_tenant_ids(
            db,
            tenant_ids=normalized,
            at_time=at_time,
        )
    )
    return {tenant_id: tenant_id in enabled for tenant_id in normalized}


def compute_tenant_financials_enabled(
    db: Session,
    tenant_id: UUID | str,
    *,
    at_time: datetime | None = None,
) -> bool:
    normalized = UUID(str(tenant_id))
    return compute_tenant_financials_enabled_map(
        db,
        [normalized],
        at_time=at_time,
    ).get(normalized, False)


def windows_overlap(
    start_a: datetime,
    end_a: datetime | None,
    start_b: datetime,
    end_b: datetime | None,
) -> bool:
    normalized_end_a = end_a or datetime.max.replace(tzinfo=timezone.utc)
    normalized_end_b = end_b or datetime.max.replace(tzinfo=timezone.utc)
    return start_a <= normalized_end_b and start_b <= normalized_end_a


def assert_no_conflicting_active_assignment(
    db: Session,
    *,
    tenant_id: UUID | str,
    billing_provider_organization_id: UUID | str,
    effective_start_at: datetime,
    effective_end_at: datetime | None,
    exclude_assignment_id: UUID | str | None = None,
) -> None:
    query = db.query(BillingProviderAgencyAssignment).filter(
        BillingProviderAgencyAssignment.tenant_id == UUID(str(tenant_id)),
        BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
        BillingProviderAgencyAssignment.billing_provider_organization_id
        != UUID(str(billing_provider_organization_id)),
    )
    if exclude_assignment_id is not None:
        query = query.filter(BillingProviderAgencyAssignment.id != UUID(str(exclude_assignment_id)))

    for row in query.all():
        if windows_overlap(
            row.effective_start_at,
            row.effective_end_at,
            effective_start_at,
            effective_end_at,
        ):
            # HYBRID multi-provider arrangements are not yet supported;
            # only one provider may own a tenant's effective managed-
            # billing period at a time.
            raise HTTPException(
                status_code=409,
                detail="Conflicting active billing-provider assignment exists for this tenant.",
            )


def resolve_authorized_tenant_ids_for_scope(
    db: Session,
    *,
    user,
    requested_scope: str,
    required_permission_level: str = "VIEW",
    requested_tenant_id: UUID | str | None = None,
    requested_tenant_ids: list[UUID | str] | tuple[UUID | str, ...] | None = None,
    all_agencies: bool = False,
) -> list[UUID]:
    requested_scope = (requested_scope or "").strip().upper()
    if requested_scope not in BILLING_PROVIDER_SERVICE_SCOPES:
        raise HTTPException(status_code=400, detail=f"Unknown billing scope '{requested_scope}'.")
    normalized_permission_level = (required_permission_level or "VIEW").strip().upper()
    if normalized_permission_level not in BILLING_PROVIDER_PERMISSION_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown permission level '{required_permission_level}'.",
        )

    role = normalize_role(getattr(user, "role", None))
    if is_owner_role(role):
        return _resolve_owner_tenant_ids(
            db,
            requested_tenant_id=requested_tenant_id,
            requested_tenant_ids=requested_tenant_ids,
            all_agencies=all_agencies,
        )

    provider_org_ids = _active_billing_provider_org_ids_for_user(db, user)
    explicit_requested_ids = _normalize_requested_ids(
        requested_tenant_id=requested_tenant_id,
        requested_tenant_ids=requested_tenant_ids,
    )

    if provider_org_ids:
        if explicit_requested_ids:
            candidate_ids: list[UUID] | None = explicit_requested_ids
        elif all_agencies:
            candidate_ids = None
        else:
            own_tenant = _user_tenant_row(db, user)
            if own_tenant and own_tenant.tenant_type not in NON_AGENCY_TENANT_TYPES:
                candidate_ids = [UUID(str(own_tenant.id))]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Select an agency tenant to view billing data.",
                )

        resolved = _resolve_effective_managed_billing_tenant_ids(
            db,
            requested_scope=requested_scope,
            required_permission_level=normalized_permission_level,
            provider_org_ids=provider_org_ids,
            tenant_ids=candidate_ids,
        )
        if explicit_requested_ids and not resolved:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to access billing data for the requested tenant.",
            )
        return resolved

    own_tenant = _user_tenant_row(db, user)
    if role == "PLATFORM_BILLING" or (
        access_scope_for_role(role) == "billing"
        and own_tenant
        and own_tenant.tenant_type in NON_AGENCY_TENANT_TYPES
    ):
        if explicit_requested_ids:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to access billing data for the requested tenant.",
            )
        if all_agencies:
            return []
        raise HTTPException(
            status_code=400,
            detail="Select an assigned agency tenant to view billing data.",
        )

    return _resolve_plain_tenant_user_tenant_ids(
        user,
        requested_tenant_id=requested_tenant_id,
        requested_tenant_ids=requested_tenant_ids,
        all_agencies=all_agencies,
    )
