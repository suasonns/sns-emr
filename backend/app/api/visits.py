from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.visit_types import normalize_visit_service, normalize_visit_discipline
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.audit_logger import log_event
from app.services.task_completion import auto_complete_tasks_for_visit
from app.services.benefit_periods import get_current_benefit_period
from app.services.task_engine import handle_visit_finalized


router = APIRouter(prefix="/visits", tags=["visits"])


class VisitCreate(BaseModel):
    patient_id: uuid.UUID

    # SERVICE delivered (SN/SW/CHHA/etc)
    visit_service: str = Field(..., description="Clinical service delivered (SN, SW, CHAPLAIN, CHHA, VOLUNTEER)")

    # Discipline who delivered it (RN/LVN/NP/MD/etc)
    visit_discipline: str = Field(..., description="Discipline delivering care (RN, LVN, NP, MD, SW, CHAPLAIN, AIDE)")

    visit_datetime: datetime | None = None
    is_supervisory: bool = False

    # ROUTINE / CRISIS (optional)
    acuity_state_at_visit: str | None = None


def _set_db_context(db: Session, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """
    Transaction-local:
    - RLS tenant setting
    - audit/user setting
    """
    db.execute(text("SET LOCAL app.current_tenant = :tid"), {"tid": str(tenant_id)})
    db.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)})


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create visit")
def create_visit(
    payload: VisitCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    user_role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    # Normalize
    visit_service = normalize_visit_service(payload.visit_service)
    visit_discipline = normalize_visit_discipline(payload.visit_discipline)

    acuity = payload.acuity_state_at_visit.strip().upper() if payload.acuity_state_at_visit else None
    if acuity is not None and acuity not in {"ROUTINE", "CRISIS"}:
        raise HTTPException(status_code=400, detail="acuity_state_at_visit must be ROUTINE or CRISIS")

    # Patient must exist in tenant
    patient = (
        db.query(Patient)
        .filter(Patient.id == payload.patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        provider_id=user_id,
        visit_type=visit_service,
        visit_discipline=visit_discipline,
        visit_datetime=payload.visit_datetime or datetime.now(timezone.utc),
        is_supervisory=payload.is_supervisory,
        acuity_state_at_visit=acuity,
        status="draft",
    )

    db.add(visit)
    db.commit()
    db.refresh(visit)

    log_event(
        user_id=user_id,
        role=user_role,
        action="VISIT_CREATED",
        entity_type="VISIT",
        entity_id=str(visit.id),
        db=db,
    )

    return {"visit_id": str(visit.id), "status": visit.status}


@router.post("/{visit_id}/finalize", status_code=status.HTTP_200_OK, summary="Finalize visit")
def finalize_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    user_role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    visit = (
        db.query(Visit)
        .filter(Visit.id == visit_id, Visit.tenant_id == tenant_id)
        .one_or_none()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Idempotency
    if visit.status == "finalized" or getattr(visit, "finalized_at", None):
        return {"status": "already_finalized", "visit_id": str(visit.id)}

    # Finalize snapshot
    now = datetime.now(timezone.utc)
    visit.status = "finalized"
    visit.finalized_at = now
    visit.finalized_by = user_id

    # Benefit period anchoring
    on_date = (visit.visit_datetime or now).date()
    bp = get_current_benefit_period(db=db, tenant_id=tenant_id, patient_id=visit.patient_id, on_date=on_date)
    benefit_period_id = getattr(bp, "id", None) if bp else None

    # Task engine hook
    handle_visit_finalized(
        db=db,
        visit=visit,
        tenant_id=tenant_id,
        user_id=user_id,
        benefit_period_id=benefit_period_id,
    )

    # Auto-complete other visit-driven tasks (if any)
    auto_complete_tasks_for_visit(
        db=db,
        tenant_id=tenant_id,
        visit=visit,
        completed_by=user_id,
    )

    db.add(visit)
    db.commit()
    db.refresh(visit)

    log_event(
        user_id=user_id,
        role=user_role,
        action="VISIT_FINALIZED",
        entity_type="VISIT",
        entity_id=str(visit.id),
        db=db,
    )

    return {
        "status": "finalized",
        "visit_id": str(visit.id),
        "finalized_at": str(visit.finalized_at),
        "benefit_period_id": str(benefit_period_id) if benefit_period_id else None,
        "acuity_state_at_visit": getattr(visit, "acuity_state_at_visit", None),
        "visit_discipline": getattr(visit, "visit_discipline", None),
    }
