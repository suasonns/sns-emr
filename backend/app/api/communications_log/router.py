from __future__ import annotations

import logging
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.dependencies.auth import get_current_user
from app.models.communications_log import CommunicationsLog
from app.api.communications_log.schemas import (
    CommunicationsLogCreate,
    CommunicationsLogRead,
    CommunicationsLogAction,
)
from app.services.communications_log_alerts import create_commlog_alerts
from app.services.commlog_to_task_bridge import handle_commlog_for_tasks

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/communications-log",
    tags=["Communications Log"],
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _user_get(user, key: str, default=None):
    """
    Support user being either dict-like or object-like.
    """
    if isinstance(user, dict):
        return user.get(key, default)
    return getattr(user, key, default)


def _apply_tenant_search_path(db: Session, schema_name: str) -> None:
    """
    Set tenant search_path safely.
    Keeps public available for shared tables.
    """
    if not schema_name:
        raise HTTPException(status_code=400, detail="Tenant schema not found")

    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid tenant schema name")

    db.execute(text(f'SET search_path TO "{schema_name}", public'))


def _resolve_tenant_schema_name(db: Session, request: Request, user) -> str:
    """
    Resolve tenant schema safely.

    Order:
    1. request.state.tenant_schema_name
    2. request.state.schema_name
    3. fallback to public
    """
    schema_name = getattr(request.state, "tenant_schema_name", None) or getattr(
        request.state, "schema_name", None
    )

    if schema_name:
        return str(schema_name)

    return "public"


def require_create_access(user) -> None:
    """
    Communications Log is tenant clinical/operational.
    OWNER/BILLING are blocked.
    """
    role = (_user_get(user, "role", "") or "").upper()
    if role in {"OWNER", "BILLING"}:
        raise HTTPException(status_code=403, detail="Access denied")


