from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.billing.models.appeal import Appeal
from app.billing.models.claim import Claim
from app.billing.models.denial import Denial
from app.billing.security import require_automated_billing
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet

router = APIRouter(prefix="/billing", tags=["Billing Denials & Appeals"])

# Denial.status already reflects the real appeal outcome (see
# app.billing.models.denial.Denial) -- no separate "appeal status" needs to
# be fabricated, just relabeled for the UI's column header.
APPEAL_STATUS_LABEL = {
    "OPEN": "Not Appealed",
    "APPEALED": "In Review",
    "OVERTURNED": "Overturned",
    "UPHELD": "Upheld",
    "WRITTEN_OFF": "Written Off",
}


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@router.get("/denials")
def list_denials(
    reason: str | None = None,
    payer_name: str | None = None,
    status: str | None = None,
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only view over real ``denials`` rows (each created
    from an actual posted 835 remittance denial -- see
    app.billing.models.denial.Denial) for the Denials & Appeals page:
    registry table, denial-reason breakdown, and appeal/overturn metrics.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    base_query = (
        db.query(
            Denial.id.label("denial_id"),
            Denial.claim_id.label("claim_id"),
            Denial.carc_code.label("carc_code"),
            Denial.reason_description.label("reason_description"),
            Denial.denied_amount.label("denied_amount"),
            Denial.denial_date.label("denial_date"),
            Denial.appeal_deadline.label("appeal_deadline"),
            Denial.status.label("status"),
            Denial.updated_at.label("updated_at"),
            Denial.created_at.label("created_at"),
            Claim.patient_id.label("patient_id"),
            Claim.payer_name.label("payer_name"),
            Patient.mrn.label("mrn"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
        )
        .join(Claim, Claim.id == Denial.claim_id)
        .join(Patient, Patient.id == Claim.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Denial.tenant_id == scoped_tenant_id)
    )

    all_denials = base_query.with_entities(
        Denial.id, Denial.status, Denial.reason_description
    ).all()
    total_denials = len(all_denials)
    appealed_statuses = {"APPEALED", "OVERTURNED", "UPHELD"}
    appeals_filed = sum(1 for d in all_denials if str(d.status or "").upper() in appealed_statuses)
    decided = sum(1 for d in all_denials if str(d.status or "").upper() in {"OVERTURNED", "UPHELD"})
    overturned = sum(1 for d in all_denials if str(d.status or "").upper() == "OVERTURNED")

    reason_counts: dict[str, int] = {}
    for d in all_denials:
        label = d.reason_description or "Uncategorized"
        reason_counts[label] = reason_counts.get(label, 0) + 1
    reason_breakdown = [
        {
            "reason": reason,
            "count": count,
            "percent": round(count / total_denials * 100, 1) if total_denials else 0.0,
        }
        for reason, count in sorted(reason_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # Avg resolution = mean(decision_date - submitted_date) across appeals
    # that have actually been decided (never fabricated when none exist yet).
    resolved_appeals = (
        db.query(Appeal.submitted_date, Appeal.decision_date)
        .join(Denial, Denial.id == Appeal.denial_id)
        .filter(
            Denial.tenant_id == scoped_tenant_id,
            Appeal.submitted_date.isnot(None),
            Appeal.decision_date.isnot(None),
        )
        .all()
    )
    if resolved_appeals:
        avg_resolution_days = round(
            sum((a.decision_date - a.submitted_date).days for a in resolved_appeals)
            / len(resolved_appeals),
            1,
        )
    else:
        avg_resolution_days = None

    query = base_query
    if reason:
        query = query.filter(Denial.reason_description.ilike(f"%{reason}%"))
    if payer_name:
        query = query.filter(Claim.payer_name.ilike(f"%{payer_name}%"))
    if status:
        query = query.filter(Denial.status == status.upper())

    rows = (
        query.order_by(Denial.denial_date.desc().nullslast(), Denial.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for r in rows:
        results.append(
            {
                "denial_id": str(r.denial_id),
                "claim_id": str(r.claim_id),
                "patient_id": str(r.patient_id),
                "patient_name": _patient_name(
                    r.patient_first_name, r.patient_middle_name, r.patient_last_name
                ),
                "mrn": r.mrn,
                "payer_name": r.payer_name,
                "denial_date": r.denial_date.isoformat() if r.denial_date else None,
                "carc_code": r.carc_code,
                "reason_description": r.reason_description,
                "denied_amount": float(r.denied_amount) if r.denied_amount is not None else None,
                "status": r.status,
                "appeal_status_label": APPEAL_STATUS_LABEL.get(str(r.status or "").upper(), r.status),
                "appeal_deadline": r.appeal_deadline.isoformat() if r.appeal_deadline else None,
                "days_elapsed": (
                    (date.today() - r.denial_date).days if r.denial_date else None
                ),
            }
        )

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "total_denials": total_denials,
        "appeals_filed": appeals_filed,
        "appeal_rate": round(appeals_filed / total_denials * 100, 1) if total_denials else None,
        "overturn_rate": round(overturned / decided * 100, 1) if decided else None,
        "avg_resolution_days": avg_resolution_days,
        "reason_breakdown": reason_breakdown,
        "denials": results,
    }
