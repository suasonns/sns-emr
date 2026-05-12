from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.visit_types import (
    normalize_visit_service,
    normalize_visit_discipline,
)

from app.models.patient import Patient
from app.models.visit import Visit

from app.services.audit_logger import log_event
from app.services.task_completion import auto_complete_tasks_for_visit

# ✅ Benefit period anchoring + task engine hook
from app.services.benefit_periods import get_current_benefit_period
from app.services.task_engine import handle_visit_finalized


router = APIRouter(prefix="/visits", tags=["visits"])


# =========================================================
# SCHEMAS
# =========================================================
class VisitCreate(BaseModel):
    patient_id: uuid.UUID

    # ✅ SERVICE (what was delivered)
    visit_service: str = Field(
        ...,
        description="Clinical service delivered (SN, SW, CHAPLAIN, CHHA, VOLUNTEER)",
    )

    # ✅ DISCIPLINE (who delivered it)
    visit_discipline: str = Field(
        ...,
        description="Discipline delivering care (RN, LVN, NP, MD, SW, CHAPLAIN, AIDE)",
    )

    visit_datetime: datetime | None = None
    is_supervisory: bool = False
    acuity_state_at_visit: str | None = None  # ROUTINE / CRISIS


# =========================================================
# VISIT CREATE (JSON BODY — COMPLIANT)
# =========================================================
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
        raise HTTPException(status_code=500, detail="Tenant context missing on user session")

    # ✅ Normalize and validate explicitly
    visit_service = normalize_visit_service(payload.visit_service)
    visit_discipline = normalize_visit_discipline(payload.visit_discipline)

    # Normalize acuity (optional)
    acuity = (payload.acuity_state_at_visit or None)
    if acuity is not None:
        acuity = acuity.strip().upper()
        if acuity not in {"ROUTINE", "CRISIS"}:
            raise HTTPException(status_code=400, detail="acuity_state_at_visit must be ROUTINE or CRISIS")

    # ✅ Ensure patient exists and belongs to tenant
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == payload.patient_id,
            Patient.tenant_id == tenant_id,
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        provider_id=user_id,

        # ✅ EXPLICIT SEMANTICS
        visit_type=visit_service,           # SERVICE (SN/SW/CHHA/etc)
        visit_discipline=visit_discipline,  # DISCIPLINE (RN/LVN/NP/MD/etc)

        visit_datetime=payload.visit_datetime or datetime.now(timezone.utc),
        is_supervisory=payload.is_supervisory,
        acuity_state_at_visit=acuity,
        status="draft",
    )

    db.add(visit)
    db.commit()
    db.refresh(visit)

    # ✅ AUDIT
    log_event(
        user_id=user_id,
        role=user_role,
        action="VISIT_CREATED",
        entity_type="VISIT",
        entity_id=str(visit.id),
        db=db,
    )

    return {
        "visit_id": str(visit.id),
        "status": visit.status,
    }


# =========================================================
# VISIT FINALIZE (COMPLIANCE TRIGGER)
# =========================================================
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
        raise HTTPException(status_code=500, detail="Tenant context missing on user session")

    visit = (
        db.query(Visit)
        .filter(
            Visit.id == visit_id,
            Visit.tenant_id == tenant_id,
        )
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Idempotency guard
    if visit.status == "finalized" or getattr(visit, "finalized_at", None) is not None:
        return {"status": "already_finalized"}

    # ✅ Normalize discipline for downstream rules (RN logic uses discipline)
    if getattr(visit, "visit_discipline", None):
        visit.visit_discipline = normalize_visit_discipline(visit.visit_discipline)

    # Finalize (legal snapshot)
    visit.status = "finalized"
    visit.finalized_at = datetime.now(timezone.utc)
    visit.finalized_by = user_id

    # ✅ Benefit period anchoring (obligations must attach when available)
    on_date = visit.visit_datetime.date() if getattr(visit, "visit_datetime", None) else datetime.now(timezone.utc).date()
    active_bp_id = get_active_benefit_period_id(
        db,
        patient_id=visit.patient_id,
        on_date=on_date,
    )

    # ✅ Trigger compliance task engine (ROUTINE vs CRISIS POC_UPDATE)
    handle_visit_finalized(
        db,
        visit,
        active_benefit_period_id=active_bp_id,
    )

    # ✅ Evidence linkage + completion for other due tasks tied to a finalized visit
    # (This should NOT commit; we commit once below.)
    auto_complete_tasks_for_visit(
        db=db,
        visit=visit,
        completed_by=user_id,
    )

    # ✅ Single atomic commit for visit + tasks
    db.add(visit)
    db.commit()
    db.refresh(visit)

    # ✅ AUDIT
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
        "benefit_period_id": str(active_bp_id) if active_bp_id else None,
        "acuity_state_at_visit": getattr(visit, "acuity_state_at_visit", None),
        "visit_discipline": getattr(visit, "visit_discipline", None),
    }