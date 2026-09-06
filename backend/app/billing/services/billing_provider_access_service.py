from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.billing.models.billing_provider_agency_assignment import (
    BILLING_PROVIDER_SERVICE_SCOPES,
    BillingProviderAgencyAssignment,
    BillingProviderAgencyServiceScope,
)
from app.core.roles import access_scope_for_role, is_owner_role, normalize_role
from app.core.tenant_scope import NON_AGENCY_TENANT_TYPES, list_billable_agency_tenants
from app.models.tenant import Tenant
from app.models.user import User


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _provider_org_id_for_user(db: Session, user) -> UUID | None:
    row = (
        db.query(User.billing_provider_organization_id)
        .filter(User.id == getattr(user, "user_id", None))
        .one_or_none()
    )
    if row is None:
        return None
    return row[0]


def _is_provider_affiliated_billing_user(db: Session, user) -> bool:
    provider_org_id = _provider_org_id_for_user(db, user)
    if provider_org_id is None:
        return False
    role = normalize_role(getattr(user, "role", None))
    return bool(role) and (role == "PLATFORM_BILLING" or access_scope_for_role(role) == "billing")


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


def resolve_authorized_tenant_ids_for_scope(
    db: Session,
    *,
    user,
    requested_scope: str,
    requested_tenant_id: UUID | str | None = None,
    requested_tenant_ids: list[UUID | str] | tuple[UUID | str, ...] | None = None,
    all_agencies: bool = False,
) -> list[UUID]:
    requested_scope = (requested_scope or "").strip().upper()
    if requested_scope not in BILLING_PROVIDER_SERVICE_SCOPES:
        raise HTTPException(status_code=400, detail=f"Unknown billing scope '{requested_scope}'.")

    role = normalize_role(getattr(user, "role", None))
    if is_owner_role(role):
        return _resolve_owner_tenant_ids(
            db,
            requested_tenant_id=requested_tenant_id,
            requested_tenant_ids=requested_tenant_ids,
            all_agencies=all_agencies,
        )

    if not _is_provider_affiliated_billing_user(db, user):
        return _resolve_plain_tenant_user_tenant_ids(
            user,
            requested_tenant_id=requested_tenant_id,
            requested_tenant_ids=requested_tenant_ids,
            all_agencies=all_agencies,
        )

    provider_org_id = _provider_org_id_for_user(db, user)
    if provider_org_id is None:
        return []

    explicit_requested_ids = _normalize_requested_ids(
        requested_tenant_id=requested_tenant_id,
        requested_tenant_ids=requested_tenant_ids,
    )
    if explicit_requested_ids:
        candidate_ids: list[UUID] | None = explicit_requested_ids
    elif all_agencies:
        candidate_ids = None
    else:
        own_tenant = (
            db.query(Tenant.id, Tenant.tenant_type)
            .filter(Tenant.id == getattr(user, "tenant_id", None))
            .one_or_none()
        )
        if own_tenant and own_tenant.tenant_type not in NON_AGENCY_TENANT_TYPES:
            candidate_ids = [UUID(str(own_tenant.id))]
        else:
            raise HTTPException(
                status_code=400,
                detail="Select an agency tenant to view billing data.",
            )

    now = _now_utc()
    query = (
        db.query(BillingProviderAgencyAssignment.tenant_id)
        .join(
            BillingProviderAgencyServiceScope,
            BillingProviderAgencyServiceScope.assignment_id == BillingProviderAgencyAssignment.id,
        )
        .join(Tenant, Tenant.id == BillingProviderAgencyAssignment.tenant_id)
        .filter(
            BillingProviderAgencyAssignment.billing_provider_organization_id == provider_org_id,
            BillingProviderAgencyAssignment.relationship_status == "ACTIVE",
            BillingProviderAgencyAssignment.financials_enabled.is_(True),
            BillingProviderAgencyServiceScope.scope == requested_scope,
            Tenant.financials_enabled.is_(True),
            ~Tenant.tenant_type.in_(sorted(NON_AGENCY_TENANT_TYPES)),
            BillingProviderAgencyAssignment.effective_start_at <= now,
            or_(
                BillingProviderAgencyAssignment.effective_end_at.is_(None),
                BillingProviderAgencyAssignment.effective_end_at >= now,
            ),
        )
    )
    if candidate_ids is not None:
        query = query.filter(BillingProviderAgencyAssignment.tenant_id.in_(candidate_ids))

    resolved = [UUID(str(row[0])) for row in query.distinct().all()]

    if explicit_requested_ids and not resolved:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access billing data for the requested tenant.",
        )

    return resolved
