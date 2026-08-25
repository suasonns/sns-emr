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
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.models.patient import Patient
from app.models.patient_order import PatientOrder
from app.models.rnica_assessment import RnicaAssessment
from app.services import rnica_poc_adapter
from app.services.rnica_finalization_service import evaluate_finalization_readiness
from app.services.order_suggestion_service import generate_order_suggestions
from app.services.audit_logger import log_event

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


class LinkExistingPocProblemRequest(BaseModel):
    rule_key: str = Field(..., min_length=1)
    evidence_text: str = Field(..., min_length=1)

    @field_validator("evidence_text")
    @classmethod
    def _evidence_text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evidence_text must not be blank")
        return v


class MergeDuplicateProblemsRequest(BaseModel):
    surviving_rule_key: str = Field(..., min_length=1)
    duplicate_rule_keys: list[str] = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be blank")
        return v


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


@router.post("/{assessment_id}/poc/merge")
def merge_duplicate_poc_problems(
    assessment_id: str,
    payload: MergeDuplicateProblemsRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """SECTION 11 — Master Plan of Care Review 'Merge Duplicate Problems'.

    Cross-section control: unlike Link Existing (documented per-section),
    merging operates across the whole problem list, so this route is not
    nested under a `section_key`. Folds each duplicate's evidence and
    description into the surviving problem, marks the duplicate(s)
    SUPERSEDED with a `merged_into_rule_key` pointer, and never deletes
    anything. This is a genuine POC content mutation, so it is lock-gated
    like every other write path.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.merge_duplicate_problems(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            surviving_rule_key=payload.surviving_rule_key,
            duplicate_rule_keys=payload.duplicate_rule_keys,
            merge_reason=payload.reason,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"assessmentId": str(record.id), **_jsonable(result)}


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


@router.post("/{assessment_id}/poc/{section_key}/link-existing")
def link_existing_section_poc_problem(
    assessment_id: str,
    section_key: str,
    payload: LinkExistingPocProblemRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """SECTION 11.C — Master Plan of Care Review 'Link Existing Problem'.

    Attaches additional source evidence (documented in `section_key`) to
    an already-existing Plan of Care problem identified by `rule_key`.
    Never creates a new problem row, never changes the problem's origin
    section, and never duplicates identical evidence.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    _reject_if_locked(record)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = rnica_poc_adapter.link_existing_problem(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            rnica_assessment_id=record.id,
            section_key=section_key,
            rule_key=payload.rule_key,
            evidence_text=payload.evidence_text,
        )
    except rnica_poc_adapter.RnicaPocAdapterError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

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


class ApplySuggestedOrdersRequest(BaseModel):
    suggestion_keys: list[str] = Field(..., min_length=1)


@router.get("/{assessment_id}/suggested-orders")
def view_suggested_orders(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Suggest-only, non-persistent DME/Supply/Treatment/Diet order drafts
    derived from the same respiratory/skin/nutrition/fall-risk findings the
    POC-generation engine already detects on this assessment. Nothing here
    is ever written to `patient_orders` until a clinician explicitly calls
    POST .../suggested-orders/apply below -- read-only, safe to call at any
    time including after the assessment is locked.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    note = rnica_poc_adapter._RnicaNoteAdapter(record)
    result = generate_order_suggestions(note)

    # Filter out any suggestion whose order_text already exists as an active
    # (non-discontinued) order for this patient, so the clinician isn't
    # re-prompted to add something that's already on the chart.
    existing_texts = {
        (o.order_text or "").strip().lower()
        for o in db.query(PatientOrder)
        .filter(
            PatientOrder.patient_id == record.patient_id,
            PatientOrder.tenant_id == tenant_id,
            PatientOrder.status == "active",
        )
        .all()
    }
    result["suggestions"] = [
        s for s in result["suggestions"] if s["order_text"].strip().lower() not in existing_texts
    ]

    return {"assessmentId": str(record.id), **result}


@router.post("/{assessment_id}/suggested-orders/apply", status_code=status.HTTP_201_CREATED)
def apply_suggested_orders(
    assessment_id: str,
    payload: ApplySuggestedOrdersRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Explicit clinician "Add to Orders" action. Creates real
    `PatientOrder` rows -- the same table and same Tx/Med/DME views used by
    every other order -- for the chosen suggestion_key(s) only. Nothing is
    ever applied automatically; this endpoint is the only path from a
    suggestion to a persisted order.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    note = rnica_poc_adapter._RnicaNoteAdapter(record)
    generated = generate_order_suggestions(note)
    by_key = {s["suggestion_key"]: s for s in generated["suggestions"]}

    user_id = _user_id(current_user)
    created: list[dict] = []
    not_found: list[str] = []
    for key in payload.suggestion_keys:
        suggestion = by_key.get(key)
        if not suggestion:
            not_found.append(key)
            continue
        order = PatientOrder(
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            order_type=suggestion["order_type"],
            sub_type=suggestion["sub_type"],
            order_text=suggestion["order_text"],
            indication=suggestion["indication"],
            source_kind="RULE_SUGGESTED",
            source_rnica_assessment_id=record.id,
            created_by=user_id,
        )
        db.add(order)
        db.flush()
        created.append(
            {
                "id": str(order.id),
                "order_type": order.order_type,
                "sub_type": order.sub_type,
                "order_text": order.order_text,
                "indication": order.indication,
                "source_kind": order.source_kind,
            }
        )
        log_event(
            user_id=user_id,
            role=getattr(current_user, "role", None),
            action="ADD_PATIENT_ORDER_FROM_RNICA_SUGGESTION",
            entity_type="patient_order",
            entity_id=str(order.id),
            metadata={
                "patient_id": str(record.patient_id),
                "rnica_assessment_id": str(record.id),
                "suggestion_key": key,
                "rule_key": suggestion["rule_key"],
            },
        )

    db.commit()
    return {
        "assessmentId": str(record.id),
        "created": created,
        "notFound": not_found,
    }


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
