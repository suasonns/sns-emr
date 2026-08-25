from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.billing.models.claim import Claim
from app.billing.security import require_automated_billing
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet

router = APIRouter(prefix="/billing", tags=["Billing Claims"])

# Claims Management Figma mockup groups claim.status into 4 lifecycle stages;
# "READY" claims are shown as "Draft Batching" (pre-audit, not yet submitted).
LIFECYCLE_STAGE_BY_STATUS = {
    "READY": "draft",
    "SENT": "submitted",
    "ACCEPTED": "accepted",
    "PAID": "paid",
    "DENIED": "denied",
}


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@router.get("/claims")
def list_claims(
    status: str | None = None,
    payer_name: str | None = None,
    service_date_from: date | None = None,
    service_date_to: date | None = None,
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only view over real ``claims`` rows for the Claims
    Management page: the active claims registry table plus the counts that
    back its metric cards and lifecycle pipeline row.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    base_query = (
        db.query(
            Claim.id.label("claim_id"),
            Claim.patient_id.label("patient_id"),
            Claim.payer_name.label("payer_name"),
            Claim.service_date.label("service_date"),
            Claim.total_charge.label("total_charge"),
            Claim.total_units.label("total_units"),
            Claim.status.label("status"),
            Claim.claim_control_number.label("claim_control_number"),
            Claim.last_status_reason.label("last_status_reason"),
            Claim.created_at.label("created_at"),
            Claim.updated_at.label("updated_at"),
            Patient.mrn.label("mrn"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
        )
        .join(Patient, Patient.id == Claim.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Claim.tenant_id == scoped_tenant_id)
    )

    # Lifecycle + metric-card counts are computed over the FULL tenant claim
    # set (not the filtered/paginated table below) so they always reflect
    # "all active claims", matching the Figma cards' framing.
    all_statuses = [r.status for r in base_query.with_entities(Claim.status).all()]
    lifecycle_counts = {"draft": 0, "submitted": 0, "accepted": 0, "paid": 0, "denied": 0}
    for s in all_statuses:
        stage = LIFECYCLE_STAGE_BY_STATUS.get(str(s or "").upper())
        if stage:
            lifecycle_counts[stage] += 1

    query = base_query
    if status:
        query = query.filter(Claim.status == status.upper())
    if payer_name:
        query = query.filter(Claim.payer_name.ilike(f"%{payer_name}%"))
    if service_date_from:
        query = query.filter(Claim.service_date >= service_date_from)
    if service_date_to:
        query = query.filter(Claim.service_date <= service_date_to)

    rows = (
        query.order_by(Claim.service_date.desc().nullslast(), Claim.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for r in rows:
        results.append(
            {
                "claim_id": str(r.claim_id),
                "patient_id": str(r.patient_id),
                "patient_name": _patient_name(
                    r.patient_first_name, r.patient_middle_name, r.patient_last_name
                ),
                "mrn": r.mrn,
                "payer_name": r.payer_name,
                "service_date": r.service_date.isoformat() if r.service_date else None,
                "total_charge": float(r.total_charge) if r.total_charge is not None else None,
                "total_units": r.total_units,
                "status": r.status,
                "claim_control_number": r.claim_control_number,
                "last_status_reason": r.last_status_reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "days_in_status": (
                    (date.today() - (r.updated_at.date() if r.updated_at else r.created_at.date())).days
                    if (r.updated_at or r.created_at)
                    else None
                ),
            }
        )

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "total_claims": len(all_statuses),
        "submitted_count": lifecycle_counts["submitted"],
        "accepted_count": lifecycle_counts["accepted"],
        "denied_count": lifecycle_counts["denied"],
        "lifecycle": lifecycle_counts,
        "claims": results,
    }
