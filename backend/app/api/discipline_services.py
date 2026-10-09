from __future__ import annotations

"""
Interdisciplinary continuity API (MSW / CHAPLAIN / VOLUNTEER ONLY).

Owner-authorized scope: MSW, CHAPLAIN, VOLUNTEER discipline continuity.
RN/MD/F2F/Hospice-Aide refusal pathways are untouched and continue to use
app.api.refusals (or equivalent) backed by app.services.refusal_engine.

All state mutation is delegated to
app.services.discipline_service_engine -- this router never assigns
PatientDisciplineService.current_state directly, never creates a visit
record, and never mutates POCProblem/POCGoal/POCIntervention.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.admission import Admission
from app.models.discipline_service import PatientDisciplineService, PatientDisciplineServiceEvent
from app.models.idg_recommendation import IDGRecommendation
from app.models.idg_review import IDGReview
from app.services import discipline_service_engine as engine
from app.services.audit_events import audit_event

router = APIRouter(prefix="/discipline-services", tags=["discipline-services"])

CONTINUITY_VIEW_ROLES = [
    "SW", "CHAPLAIN", "RN", "LVN", "CASE_MANAGER", "CLINICAL_SUPERVISOR",
    "MEDICAL_DIRECTOR", "VOLUNTEER_COORDINATOR", "Surveyor",
]
CONTINUITY_EDIT_ROLES = [
    "SW", "CHAPLAIN", "RN", "LVN", "CASE_MANAGER", "CLINICAL_SUPERVISOR",
    "MEDICAL_DIRECTOR", "VOLUNTEER_COORDINATOR",
]


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, engine.PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (engine.InvalidTransitionError, engine.ConcurrencyError, engine.IdempotencyConflictError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, engine.DisciplineServiceError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


def _admission_status(admission_id, current_admission: Optional[Admission]) -> str:
    """Shared CURRENT / HISTORICAL / LEGACY_ADMISSION_UNASSIGNED
    classifier -- the single server-side source of truth reused across
    services, IDG reviews, and recommendations so the frontend never
    infers this label client-side."""
    if admission_id is None:
        return "LEGACY_ADMISSION_UNASSIGNED"
    if current_admission is not None and admission_id == current_admission.id:
        return "CURRENT"
    return "HISTORICAL"


def _resolve_current_admission_or_none(db: Session, *, tenant_id, patient_id) -> Optional[Admission]:
    """Read-path variant: ambiguous-active-admission data must not block
    an entire historical/listing read (that would make history itself
    unreadable). When ambiguous or absent, no row is labeled CURRENT --
    safer than guessing. Mutations remain exclusively gated by
    _require_current_admission, never by this function."""
    try:
        return engine.resolve_current_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    except engine.DisciplineServiceError:
        return None



    """Ordinary CURRENT clinical mutation mode (not historical read, not
    authorized correction): requires exactly one active admission and
    raises -- via engine.DisciplineServiceError, translated to 400 by
    _error() -- when none exists or when more than one exists
    (ambiguous). Never falls back to an admission-unassigned/legacy row;
    that fallback was the exact unsafe behavior this function replaces."""
    try:
        admission = engine.resolve_current_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    if admission is None:
        raise _error(
            engine.DisciplineServiceError(
                "No active hospice admission exists for this patient; current-admission continuity actions "
                "require an active admission and are rejected"
            )
        )
    return admission


def _load_service(db: Session, *, tenant_id, patient_id, discipline: str) -> PatientDisciplineService:
    """Current-admission mutation/status lookup (CURRENT CLINICAL
    MUTATION MODE). Requires an active, unambiguous admission via
    _require_current_admission() and scopes the lookup to it exactly --
    it no longer falls back to admission_id IS NULL. A legacy/admission-
    unassigned or other-admission service row is never silently
    substituted; if no PatientDisciplineService exists for the current
    admission, this is a 404 (the discipline has not yet been identified
    in this admission -- call .../identify first), not a reuse of
    history. Historical records remain reachable only through the
    patient-wide list_services endpoint (unfiltered, read-only) or a
    future dedicated historical-read endpoint -- never through this
    function, which is the single chokepoint used by every mutation
    route plus the current-status/event-history read routes."""
    try:
        canonical = engine.normalize_continuity_discipline(discipline)
    except engine.DisciplineServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    admission = _require_current_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    service = (
        db.query(PatientDisciplineService)
        .execution_options(skip_tenant_filter=True)
        .filter(
            PatientDisciplineService.tenant_id == tenant_id,
            PatientDisciplineService.patient_id == patient_id,
            PatientDisciplineService.discipline == canonical,
            PatientDisciplineService.admission_id == admission.id,
        )
        .one_or_none()
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discipline service record not found for the current admission",
        )
    return service


def _audit(db: Session, user: CurrentUser, action: str, service: PatientDisciplineService, event: PatientDisciplineServiceEvent):
    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action=action,
        entity_type="PATIENT_DISCIPLINE_SERVICE",
        entity_id=str(service.id),
        meta={
            "patient_id": str(service.patient_id),
            "discipline": service.discipline,
            "from_state": event.from_state,
            "to_state": event.to_state,
            "event_id": str(event.id),
        },
    )


# =========================================================
# SCHEMAS
# =========================================================

class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    admission_id: Optional[uuid.UUID] = None
    admission_status: str = "LEGACY_ADMISSION_UNASSIGNED"
    discipline: str
    current_state: str
    row_version: int
    last_decision_maker_name: Optional[str] = None
    last_decision_maker_relationship: Optional[str] = None
    last_information_source: Optional[str] = None
    last_offered_at: Optional[datetime] = None
    last_decision_at: Optional[datetime] = None
    last_refused_at: Optional[datetime] = None
    reoffer_due_at: Optional[datetime] = None
    rn_monitoring_assigned_user_id: Optional[uuid.UUID] = None
    idg_review_required: bool
    idg_review_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    discipline_service_id: uuid.UUID
    event_type: str
    from_state: Optional[str] = None
    to_state: str
    recorded_by_user_id: Optional[uuid.UUID] = None
    recorded_by_role: Optional[str] = None
    information_source: Optional[str] = None
    decision_maker_name: Optional[str] = None
    decision_maker_relationship: Optional[str] = None
    reason: Optional[str] = None
    effective_at: datetime
    related_task_id: Optional[uuid.UUID] = None
    related_idg_review_id: Optional[uuid.UUID] = None
    related_patient_issue_id: Optional[uuid.UUID] = None
    corrects_event_id: Optional[uuid.UUID] = None
    created_at: datetime


class _BaseAction(BaseModel):
    expected_row_version: Optional[int] = None
    idempotency_key: Optional[str] = None


class OfferRequest(_BaseAction):
    information_source: Optional[str] = None
    reason: Optional[str] = None


class PendingDecisionRequest(_BaseAction):
    pass


class AcceptRequest(_BaseAction):
    decision_maker_name: str = Field(min_length=1)
    decision_maker_relationship: str = Field(min_length=1)
    information_source: Optional[str] = None

    @field_validator("decision_maker_name", "decision_maker_relationship")
    @classmethod
    def _required(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("value is required")
        return value


class RefuseRequest(_BaseAction):
    reason: str = Field(min_length=1)
    decision_maker_name: str = Field(min_length=1)
    decision_maker_relationship: str = Field(min_length=1)
    information_source: Optional[str] = None
    assign_rn_monitoring_user_id: Optional[uuid.UUID] = None
    requires_idg_review: bool = False
    related_patient_issue_id: Optional[uuid.UUID] = None
    create_reoffer_task: bool = True
    reoffer_due_date: Optional[date] = None


class SimpleActionRequest(_BaseAction):
    reason: Optional[str] = None


class WithdrawRefusalRequest(_BaseAction):
    reason: str = Field(min_length=1)
    decision_maker_name: str = Field(min_length=1)
    decision_maker_relationship: str = Field(min_length=1)


class ScheduleReofferRequest(_BaseAction):
    due_date: Optional[date] = None
    trigger_description: Optional[str] = None


class ReofferRequest(_BaseAction):
    information_source: Optional[str] = None


class CorrectionRequest(BaseModel):
    corrects_event_id: uuid.UUID
    reason: str = Field(min_length=1)
    decision_maker_name: Optional[str] = None
    decision_maker_relationship: Optional[str] = None
    information_source: Optional[str] = None
    expected_row_version: Optional[int] = None


class RnMonitoringAssignRequest(BaseModel):
    rn_user_id: uuid.UUID
    reason: Optional[str] = None
    expected_row_version: Optional[int] = None


class RnMonitoringEndRequest(BaseModel):
    reason: str = Field(min_length=1)
    expected_row_version: Optional[int] = None


class IdgReviewCompleteRequest(BaseModel):
    idg_review_id: uuid.UUID
    notes: Optional[str] = None
    expected_row_version: Optional[int] = None


class IdgReviewSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    admission_id: Optional[uuid.UUID] = None
    admission_status: str = "LEGACY_ADMISSION_UNASSIGNED"
    review_date: Optional[datetime] = None
    is_finalized: bool
    summary: Optional[str] = None


class IdgRecommendationCreate(BaseModel):
    patient_id: uuid.UUID
    idg_review_id: uuid.UUID
    discipline: str
    recommendation_type: str
    recommendation_text: str = Field(min_length=1)
    discipline_service_id: Optional[uuid.UUID] = None
    related_patient_issue_id: Optional[uuid.UUID] = None
    requires_poc_change: bool = False
    linked_poc_problem_id: Optional[uuid.UUID] = None
    linked_poc_goal_id: Optional[uuid.UUID] = None
    linked_poc_intervention_id: Optional[uuid.UUID] = None


class IdgRecommendationReview(BaseModel):
    review_notes: Optional[str] = None


class IdgRecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    admission_id: Optional[uuid.UUID] = None
    admission_status: str = "LEGACY_ADMISSION_UNASSIGNED"
    idg_review_id: uuid.UUID
    discipline_service_id: Optional[uuid.UUID] = None
    discipline: Optional[str] = None
    recommendation_type: str
    recommendation_text: str
    no_direct_visit: bool
    status: str
    related_patient_issue_id: Optional[uuid.UUID] = None
    requires_poc_change: bool = False
    linked_poc_problem_id: Optional[uuid.UUID] = None
    linked_poc_goal_id: Optional[uuid.UUID] = None
    linked_poc_intervention_id: Optional[uuid.UUID] = None
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    reviewed_by_user_id: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class AdmissionHistoryGroup(BaseModel):
    """One Admission's continuity data, grouped (section 12/13: never
    merged into one unlabeled timeline). admission_id is None only for
    the single reserved LEGACY_ADMISSION_UNASSIGNED group."""

    admission_id: Optional[uuid.UUID] = None
    admission_status: str
    admission_start: Optional[datetime] = None
    admission_end: Optional[datetime] = None
    services: list[ServiceRead] = Field(default_factory=list)
    idg_reviews: list[IdgReviewSummary] = Field(default_factory=list)
    recommendations: list[IdgRecommendationRead] = Field(default_factory=list)


class PatientContinuityHistory(BaseModel):
    current_admission_id: Optional[uuid.UUID] = None
    admissions: list[AdmissionHistoryGroup] = Field(default_factory=list)
    legacy: AdmissionHistoryGroup


# =========================================================
# SERVICE LOOKUP / LISTING
# =========================================================

@router.get("/patient/{patient_id}", response_model=list[ServiceRead])
def list_services(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    """Patient-wide, admission-agnostic read. Unlike get_service (which
    hard-requires the current admission), this is the only route that
    can surface a discharged/readmitted patient's historical continuity
    rows -- every row is labeled via _admission_status so the frontend
    never has to infer current-vs-historical itself."""
    patient = get_authorized_patient(db, patient_id, user)
    current_admission = _resolve_current_admission_or_none(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    services = (
        db.query(PatientDisciplineService)
        .execution_options(skip_tenant_filter=True)
        .filter(
            PatientDisciplineService.tenant_id == patient.tenant_id,
            PatientDisciplineService.patient_id == patient.id,
        )
        .order_by(PatientDisciplineService.discipline)
        .all()
    )
    results = []
    for svc in services:
        item = ServiceRead.model_validate(svc)
        item.admission_status = _admission_status(svc.admission_id, current_admission)
        results.append(item)
    return results


@router.get("/patient/{patient_id}/history", response_model=PatientContinuityHistory)
def get_patient_continuity_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    """Patient-wide continuity history GROUPED BY ADMISSION (read only).
    Never merges admissions into one unlabeled timeline and never
    computes "current" by taking the newest event across admissions --
    current status is still exclusively derived from
    resolve_current_admission. CURRENT/HISTORICAL groups are keyed by
    actual Admission id; admission-unassigned (legacy) rows are
    collected into a single separate LEGACY group."""
    patient = get_authorized_patient(db, patient_id, user)
    current_admission = _resolve_current_admission_or_none(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    current_admission_id = current_admission.id if current_admission else None

    services = (
        db.query(PatientDisciplineService)
        .execution_options(skip_tenant_filter=True)
        .filter(PatientDisciplineService.tenant_id == patient.tenant_id, PatientDisciplineService.patient_id == patient.id)
        .all()
    )
    reviews = (
        db.query(IDGReview)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGReview.tenant_id == patient.tenant_id, IDGReview.patient_id == patient.id)
        .all()
    )
    recommendations = (
        db.query(IDGRecommendation)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGRecommendation.tenant_id == patient.tenant_id, IDGRecommendation.patient_id == patient.id)
        .all()
    )

    admission_ids: set = set()
    for row in (*services, *reviews, *recommendations):
        if row.admission_id is not None:
            admission_ids.add(row.admission_id)
    if current_admission_id is not None:
        admission_ids.add(current_admission_id)

    admissions_by_id = {}
    if admission_ids:
        for a in (
            db.query(Admission)
            .execution_options(skip_tenant_filter=True)
            .filter(Admission.id.in_(admission_ids), Admission.tenant_id == patient.tenant_id)
            .all()
        ):
            admissions_by_id[a.id] = a

    groups: dict = {}
    for admission_id in admission_ids:
        admission = admissions_by_id.get(admission_id)
        groups[admission_id] = AdmissionHistoryGroup(
            admission_id=admission_id,
            admission_status="CURRENT" if admission_id == current_admission_id else "HISTORICAL",
            admission_start=getattr(admission, "soc_date", None) or getattr(admission, "admission_date", None),
            admission_end=getattr(admission, "discharged_at", None),
            services=[], idg_reviews=[], recommendations=[],
        )
    legacy_group = AdmissionHistoryGroup(
        admission_id=None, admission_status="LEGACY_ADMISSION_UNASSIGNED",
        admission_start=None, admission_end=None, services=[], idg_reviews=[], recommendations=[],
    )

    for svc in services:
        item = ServiceRead.model_validate(svc)
        item.admission_status = _admission_status(svc.admission_id, current_admission)
        (groups[svc.admission_id] if svc.admission_id in groups else legacy_group).services.append(item)
    for rv in reviews:
        item = IdgReviewSummary.model_validate(rv)
        item.admission_status = _admission_status(rv.admission_id, current_admission)
        (groups[rv.admission_id] if rv.admission_id in groups else legacy_group).idg_reviews.append(item)
    for rec in recommendations:
        item = IdgRecommendationRead.model_validate(rec)
        item.admission_status = _admission_status(rec.admission_id, current_admission)
        (groups[rec.admission_id] if rec.admission_id in groups else legacy_group).recommendations.append(item)

    ordered_groups = sorted(groups.values(), key=lambda g: (g.admission_start or datetime.min.replace(tzinfo=None)), reverse=True)
    return PatientContinuityHistory(current_admission_id=current_admission_id, admissions=ordered_groups, legacy=legacy_group)


@router.get("/patient/{patient_id}/admission/{admission_id}", response_model=AdmissionHistoryGroup)
def get_admission_continuity_history(
    patient_id: uuid.UUID,
    admission_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    """Explicit HISTORICAL READ CONTEXT for one named admission -- always
    read only (no mutation route exists at this path). Validates tenant
    and patient ownership of the admission; never makes a discharged
    admission "current" merely because it was selected for viewing."""
    patient = get_authorized_patient(db, patient_id, user)
    admission = (
        db.query(Admission)
        .execution_options(skip_tenant_filter=True)
        .filter(Admission.id == admission_id, Admission.tenant_id == patient.tenant_id, Admission.patient_id == patient.id)
        .one_or_none()
    )
    if admission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found for this patient")
    current_admission = _resolve_current_admission_or_none(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    admission_status = "CURRENT" if current_admission is not None and admission.id == current_admission.id else "HISTORICAL"

    services, reviews, recs = [], [], []
    for svc in (
        db.query(PatientDisciplineService)
        .execution_options(skip_tenant_filter=True)
        .filter(PatientDisciplineService.tenant_id == patient.tenant_id, PatientDisciplineService.patient_id == patient.id, PatientDisciplineService.admission_id == admission.id)
        .all()
    ):
        item = ServiceRead.model_validate(svc)
        item.admission_status = admission_status
        services.append(item)
    for rv in (
        db.query(IDGReview)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGReview.tenant_id == patient.tenant_id, IDGReview.patient_id == patient.id, IDGReview.admission_id == admission.id)
        .all()
    ):
        item = IdgReviewSummary.model_validate(rv)
        item.admission_status = admission_status
        reviews.append(item)
    for rec in (
        db.query(IDGRecommendation)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGRecommendation.tenant_id == patient.tenant_id, IDGRecommendation.patient_id == patient.id, IDGRecommendation.admission_id == admission.id)
        .all()
    ):
        item = IdgRecommendationRead.model_validate(rec)
        item.admission_status = admission_status
        recs.append(item)

    return AdmissionHistoryGroup(
        admission_id=admission.id,
        admission_status=admission_status,
        admission_start=getattr(admission, "soc_date", None) or getattr(admission, "admission_date", None),
        admission_end=getattr(admission, "discharged_at", None),
        services=services, idg_reviews=reviews, recommendations=recs,
    )


@router.get("/patient/{patient_id}/{discipline}", response_model=ServiceRead)
def get_service(
    patient_id: uuid.UUID,
    discipline: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    item = ServiceRead.model_validate(service)
    # _load_service already enforces current-admission-or-unassigned scoping,
    # so every row reachable here is, by construction, part of the current
    # episode of care.
    item.admission_status = "CURRENT"
    return item


@router.get("/patient/{patient_id}/{discipline}/events", response_model=list[EventRead])
def list_events(
    patient_id: uuid.UUID,
    discipline: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    return (
        db.query(PatientDisciplineServiceEvent)
        .execution_options(skip_tenant_filter=True)
        .filter(PatientDisciplineServiceEvent.discipline_service_id == service.id)
        .order_by(PatientDisciplineServiceEvent.created_at.asc())
        .all()
    )


@router.post("/patient/{patient_id}/{discipline}/identify", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def identify_discipline(
    patient_id: uuid.UUID,
    discipline: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    admission = _require_current_admission(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    try:
        service = engine.get_or_create_service(
            db,
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            discipline=discipline,
            admission_id=admission.id,
            actor_user_id=user.user_id,
            actor_role=user.role,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    db.commit()
    db.refresh(service)
    return service


# =========================================================
# STATE TRANSITIONS
# =========================================================

@router.post("/patient/{patient_id}/{discipline}/offer", response_model=ServiceRead)
def offer(
    patient_id: uuid.UUID,
    discipline: str,
    payload: OfferRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.offer_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            information_source=payload.information_source, reason=payload.reason,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_OFFERED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/pending-decision", response_model=ServiceRead)
def pending_decision(
    patient_id: uuid.UUID,
    discipline: str,
    payload: PendingDecisionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.record_pending_decision(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_DECISION_PENDING", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/accept", response_model=ServiceRead)
def accept(
    patient_id: uuid.UUID,
    discipline: str,
    payload: AcceptRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.accept_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            decision_maker_name=payload.decision_maker_name,
            decision_maker_relationship=payload.decision_maker_relationship,
            information_source=payload.information_source,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_ACCEPTED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/refuse", response_model=ServiceRead)
def refuse(
    patient_id: uuid.UUID,
    discipline: str,
    payload: RefuseRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event, task = engine.refuse_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            decision_maker_name=payload.decision_maker_name,
            decision_maker_relationship=payload.decision_maker_relationship,
            information_source=payload.information_source,
            assign_rn_monitoring_user_id=payload.assign_rn_monitoring_user_id,
            requires_idg_review=payload.requires_idg_review,
            related_patient_issue_id=payload.related_patient_issue_id,
            create_reoffer_task=payload.create_reoffer_task,
            reoffer_due_date=payload.reoffer_due_date,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_REFUSED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/activate", response_model=ServiceRead)
def activate(
    patient_id: uuid.UUID,
    discipline: str,
    payload: _BaseAction,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.activate_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_ACTIVATED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/pause", response_model=ServiceRead)
def pause(
    patient_id: uuid.UUID,
    discipline: str,
    payload: SimpleActionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.pause_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_PAUSED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/resume", response_model=ServiceRead)
def resume(
    patient_id: uuid.UUID,
    discipline: str,
    payload: _BaseAction,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.resume_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_RESUMED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/end", response_model=ServiceRead)
def end(
    patient_id: uuid.UUID,
    discipline: str,
    payload: SimpleActionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    if not payload.reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reason is required to end a service")
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.end_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_ENDED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/withdraw-refusal", response_model=ServiceRead)
def withdraw_refusal(
    patient_id: uuid.UUID,
    discipline: str,
    payload: WithdrawRefusalRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.withdraw_refusal(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            decision_maker_name=payload.decision_maker_name,
            decision_maker_relationship=payload.decision_maker_relationship,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_REFUSAL_WITHDRAWN", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/schedule-reoffer", response_model=ServiceRead)
def schedule_reoffer(
    patient_id: uuid.UUID,
    discipline: str,
    payload: ScheduleReofferRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.schedule_reoffer(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            due_date=payload.due_date, trigger_description=payload.trigger_description,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_REOFFER_SCHEDULED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/reoffer", response_model=ServiceRead)
def reoffer(
    patient_id: uuid.UUID,
    discipline: str,
    payload: ReofferRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.reoffer_service(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            information_source=payload.information_source,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_REOFFERED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/unable-to-contact", response_model=ServiceRead)
def unable_to_contact(
    patient_id: uuid.UUID,
    discipline: str,
    payload: SimpleActionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.record_unable_to_contact(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_UNABLE_TO_CONTACT", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/decision-maker-unavailable", response_model=ServiceRead)
def decision_maker_unavailable(
    patient_id: uuid.UUID,
    discipline: str,
    payload: SimpleActionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.record_decision_maker_unavailable(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            reason=payload.reason,
            expected_row_version=payload.expected_row_version, idempotency_key=payload.idempotency_key,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_DECISION_MAKER_UNAVAILABLE", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/correction", response_model=EventRead)
def correction(
    patient_id: uuid.UUID,
    discipline: str,
    payload: CorrectionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.record_correction(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            corrects_event_id=payload.corrects_event_id, reason=payload.reason,
            decision_maker_name=payload.decision_maker_name,
            decision_maker_relationship=payload.decision_maker_relationship,
            information_source=payload.information_source,
            expected_row_version=payload.expected_row_version,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_CORRECTION_RECORDED", service, event)
    db.commit()
    db.refresh(event)
    return event


# =========================================================
# RN MONITORING
# =========================================================

@router.post("/patient/{patient_id}/{discipline}/rn-monitoring/assign", response_model=ServiceRead)
def rn_monitoring_assign(
    patient_id: uuid.UUID,
    discipline: str,
    payload: RnMonitoringAssignRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.assign_rn_monitoring(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            rn_user_id=payload.rn_user_id, reason=payload.reason,
            expected_row_version=payload.expected_row_version,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_RN_MONITORING_ASSIGNED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.post("/patient/{patient_id}/{discipline}/rn-monitoring/end", response_model=ServiceRead)
def rn_monitoring_end(
    patient_id: uuid.UUID,
    discipline: str,
    payload: RnMonitoringEndRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.end_rn_monitoring(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role, reason=payload.reason,
            expected_row_version=payload.expected_row_version,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_RN_MONITORING_ENDED", service, event)
    db.commit()
    db.refresh(service)
    return service


# =========================================================
# IDG REVIEW LIFECYCLE
# =========================================================

@router.post("/patient/{patient_id}/{discipline}/idg-review/complete", response_model=ServiceRead)
def idg_review_complete(
    patient_id: uuid.UUID,
    discipline: str,
    payload: IdgReviewCompleteRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    """M1 fix: closes the loop left open by request_idg_review --
    idg_review_required was previously a one-way latch with no path to
    ever clear it back to False."""
    patient = get_authorized_patient(db, patient_id, user)
    service = _load_service(db, tenant_id=patient.tenant_id, patient_id=patient.id, discipline=discipline)
    try:
        service, event = engine.complete_idg_review(
            db, service=service, actor_user_id=user.user_id, actor_role=user.role,
            idg_review_id=payload.idg_review_id, notes=payload.notes,
            expected_row_version=payload.expected_row_version,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    _audit(db, user, "DISCIPLINE_SERVICE_IDG_REVIEW_COMPLETED", service, event)
    db.commit()
    db.refresh(service)
    return service


@router.get("/idg-reviews/patient/{patient_id}", response_model=list[IdgReviewSummary])
def list_patient_idg_reviews(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    """L2 fix: lets the UI offer a patient-scoped picker of this patient's
    own IDG reviews instead of a free-text pasted UUID, which was the
    error-prone entry point behind the H1 cross-patient linkage defect.

    Readmission episode-scoping: every row is annotated with
    admission_status (CURRENT / HISTORICAL / LEGACY_ADMISSION_UNASSIGNED)
    computed server-side -- never inferred client-side -- so the UI can
    restrict the "current recommendation" picker to CURRENT rows while
    still surfacing the full patient history for read-only timeline use.
    Legacy reviews (admission_id is null) are never labeled CURRENT."""
    patient = get_authorized_patient(db, patient_id, user)
    # Read/listing endpoint: ambiguous active-admission data must not block
    # the whole historical listing (that would make history itself
    # unreadable). Instead, when ambiguous, no row is labeled CURRENT --
    # safer than guessing, and the ambiguity remains blocked at every
    # mutation route via _require_current_admission.
    admission = _resolve_current_admission_or_none(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    reviews = (
        db.query(IDGReview)
        .execution_options(skip_tenant_filter=True)
        .filter(
            IDGReview.tenant_id == patient.tenant_id,
            IDGReview.patient_id == patient.id,
        )
        .order_by(IDGReview.review_date.desc().nullslast(), IDGReview.created_at.desc())
        .all()
    )
    results = []
    for review in reviews:
        item = IdgReviewSummary.model_validate(review)
        item.admission_status = _admission_status(review.admission_id, admission)
        results.append(item)
    return results


# =========================================================
# IDG RECOMMENDATIONS (no visit / no billable encounter)
# =========================================================

@router.post("/idg-recommendations", response_model=IdgRecommendationRead, status_code=status.HTTP_201_CREATED)
def create_idg_recommendation(
    payload: IdgRecommendationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)
    admission = _require_current_admission(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    service = None
    if payload.discipline_service_id:
        service = (
            db.query(PatientDisciplineService)
            .execution_options(skip_tenant_filter=True)
            .filter(
                PatientDisciplineService.id == payload.discipline_service_id,
                PatientDisciplineService.tenant_id == patient.tenant_id,
                PatientDisciplineService.patient_id == patient.id,
            )
            .one_or_none()
        )
        if service is None:
            raise _error(engine.DisciplineServiceError("discipline_service_id not found for this patient/tenant"))
        if service.admission_id is not None and service.admission_id != admission.id:
            raise _error(
                engine.DisciplineServiceError(
                    "discipline_service_id belongs to a different hospice admission; cross-admission "
                    "recommendation is rejected"
                )
            )
    try:
        recommendation = engine.create_idg_recommendation(
            db,
            service=service,
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            idg_review_id=payload.idg_review_id,
            discipline=payload.discipline,
            recommendation_type=payload.recommendation_type,
            recommendation_text=payload.recommendation_text,
            actor_user_id=user.user_id,
            actor_role=user.role,
            current_admission_id=admission.id,
            related_patient_issue_id=payload.related_patient_issue_id,
            requires_poc_change=payload.requires_poc_change,
            linked_poc_problem_id=payload.linked_poc_problem_id,
            linked_poc_goal_id=payload.linked_poc_goal_id,
            linked_poc_intervention_id=payload.linked_poc_intervention_id,
        )
    except engine.DisciplineServiceError as exc:
        raise _error(exc)
    audit_event(
        db=db, tenant_id=str(user.tenant_id), user_id=str(user.user_id),
        role=(user.role or "").strip().upper(), action="IDG_RECOMMENDATION_CREATED",
        entity_type="IDG_RECOMMENDATION", entity_id=str(recommendation.id),
        meta={"patient_id": str(patient.id), "idg_review_id": str(payload.idg_review_id)},
    )
    if recommendation.requires_poc_change:
        audit_event(
            db=db, tenant_id=str(user.tenant_id), user_id=str(user.user_id),
            role=(user.role or "").strip().upper(), action="IDG_RECOMMENDATION_POC_LINKED",
            entity_type="IDG_RECOMMENDATION", entity_id=str(recommendation.id),
            meta={
                "patient_id": str(patient.id),
                "linked_poc_problem_id": str(recommendation.linked_poc_problem_id) if recommendation.linked_poc_problem_id else None,
                "linked_poc_goal_id": str(recommendation.linked_poc_goal_id) if recommendation.linked_poc_goal_id else None,
                "linked_poc_intervention_id": str(recommendation.linked_poc_intervention_id) if recommendation.linked_poc_intervention_id else None,
            },
        )
    db.commit()
    db.refresh(recommendation)
    item = IdgRecommendationRead.model_validate(recommendation)
    item.admission_status = "CURRENT"
    return item


@router.get("/idg-recommendations/patient/{patient_id}", response_model=list[IdgRecommendationRead])
def list_idg_recommendations(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    admission = _resolve_current_admission_or_none(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    recs = (
        db.query(IDGRecommendation)
        .execution_options(skip_tenant_filter=True)
        .filter(
            IDGRecommendation.tenant_id == patient.tenant_id,
            IDGRecommendation.patient_id == patient.id,
        )
        .order_by(IDGRecommendation.created_at.desc())
        .all()
    )
    results = []
    for rec in recs:
        item = IdgRecommendationRead.model_validate(rec)
        item.admission_status = _admission_status(rec.admission_id, admission)
        results.append(item)
    return results


@router.post("/idg-recommendations/{recommendation_id}/accept", response_model=IdgRecommendationRead)
def accept_idg_recommendation(
    recommendation_id: uuid.UUID,
    payload: IdgRecommendationReview,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    recommendation = (
        db.query(IDGRecommendation)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGRecommendation.id == recommendation_id, IDGRecommendation.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if recommendation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IDG recommendation not found")
    patient = get_authorized_patient(db, recommendation.patient_id, user)
    admission = _require_current_admission(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    if recommendation.admission_id != admission.id:
        raise _error(
            engine.DisciplineServiceError(
                "This IDG recommendation does not belong to the patient's current hospice admission; "
                "ordinary recommendation review is rejected for a historical or admission-unassigned record"
            )
        )
    if recommendation.requires_poc_change:
        actor_role_norm = (user.role or "").strip().upper()
        if actor_role_norm not in engine.POC_ACCEPTANCE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This recommendation requires a Plan of Care change and may only be accepted by "
                    "RN, Case Manager, Clinical Supervisor, or Medical Director roles"
                ),
            )
    recommendation = engine.accept_idg_recommendation(db, recommendation=recommendation, actor_user_id=user.user_id, review_notes=payload.review_notes)
    audit_event(
        db=db, tenant_id=str(user.tenant_id), user_id=str(user.user_id),
        role=(user.role or "").strip().upper(), action="IDG_RECOMMENDATION_ACCEPTED",
        entity_type="IDG_RECOMMENDATION", entity_id=str(recommendation.id), meta={},
    )
    db.commit()
    db.refresh(recommendation)
    item = IdgRecommendationRead.model_validate(recommendation)
    item.admission_status = "CURRENT"
    return item


@router.post("/idg-recommendations/{recommendation_id}/decline", response_model=IdgRecommendationRead)
def decline_idg_recommendation(
    recommendation_id: uuid.UUID,
    payload: IdgRecommendationReview,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CONTINUITY_EDIT_ROLES)),
):
    recommendation = (
        db.query(IDGRecommendation)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGRecommendation.id == recommendation_id, IDGRecommendation.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if recommendation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IDG recommendation not found")
    patient = get_authorized_patient(db, recommendation.patient_id, user)
    admission = _require_current_admission(db, tenant_id=patient.tenant_id, patient_id=patient.id)
    if recommendation.admission_id != admission.id:
        raise _error(
            engine.DisciplineServiceError(
                "This IDG recommendation does not belong to the patient's current hospice admission; "
                "ordinary recommendation review is rejected for a historical or admission-unassigned record"
            )
        )
    recommendation = engine.decline_idg_recommendation(db, recommendation=recommendation, actor_user_id=user.user_id, review_notes=payload.review_notes)
    audit_event(
        db=db, tenant_id=str(user.tenant_id), user_id=str(user.user_id),
        role=(user.role or "").strip().upper(), action="IDG_RECOMMENDATION_DECLINED",
        entity_type="IDG_RECOMMENDATION", entity_id=str(recommendation.id), meta={},
    )
    db.commit()
    db.refresh(recommendation)
    item = IdgRecommendationRead.model_validate(recommendation)
    item.admission_status = "CURRENT"
    return item
