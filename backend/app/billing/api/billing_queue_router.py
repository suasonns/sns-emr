from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id

router = APIRouter(prefix="/billing", tags=["Billing Queue"])


@router.get("/queue")
def get_billing_queue(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped billing queue.

    - Tenant users see ONLY their own claims
    - Billing-department (biller) users must select an agency tenant from
      the Biller's Dashboard dropdown; results are scoped to that agency
      only, never blended across agencies
    - Prevents cross-tenant billing visibility
    """

    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))

    rows = db.execute(
        text(
            """
            SELECT
                c.id::text AS claim_id,
                c.billing_cycle_id::text AS billing_cycle_id,
                c.patient_id::text AS patient_id,
                pf.first_name,
                pf.last_name,
                p.mrn AS patient_mrn,
                c.payer_name,
                t.display_name AS tenant_name,
                c.tenant_id::text AS tenant_id,
                c.total_charge,
                c.total_units,
                c.risk_score,
                c.status,
                c.service_date,
                c.claim_control_number,
                c.exported_at,
                c.last_status_reason
            FROM claims c
            LEFT JOIN patients p ON p.id = c.patient_id
            LEFT JOIN patient_facesheet pf ON pf.patient_id = c.patient_id
            LEFT JOIN tenants t ON t.id = c.tenant_id
            WHERE c.tenant_id = :tenant_id
            ORDER BY c.created_at DESC
            """
        ),
        {"tenant_id": scoped_tenant_id},
    ).mappings().all()

    def _patient_name(row) -> str | None:
        if not row["first_name"] and not row["last_name"]:
            return None
        return f"{row['last_name'] or ''}, {row['first_name'] or ''}".strip(", ")

    return [
        {
            "claim_id": row["claim_id"],
            "billing_cycle_id": row["billing_cycle_id"],
            "patient_id": row["patient_id"],
            "patient_name": _patient_name(row),
            "patient_mrn": row["patient_mrn"],
            "payer_name": row["payer_name"],
            "tenant_name": row["tenant_name"],
            "tenant_id": row["tenant_id"],
            "total_charge": float(row["total_charge"] or 0),
            "total_units": row["total_units"],
            "risk_score": row["risk_score"],
            "status": row["status"],
            "service_date": str(row["service_date"]) if row["service_date"] else None,
            "claim_control_number": row["claim_control_number"],
            "exported_at": row["exported_at"].isoformat() if row["exported_at"] else None,
            "last_status_reason": row["last_status_reason"],
        }
        for row in rows
    ]