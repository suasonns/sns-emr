from __future__ import annotations

from uuid import UUID
from types import SimpleNamespace
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.role_guards import require_owner
from app.db_request_dependency import get_db_tenant_with_request_state
from app.core.database import get_db

# ---------------------------------------------------------
# Dashboard services (DB-backed)
# ---------------------------------------------------------
from app.services.dashboard_service import (
    get_billing_dashboard,
    get_claim_lifecycle_dashboard,
    get_clinical_compliance_dashboard,
    get_owner_dashboard,
    get_patient_compliance_detail,
)

# ---------------------------------------------------------
# Billing lifecycle engine (IN-MEMORY for now)
# ---------------------------------------------------------
from app.billing.store import count_lifecycle

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =========================================================
# ✅ DEV AUTH RESOLVER (STRICTLY NON-OWNER)
# =========================================================
def resolve_tenant_user(request: Request):
    """
    DEV-only tenant resolver.
    NEVER used for OWNER dashboards.
    """

    allow_bypass = (
        os.getenv("ALLOW_DEV_DASHBOARD_BYPASS", "false").lower() == "true"
    )

    try:
        return get_current_user(request)
    except Exception:
        pass

    if allow_bypass:
        tenant_id = os.getenv("DEV_DASHBOARD_TENANT_ID")
        if not tenant_id:
            raise HTTPException(status_code=500, detail="DEV_DASHBOARD_TENANT_ID missing")

        return SimpleNamespace(
            id="dev-user",
            tenant_id=UUID(tenant_id),
            role=os.getenv("DEV_DASHBOARD_ROLE", "TENANT"),
            ai_enabled=True,
        )

    raise HTTPException(status_code=401, detail="Not authenticated")


# =========================================================
# ✅ BILLING DASHBOARD
# =========================================================
@router.get("/billing")
def billing_dashboard(
    request: Request,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Billing dashboard.

    Accessible by:
    - TENANT users (own tenant only)
    - BILLING users (scoped externally)
    - OWNER users (oversight)
    """

    user = resolve_tenant_user(request)

    if not getattr(user, "tenant_id", None):
        raise HTTPException(
            status_code=400,
            detail="Tenant context required for billing dashboard",
        )

    return get_billing_dashboard(
        db=db,
        tenant_id=user.tenant_id,
    )


# =========================================================
# ✅ CLAIM LIFECYCLE (ENGINE-BASED)
# =========================================================
@router.get("/claim-lifecycle")
def claim_lifecycle():
    """
    Billing lifecycle distribution.

    ✅ Single source of truth (engine store)
    ✅ Safe during staged rollout
    """
    return count_lifecycle()


# =========================================================
# ✅ TENANT DASHBOARD
# =========================================================
@router.get("/tenant")
def tenant_dashboard(
    request: Request,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    user = resolve_tenant_user(request)

    return {
        "tenant_id": str(user.tenant_id),
        "ai_enabled": getattr(user, "ai_enabled", False),
        "user_session_reference": getattr(user, "user_session_reference", None),
        "dashboard": get_clinical_compliance_dashboard(
            db=db,
            tenant_id=user.tenant_id,
        ),
    }

# =========================================================
# ✅ PATIENT COMPLIANCE DETAIL
# =========================================================
@router.get("/clinical-compliance/patients/{patient_id}")
def patient_compliance_detail(
    patient_id: UUID,
    request: Request,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    user = resolve_tenant_user(request)

    return get_patient_compliance_detail(
        db=db,
        tenant_id=user.tenant_id,
        patient_id=patient_id,
    )


# =========================================================
# ✅ OWNER DASHBOARD (MANAGEMENT)
# =========================================================
@router.get("/owner")
def owner_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    OWNER (management) dashboard.

    ✅ OWNER-only
    ✅ No tenant routing
    ✅ Core schema only
    """

    require_owner(user)
    return get_owner_dashboard(db=db)
