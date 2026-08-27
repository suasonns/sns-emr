# core/tenant_scope.py
#
# Resolves which single agency tenant a request should be scoped to, for
# the two roles that are allowed to look at more than their own tenant's
# data: the platform OWNER and the BILLING-department (biller) staff.
#
# The billing organization (e.g. "North East Billing") is its own tenant,
# separate from every hospice agency it bills for. Its staff therefore
# cannot rely on `user.tenant_id` to find an agency's claims -- they must
# explicitly pick which agency tenant they're working, via the Biller's
# Dashboard tenant dropdown. This module is the single place that
# authorizes and resolves that selection so every billing endpoint applies
# the same rule.

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.roles import access_scope_for_role

# Tenants that are never a billable "client agency" -- the platform vendor
# org and the billing org itself never appear in the agency dropdown and
# can never be selected as the scope of a billing request.
NON_AGENCY_TENANT_TYPES = {"PLATFORM", "BILLING"}


def resolve_billing_scope_tenant_id(
    db: Session,
    user,
    tenant_id: UUID | str | None,
) -> UUID:
    """
    Resolve the effective agency tenant_id for a billing-surface request.

    - Ordinary agency/tenant users (access_scope == "tenant") are always
      scoped to their own tenant_id. An explicit `tenant_id` is only
      accepted if it matches their own -- otherwise this is a cross-tenant
      access attempt and is rejected.
    - Billing-department users (access_scope == "billing" -- the biller's
      staff) belong to the BILLING organization tenant, not to any single
      agency, so they MUST pass an explicit `tenant_id` selecting which
      client agency's billing data to view. That tenant must exist and be
      a real agency (never PLATFORM or BILLING).
    """
    scope = access_scope_for_role(getattr(user, "role", None))

    if scope != "billing":
        if tenant_id is not None and str(tenant_id) != str(user.tenant_id):
            raise HTTPException(
                status_code=403,
                detail="You may only view your own tenant's billing data.",
            )
        return user.tenant_id

    if tenant_id:
        row = (
            db.execute(
                text("SELECT id, tenant_type FROM tenants WHERE id = :id"),
                {"id": str(tenant_id)},
            )
            .mappings()
            .first()
        )

        if not row:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        if row["tenant_type"] in NON_AGENCY_TENANT_TYPES:
            raise HTTPException(
                status_code=403,
                detail="Cannot view billing data for a platform or billing organization tenant.",
            )

        return row["id"]

    # No explicit tenant_id: fall back to the billing user's own tenant,
    # but only if that tenant is itself a real agency (an in-house biller
    # whose account lives directly in the one agency they bill for). A
    # billing-department user whose own tenant is the separate billing
    # organization (tenant_type BILLING, e.g. an outside contractor billing
    # for many agencies) has no single agency to default to and must pick
    # one explicitly from the Biller's Dashboard dropdown.
    own_tenant = (
        db.execute(
            text("SELECT id, tenant_type FROM tenants WHERE id = :id"),
            {"id": str(user.tenant_id)},
        )
        .mappings()
        .first()
    )

    if own_tenant and own_tenant["tenant_type"] not in NON_AGENCY_TENANT_TYPES:
        return user.tenant_id

    raise HTTPException(
        status_code=400,
        detail="Select an agency tenant to view its billing data.",
    )


def list_billable_agency_tenants(db: Session) -> list[dict]:
    """
    Agency tenants selectable in the Biller's Dashboard tenant dropdown --
    every real hospice agency tenant, excluding the platform and billing
    organization tenants themselves.
    """
    rows = (
        db.execute(
            text(
                """
                SELECT
                    id::text AS tenant_id,
                    legal_name,
                    COALESCE(display_name, legal_name) AS display_name,
                    tenant_type,
                    status,
                    billing_enabled
                FROM tenants
                WHERE tenant_type NOT IN ('PLATFORM', 'BILLING')
                ORDER BY display_name
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]
