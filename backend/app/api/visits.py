from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.visit_types import normalize_visit_type

from app.models.patient import Patient
from app.models.visit import Visit
from app.models.chha_poc import CHHAPOC
from app.models.task import Task

from app.services.audit_logger import log_event
from app.services.task_completion import auto_complete_tasks_for_visit

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_visit(
    *,
    patient_id: uuid.UUID,
    visit_type: str,
    visit_datetime: datetime | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD"])),
):
    """
    Create a clinical visit for a patient (draft).
    visit_type is normalized to canonical values.
    Also stamps acuity_state_at_visit for audit readiness.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vt = normalize_visit_type(visit_type)

    visit = Visit(
        patient_id=patient.id,
        provider_id=user.user_id,
        visit_type=vt,
        visit_datetime=visit_datetime or datetime.utcnow(),
        status="draft",
        created_by=user.user_id,

        # Snapshot acuity at time of visit creation (audit-critical)
        acuity_state_at_visit=getattr(patient, "acuity_state", None),
    )

    db.add(visit)
    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="CREATE_VISIT",
        entity_type="visit",
        entity_id=str(visit.id),
        db=db,
    )

    db.commit()
    db.refresh(visit)

    return {
        "visit_id": str(visit.id),
        "patient_id": str(patient.id),
        "visit_type": visit.visit_type,
        "visit_datetime": visit.visit_datetime,
        "status": visit.status,
        "chha_poc_id": str(visit.chha_poc_id) if getattr(visit, "chha_poc_id", None) else None,
        "acuity_state_at_visit": getattr(visit, "acuity_state_at_visit", None),
    }


@router.patch(
    "/{visit_id}/chha-poc/{poc_id}",
    summary="Attach an RN-authored CHHA POC to a CHHA visit (must be before finalization)",
)
def attach_chha_poc_to_visit(
    visit_id: uuid.UUID,
    poc_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    if visit.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Finalized visits cannot be modified")

    vt = normalize_visit_type(visit.visit_type)
    if vt != "CHHA":
        raise HTTPException(status_code=400, detail="CHHA POC can only be attached to CHHA visits")

    poc = db.query(CHHAPOC).filter(CHHAPOC.id == poc_id).first()
    if not poc:
        raise HTTPException(status_code=404, detail="CHHA POC not found")

    visit.chha_poc_id = poc.id
    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ATTACH_CHHA_POC",
        entity_type="visit",
        entity_id=str(visit.id),
        db=db,
    )

    db.commit()
    db.refresh(visit)

    return {
        "visit_id": str(visit.id),
        "visit_type": visit.visit_type,
        "chha_poc_id": str(visit.chha_poc_id),
        "status": visit.status,
    }


@router.post("/{visit_id}/finalize", status_code=status.HTTP_200_OK)
def finalize_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    """
    Finalize a visit.

    Compliance rules:
    - RN ROUTINE visits must be explicitly supervisory before finalization.
    - RN CRISIS visits are exempt.
    - CHHA visits require an active, RN-finalized CHHA POC (separate rule).
    - POC_UPDATE task automation:
        * CRISIS: finalized RN visit creates + completes same-day POC_UPDATE (origin MANUAL).
        * ROUTINE: finalized supervisory RN visit creates next POC_UPDATE due +14 days (origin PERIODIC).
    """
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    if visit.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Visit already finalized")

    vt = normalize_visit_type(visit.visit_type)

    # =========================================================
    # RN SUPERVISORY GUARDRAIL (clinical POC)
    # =========================================================
    care_level = getattr(visit, "acuity_state_at_visit", None)

    # Backward compatibility if care_level ever exists on Visit
    if care_level is None:
        care_level = getattr(visit, "care_level", None)

    # Fallback to Patient for older rows without snapshot
    if care_level is None:
        patient = db.query(Patient).filter(Patient.id == visit.patient_id).first()
        if patient:
            care_level = getattr(patient, "acuity_state", None)

    care_level = (care_level or "").upper()

    if vt == "RN" and care_level != "CRISIS":
        if getattr(visit, "is_supervisory", False) is not True:
            raise HTTPException(
                status_code=400,
                detail=(
                    "RN routine visits must be explicitly marked as supervisory "
                    "before finalization to satisfy Plan of Care review requirements."
                ),
            )

    # =========================================================
    # CHHA POC ENFORCEMENT (separate from clinical POC)
    # =========================================================
    if vt == "CHHA":
        if getattr(visit, "chha_poc_id", None) is None:
            raise HTTPException(
                status_code=400,
                detail="CHHA visit requires an active RN-authored CHHA Plan of Care (chha_poc_id)",
            )

        poc = db.query(CHHAPOC).filter(CHHAPOC.id == visit.chha_poc_id).first()
        if not poc:
            raise HTTPException(status_code=400, detail="Referenced CHHA Plan of Care does not exist")

        if poc.finalized_at is None or poc.status != "active":
            raise HTTPException(
                status_code=400,
                detail="CHHA Plan of Care must be finalized and active before CHHA visit can be finalized",
            )

        if poc.effective_start and visit.visit_datetime.date() < poc.effective_start:
            raise HTTPException(status_code=400, detail="CHHA visit date is before CHHA POC effective start")
        if poc.effective_end and visit.visit_datetime.date() > poc.effective_end:
            raise HTTPException(status_code=400, detail="CHHA visit date is after CHHA POC effective end")

    # =========================================================
    # FINALIZE VISIT (authoritative model method)
    # =========================================================
    try:
        visit.finalize(finalized_by=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.flush()

    # Existing task engine (non-POC tasks)
    auto_complete_tasks_for_visit(db=db, visit=visit, completed_by=user.user_id)

    # NOTE:
    # handle_poc_update_for_visit() implements legacy POC_UPDATE task creation logic.
    # POC_UPDATE tasks are now created explicitly within finalize_visit() using
    # visit-acuity–aware, compliance-driven rules:
    #
    #   • CRISIS:
    #       - Every finalized RN visit creates and completes a same-day POC_UPDATE task
    #       - origin = MANUAL
    #       - evidence linked to the finalized visit
    #
    #   • ROUTINE:
    #       - Only supervisory RN visits create the next POC_UPDATE task
    #       - due_date = visit_date + 14 days
    #       - origin = PERIODIC
    #
    # Calling handle_poc_update_for_visit() in addition to this logic causes
    # duplicate POC_UPDATE task insertion and violates the database uniqueness
    # constraint (uq_poc_update_manual_per_visit).
    #
    # Therefore, handle_poc_update_for_visit() is intentionally disabled here
    # to ensure a single, deterministic source of truth for POC_UPDATE task
    # creation and to preserve audit-safe, survey-defensible behavior.
    #
    # handle_poc_update_for_visit(db=db, visit=visit, user_id=user.user_id)

    # =========================================================
    # POC_UPDATE TASK AUTOMATION (COMPLIANCE-CRITICAL)
    # =========================================================
    acuity = getattr(visit, "acuity_state_at_visit", None)
    if not acuity:
        patient = db.query(Patient).filter(Patient.id == visit.patient_id).first()
        acuity = getattr(patient, "acuity_state", None)

    acuity = (acuity or "").upper()

    if vt == "RN":
        # Match unique constraint key for CRISIS (origin MANUAL) exactly.
        existing_manual = (
            db.query(Task)
            .filter(
                Task.task_type == "POC_UPDATE",
                Task.origin == "MANUAL",
                Task.completion_reference_type == "VISIT",
                Task.completion_reference_id == str(visit.id),  # VARCHAR compare
            )
            .first()
        )

        # Also avoid duplicate PERIODIC per same visit.
        existing_periodic = (
            db.query(Task)
            .filter(
                Task.task_type == "POC_UPDATE",
                Task.origin == "PERIODIC",
                Task.completion_reference_type == "VISIT",
                Task.completion_reference_id == str(visit.id),  # VARCHAR compare
            )
            .first()
        )

        # CRISIS: create + complete same day
        if acuity == "CRISIS":
            if not existing_manual:
                task = Task(
                    patient_id=visit.patient_id,
                    benefit_period_id=None,  # attribute to benefit period when available
                    task_type="POC_UPDATE",
                    origin="MANUAL",               # valid enum
                    discipline="RN",               # required
                    regulatory_basis="POC_UPDATE", # required
                    due_date=visit.visit_datetime.date(),
                    status="COMPLETED",            # valid enum
                    completed_at=visit.finalized_at,
                    completion_reference_type="VISIT",
                    completion_reference_id=str(visit.id),  # store as varchar
                    created_by=user.user_id,
                )
                db.add(task)

        # ROUTINE: supervisory RN creates next due +14 days
        elif acuity == "ROUTINE" and getattr(visit, "is_supervisory", False) is True:
            if not existing_periodic:
                task = Task(
                    patient_id=visit.patient_id,
                    benefit_period_id=None,
                    task_type="POC_UPDATE",
                    origin="PERIODIC",             # valid enum
                    discipline="RN",
                    regulatory_basis="POC_UPDATE",
                    due_date=(visit.visit_datetime + timedelta(days=14)).date(),
                    status="PENDING",              # valid enum (OPEN == PENDING)
                    completion_reference_type="VISIT",
                    completion_reference_id=str(visit.id),
                    created_by=user.user_id,
                )
                db.add(task)

    # Audit log
    log_event(
        user_id=user.user_id,
        role=user.role,
        action="FINALIZE_VISIT",
        entity_type="visit",
        entity_id=str(visit.id),
        db=db,
    )

    db.commit()
    db.refresh(visit)

    return {
        "visit_id": str(visit.id),
        "patient_id": str(visit.patient_id),
        "visit_type": visit.visit_type,
        "status": visit.status,
        "finalized_at": visit.finalized_at,
        "finalized_by": str(visit.finalized_by) if visit.finalized_by else None,
        "is_supervisory": bool(getattr(visit, "is_supervisory", False)),
        "chha_poc_id": str(visit.chha_poc_id) if getattr(visit, "chha_poc_id", None) else None,
        "acuity_state_at_visit": getattr(visit, "acuity_state_at_visit", None),
    }


@router.patch(
    "/{visit_id}/supervisory",
    summary="Mark a visit as RN supervisory (must be before finalization)",
)
def mark_visit_supervisory(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    if visit.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Finalized visits cannot be marked supervisory")

    if not hasattr(visit, "is_supervisory"):
        raise HTTPException(status_code=500, detail="Visit model missing is_supervisory column")

    visit.is_supervisory = True
    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="MARK_VISIT_SUPERVISORY",
        entity_type="visit",
        entity_id=str(visit.id),
        db=db,
    )

    db.commit()
    db.refresh(visit)

    return {
        "visit_id": str(visit.id),
        "is_supervisory": bool(getattr(visit, "is_supervisory", False)),
    }