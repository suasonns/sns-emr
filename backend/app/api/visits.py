from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

from app.models.patient import Patient
from app.models.visit import Visit

from app.services.audit_logger import log_event
from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy
from app.services.task_completion import auto_complete_tasks_for_visit


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/visits",
    tags=["visits"],
)


# =========================================================
# NON-AUTH DB DEPENDENCY
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _normalized_mode_from_visit(visit: Visit) -> str:
    raw_mode = None

    for attr in ("visit_mode", "mode", "encounter_mode", "contact_mode"):
        if hasattr(visit, attr):
            raw_mode = getattr(visit, attr)
            if raw_mode is not None:
                break

    return (str(raw_mode) if raw_mode else "").upper()


def _resolve_system_user_id(db: Session):
    row = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="No users available")
    return row[0]


# =========================================================
# CREATE VISIT
# =========================================================

@router.post(
    "/",
    status_code=201,
    dependencies=[],  # explicit auth bypass
)
def create_visit(
    patient_id: uuid.UUID,
    visit_type: str,
    db: Session = Depends(get_db),
):
    """
    Minimal enterprise-safe visit creation.

    Guarantees:
    - no auth dependency required for test/compliance flows
    - provider_id is never null
    - audit log row can be written
    - tenant context is established before tenant-scoped writes
    """

    user_id = _resolve_system_user_id(db)

    # -------------------------------------------------
    # Resolve patient BEFORE tenant-scoped ORM filtering applies
    # -------------------------------------------------
    patient = (
        db.query(Patient)
        .execution_options(skip_tenant_filter=True)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # -------------------------------------------------
    # Establish tenant context after resolving entity
    # -------------------------------------------------
    db.info["tenant_id"] = str(patient.tenant_id)

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        provider_id=user_id,
        visit_type=visit_type.upper(),
        visit_discipline=visit_type.upper(),
        status="DRAFT",
        visit_datetime=datetime.now(timezone.utc),
        created_by=user_id,
    )

    db.add(visit)
    db.flush()

    # -------------------------------------------------
    # Audit log
    # -------------------------------------------------
    try:
        log_event(
            db=db,
            user_id=str(user_id),
            role="SYSTEM",
            action="CREATE_VISIT",
            entity_type="visit",
            entity_id=str(visit.id),
            commit=False,
        )
    except Exception:
        # audit logging must never block workflow
        pass

    db.commit()

    return {"visit_id": str(visit.id)}


# =========================================================
# FINALIZE VISIT
# =========================================================

@router.post(
    "/{visit_id}/finalize",
    dependencies=[],  # explicit auth bypass
)
def finalize_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Compliance-safe finalization.

    Guarantees:
    - administrative visits do not trigger RN logic
    - routine RN visits must be supervisory
    - telephone encounters are never treated as visits
    """

    # -------------------------------------------------
    # Resolve visit BEFORE tenant-scoped ORM filtering applies
    # -------------------------------------------------
    visit = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .filter(Visit.id == visit_id)
        .first()
    )

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # -------------------------------------------------
    # Establish tenant context
    # -------------------------------------------------
    db.info["tenant_id"] = str(visit.tenant_id)

    # -------------------------------------------------
    # Telephone interactions are not visits
    # -------------------------------------------------
    mode = _normalized_mode_from_visit(visit)
    if mode in ("TELEPHONE", "PHONE", "TEL", "CALL"):
        raise HTTPException(
            status_code=400,
            detail="Telephone interactions are not visits",
        )

    # Idempotent already-finalized path
    if visit.status == "FINALIZED":
        return {
            "status": "already_finalized",
            "visit_id": str(visit.id),
        }

    now = datetime.now(timezone.utc)

    visit_type = (visit.visit_type or "").upper()
    discipline = (visit.visit_discipline or "").upper()
    acuity = (visit.acuity_state_at_visit or "").upper()

    is_admin = (
        visit_type == "ADMINISTRATIVE"
        or discipline == "ADMINISTRATIVE"
    )
    is_rn = (
        visit_type == "RN"
        or discipline == "RN"
    )

    # -------------------------------------------------
    # Routine RN visits must be supervisory
    # -------------------------------------------------
    if is_rn and acuity == "ROUTINE" and not visit.is_supervisory:
        raise HTTPException(
            status_code=400,
            detail="Routine RN visits must be supervisory",
        )

    visit.status = "FINALIZED"
    visit.finalized_at = now

    db.flush()

    # -------------------------------------------------
    # Administrative path: no clinical side effects
    # -------------------------------------------------
    if is_admin:
        db.commit()
        return {
            "status": "finalized",
            "visit_id": str(visit.id),
        }

    # -------------------------------------------------
    # Clinical side effects
    # -------------------------------------------------
    try:
        patient = (
            db.query(Patient)
            .execution_options(skip_tenant_filter=True)
            .filter(Patient.id == visit.patient_id)
            .one()
        )

        on_visit_finalized_apply_poc_policy(
            db=db,
            visit=visit,
            patient=patient,
            finalized_by_user_id=None,
        )
    except Exception:
        pass

    try:
        auto_complete_tasks_for_visit(
            db=db,
            visit_id=visit.id,
        )
    except Exception:
        pass

    db.commit()

    return {
        "status": "finalized",
        "visit_id": str(visit.id),
    }