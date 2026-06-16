from __future__ import annotations

import uuid
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.dependencies.auth import get_current_user

from app.models.communications_log import CommunicationsLog
from app.api.communications_log.schemas import (
    CommunicationsLogCreate,
    CommunicationsLogRead,
)

from app.services.communications_log_alerts import create_commlog_alerts
from app.services.commlog_to_task_bridge import handle_commlog_for_tasks


router = APIRouter(
    prefix="/communications-log",
    tags=["Communications Log"],
)


# ---------------------------------------------------------
# Helpers (enterprise-safe)
# ---------------------------------------------------------

def _user_get(user, key: str, default=None):
    """Support user being either dict-like or object-like."""
    if isinstance(user, dict):
        return user.get(key, default)
    return getattr(user, key, default)


def _apply_tenant_search_path(db: Session, schema_name: str) -> None:
    """
    Set tenant search_path so tenant-scoped tables resolve correctly.
    """
    if not schema_name:
        raise HTTPException(status_code=400, detail="Tenant schema not found")

    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid tenant schema")

    db.execute(text(f"SET search_path TO {schema_name}, public"))


def _resolve_tenant_schema_name(db: Session, request: Request, user) -> str:
    """
    Resolve tenant schema name safely.
    Prefer request.state.tenant_schema_name if middleware sets it.
    Fallback: query core.tenants using tenant_id from authenticated user.
    """
    schema_name = getattr(request.state, "tenant_schema_name", None) or getattr(request.state, "schema_name", None)
    if schema_name:
        return str(schema_name)

    tenant_id = _user_get(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")

    schema_name = db.execute(
        text("SELECT schema_name FROM core.tenants WHERE id = :tid"),
        {"tid": str(tenant_id)},
    ).scalar()

    if not schema_name:
        raise HTTPException(status_code=400, detail="Tenant schema not found")

    return str(schema_name)


def require_create_access(user) -> None:
    """
    Communications Log is tenant clinical/operational.
    OWNER/BILLING are blocked.
    """
    role = (_user_get(user, "role", "") or "").upper()
    if role in {"OWNER", "BILLING"}:
        raise HTTPException(status_code=403, detail="Access denied")


def _resolve_user_ids_to_notify(db: Session, patient_id: UUID) -> list[UUID]:
    """
    Resolve recipients for Communications Log alerts.
    Best-effort:
    - patient assignment notifications (if model exists)
    - always notify DPCS_ADMIN
    - never block comm log creation if resolution fails
    """
    user_ids: set[UUID] = set()

    try:
        from app.models.patient_assignment import PatientAssignment  # type: ignore

        rows = (
            db.query(PatientAssignment)
            .filter(PatientAssignment.patient_id == patient_id)
            .all()
        )
        for r in rows:
            uid = getattr(r, "user_id", None)
            if uid:
                user_ids.add(uid)
    except Exception:
        pass

    try:
        dpcs_rows = db.execute(
            text("SELECT id FROM users WHERE role = 'DPCS_ADMIN'")
        ).fetchall()
        for row in dpcs_rows:
            user_ids.add(row[0])
    except Exception:
        pass

    return list(user_ids)


# ---------------------------------------------------------
# POST: Create Communications Log (Phase 1B + Alerts + Tasks)
# ---------------------------------------------------------

@router.post("", response_model=CommunicationsLogRead)
def create_communications_log(
    payload: CommunicationsLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_create_access(user)

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entry = CommunicationsLog(
        id=uuid.uuid4(),
        patient_id=payload.patient_id,
        event_type=payload.event_type,
        focus_area=payload.focus_area,
        event_time=payload.event_time,
        summary=payload.summary,
        details=payload.details,
        created_by=_user_get(user, "id"),
    )

    db.add(entry)
    db.flush()  # entry.id now available for notifications/tasks

    # 🔔 Alerts (Phase 2.1)
    try:
        user_ids_to_notify = _resolve_user_ids_to_notify(db, payload.patient_id)
        if user_ids_to_notify:
            create_commlog_alerts(
                db=db,
                patient_id=payload.patient_id,
                commlog_id=entry.id,
                message=payload.summary,
                user_ids=user_ids_to_notify,
            )
    except Exception:
        pass

    # 🧾 Task automation (Phase 2.2) - best effort
    try:
        handle_commlog_for_tasks(db, entry)
    except Exception:
        pass

    # ✅ Critical tenant-schema ORM safety:
    # Prevent SQLAlchemy from expiring objects and triggering a refresh/select
    # on a new connection without search_path.
    db.expire_on_commit = False
    db.commit()

    return entry


# ---------------------------------------------------------
# GET: Patient Communications Log Timeline
# ---------------------------------------------------------

@router.get("/patients/{patient_id}", response_model=list[CommunicationsLogRead])
def get_patient_communications_log(
    patient_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entries = (
        db.query(CommunicationsLog)
        .filter(CommunicationsLog.patient_id == patient_id)
        .order_by(CommunicationsLog.event_time.desc())
        .all()
    )
    return entries