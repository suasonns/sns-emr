from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.billing.audit_store import list_audit_events
from app.db_request_dependency import get_db_tenant_with_request_state

router = APIRouter(prefix="/billing", tags=["Billing Audit"])


@router.get("/audit-history")
def get_audit_history(
    patient_id: Optional[str] = None,
    billing_cycle_id: Optional[str] = None,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    # db dependency is intentionally injected so request.state.db is populated
    # for audit middleware and future DB-backed persistence.
    _ = db

    return list_audit_events(
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
    )