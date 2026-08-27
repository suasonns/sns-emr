from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.billing.security import require_automated_billing
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.db_request_dependency import get_db_tenant_with_request_state

from app.services.edi_835_parser import EDI835ParseError, parse_835_file
from app.services.payment_service import post_payments_from_835

router = APIRouter(prefix="/billing/835", tags=["835 Payments"])


@router.post("/upload")
async def upload_835(
    file: UploadFile,
    tenant_id: UUID | None = Query(None, description="Agency tenant to post payments for. Required for billing-department accounts, which must explicitly pick an agency."),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Upload an ERA (835) file and post its claim-level payments/denials,
    matching each to a real claim by claim control number where possible.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, current_user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    content = await file.read()
    raw_text = content.decode("utf-8", errors="replace")

    try:
        parsed = parse_835_file(raw_text)
    except EDI835ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    remittance = post_payments_from_835(
        db=db,
        tenant_id=scoped_tenant_id,
        parsed=parsed,
        file_name=file.filename,
        raw_content=raw_text,
    )

    return {
        "remittance_advice_id": str(remittance.id),
        "processed": remittance.claim_count,
        "payer_name": remittance.payer_name,
        "total_paid_amount": float(remittance.total_paid_amount or 0),
        "message": "835 file processed successfully",
    }