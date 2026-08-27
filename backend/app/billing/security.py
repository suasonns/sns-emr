"""
Billing security helpers.

This module enforces and evaluates billing capability rules:
- AUTOMATED billing (NE Billing only)
- MANUAL billing (all other billers)

Used for:
- blocking unauthorized automation
- shaping remittance / claim visibility
"""

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def require_automated_billing(
    db: Session,
    tenant_id: str,
) -> None:
    """
    Enforces that the tenant is authorized for automated billing.

    Canonical source: tenants.billing_enabled (public schema). This flag is
    only ever set true once a tenant has real operating authority on file
    (EIN + PTAN) — enforced by ck_tenant_billing_requires_operating_authority
    on the tenants table.

    NOTE: this previously queried a non-existent core.tenants /
    core.billing_organizations schema (dead code — every call 500'd).
    Replaced with the real tenants.billing_enabled column.

    Used to protect:
    - claim generation
    - claim export
    - EDI submission
    - other automated billing features
    """

    row = db.execute(
        text(
            """
            SELECT billing_enabled
            FROM tenants
            WHERE id = :tenant_id
            """
        ),
        {"tenant_id": tenant_id},
    ).fetchone()

    if not row or not row.billing_enabled:
        raise HTTPException(
            status_code=403,
            detail="Automated billing features are available only for tenants with billing enabled (requires EIN + PTAN on file).",
        )


def tenant_has_automated_billing(
    db: Session,
    tenant_id: str,
) -> bool:
    """
    Returns True if the tenant has automated billing enabled
    (tenants.billing_enabled).

    Used for:
    - remittance advice visibility
    - claim status response shaping
    - UI feature gating
    """

    row = db.execute(
        text(
            """
            SELECT billing_enabled
            FROM tenants
            WHERE id = :tenant_id
            """
        ),
        {"tenant_id": tenant_id},
    ).fetchone()

    return bool(row and row.billing_enabled)
