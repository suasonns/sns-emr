"""
AR Aging Report API -- read-only aggregation over existing claims/payment/
adjustment/denial records (see aging_report_service for the calculation).
No new data store; no new claim/payment/denial logic is created here.

Agency filtering mirrors the existing Biller's Dashboard pattern
(core.tenant_scope.resolve_billing_scope_tenant_id / list_billable_agency_
tenants) and extends it to support the three scopes this report requires:
  - Single Agency:        ?tenant_id=<uuid>
  - Multi-Agency:         ?tenant_ids=<uuid>,<uuid>,...
  - All Assigned Agencies ?all_agencies=true (billing-department users only;
                          an ordinary agency user only ever has one agency,
                          so this is a no-op for them)
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.billing.security import require_automated_billing, tenant_has_automated_billing
from app.billing.services.aging_report_service import build_ar_aging_report
from app.core.database import get_db
from app.core.roles import access_scope_for_role
from app.core.security import get_current_user
from app.core.tenant_scope import list_billable_agency_tenants, resolve_billing_scope_tenant_id

router = APIRouter(prefix="/billing", tags=["Billing Reports"])


def _resolve_scope_tenant_ids(
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


@router.get("/aging-report")
def get_aging_report(
    tenant_id: UUID | None = Query(
        None, description="Single agency tenant to view. Required for billing-department accounts unless tenant_ids/all_agencies is used."
    ),
    tenant_ids: str | None = Query(
        None, description="Comma-separated agency tenant IDs for a multi-agency aging view (billing-department accounts only)."
    ),
    all_agencies: bool = Query(
        False, description="If true, aggregate across every agency the current billing-department user is assigned to."
    ),
    as_of: date | None = Query(None, description="Aging as-of date; defaults to today."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Standard healthcare AR aging report: Outstanding Balance = Total Charges
    - Posted Payments - Adjustments - Write-offs, aged from claim submission
    /export date (never service date), bucketed 0-30/31-60/61-90/91-120/120+.
    Grouped by agency, by payer, by bucket, and per-claim detail.
    """
    resolved_tenant_ids = _resolve_scope_tenant_ids(db, user, tenant_id, tenant_ids, all_agencies)

    if len(resolved_tenant_ids) == 1:
        require_automated_billing(db, str(resolved_tenant_ids[0]))
    else:
        # Aggregate views silently drop agencies without automated billing
        # enabled rather than failing the whole multi-agency request.
        resolved_tenant_ids = [
            tid for tid in resolved_tenant_ids if tenant_has_automated_billing(db, str(tid))
        ]

    return build_ar_aging_report(db, resolved_tenant_ids, as_of=as_of)