def _get_user_admin_flag(db: Session, *, user_id: UUID) -> bool:
    """
    Look up tenant-configurable admin access from public.users.
    """
    user_row = db.execute(
        text(
            """
            SELECT has_admin_access
            FROM public.users
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchone()

    return bool(user_row[0]) if user_row else False


def _resolve_user_ids_to_notify(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
) -> list[UUID]:
    """
    Resolve notification recipients.

    Privacy rules:
    - ONLY users assigned to this patient
    - PLUS clinical admin / DPCS for the same tenant
    - NEVER broadcast to all users
    """
    user_ids: set[UUID] = set()

    # -------------------------------------------------
    # 1. PATIENT-ASSIGNED USERS (via tasks)
    # -------------------------------------------------
    try:
        assigned_rows = db.execute(
            text(
                """
                SELECT DISTINCT assigned_user_id
                FROM tasks
                WHERE patient_id = :patient_id
                  AND tenant_id = :tenant_id
                  AND assigned_user_id IS NOT NULL
                """
            ),
            {
                "patient_id": patient_id,
                "tenant_id": tenant_id,
            },
        ).fetchall()

        for row in assigned_rows:
            if row[0]:
                user_ids.add(row[0])

    except Exception as e:
        logger.error(
            "COMMLOG ALERT RECIPIENT RESOLUTION (ASSIGNED USERS) FAILED: %s",
            e,
        )

    # -------------------------------------------------
    # 2. CLINICAL ADMIN / DPCS (tenant-scoped)
    # -------------------------------------------------
    try:
        admin_rows = db.execute(
            text(
                """
                SELECT id
                FROM public.users
                WHERE tenant_id = :tenant_id
                  AND active = true
                  AND (
                        role = 'DPCS'
                        OR has_admin_access = true
                        OR role ILIKE '%ADMIN%'
                      )
                """
            ),
            {
                "tenant_id": tenant_id,
            },
        ).fetchall()

        for row in admin_rows:
            if row[0]:
                user_ids.add(row[0])

    except Exception as e:
        logger.error(
            "COMMLOG ALERT RECIPIENT RESOLUTION (ADMINS) FAILED: %s",
            e,
        )

    return list(user_ids)


def _require_patient_visibility(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
    user,
) -> None:
    """
    Enterprise-grade access control for communications log visibility.

    Rules:
    - ADMIN → full system access
    - DPCS → full clinical access (all patients)
    - has_admin_access = true → full clinical access (tenant-configurable,
      e.g. Assistant DPCS / senior case manager if explicitly granted)
    - Others → only assigned patients
    """
    user_id = _user_get(user, "id")
    role = (_user_get(user, "role") or "").upper()

    has_admin_access = _get_user_admin_flag(db, user_id=user_id)

    # -------------------------------------------------
    # 1. OFFICE ADMIN → FULL SYSTEM ACCESS
    # -------------------------------------------------
    if role == "ADMIN":
        return

    # -------------------------------------------------
    # 2. DPCS → ALWAYS FULL CLINICAL ACCESS
    # -------------------------------------------------
    if role == "DPCS":
        return

    # -------------------------------------------------
    # 3. TENANT-CONFIGURABLE CLINICAL ADMIN ACCESS
    # -------------------------------------------------
    if has_admin_access:
        return

    # -------------------------------------------------
    # 4. DEFAULT → ASSIGNMENT-BASED ACCESS
    # -------------------------------------------------
    recipients = _resolve_user_ids_to_notify(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
    )

    if user_id not in recipients:
        raise HTTPException(
            status_code=403,
            detail="Access denied for this patient communication log",
        )


def _is_clinically_qualified_to_verify_or_resolve(
    *,
    role: str,
    has_admin_access: bool,
) -> bool:
    """
    Verify/Resolve require a clinically qualified actor.

    Allowed:
    - DPCS
    - RN
    - NP
    - MD
    - LVN
    - any user explicitly granted has_admin_access (e.g. Assistant DPCS/senior CM)
      under tenant policy
    """
    role = (role or "").upper()

    if role in {"DPCS", "RN", "NP", "MD", "LVN"}:
        return True

    if has_admin_access:
        return True

    return False


def _append_workflow_note(
    entry: CommunicationsLog,
    *,
    status: str,
    actor_id: UUID,
    note: str | None,
) -> None:
    """
    Append workflow_notes without destroying existing details such as:
    - trigger_type
    - reports
    - required_actions
    """
    if entry.details is None or not isinstance(entry.details, dict):
        entry.details = {}

    entry.details.setdefault("workflow_notes", [])
    entry.details["workflow_notes"].append(
        {
            "status": status,
            "actor_id": str(actor_id),
            "note": note,
            "recorded_at": datetime.utcnow().isoformat(),
        }
    )


def _get_commlog_for_patient_scope(
    db: Session,
    *,
    commlog_id: UUID,
    tenant_id: UUID,
) -> CommunicationsLog:
    entry = (
        db.query(CommunicationsLog)
        .filter(
            CommunicationsLog.id == commlog_id,
            CommunicationsLog.tenant_id == tenant_id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Communications log entry not found")

    return entry


# ---------------------------------------------------------
# POST: Create Communications Log
# ---------------------------------------------------------

@router.post("", response_model=CommunicationsLogRead)
def create_communications_log(
    payload: CommunicationsLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_create_access(user)

    tenant_id = _user_get(user, "tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Authenticated user missing tenant_id")

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entry = CommunicationsLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        event_type=payload.event_type,
        focus_area=payload.focus_area,
        event_time=payload.event_time,
        summary=payload.summary,
        details=payload.details,
        created_by=_user_get(user, "id"),
        status="RECEIVED",
    )

    db.add(entry)
    db.flush()  # entry.id available for alerts/tasks

    # -------------------------------------------------
    # Alerts (best-effort, but logged)
    # -------------------------------------------------
    try:
        user_ids_to_notify = _resolve_user_ids_to_notify(
            db,
            patient_id=payload.patient_id,
            tenant_id=tenant_id,
        )

        logger.info(
            "COMMLOG ALERT RECIPIENTS resolved patient_id=%s tenant_id=%s recipients=%s",
            str(payload.patient_id),
            str(tenant_id),
            [str(x) for x in user_ids_to_notify],
        )

        if user_ids_to_notify:
            create_commlog_alerts(
                db=db,
                tenant_id=tenant_id,
                patient_id=payload.patient_id,
                commlog_id=entry.id,
                message=payload.summary,
                user_ids=user_ids_to_notify,
            )
        else:
            logger.warning(
                "COMMLOG ALERTS SKIPPED: no recipients found for patient_id=%s tenant_id=%s",
                str(payload.patient_id),
                str(tenant_id),
            )

    except Exception as e:
        logger.error("COMMLOG ALERT FAILURE: %s", e)

    # -------------------------------------------------
    # Task bridge (best-effort, but logged)
    # -------------------------------------------------
    try:
        handle_commlog_for_tasks(db, entry)
    except Exception as e:
        logger.error("COMMLOG TASK FAILURE: %s", e)

    db.expire_on_commit = False
    db.commit()
    db.refresh(entry)

    return entry


# ---------------------------------------------------------
# GET: Patient Communications Log Timeline
# ---------------------------------------------------------

@router.get("/patients/", response_model=list[CommunicationsLogRead])
def get_patient_communications_log(
    patient_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = _user_get(user, "tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Authenticated user missing tenant_id")

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    _require_patient_visibility(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        user=user,
    )

    rows = (
        db.query(CommunicationsLog)
        .filter(
            CommunicationsLog.patient_id == patient_id,
            CommunicationsLog.tenant_id == tenant_id,
        )
        .order_by(CommunicationsLog.event_time.desc(), CommunicationsLog.created_at.desc())
        .all()
    )

    return rows


# ---------------------------------------------------------
# POST: Acknowledge
# ---------------------------------------------------------

@router.post("/{commlog_id}/acknowledge", response_model=CommunicationsLogRead)
def acknowledge_communications_log(
    commlog_id: UUID,
    payload: CommunicationsLogAction | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = _user_get(user, "tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Authenticated user missing tenant_id")

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entry = _get_commlog_for_patient_scope(
        db,
        commlog_id=commlog_id,
        tenant_id=tenant_id,
    )

    _require_patient_visibility(
        db,
        patient_id=entry.patient_id,
        tenant_id=tenant_id,
        user=user,
    )

    # Strict forward progression:
    if entry.status != "RECEIVED":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot acknowledge from status {entry.status}. Expected RECEIVED.",
        )

    entry.status = "ACKNOWLEDGED"
    entry.acknowledged_by = _user_get(user, "id")
    entry.acknowledged_at = datetime.utcnow()

    _append_workflow_note(
        entry,
        status="ACKNOWLEDGED",
        actor_id=_user_get(user, "id"),
        note=(payload.note if payload else None),
    )

    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------
# POST: Verify
# ---------------------------------------------------------

@router.post("/{commlog_id}/verify", response_model=CommunicationsLogRead)
def verify_communications_log(
    commlog_id: UUID,
    payload: CommunicationsLogAction | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = _user_get(user, "tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Authenticated user missing tenant_id")

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entry = _get_commlog_for_patient_scope(
        db,
        commlog_id=commlog_id,
        tenant_id=tenant_id,
    )

    _require_patient_visibility(
        db,
        patient_id=entry.patient_id,
        tenant_id=tenant_id,
        user=user,
    )

    role = (_user_get(user, "role") or "").upper()
    has_admin_access = _get_user_admin_flag(
        db,
        user_id=_user_get(user, "id"),
    )

    if not _is_clinically_qualified_to_verify_or_resolve(
        role=role,
        has_admin_access=has_admin_access,
    ):
        raise HTTPException(
            status_code=403,
            detail="Current user is not clinically qualified to verify this communication log",
        )

    # Strict forward progression:
    if entry.status != "ACKNOWLEDGED":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot verify from status {entry.status}. Expected ACKNOWLEDGED.",
        )

    entry.status = "VERIFIED"
    entry.verified_by = _user_get(user, "id")
    entry.verified_at = datetime.utcnow()

    _append_workflow_note(
        entry,
        status="VERIFIED",
        actor_id=_user_get(user, "id"),
        note=(payload.note if payload else None),
    )

    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------
# POST: Resolve
# ---------------------------------------------------------

@router.post("/{commlog_id}/resolve", response_model=CommunicationsLogRead)
def resolve_communications_log(
    commlog_id: UUID,
    payload: CommunicationsLogAction | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = _user_get(user, "tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Authenticated user missing tenant_id")

    schema_name = _resolve_tenant_schema_name(db, request, user)
    _apply_tenant_search_path(db, schema_name)

    entry = _get_commlog_for_patient_scope(
        db,
        commlog_id=commlog_id,
        tenant_id=tenant_id,
    )

    _require_patient_visibility(
        db,
        patient_id=entry.patient_id,
        tenant_id=tenant_id,
        user=user,
    )

    role = (_user_get(user, "role") or "").upper()
    has_admin_access = _get_user_admin_flag(
        db,
        user_id=_user_get(user, "id"),
    )

    if not _is_clinically_qualified_to_verify_or_resolve(
        role=role,
        has_admin_access=has_admin_access,
    ):
        raise HTTPException(
            status_code=403,
            detail="Current user is not clinically qualified to resolve this communication log",
        )

    # Strict forward progression:
    if entry.status != "VERIFIED":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot resolve from status {entry.status}. Expected VERIFIED.",
        )

    entry.status = "RESOLVED"
    entry.resolved_by = _user_get(user, "id")
    entry.resolved_at = datetime.utcnow()

    _append_workflow_note(
        entry,
        status="RESOLVED",
        actor_id=_user_get(user, "id"),
        note=(payload.note if payload else None),
    )

    db.commit()
    db.refresh(entry)
    return entry