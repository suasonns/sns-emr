"""
Shared Single/Multi-Agency/All-Assigned-Agencies tenant-scope resolution
for billing report endpoints.

Extracted from app.billing.api.aging_report_router so every report that
needs this selection pattern (Aging Report, Credit Balance Report, and any
future one) shares identical authorization logic instead of each
reimplementing it.

Scopes:
  - Single Agency:        ?tenant_id=<uuid>
  - Multi-Agency:         ?tenant_ids=<uuid>,<uuid>,...
  - All Assigned Agencies ?all_agencies=true (billing-department users
                          only; an ordinary agency user only ever has one
                          agency, so this is a no-op for them)

This is a natural extension of the existing single-tenant-per-request
security model in app.core.tenant_scope -- not a new/parallel security
mechanism. All authorization still funnels through
resolve_billing_scope_tenant_id.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.roles import access_scope_for_role
from app.core.tenant_scope import list_billable_agency_tenants, resolve_billing_scope_tenant_id


def resolve_multi_agency_tenant_ids(
    db: Session,
    user,
    tenant_id: UUID | None,
    tenant_ids: str | None,
    all_agencies: bool,
) -> list[UUID]:
    scope = access_scope_for_role(getattr(user, "role", None))

    if scope != "billing":
        # Ordinary agency users only ever have one agency -- multi/all
        # selectors are meaningless for them; always resolve to their own.
        return [resolve_billing_scope_tenant_id(db, user, tenant_id)]

    if all_agencies:
        return [UUID(a["tenant_id"]) for a in list_billable_agency_tenants(db)]

    if tenant_ids:
        ids = [t.strip() for t in tenant_ids.split(",") if t.strip()]
        return [resolve_billing_scope_tenant_id(db, user, tid) for tid in ids]

    # Single-agency selection (or "no selection" -- resolve_billing_scope_
    # tenant_id raises a clear 400 for billing-department users who haven't
    # picked an agency yet, same as every other billing endpoint).
    return [resolve_billing_scope_tenant_id(db, user, tenant_id)]
