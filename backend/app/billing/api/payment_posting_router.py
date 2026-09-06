from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.billing.models.payment import Payment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.security import require_automated_billing
from app.billing.services.billing_provider_access_service import (
    resolve_authorized_tenant_ids_for_scope,
)
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing Payment Posting"])


@router.get("/remittances")
def list_remittances(
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
    Tenant-scoped, read-only view over real ``remittance_advices`` (ERA
    headers) and ``payments`` (claim-level payment lines) rows for the
    Payment Posting page: the electronic remittance registry, MTD payment
    totals, per-payer breakdown, and unmatched-payment worklist.
    """
    scoped_tenant_id = str(
        resolve_authorized_tenant_ids_for_scope(
            db,
            user=user,
            requested_scope="PAYMENT_POSTING",
            requested_tenant_id=tenant_id,
        )[0]
    )
    require_automated_billing(db, scoped_tenant_id)

    era_query = db.query(RemittanceAdvice).filter(RemittanceAdvice.tenant_id == scoped_tenant_id)

    all_eras = era_query.all()
    era_received_count = len(all_eras)
    posted_count = sum(1 for e in all_eras if str(e.status or "").upper() == "POSTED")

    today = date.today()
    month_start = today.replace(day=1)
    mtd_paid = (
        db.query(func.coalesce(func.sum(Payment.paid_amount), 0))
        .join(RemittanceAdvice, RemittanceAdvice.id == Payment.remittance_advice_id)
        .filter(
            Payment.tenant_id == scoped_tenant_id,
            RemittanceAdvice.received_at >= month_start,
        )
        .scalar()
    )

    pending_manual_match = (
        db.query(func.count(Payment.id))
        .filter(
            Payment.tenant_id == scoped_tenant_id,
            Payment.match_status.in_(["UNMATCHED", "MANUAL_REVIEW"]),
        )
        .scalar()
    )

    payer_breakdown_rows = (
        db.query(
            RemittanceAdvice.payer_name.label("payer_name"),
            func.coalesce(func.sum(RemittanceAdvice.total_paid_amount), 0).label("total"),
        )
        .filter(RemittanceAdvice.tenant_id == scoped_tenant_id)
        .group_by(RemittanceAdvice.payer_name)
        .order_by(func.sum(RemittanceAdvice.total_paid_amount).desc())
        .all()
    )
    payer_breakdown = [
        {"payer_name": r.payer_name or "Unknown Payer", "total_paid": float(r.total)}
        for r in payer_breakdown_rows
    ]

    unmatched_rows = (
        db.query(Payment)
        .filter(
            Payment.tenant_id == scoped_tenant_id,
            Payment.match_status.in_(["UNMATCHED", "MANUAL_REVIEW"]),
        )
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )
    unmatched_payments = [
        {
            "payment_id": str(p.id),
            "claim_control_number": p.claim_control_number,
            "patient_name": p.patient_name,
            "paid_amount": float(p.paid_amount) if p.paid_amount is not None else None,
            "match_status": p.match_status,
        }
        for p in unmatched_rows
    ]

    query = era_query
    if payer_name:
        query = query.filter(RemittanceAdvice.payer_name.ilike(f"%{payer_name}%"))
    if status:
        query = query.filter(RemittanceAdvice.status == status.upper())

    rows = query.order_by(RemittanceAdvice.received_at.desc()).limit(limit).all()
    remittances = [
        {
            "era_id": str(r.id),
            "payer_name": r.payer_name,
            "received_at": r.received_at.isoformat() if r.received_at else None,
            "claim_count": r.claim_count,
            "total_paid_amount": float(r.total_paid_amount) if r.total_paid_amount is not None else None,
            "status": r.status,
            "file_name": r.file_name,
        }
        for r in rows
    ]

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(remittances),
        "total_payments_mtd": float(mtd_paid or 0),
        "era_received_count": era_received_count,
        "posted_count": posted_count,
        "pending_manual_match_count": int(pending_manual_match or 0),
        "payer_breakdown": payer_breakdown,
        "unmatched_payments": unmatched_payments,
        "remittances": remittances,
    }
