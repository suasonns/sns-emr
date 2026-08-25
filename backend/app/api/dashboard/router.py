# api/dashboard/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.role_guards import require_owner
from app.core.roles import access_scope_for_role
from app.core.security import get_current_user
from app.core.database import get_db
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.db_request_dependency import get_db_tenant_with_request_state
from app.models.tenant import Tenant
from app.services.dashboard_service import (
    count_claim_lifecycle,
    get_billing_dashboard,
    get_clinical_alerts_dashboard,
    get_clinical_compliance_dashboard,
    get_denials_appeals_summary,
    get_owner_dashboard,
    get_patient_compliance_detail,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _require_tenant_dashboard_access(user) -> None:
    if access_scope_for_role(getattr(user, "role", None)) != "tenant":
        raise HTTPException(
            status_code=403,
            detail="This dashboard is not available for platform or billing accounts",
        )


def _require_billing_feature_access(db: Session, tenant_id) -> None:
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant context required for billing dashboard",
        )
    tenant = db.get(Tenant, tenant_id)
    if not getattr(tenant, "billing_enabled", False):
        raise HTTPException(
            status_code=403,
            detail="Billing features are not enabled for this tenant",
        )


@router.get("/billing")
def billing_dashboard(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    if access_scope_for_role(getattr(user, "role", None)) == "platform":
        raise HTTPException(
            status_code=403,
            detail="Billing is not available to platform accounts",
        )
    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    _require_billing_feature_access(db, scoped_tenant_id)
    return get_billing_dashboard(db=db, tenant_id=scoped_tenant_id)


@router.get("/claim-lifecycle")
def claim_lifecycle(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    if access_scope_for_role(getattr(user, "role", None)) == "platform":
        raise HTTPException(
            status_code=403,
            detail="Billing is not available to platform accounts",
        )
    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    _require_billing_feature_access(db, scoped_tenant_id)
    return count_claim_lifecycle(db, scoped_tenant_id)


@router.get("/denials-appeals")
def denials_appeals(
    tenant_id: UUID | None = Query(None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    """
    Real Denials & Appeals summary, shared by the Biller's Dashboard and
    the owner's Tenant Analytics financials/billing mirror (see
    app.services.dashboard_service.get_denials_appeals_summary).
    """
    if access_scope_for_role(getattr(user, "role", None)) == "platform":
        raise HTTPException(
            status_code=403,
            detail="Billing is not available to platform accounts",
        )
    scoped_tenant_id = resolve_billing_scope_tenant_id(db, user, tenant_id)
    _require_billing_feature_access(db, scoped_tenant_id)
    return get_denials_appeals_summary(db, scoped_tenant_id)


@router.get("/tenant")
def tenant_dashboard(
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    _require_tenant_dashboard_access(user)
    tenant = db.get(Tenant, user.tenant_id)
    return {
        "tenant_id": str(user.tenant_id),
        "tenant_name": getattr(tenant, "display_name", None) or getattr(tenant, "legal_name", None),
        "ai_enabled": bool(getattr(tenant, "ai_enabled", False)),
        "billing_enabled": bool(getattr(tenant, "billing_enabled", False)),
        "user_session_reference": getattr(user, "user_session_reference", None),
        "dashboard": get_clinical_compliance_dashboard(
            db=db,
            tenant_id=user.tenant_id,
            role=getattr(user, "role", None),
            user_id=getattr(user, "id", None),
        ),
    }


@router.get("/clinical-compliance/patients/{patient_id}")
def patient_compliance_detail(
    patient_id: UUID,
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    _require_tenant_dashboard_access(user)
    get_authorized_patient(db, patient_id, user)
    return get_patient_compliance_detail(db=db, tenant_id=user.tenant_id, patient_id=patient_id)


@router.get("/clinical-alerts")
def clinical_alerts_dashboard(
    db: Session = Depends(get_db_tenant_with_request_state),
    user=Depends(get_current_user),
):
    _require_tenant_dashboard_access(user)
    return get_clinical_alerts_dashboard(db=db, tenant_id=user.tenant_id)


@router.get("/owner")
def owner_dashboard(
    tenant_id: UUID | None = Query(None, description="Optional single tenant to scope the dashboard to. Omit for the platform-wide view."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_owner(user)
    return get_owner_dashboard(db=db, tenant_id=tenant_id)
