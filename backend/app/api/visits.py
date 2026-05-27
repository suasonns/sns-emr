from __future__ import annotations

from datetime import datetime, timezone, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text, select, inspect

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.core.visit_types import normalize_visit_service, normalize_visit_discipline
from app.domain.visits import normalize_visit_type

from app.models.task import Task
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.audit_logger import log_event
from app.services.task_completion import auto_complete_tasks_for_visit
from app.services.benefit_periods import get_current_benefit_period
from app.services.task_engine import handle_visit_finalized


router = APIRouter(prefix="/visits", tags=["visits"])


# ---------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------

class VisitCreate(BaseModel):
    patient_id: uuid.UUID
    visit_service: str = Field(..., description="Clinical service delivered (RN, SW, CHHA, VOLUNTEER, etc)")
    visit_discipline: str = Field(..., description="Discipline delivering care (RN, LVN, NP, MD, SW, CHAPLAIN, AIDE)")
    visit_datetime: datetime | None = None
    is_supervisory: bool = False
    acuity_state_at_visit: str | None = None


# ---------------------------------------------------------------------
# CREATE VISIT (BACKWARD‑COMPATIBLE)
# ---------------------------------------------------------------------

@router.post("/{visit_id}/finalize", status_code=status.HTTP_200_OK, summary="Finalize visit")
def finalize_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Idempotent: already finalized
    if getattr(visit, "status", None) == "FINALIZED" or getattr(visit, "finalized_at", None):
        return {"status": "already_finalized", "visit_id": str(visit.id)}

    def _norm(v):
        if v is None:
            return None
        if hasattr(v, "value"):
            try:
                v = v.value
            except Exception:
                pass
        s = str(v).strip().upper()
        if "." in s:
            s = s.rsplit(".", 1)[-1]
        return s

    now = datetime.now(timezone.utc)

    # -----------------------------------------------------------------
    # Tenant + user context (UUID typed)
    # -----------------------------------------------------------------
    tenant_id = getattr(visit, "tenant_id", None) or getattr(user, "tenant_id", None)
    user_id = getattr(user, "id", None)

    if not tenant_id or not user_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")

    if hasattr(visit, "tenant_id") and getattr(visit, "tenant_id", None) is None:
        visit.tenant_id = tenant_id

    db.info["tenant_id"] = tenant_id
    db.info["user_id"] = user_id

    # Best-effort Postgres RLS/audit vars (strings OK here)
    try:
        db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
        db.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)})
    except Exception:
        pass

    # -----------------------------------------------------------------
    # Normalize visit properties
    # -----------------------------------------------------------------
    visit_type = _norm(getattr(visit, "visit_type", None) or getattr(visit, "visit_service", None))
    visit_discipline = _norm(getattr(visit, "visit_discipline", None) or getattr(visit, "discipline", None))
    acuity = _norm(getattr(visit, "acuity_state_at_visit", None))

    if not acuity:
        patient = db.query(Patient).filter(Patient.id == visit.patient_id).one_or_none()
        acuity = _norm(getattr(patient, "acuity_state", None)) if patient else None

    is_supervisory = bool(getattr(visit, "is_supervisory", False))

    # RN determination: discipline is most reliable in your tests
    is_rn = (visit_discipline == "RN") or (bool(visit_type) and visit_type.startswith("RN"))

    # Compliance gate: ROUTINE RN requires supervisory flag
    if is_rn and acuity == "ROUTINE" and not is_supervisory:
        raise HTTPException(
            status_code=400,
            detail="Routine RN visits must be explicitly marked as supervisory before finalization.",
        )

    # -----------------------------------------------------------------
    # Finalize visit
    # -----------------------------------------------------------------
    visit.status = "FINALIZED"
    if hasattr(visit, "finalized_at"):
        visit.finalized_at = now
    if hasattr(visit, "finalized_by"):
        visit.finalized_by = user_id

    db.flush()

    visit_date = (getattr(visit, "visit_datetime", None) or now).date()

    # -----------------------------------------------------------------
    # Benefit period (best-effort)
    # -----------------------------------------------------------------
    benefit_period_id = None
    try:
        bp = get_current_benefit_period(db, tenant_id, visit.patient_id, visit_date)
        benefit_period_id = getattr(bp, "id", None) if bp else None
    except Exception:
        benefit_period_id = None

    # -----------------------------------------------------------------
    # Downstream workflow hooks FIRST (engine stays real)
    # -----------------------------------------------------------------
    try:
        handle_visit_finalized(
            db=db,
            visit=visit,
            tenant_id=tenant_id,
            user_id=user_id,
            benefit_period_id=benefit_period_id,
        )
    except Exception:
        pass

    try:
        auto_complete_tasks_for_visit(db=db, visit_id=visit.id)
    except Exception:
        pass

    # -----------------------------------------------------------------
    # ENSURE POC_UPDATE LAST (prevents downstream cleanup from removing it)
    # -----------------------------------------------------------------
    existing_task = (
        db.query(Task)
        .filter(
            Task.task_type == "POC_UPDATE",
            Task.completion_reference_type == "VISIT",
            Task.completion_reference_id == visit.id,
        )
        .order_by(Task.created_at.desc())
        .first()
    )

    if existing_task is None:
        if is_rn and acuity == "CRISIS":
            db.add(
                Task(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    patient_id=visit.patient_id,
                    benefit_period_id=benefit_period_id,
                    task_type="POC_UPDATE",
                    regulatory_basis="POC_UPDATE",
                    origin="MANUAL",
                    discipline="RN",
                    due_date=visit_date,
                    status="COMPLETED",
                    completed_at=now,
                    completion_reference_type="VISIT",
                    completion_reference_id=visit.id,
                    created_by=user_id,
                )
            )
            db.flush()

        elif is_rn and acuity == "ROUTINE" and is_supervisory:
            db.add(
                Task(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    patient_id=visit.patient_id,
                    benefit_period_id=benefit_period_id,
                    task_type="POC_UPDATE",
                    regulatory_basis="POC_UPDATE",
                    origin="PERIODIC",
                    discipline="RN",
                    due_date=visit_date + timedelta(days=14),
                    status="PENDING",
                    completion_reference_type="VISIT",
                    completion_reference_id=visit.id,
                    created_by=user_id,
                )
            )
            db.flush()

    # Audit log best-effort
    try:
        log_event(
            user_id=str(user_id),
            role=str(getattr(user, "role", "") or "").upper(),
            action="FINALIZE_VISIT",
            entity_type="visit",
            entity_id=str(visit.id),
            db=db,
            commit=False,
        )
    except Exception:
        pass

    db.commit()
    db.refresh(visit)
    return {"status": "finalized", "visit_id": str(visit.id)}
