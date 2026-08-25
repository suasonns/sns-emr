"""Hospice aggregate cap tracking -- tenant-scoped.

Backs a real, biller-entered record of the two external inputs
hospice_cap_service.compute_agency_cap_usage() needs per cap year:
beneficiary_count and gross_reimbursement_collected. Both figures only
exist on the agency's real NGS PS&R cap report (cross-provider
proportional methodology this app cannot compute on its own) -- this API
never fabricates them. Until a biller/admin logs a record for a given
cap year, that year's usage is reported as "not_configured", not a
fabricated $0.00 or 100%.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.models.hospice_cap_record import HospiceCapRecord
from app.billing.security import require_automated_billing
from app.billing.services.hospice_cap_service import HospiceCapError, compute_agency_cap_usage
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id

router = APIRouter(prefix="/billing/hospice-cap", tags=["hospice-cap"])


class HospiceCapRecordRequest(BaseModel):
    cap_year: int = Field(..., description="Cap year (starting calendar year of the Nov 1 - Oct 31 cap accounting year).")
    beneficiary_count: str = Field(..., description="Real NGS/PS&R-sourced proportional beneficiary count for this cap year.")
    gross_reimbursement_collected: str = Field(..., description="Real total Medicare hospice reimbursement collected for this cap year.")
    source_note: str | None = None


def _record_to_dict(record: HospiceCapRecord) -> dict:
    payload: dict = {
        "cap_year": record.cap_year,
        "beneficiary_count": str(record.beneficiary_count),
        "gross_reimbursement_collected": str(record.gross_reimbursement_collected),
        "source_note": record.source_note,
        "updated_by": record.updated_by,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "configured": True,
    }
    try:
        usage = compute_agency_cap_usage(
            cap_year=record.cap_year,
            beneficiary_count=record.beneficiary_count,
            gross_reimbursement_collected=record.gross_reimbursement_collected,
        )
    except HospiceCapError as exc:
        payload["cap_usage"] = None
        payload["cap_error"] = str(exc)
        return payload

    payload["cap_usage"] = {
        key: (str(value) if isinstance(value, Decimal) else value)
        for key, value in usage.items()
    }
    return payload


@router.get("")
def list_hospice_cap_records(
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """All cap-year records this tenant has logged, most recent year first."""
    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    require_automated_billing(db, str(scoped_tenant_id))
    records = (
        db.execute(
            select(HospiceCapRecord)
            .where(HospiceCapRecord.tenant_id == scoped_tenant_id)
            .order_by(HospiceCapRecord.cap_year.desc())
        )
        .scalars()
        .all()
    )
    return [_record_to_dict(r) for r in records]


@router.get("/{cap_year}")
def get_hospice_cap_record(
    cap_year: int,
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    require_automated_billing(db, str(scoped_tenant_id))
    record = db.execute(
        select(HospiceCapRecord).where(
            HospiceCapRecord.tenant_id == scoped_tenant_id,
            HospiceCapRecord.cap_year == cap_year,
        )
    ).scalar_one_or_none()

    if record is None:
        return {"cap_year": cap_year, "configured": False, "cap_usage": None}

    return _record_to_dict(record)


@router.put("/{cap_year}")
def upsert_hospice_cap_record(
    cap_year: int,
    payload: HospiceCapRecordRequest,
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to update. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Log (or update) this tenant's real, PS&R-sourced beneficiary_count and
    gross_reimbursement_collected for a cap year. This is the only way
    cap usage becomes available for that year -- the app cannot derive
    these figures on its own.
    """
    if cap_year != payload.cap_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cap_year in path must match cap_year in body",
        )

    try:
        beneficiary_count = Decimal(payload.beneficiary_count)
        gross_reimbursement_collected = Decimal(payload.gross_reimbursement_collected)
    except InvalidOperation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="beneficiary_count and gross_reimbursement_collected must be valid decimal numbers",
        )

    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    require_automated_billing(db, str(scoped_tenant_id))
    record = db.execute(
        select(HospiceCapRecord).where(
            HospiceCapRecord.tenant_id == scoped_tenant_id,
            HospiceCapRecord.cap_year == cap_year,
        )
    ).scalar_one_or_none()

    updated_by = getattr(user, "email", None) or getattr(user, "id", None)
    updated_by = str(updated_by) if updated_by is not None else None

    if record is None:
        record = HospiceCapRecord(
            tenant_id=scoped_tenant_id,
            cap_year=cap_year,
            beneficiary_count=beneficiary_count,
            gross_reimbursement_collected=gross_reimbursement_collected,
            source_note=payload.source_note,
            updated_by=updated_by,
        )
        db.add(record)
    else:
        record.beneficiary_count = beneficiary_count
        record.gross_reimbursement_collected = gross_reimbursement_collected
        record.source_note = payload.source_note
        record.updated_by = updated_by

    db.commit()
    db.refresh(record)

    return _record_to_dict(record)
