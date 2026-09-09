# backend/app/billing/api/readiness_workflow_router.py
"""
Sprint 2 -- Billing Readiness Operational Workflow endpoints (dashboard,
operational queue, read-only history, and the assignment/follow-up/
blocker-resolve mutations). All additive to the existing `/billing`
surface -- none of Sprint 1's endpoints in billing_router.py are touched.

Every endpoint tenant-scopes exactly like the existing
`/billing/readiness/{patient_id}` and `/billing/readiness-report`
endpoints (app.core.tenant_scope.resolve_billing_scope_tenant_id +
app.billing.security.require_automated_billing), so a billing-department
user must explicitly pick an agency tenant and an ordinary agency user is
confined to their own tenant.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.billing.models.billing_blocker_record import BLOCKER_RECORD_STATUSES
from app.billing.security import require_automated_billing
from app.billing.services.readiness_dashboard_service import (
    build_readiness_history,
    build_readiness_queue,
    build_tenant_readiness_dashboard,
)
from app.billing.services.readiness_workflow_service import (
    resolve_blocker_manually,
    upsert_assignment,
    upsert_follow_up,
)
from app.billing.schemas.billing_schema import (
    ReadinessAssignmentResponse,
    ReadinessBlockerResponse,
    ReadinessFollowUpResponse,
    ReadinessHistoryResponse,
    ReadinessQueueResponse,
    ResolveReadinessBlockerRequest,
    TenantReadinessDashboardResponse,
    UpsertReadinessAssignmentRequest,
    UpsertReadinessFollowUpRequest,
)
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id

router = APIRouter(prefix="/billing", tags=["Billing Readiness Workflow"])


def _parse_date(value: Optional[str], *, field_name: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {value}")


# =========================================================
# DASHBOARD (Deliverable 1)
# =========================================================

@router.get("/readiness-dashboard", response_model=TenantReadinessDashboardResponse)
def get_readiness_dashboard(
    service_date: date = Query(..., description="Date used to evaluate every ACTIVE patient, same as readiness-report."),
    tenant_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    return build_tenant_readiness_dashboard(
        db, tenant_id=scoped_tenant_id, service_date=service_date
    )


# =========================================================
# OPERATIONAL QUEUE (Deliverable 7)
# =========================================================

@router.get("/readiness-queue", response_model=ReadinessQueueResponse)
def get_readiness_queue(
    tenant_id: UUID | None = Query(None),
    status: Optional[str] = Query(None, description="READY | AT_RISK | NOT_READY | BLOCKED"),
    assignment_status: Optional[str] = Query(None),
    due: Optional[str] = Query(None, description="SOON | OVERDUE"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    if due is not None and due not in {"SOON", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="due must be SOON or OVERDUE")

    patients = build_readiness_queue(
        db,
        tenant_id=scoped_tenant_id,
        status_filter=status,
        assignment_status_filter=assignment_status,
        due_filter=due,
    )
    return {"tenant_id": scoped_tenant_id, "patients": patients}


# =========================================================
# READINESS HISTORY (Deliverable 6, read-only)
# =========================================================

@router.get("/readiness-history/{patient_id}", response_model=ReadinessHistoryResponse)
def get_readiness_history(
    patient_id: str,
    tenant_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    return build_readiness_history(db, tenant_id=scoped_tenant_id, patient_id=patient_id)


# =========================================================
# ASSIGNMENTS (Deliverable 4)
# =========================================================

@router.post("/readiness-assignments", response_model=ReadinessAssignmentResponse)
def create_or_update_readiness_assignment(
    payload: UpsertReadinessAssignmentRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)

    try:
        assignment = upsert_assignment(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=payload.patient_id,
            actor_user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
            assigned_user_id=payload.assigned_user_id,
            assigned_role=payload.assigned_role,
            assignment_status=payload.assignment_status,
            related_verdict_id=payload.related_verdict_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "id": str(assignment.id),
        "tenant_id": str(assignment.tenant_id),
        "patient_id": str(assignment.patient_id),
        "assigned_user_id": str(assignment.assigned_user_id) if assignment.assigned_user_id else None,
        "assigned_role": assignment.assigned_role,
        "assigned_date": assignment.assigned_date.isoformat() if assignment.assigned_date else None,
        "assigned_by": str(assignment.assigned_by) if assignment.assigned_by else None,
        "assignment_status": assignment.assignment_status,
    }


# =========================================================
# FOLLOW-UPS (Deliverable 5)
# =========================================================

@router.post("/readiness-followups", response_model=ReadinessFollowUpResponse)
def create_or_update_readiness_follow_up(
    payload: UpsertReadinessFollowUpRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(
        resolve_billing_scope_tenant_id(
            db, user, UUID(payload.tenant_id) if payload.tenant_id else None
        )
    )
    require_automated_billing(db, scoped_tenant_id)

    due_date = _parse_date(payload.due_date, field_name="due_date")

    try:
        follow_up = upsert_follow_up(
            db,
            tenant_id=scoped_tenant_id,
            patient_id=payload.patient_id,
            actor_user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
            status=payload.status,
            follow_up_id=payload.follow_up_id,
            assignment_id=payload.assignment_id,
            follow_up_required=payload.follow_up_required,
            due_date=due_date,
            notes=payload.notes,
            reason=payload.reason,
            related_verdict_id=payload.related_verdict_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    return {
        "id": str(follow_up.id),
        "tenant_id": str(follow_up.tenant_id),
        "patient_id": str(follow_up.patient_id),
        "assignment_id": str(follow_up.assignment_id) if follow_up.assignment_id else None,
        "follow_up_required": follow_up.follow_up_required,
        "status": follow_up.status,
        "due_date": follow_up.due_date.isoformat() if follow_up.due_date else None,
        "resolved_date": follow_up.resolved_date.isoformat() if follow_up.resolved_date else None,
        "created_date": follow_up.created_date.isoformat(),
        "notes": follow_up.notes,
    }


# =========================================================
# MANUAL BLOCKER RESOLUTION (Deliverable 3)
# =========================================================

@router.post("/readiness-blockers/{blocker_id}/resolve", response_model=ReadinessBlockerResponse)
def resolve_readiness_blocker(
    blocker_id: str,
    payload: ResolveReadinessBlockerRequest,
    tenant_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    try:
        record = resolve_blocker_manually(
            db,
            blocker_id=blocker_id,
            actor_user_id=str(getattr(user, "user_id", None) or getattr(user, "id", None)),
            reason=payload.reason,
            tenant_id=scoped_tenant_id,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Blocker not found for this tenant")

    return {
        "id": str(record.id),
        "patient_id": str(record.patient_id),
        "blocker_code": record.blocker_code,
        "message": record.message,
        "status": record.status,
        "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
        "resolved_by": record.resolved_by,
        "resolution_reason": record.resolution_reason,
    }
