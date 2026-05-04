from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.models.chha_poc import CHHAPOC
from app.services.audit_logger import log_event

router = APIRouter(
    prefix="/chha-pocs",
    tags=["CHHA Plan of Care"],
)


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create CHHA POC (draft)")
def create_chha_poc(
    *,
    patient_id: uuid.UUID,
    frequency: str | None = None,
    instructions: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    poc = CHHAPOC(
        patient_id=patient_id,
        status="draft",
        frequency=frequency,
        instructions=instructions,
        created_by=user.user_id,
    )

    db.add(poc)
    db.flush()  # ensures poc.id exists

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="CREATE_CHHA_POC",
        entity_type="chha_poc",
        entity_id=str(poc.id),
        db=db,
    )

    db.commit()
    db.refresh(poc)

    return {
        "chha_poc_id": str(poc.id),
        "patient_id": str(poc.patient_id),
        "status": poc.status,
        "created_at": poc.created_at,
    }


@router.get("/patient/{patient_id}", summary="List CHHA POCs for a patient")
def list_chha_pocs_for_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "CHHA"])),
):
    pocs = (
        db.query(CHHAPOC)
        .filter(CHHAPOC.patient_id == patient_id)
        .order_by(CHHAPOC.created_at.desc())
        .all()
    )

    return [
        {
            "chha_poc_id": str(poc.id),
            "status": poc.status,
            "finalized_at": poc.finalized_at,
            "finalized_by": str(poc.finalized_by) if poc.finalized_by else None,
            "effective_start": poc.effective_start,
            "effective_end": poc.effective_end,
            "frequency": poc.frequency,
        }
        for poc in pocs
    ]


@router.post(
    "/{chha_poc_id}/finalize",
    status_code=status.HTTP_200_OK,
    summary="Finalize (activate) a CHHA Plan of Care",
)
def finalize_chha_poc(
    chha_poc_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()
    if not poc:
        raise HTTPException(status_code=404, detail="CHHA Plan of Care not found")

    if poc.status == "active":
        raise HTTPException(status_code=400, detail="CHHA Plan of Care is already active")

    if poc.status == "superseded":
        raise HTTPException(status_code=400, detail="Superseded CHHA Plan of Care cannot be finalized")

    # One active per patient: supersede any other active
    active_pocs = (
        db.query(CHHAPOC)
        .filter(CHHAPOC.patient_id == poc.patient_id, CHHAPOC.status == "active")
        .all()
    )
    for old in active_pocs:
        old.status = "superseded"
        old.effective_end = datetime.utcnow().date()

    poc.status = "active"
    poc.finalized_at = datetime.utcnow()
    poc.finalized_by = user.user_id
    poc.effective_start = poc.effective_start or datetime.utcnow().date()

    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="FINALIZE_CHHA_POC",
        entity_type="chha_poc",
        entity_id=str(poc.id),
        db=db,
    )

    db.commit()
    db.refresh(poc)

    return {
        "chha_poc_id": str(poc.id),
        "patient_id": str(poc.patient_id),
        "status": poc.status,
        "finalized_at": poc.finalized_at,
        "finalized_by": str(poc.finalized_by),
        "effective_start": poc.effective_start,
        "effective_end": poc.effective_end,
    }


@router.post(
    "/{chha_poc_id}/supersede",
    status_code=status.HTTP_200_OK,
    summary="Supersede (retire) an active CHHA Plan of Care",
)
def supersede_chha_poc(
    chha_poc_id: uuid.UUID,
    reason: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()
    if not poc:
        raise HTTPException(status_code=404, detail="CHHA Plan of Care not found")

    if poc.status != "active":
        raise HTTPException(status_code=400, detail="Only an active CHHA Plan of Care can be superseded")

    poc.status = "superseded"
    poc.effective_end = datetime.utcnow().date()

    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="SUPERSEDE_CHHA_POC",
        entity_type="chha_poc",
        entity_id=str(poc.id),
        db=db,
    )

    db.commit()
    db.refresh(poc)

    return {
        "chha_poc_id": str(poc.id),
        "patient_id": str(poc.patient_id),
        "status": poc.status,
        "effective_end": poc.effective_end,
        "reason": reason,
    }