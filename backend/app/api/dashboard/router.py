# api/dashboard/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.role_guards import require_owner
from app.core.security import get_current_user
from app.core.database import get_db
from app.db_request_dependency import get_db_tenant_with_request_state
from app.models.tenant import Tenant
from app.services.dashboard_service import (
    get_billing_dashboard,
    get_clinical_alerts_dashboard,
    get_clinical_compliance_dashboard,
    get_owner_dashboard,
    get_patient_compliance_detail,
)
from app.billing.store import count_lifecycle

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/billing")
def billing_dashboard(
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    if not getattr(user, "tenant_id", None):
        raise HTTPException(
            status_code=400,
            detail="Tenant context required for billing dashboard",
        )

    tenant = db.get(Tenant, user.tenant_id)
    if getattr(user, "role", "").upper() != "OWNER" and not getattr(tenant, "billing_enabled", False):
        raise HTTPException(
            status_code=403,
            detail="Billing features are not enabled for this tenant",
        )

    return get_billing_dashboard(db=db, tenant_id=user.tenant_id)


@router.get("/claim-lifecycle")
def claim_lifecycle():
    return count_lifecycle()


@router.get("/tenant")
def tenant_dashboard(
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    tenant = db.get(Tenant, user.tenant_id)
    return {
        "tenant_id": str(user.tenant_id),
        "tenant_name": getattr(tenant, "display_name", None) or getattr(tenant, "legal_name", None),
        "ai_enabled": bool(getattr(tenant, "ai_enabled", False)),
        "billing_enabled": bool(getattr(tenant, "billing_enabled", False)),
        "user_session_reference": getattr(user, "user_session_reference", None),
        "dashboard": get_clinical_compliance_dashboard(db=db, tenant_id=user.tenant_id),
    }


@router.get("/clinical-compliance/patients/{patient_id}")
def patient_compliance_detail(
    patient_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    return get_patient_compliance_detail(db=db, tenant_id=user.tenant_id, patient_id=patient_id)


@router.get("/clinical-alerts")
def clinical_alerts_dashboard(
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    return get_clinical_alerts_dashboard(db=db, tenant_id=user.tenant_id)


@router.get("/owner")
def owner_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_owner(user)
    return get_owner_dashboard(db=db)
