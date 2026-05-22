from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.visit_types import normalize_visit_discipline

from app.models.visit import Visit
from app.models.patient import Patient

from app.services.audit_logger import log_event
from app.services.task_completion import auto_complete_tasks_for_visit
from app.services.benefit_periods import get_current_benefit_period
from app.services.task_engine import handle_visit_finalized

router = APIRouter(prefix="/visits", tags=["visits"])


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

    # Normalize discipline (rules are RN-anchored)
    visit.visit_discipline = normalize_visit_discipline(getattr(visit, "visit_discipline", "") or "")

    # Finalize visit (legal snapshot)
    now = datetime.now(timezone.utc)
    visit.status = "finalized"
    visit.finalized_at = now
    visit.finalized_by = user_id

    # Benefit period anchoring
    on_date = (visit.visit_datetime or now).date()
    bp = get_current_benefit_period(db=db, tenant_id=tenant_id, patient_id=visit.patient_id, on_date=on_date)
    benefit_period_id = getattr(bp, "id", None) if bp else None

    # CRITICAL: DB trigger requires app_user_id set before task writes
    db.execute(text("SELECT set_config('app_user_id', :uid, true)"), {"uid": str(user_id)})

    # Task engine hook (creates/updates POC_UPDATE tasks)
    handle_visit_finalized(
        db=db,
        visit=visit,
        tenant_id=tenant_id,
        user_id=user_id,
        benefit_period_id=benefit_period_id,
    )

    # Auto-complete any other visit-driven tasks (HUV/SFV etc.)
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