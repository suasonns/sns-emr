# app/api/routes/rnica_poc.py
"""RN ICA -> Plan of Care control routes.

Exposes "Add to POC / View POC / Update POC / Resolve POC" for RN ICA
Body System Assessment subcards. These routes are a thin HTTP layer over
`app.services.rnica_poc_adapter`, which is the only code that touches the
authoritative Plan of Care document model
(`app.models.plan_of_care`, `app.models.plan_of_care_version`,
`app.models.poc`). No separate/duplicate POC storage is introduced here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Security, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.services import rnica_poc_adapter
from app.services.rnica_finalization_service import evaluate_finalization_readiness

router = APIRouter(prefix="/visits/rnica", tags=["rnica-poc"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AddPocProblemRequest(BaseModel):
    problem_label: str = Field(..., min_length=1)
    evidence_text: str = Field(..., min_length=1)
    goal_text: str | None = None
    intervention_text: str | None = None
    discipline: str = "RN"


class UpdatePocProblemRequest(BaseModel):
    label: str | None = None
    description_addendum: str | None = None
    severity: str | None = None


def _load_assessment_and_authorize(db: Session, assessment_id: str, current_user: CurrentUser) -> RnicaAssessment:
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None

    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_uuid).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")

    get_authorized_patient(db, record.patient_id, current_user)
    return record


def _tenant_id_for(db: Session, record: RnicaAssessment):
    if record.tenant_id:
        return record.tenant_id
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    return getattr(patient, "tenant_id", None)


def _user_id(current_user: CurrentUser):
    raw = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
    return raw


def _reject_if_locked(record: RnicaAssessment) -> None:
    """Mirror the immutability guard in app/api/visits.py::update_rnica_assessment.

    A signed/locked RN ICA assessment must not be mutated through any path,
    including Plan of Care problem management reached from its subcards.
    """
    if record.locked:
        raise HTTPException(
            status_code=423,
            detail=(
                "This RN ICA assessment is locked and cannot be edited. "
                "Use the correction/amendment workflow (POST /rnica/{assessment_id}/correction-request) "
                "to request a traceable addendum instead of modifying signed content."
            ),
        )


@router.get("/{assessment_id}/poc")
def view_all_poc(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """SECTION 11 — Master Plan of Care Review. Returns every RN-ICA-sourced
    problem (any originating section) for the current active Plan of Care
    version. Read-only synchronization view; does not create problems.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    problems = rnica_poc_adapter.list_all_problems(
        db,
        tenant_id=tenant_id,
        patient_id=record.patient_id,
    )
    return {"assessmentId": str(record.id), "problems": problems}


@router.get("/{assessment_id}/finalization-readiness")
def get_finalization_readiness(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """SECTION 12 — Final Review Dashboard data source. Single source of
    truth shared with `lock_rnica_assessment` (app/api/visits.py) so the
    UI's Lock button and the server's lock gate can never disagree.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)

    poc_problems: list = []
    if tenant_id is not None:
        poc_problems = rnica_poc_adapter.list_all_problems(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
        )

    readiness = evaluate_finalization_readiness(record.form_data or {}, poc_problems)
    return {
        "assessmentId": str(record.id),
        "locked": record.locked,
        **readiness,
    }


@router.get("/{assessment_id}/poc/{section_key}")
def view_section_poc(
    assessment_id: str,
    section_key: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    problems = rnica_poc_adapter.list_section_problems(
        db,
        tenant_id=tenant_id,
        patient_id=record.patient_id,
        section_key=section_key,
    )
    return {"assessmentId": str(record.id), "sectionKey": section_key, "problems": problems}


@router.post("/{assessment_id}/poc/{section_key}", status_code=status.HTTP_201_CREATED)
def add_section_poc_problem(
    assessment_id: str,
    section_key: str,
    payload: AddPocProblemRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.add_manual_problem(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            rnica_assessment_id=record.id,
            section_key=section_key,
            problem_label=payload.problem_label,
            evidence_text=payload.evidence_text,
            goal_text=payload.goal_text,
            intervention_text=payload.intervention_text,
            discipline=payload.discipline,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"assessmentId": str(record.id), "sectionKey": section_key, **_jsonable(result)}


@router.put("/{assessment_id}/poc/{section_key}/{rule_key}")
def update_section_poc_problem(
    assessment_id: str,
    section_key: str,
    rule_key: str,
    payload: UpdatePocProblemRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.update_problem(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            section_key=section_key,
            rule_key=rule_key,
            label=payload.label,
            description_addendum=payload.description_addendum,
            severity=payload.severity,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"assessmentId": str(record.id), "sectionKey": section_key, **_jsonable(result)}


@router.post("/{assessment_id}/poc/{section_key}/{rule_key}/resolve")
def resolve_section_poc_problem(
    assessment_id: str,
    section_key: str,
    rule_key: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.resolve_problem(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            section_key=section_key,
            rule_key=rule_key,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"assessmentId": str(record.id), "sectionKey": section_key, **_jsonable(result)}


@router.post("/{assessment_id}/poc/{section_key}/{rule_key}/deactivate")
def deactivate_section_poc_problem(
    assessment_id: str,
    section_key: str,
    rule_key: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.deactivate_problem(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            section_key=section_key,
            rule_key=rule_key,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"assessmentId": str(record.id), "sectionKey": section_key, **_jsonable(result)}


@router.get("/{assessment_id}/poc/{section_key}/{rule_key}/history")
def get_section_poc_problem_history(
    assessment_id: str,
    section_key: str,
    rule_key: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """SECTION 11.B — Master Plan of Care Review 'View History'.

    Read-only governance view (Created By/Date, Last Updated By/Date,
    Status Changes, Resolve Events, Deactivate Events) reconstructed from
    existing `plan_of_care_versions` / `poc_problems` metadata — no new
    audit storage. See `rnica_poc_adapter.get_problem_history`.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        history = rnica_poc_adapter.get_problem_history(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            rule_key=rule_key,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"assessmentId": str(record.id), "sectionKey": section_key, **history}


def _jsonable(result: dict) -> dict:
    """UUID values in adapter results need to be stringified for the JSON response."""
    out = {}
    for k, v in result.items():
        if isinstance(v, uuid.UUID):
            out[k] = str(v)
        elif isinstance(v, list):
            out[k] = [str(item) if isinstance(item, uuid.UUID) else item for item in v]
        else:
            out[k] = v
    return out
