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


AUTOMATED = "AUTOMATED"


def require_automated_billing(
    db: Session,
    tenant_id: str,
) -> None:
    """
    Enforces that the tenant's billing organization is AUTOMATED.

    Used to protect:
    - claim generation
    - claim export
    - EDI submission
    - other automated billing features
    """

    row = db.execute(
        text(
            """
            SELECT bo.capability_tier
            FROM core.tenants t
            JOIN core.billing_organizations bo
              ON bo.id = t.billing_organization_id
            WHERE t.id = :tenant_id
            """
        ),
        {"tenant_id": tenant_id},
    ).fetchone()

    if not row or row.capability_tier != AUTOMATED:
        raise HTTPException(
            status_code=403,
            detail="Automated billing features are available only for NE Billing tenants.",
        )


def tenant_has_automated_billing(
    db: Session,
    tenant_id: str,
) -> bool:
    """
    Returns True if the tenant is linked to an AUTOMATED billing organization.

    Used for:
    - remittance advice visibility
    - claim status response shaping
    - UI feature gating
    """

    row = db.execute(
        text(
            """
            SELECT bo.capability_tier
            FROM core.tenants t
            JOIN core.billing_organizations bo
              ON bo.id = t.billing_organization_id
            WHERE t.id = :tenant_id
            """
        ),
        {"tenant_id": tenant_id},
    ).fetchone()

    return bool(row and row.capability_tier == AUTOMATED)
