from __future__ import annotations

"""
DisciplineServiceEngine -- interdisciplinary continuity state machine for
MSW / CHAPLAIN / VOLUNTEER ONLY (owner-authorized scope). RN/MD/F2F/
Hospice-Aide refusal pathways are explicitly out of scope and remain on
app.models.refusal.Refusal / app.services.refusal_engine, unchanged.

Every PatientDisciplineService.current_state transition MUST go through
one of this module's public methods -- never assign current_state
directly. Each method:
    - loads tenant-scoped records
    - applies optimistic concurrency (expected_row_version)
    - validates permission (actor_role against the discipline's allowed roles)
    - validates the transition against ALLOWED_TRANSITIONS
    - validates required clinical data
    - writes an append-only PatientDisciplineServiceEvent
    - updates the PatientDisciplineService projection
    - returns (service, event)

Commit boundary matches the existing service-layer convention in this
codebase (see app.services.idg_follow_up_service): db.flush() only --
the caller's API route is responsible for db.commit().
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.roles import CLINICAL_ADMIN_ROLES
from app.models.admission import Admission
from app.models.discipline_service import PatientDisciplineService, PatientDisciplineServiceEvent
from app.models.enums import (
    ContinuityDiscipline,
    DisciplineServiceEventType as EventType,
    DisciplineServiceState as State,
    IDGRecommendationStatus,
    IDGRecommendationType,
    TaskDiscipline,
    TaskOrigin,
    TaskStatus,
    TaskType,
)
from app.models.idg_recommendation import IDGRecommendation
from app.models.idg_review import IDGReview
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc import POCGoal, POCIntervention, POCProblem
from app.models.task import Task

REFERENCE_TYPE = "PATIENT_DISCIPLINE_SERVICE"

# Roles permitted to accept a recommendation whose requires_poc_change is
# true (i.e. actually exercise POC review authority through this
# workflow) -- intentionally a STRICTER subset of CONTINUITY_EDIT_ROLES.
# RN remains responsible for POC coordination (owner directive); SW,
# CHAPLAIN, and VOLUNTEER_COORDINATOR may author/recommend but are never
# granted POC acceptance authority merely because they can author an IDG
# recommendation -- the existing permission matrix does not authorize
# that, so this module does not invent it.
POC_ACCEPTANCE_ROLES = {"RN", "CASE_MANAGER", "CLINICAL_SUPERVISOR", "MEDICAL_DIRECTOR"}


# =========================================================
# ERRORS
# =========================================================

class DisciplineServiceError(RuntimeError):
    pass


class InvalidTransitionError(DisciplineServiceError):
    pass


class ConcurrencyError(DisciplineServiceError):
    pass


class PermissionDeniedError(DisciplineServiceError):
    pass


class IdempotencyConflictError(DisciplineServiceError):
    pass


# =========================================================
# DISCIPLINE NORMALIZATION (CONTINUITY SCOPE ONLY)
# =========================================================

_MSW_ALIASES = {"MSW", "SW", "SOCIAL_WORK", "SOCIAL_WORKER", "LCSW"}
_CHAPLAIN_ALIASES = {
    "SPIRITUAL_COUNSELOR",
    "SPIRITUAL_COUNSELOR_SERVICE",
    "SC",
    "CHAPLAIN",
    "PASTORAL_COUNSELOR",
}
_VOLUNTEER_ALIASES = {
    "VOLUNTEER",
    "VOLUNTEER_SERVICE",
    "VOLUNTEER_SUPPORT",
    "VISITTYPE_VOLUNTEER_SUPPORT",
    "SERVICECONTEXT_VOLUNTEER_VISIT",
}

CONTINUITY_DISCIPLINES = {ContinuityDiscipline.MSW.value, ContinuityDiscipline.CHAPLAIN.value, ContinuityDiscipline.VOLUNTEER.value}


def normalize_continuity_discipline(value: str) -> str:
    """Normalizes to exactly one of MSW / CHAPLAIN / VOLUNTEER. Never
    creates separate active service records for Chaplain and Spiritual
    Counselor -- both normalize to CHAPLAIN."""
    key = (value or "").strip().upper()
    if key in _MSW_ALIASES:
        return ContinuityDiscipline.MSW.value
    if key in _CHAPLAIN_ALIASES:
        return ContinuityDiscipline.CHAPLAIN.value
    if key in _VOLUNTEER_ALIASES:
        return ContinuityDiscipline.VOLUNTEER.value
    raise DisciplineServiceError(f"Unknown or out-of-scope discipline: {value!r}")


# =========================================================
# PERMISSIONS
#
# MSW/CHAPLAIN mutations: clinical department roles (SW, CHAPLAIN, RN,
# LVN, CASE_MANAGER, CLINICAL_SUPERVISOR) plus clinical admin oversight.
#
# VOLUNTEER mutations: per owner directive, NO volunteer login account is
# created. The existing VOLUNTEER_COORDINATOR role records every
# volunteer-discipline event on the volunteer's behalf.
# =========================================================

_MSW_CHAPLAIN_ROLES = {"SW", "CHAPLAIN", "RN", "LVN", "CASE_MANAGER", "CLINICAL_SUPERVISOR", "MEDICAL_DIRECTOR"} | CLINICAL_ADMIN_ROLES
_VOLUNTEER_ROLES = {"VOLUNTEER_COORDINATOR", "CASE_MANAGER", "CLINICAL_SUPERVISOR"} | CLINICAL_ADMIN_ROLES

# Recommendation authorship: MSW and CHAPLAIN disciplines only (owner directive).
_IDG_RECOMMENDATION_AUTHOR_ROLES = {"SW", "CHAPLAIN"} | CLINICAL_ADMIN_ROLES


def _allowed_roles_for_discipline(discipline: str) -> set[str]:
    if discipline == ContinuityDiscipline.VOLUNTEER.value:
        return _VOLUNTEER_ROLES
    return _MSW_CHAPLAIN_ROLES


def _check_permission(discipline: str, actor_role: Optional[str]) -> None:
    role = (actor_role or "").strip().upper()
    if role not in _allowed_roles_for_discipline(discipline):
        raise PermissionDeniedError(
            f"Role '{actor_role}' is not authorized to record {discipline} continuity events"
        )


# =========================================================
# TRANSITIONS
#
# Keyed by (from_state, event_type) -> to_state. Any pair not present is
# rejected. No direct state assignment anywhere outside this module.
# =========================================================

NYO = State.NOT_YET_OFFERED.value
OD = State.OFFER_DUE.value
OAD = State.OFFERED_AWAITING_DECISION.value
AAA = State.ACCEPTED_AWAITING_ACTIVATION.value
ACTIVE = State.ACTIVE.value
RMC = State.REFUSED_MONITORING_CONTINUES.value
RD = State.REOFFER_DUE.value
RAD = State.REOFFERED_AWAITING_DECISION.value
PAUSED = State.PAUSED.value
ENDED = State.ENDED.value
UTC_ = State.UNABLE_TO_CONTACT.value
DMU = State.DECISION_MAKER_UNAVAILABLE.value

ALLOWED_TRANSITIONS: dict[tuple[str, str], str] = {
    (NYO, EventType.SERVICE_OFFERED.value): OAD,
    (OD, EventType.SERVICE_OFFERED.value): OAD,

    (OD, EventType.DECISION_PENDING.value): OAD,
    (RD, EventType.DECISION_PENDING.value): RAD,
    (UTC_, EventType.DECISION_PENDING.value): OAD,
    (DMU, EventType.DECISION_PENDING.value): OAD,

    (OAD, EventType.SERVICE_ACCEPTED.value): AAA,
    (RAD, EventType.REOFFER_ACCEPTED.value): AAA,

    (OAD, EventType.SERVICE_REFUSED.value): RMC,
    (ACTIVE, EventType.SERVICE_REFUSED.value): RMC,
    (RAD, EventType.REOFFER_REFUSED.value): RMC,

    (AAA, EventType.SERVICE_ACTIVATED.value): ACTIVE,

    # Directive-specified transition: an accepted-but-not-yet-activated
    # service can be paused directly (e.g. activation delayed) without
    # first passing through ACTIVE.
    (AAA, EventType.SERVICE_PAUSED.value): PAUSED,

    (ACTIVE, EventType.SERVICE_PAUSED.value): PAUSED,
    (PAUSED, EventType.SERVICE_RESUMED.value): ACTIVE,

    (RMC, EventType.REFUSAL_WITHDRAWN.value): AAA,
    (RD, EventType.REFUSAL_WITHDRAWN.value): AAA,

    (RMC, EventType.REOFFER_SCHEDULED.value): RD,
    (RD, EventType.SERVICE_REOFFERED.value): RAD,

    (OAD, EventType.UNABLE_TO_CONTACT.value): UTC_,
    (RAD, EventType.UNABLE_TO_CONTACT.value): UTC_,
    (OD, EventType.UNABLE_TO_CONTACT.value): UTC_,
    (RD, EventType.UNABLE_TO_CONTACT.value): UTC_,

    (OAD, EventType.DECISION_MAKER_UNAVAILABLE.value): DMU,
    (RAD, EventType.DECISION_MAKER_UNAVAILABLE.value): DMU,
    (OD, EventType.DECISION_MAKER_UNAVAILABLE.value): DMU,
    (RD, EventType.DECISION_MAKER_UNAVAILABLE.value): DMU,
}

# end_service() may be called from any non-ENDED state -- enumerated
# explicitly rather than an "any" wildcard so a future new state must be
# added here deliberately.
_END_SOURCES = {NYO, OD, OAD, AAA, ACTIVE, RMC, RD, RAD, PAUSED, UTC_, DMU}


def _reoffer_task_type(discipline: str) -> TaskType:
    return {
        ContinuityDiscipline.MSW.value: TaskType.MSW_REOFFER,
        ContinuityDiscipline.CHAPLAIN.value: TaskType.CHAPLAIN_REOFFER,
        ContinuityDiscipline.VOLUNTEER.value: TaskType.VOLUNTEER_REOFFER,
    }[discipline]


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _check_idempotency(db: Session, *, tenant_id, idempotency_key: Optional[str], event_type: str, discipline_service_id):
    if not idempotency_key:
        return None
    existing = (
        db.query(PatientDisciplineServiceEvent)
        .execution_options(skip_tenant_filter=True)
        .filter(
            PatientDisciplineServiceEvent.tenant_id == tenant_id,
            PatientDisciplineServiceEvent.idempotency_key == idempotency_key,
        )
        .one_or_none()
    )
    if existing is None:
        return None
    if existing.event_type != event_type or existing.discipline_service_id != discipline_service_id:
        raise IdempotencyConflictError(
            "idempotency_key was already used for a different operation; payload mutation is rejected"
        )
    return existing


def _check_row_version(service: PatientDisciplineService, expected_row_version: Optional[int]) -> None:
    if expected_row_version is not None and service.row_version != expected_row_version:
        raise ConcurrencyError(
            f"Stale row_version: expected {expected_row_version}, current {service.row_version}"
        )


def _bump_row_version(service: PatientDisciplineService) -> None:
    """M2 fix: non-transition writes (RN monitoring, corrections, IDG
    review request/complete) now bump row_version the same way
    _transition() does, so a stale concurrent write to any of these
    methods is detected rather than silently last-write-wins."""
    service.row_version = (service.row_version or 1) + 1
    service.updated_at = datetime.now(timezone.utc)


def _load_and_validate_idg_review(db: Session, *, tenant_id, patient_id, idg_review_id) -> IDGReview:
    """Defect H1 fix: a recommendation/IDG-review linkage must never be
    attachable to another patient's (or another tenant's) IDGReview. A
    copied/mistyped UUID is now rejected here rather than silently
    accepted via the bare FK-exists check that previously ran. Raises
    DisciplineServiceError (400 at the API layer) -- never a bare
    AttributeError/None -- on any mismatch."""
    review = (
        db.query(IDGReview)
        .execution_options(skip_tenant_filter=True)
        .filter(IDGReview.id == idg_review_id)
        .one_or_none()
    )
    if review is None:
        raise DisciplineServiceError(f"IDG review {idg_review_id} not found")
    if review.tenant_id != tenant_id:
        raise DisciplineServiceError("IDG review belongs to a different tenant; cross-tenant linkage is rejected")
    if review.patient_id != patient_id:
        raise DisciplineServiceError("IDG review belongs to a different patient; cross-patient linkage is rejected")
    return review


def _load_and_validate_admission(db: Session, *, tenant_id, patient_id, admission_id):
    """Readmission episode-scoping fix: resolves and validates the
    Admission a continuity record is being attributed to. Raises
    DisciplineServiceError on any ownership mismatch rather than silently
    accepting a cross-patient/cross-tenant admission_id. Returns None only
    when admission_id itself is None (explicitly permitted for the
    legacy/admission-unassigned historical-row case -- never inferred).
    """
    if admission_id is None:
        return None
    admission = (
        db.query(Admission)
        .execution_options(skip_tenant_filter=True)
        .filter(Admission.id == admission_id)
        .one_or_none()
    )
    if admission is None:
        raise DisciplineServiceError(f"Admission {admission_id} not found")
    if admission.tenant_id != tenant_id:
        raise DisciplineServiceError("Admission belongs to a different tenant; cross-tenant linkage is rejected")
    if admission.patient_id != patient_id:
        raise DisciplineServiceError("Admission belongs to a different patient; cross-patient linkage is rejected")
    return admission


def resolve_current_admission(db: Session, *, tenant_id, patient_id) -> Optional[Admission]:
    """Single canonical 'current admission' resolver for continuity.
    Reuses the same ADMITTED + discharged_at IS NULL convention already
    used independently by app.api.patients._get_active_admission and
    app.api.visits._get_current_admission_for_patient, so there is exactly
    one continuity-owned definition rather than a third independent copy
    that could drift.

    Returns None when the patient genuinely has no active admission --
    callers performing an ordinary CURRENT clinical mutation must treat
    None as a hard rejection, never as permission to fall back to an
    admission-unassigned (legacy) row.

    Raises DisciplineServiceError when MORE THAN ONE active admission is
    found for the same tenant+patient. That is an invalid-data condition
    (two concurrently open admissions), and silently picking the newest
    one would let a clinician/mutation apply to the wrong episode without
    any indication something is wrong. Ambiguity must be rejected, not
    guessed around -- the caller/API layer surfaces this as a 400 with
    enough internal context for troubleshooting without PHI in the
    message itself (no patient name/MRN/dates are included)."""
    admissions = (
        db.query(Admission)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Admission.tenant_id == tenant_id,
            Admission.patient_id == patient_id,
            Admission.status == "ADMITTED",
            Admission.discharged_at.is_(None),
        )
        .order_by(Admission.created_at.desc())
        .all()
    )
    if len(admissions) > 1:
        raise DisciplineServiceError(
            "Multiple active hospice admissions were found for this patient; current-admission continuity "
            "actions are ambiguous and are rejected until the duplicate-active-admission data condition is "
            "resolved."
        )
    return admissions[0] if admissions else None


def _validate_poc_linkage(
    db: Session,
    *,
    tenant_id,
    patient_id,
    admission_id,
    poc_problem_id=None,
    poc_goal_id=None,
    poc_intervention_id=None,
) -> None:
    """True Plan-of-Care linkage ownership validation. Reuses the
    existing POCProblem -> POCGoal -> POCIntervention hierarchy and the
    PlanOfCare(admission_id) root -- no second POC system, no inferred
    foreign keys. Every supplied id must resolve to a record that
    belongs to the SAME tenant, the SAME patient, and the SAME
    (current) admission, via its PlanOfCare. Mismatched
    goal/problem or intervention/goal relationships are rejected.
    Raises DisciplineServiceError (-> HTTP 400 at the API layer) on any
    violation; never discloses whether a cross-tenant/cross-patient
    record exists (generic 'not found or not eligible for linkage'
    message only)."""
    not_found = "POC record not found, not eligible for linkage, or does not belong to the current admission"

    problem = None
    if poc_problem_id is not None:
        problem = (
            db.query(POCProblem)
            .join(PlanOfCareVersion, POCProblem.poc_version_id == PlanOfCareVersion.id)
            .join(PlanOfCare, PlanOfCareVersion.plan_of_care_id == PlanOfCare.id)
            .filter(
                POCProblem.id == poc_problem_id,
                POCProblem.tenant_id == tenant_id,
                PlanOfCare.tenant_id == tenant_id,
                PlanOfCare.patient_id == patient_id,
                PlanOfCare.admission_id == admission_id,
            )
            .one_or_none()
        )
        if problem is None:
            raise DisciplineServiceError(not_found)

    goal = None
    if poc_goal_id is not None:
        goal = (
            db.query(POCGoal)
            .join(POCProblem, POCGoal.problem_id == POCProblem.id)
            .join(PlanOfCareVersion, POCProblem.poc_version_id == PlanOfCareVersion.id)
            .join(PlanOfCare, PlanOfCareVersion.plan_of_care_id == PlanOfCare.id)
            .filter(
                POCGoal.id == poc_goal_id,
                POCGoal.tenant_id == tenant_id,
                PlanOfCare.tenant_id == tenant_id,
                PlanOfCare.patient_id == patient_id,
                PlanOfCare.admission_id == admission_id,
            )
            .one_or_none()
        )
        if goal is None:
            raise DisciplineServiceError(not_found)
        if problem is not None and goal.problem_id != problem.id:
            raise DisciplineServiceError("Linked POC goal does not belong to the linked POC problem")

    if poc_intervention_id is not None:
        intervention = (
            db.query(POCIntervention)
            .join(POCGoal, POCIntervention.goal_id == POCGoal.id)
            .join(POCProblem, POCGoal.problem_id == POCProblem.id)
            .join(PlanOfCareVersion, POCProblem.poc_version_id == PlanOfCareVersion.id)
            .join(PlanOfCare, PlanOfCareVersion.plan_of_care_id == PlanOfCare.id)
            .filter(
                POCIntervention.id == poc_intervention_id,
                POCIntervention.tenant_id == tenant_id,
                PlanOfCare.tenant_id == tenant_id,
                PlanOfCare.patient_id == patient_id,
                PlanOfCare.admission_id == admission_id,
            )
            .one_or_none()
        )
        if intervention is None:
            raise DisciplineServiceError(not_found)
        if goal is not None and intervention.goal_id != goal.id:
            raise DisciplineServiceError("Linked POC intervention does not belong to the linked POC goal")


def _check_same_admission(*, service: PatientDisciplineService, admission_id) -> None:
    """A recommendation/IDG-review action tied to a PatientDisciplineService
    must occur within that service's own admission -- never a different
    (e.g. prior-episode) admission, even if tenant/patient match."""
    if service.admission_id != admission_id:
        raise DisciplineServiceError(
            "Admission mismatch: this action does not belong to the same hospice admission as the "
            "discipline-service record (readmission episode isolation)"
        )


def _transition(
    db: Session,
    *,
    service: PatientDisciplineService,
    event_type: str,
    actor_user_id,
    actor_role: Optional[str],
    recorded_by_role: Optional[str] = None,
    information_source: Optional[str] = None,
    decision_maker_name: Optional[str] = None,
    decision_maker_relationship: Optional[str] = None,
    reason: Optional[str] = None,
    effective_at: Optional[datetime] = None,
    related_task_id=None,
    related_idg_review_id=None,
    related_patient_issue_id=None,
    correlation_id=None,
    idempotency_key: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> PatientDisciplineServiceEvent:
    key = (service.current_state, event_type)
    to_state = ALLOWED_TRANSITIONS.get(key)
    if to_state is None:
        raise InvalidTransitionError(f"{event_type} is not a valid transition from {service.current_state}")

    cached = _check_idempotency(
        db, tenant_id=service.tenant_id, idempotency_key=idempotency_key, event_type=event_type, discipline_service_id=service.id
    )
    if cached is not None:
        return cached

    from_state = service.current_state
    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=event_type,
        from_state=from_state,
        to_state=to_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=recorded_by_role or actor_role,
        information_source=information_source,
        decision_maker_name=decision_maker_name,
        decision_maker_relationship=decision_maker_relationship,
        reason=reason,
        effective_at=effective_at or datetime.now(timezone.utc),
        related_task_id=related_task_id,
        related_idg_review_id=related_idg_review_id,
        related_patient_issue_id=related_patient_issue_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        event_metadata=metadata,
    )
    db.add(event)
    db.flush()

    service.current_state = to_state
    service.current_state_event_id = event.id
    service.row_version = (service.row_version or 1) + 1
    service.updated_at = datetime.now(timezone.utc)
    if information_source:
        service.last_information_source = information_source
    if decision_maker_name:
        service.last_decision_maker_name = decision_maker_name
    if decision_maker_relationship:
        service.last_decision_maker_relationship = decision_maker_relationship
    if event_type == EventType.SERVICE_OFFERED.value:
        service.last_offered_at = event.effective_at
    if event_type in (EventType.SERVICE_ACCEPTED.value, EventType.REOFFER_ACCEPTED.value, EventType.SERVICE_REFUSED.value, EventType.REOFFER_REFUSED.value):
        service.last_decision_at = event.effective_at
    if event_type in (EventType.SERVICE_REFUSED.value, EventType.REOFFER_REFUSED.value):
        service.last_refused_at = event.effective_at
    if related_idg_review_id:
        service.idg_review_id = related_idg_review_id
    if related_task_id:
        pass  # task linkage lives on the event; projection does not store a single task id

    db.flush()
    return event


def _dedupe_reoffer_task(db: Session, *, service: PatientDisciplineService, purpose: str) -> Optional[Task]:
    return (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == service.tenant_id,
            Task.patient_id == service.patient_id,
            Task.task_type == _reoffer_task_type(service.discipline),
            Task.status == TaskStatus.PENDING,
            Task.reference_type == REFERENCE_TYPE,
            Task.reference_id == service.id,
            Task.alert_reason == purpose,
        )
        .first()
    )


def _create_reoffer_task(db: Session, *, service: PatientDisciplineService, actor_user_id, purpose: str, due_date=None) -> Task:
    existing = _dedupe_reoffer_task(db, service=service, purpose=purpose)
    if existing is not None:
        return existing
    task = Task(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        task_type=_reoffer_task_type(service.discipline),
        origin=TaskOrigin.SYSTEM,
        discipline=TaskDiscipline(service.discipline),
        status=TaskStatus.PENDING,
        alert_reason=purpose,
        reference_type=REFERENCE_TYPE,
        reference_id=service.id,
        due_date=due_date,
        created_by=actor_user_id,
    )
    db.add(task)
    db.flush()
    return task


# =========================================================
# LOOKUP / CREATE
# =========================================================

def get_or_create_service(
    db: Session,
    *,
    tenant_id,
    patient_id,
    discipline: str,
    admission_id=None,
    actor_user_id=None,
    actor_role: Optional[str] = None,
    reason: Optional[str] = None,
) -> PatientDisciplineService:
    """Readmission episode-scoping fix: lookup/creation is now scoped by
    admission_id in addition to tenant+patient+discipline, so a prior
    admission's service row (refusal/monitoring/IDG-required/re-offer
    state) is never returned for a different admission. Passing
    admission_id=None is for legacy/admission-unassigned historical rows
    only -- callers operating within a known admission MUST pass it so a
    new row is created per-admission rather than reusing history."""
    canonical = normalize_continuity_discipline(discipline)
    admission = _load_and_validate_admission(
        db, tenant_id=tenant_id, patient_id=patient_id, admission_id=admission_id
    )
    service = (
        db.query(PatientDisciplineService)
        .execution_options(skip_tenant_filter=True)
        .filter(
            PatientDisciplineService.tenant_id == tenant_id,
            PatientDisciplineService.patient_id == patient_id,
            PatientDisciplineService.discipline == canonical,
            PatientDisciplineService.admission_id == (admission.id if admission else None),
        )
        .one_or_none()
    )
    if service is not None:
        return service

    _check_permission(canonical, actor_role)
    service = PatientDisciplineService(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission.id if admission else None,
        discipline=canonical,
        current_state=NYO,
        row_version=1,
    )
    db.add(service)
    db.flush()

    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        discipline_service_id=service.id,
        event_type=EventType.DISCIPLINE_IDENTIFIED.value,
        from_state=None,
        to_state=NYO,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    service.current_state_event_id = event.id
    db.flush()
    return service


# =========================================================
# PUBLIC STATE-MACHINE METHODS
# =========================================================

def offer_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    information_source: Optional[str] = None,
    reason: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.SERVICE_OFFERED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        information_source=information_source,
        reason=reason,
        idempotency_key=idempotency_key,
    )
    return service, event


def record_pending_decision(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.DECISION_PENDING.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        idempotency_key=idempotency_key,
    )
    return service, event


def accept_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    decision_maker_name: str,
    decision_maker_relationship: str,
    information_source: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    if not decision_maker_name or not decision_maker_relationship:
        raise DisciplineServiceError("decision_maker_name and decision_maker_relationship are required to accept a service")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event_type = (
        EventType.REOFFER_ACCEPTED.value
        if service.current_state == RAD
        else EventType.SERVICE_ACCEPTED.value
    )
    event = _transition(
        db,
        service=service,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        information_source=information_source,
        decision_maker_name=decision_maker_name,
        decision_maker_relationship=decision_maker_relationship,
        idempotency_key=idempotency_key,
    )
    return service, event


def refuse_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: str,
    decision_maker_name: str,
    decision_maker_relationship: str,
    information_source: Optional[str] = None,
    assign_rn_monitoring_user_id=None,
    requires_idg_review: bool = False,
    related_patient_issue_id=None,
    create_reoffer_task: bool = True,
    reoffer_due_date=None,
    expected_row_version: Optional[int] = None,
    correlation_id=None,
    idempotency_key: Optional[str] = None,
):
    """
    Atomic refusal transaction (owner directive): service event + projection
    update + optional RN monitoring assignment + optional IDG linkage +
    optional re-offer task + related_patient_issue linkage all happen
    within this single flush sequence. The caller's db.commit() is the
    actual atomic boundary (matches this codebase's service-layer
    convention); any exception raised here leaves nothing flushed that the
    caller should commit.

    Never auto-creates a PatientIssue -- pass related_patient_issue_id only
    when a real clinical concern already exists/was separately created.
    """
    if not reason:
        raise DisciplineServiceError("reason is required to refuse a service")
    if not decision_maker_name or not decision_maker_relationship:
        raise DisciplineServiceError("decision_maker_name and decision_maker_relationship are required to refuse a service")

    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)

    correlation_id = correlation_id or uuid.uuid4()
    event_type = EventType.REOFFER_REFUSED.value if service.current_state == RAD else EventType.SERVICE_REFUSED.value

    event = _transition(
        db,
        service=service,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        information_source=information_source,
        decision_maker_name=decision_maker_name,
        decision_maker_relationship=decision_maker_relationship,
        reason=reason,
        related_patient_issue_id=related_patient_issue_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )

    task = None
    if create_reoffer_task:
        task = _create_reoffer_task(
            db,
            service=service,
            actor_user_id=actor_user_id,
            purpose=f"{service.discipline}_SERVICE_REFUSED_REOFFER_REQUIRED",
            due_date=reoffer_due_date,
        )
        event.related_task_id = task.id
        db.flush()

    if assign_rn_monitoring_user_id is not None:
        assign_rn_monitoring(
            db,
            service=service,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            rn_user_id=assign_rn_monitoring_user_id,
            correlation_id=correlation_id,
        )

    if requires_idg_review:
        request_idg_review(
            db,
            service=service,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            correlation_id=correlation_id,
        )

    return service, event, task


def activate_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.SERVICE_ACTIVATED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        idempotency_key=idempotency_key,
    )
    return service, event


def pause_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.SERVICE_PAUSED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        idempotency_key=idempotency_key,
    )
    return service, event


def resume_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.SERVICE_RESUMED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        idempotency_key=idempotency_key,
    )
    return service, event


def end_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: str,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    if not reason:
        raise DisciplineServiceError("reason is required to end a service")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    if service.current_state not in _END_SOURCES:
        raise InvalidTransitionError(f"Cannot end service from state {service.current_state}")

    cached = _check_idempotency(
        db, tenant_id=service.tenant_id, idempotency_key=idempotency_key, event_type=EventType.SERVICE_ENDED.value, discipline_service_id=service.id
    )
    if cached is not None:
        return service, cached

    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.SERVICE_ENDED.value,
        from_state=service.current_state,
        to_state=ENDED,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
        idempotency_key=idempotency_key,
    )
    db.add(event)
    db.flush()
    service.current_state = ENDED
    service.current_state_event_id = event.id
    service.row_version = (service.row_version or 1) + 1
    service.updated_at = datetime.now(timezone.utc)
    db.flush()
    return service, event


def withdraw_refusal(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: str,
    decision_maker_name: str,
    decision_maker_relationship: str,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    if not reason:
        raise DisciplineServiceError("reason is required to withdraw a refusal")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.REFUSAL_WITHDRAWN.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        decision_maker_name=decision_maker_name,
        decision_maker_relationship=decision_maker_relationship,
        idempotency_key=idempotency_key,
    )
    return service, event


def schedule_reoffer(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    due_date=None,
    trigger_description: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    """due_date (date-based) and/or trigger_description (event-based) --
    no hardcoded interval; the caller/clinician determines the cadence."""
    if due_date is None and not trigger_description:
        raise DisciplineServiceError("schedule_reoffer requires due_date and/or trigger_description")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.REOFFER_SCHEDULED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=trigger_description,
        idempotency_key=idempotency_key,
        metadata={"due_date": due_date.isoformat() if due_date else None, "trigger_description": trigger_description},
    )
    service.reoffer_due_at = (
        datetime.combine(due_date, datetime.min.time()).replace(tzinfo=timezone.utc) if due_date else None
    )
    db.flush()
    return service, event


def reoffer_service(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    information_source: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.SERVICE_REOFFERED.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        information_source=information_source,
        idempotency_key=idempotency_key,
    )
    return service, event


def record_unable_to_contact(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.UNABLE_TO_CONTACT.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        idempotency_key=idempotency_key,
    )
    return service, event


def record_decision_maker_unavailable(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: Optional[str] = None,
    expected_row_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = _transition(
        db,
        service=service,
        event_type=EventType.DECISION_MAKER_UNAVAILABLE.value,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        idempotency_key=idempotency_key,
    )
    return service, event


def record_correction(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    corrects_event_id,
    reason: str,
    decision_maker_name: Optional[str] = None,
    decision_maker_relationship: Optional[str] = None,
    information_source: Optional[str] = None,
    expected_row_version: Optional[int] = None,
):
    """Never changes current_state or rewrites history -- records a new
    CORRECTION_RECORDED event referencing the event it corrects. All
    corrections remain historically visible; no event/audit deletion."""
    if not reason:
        raise DisciplineServiceError("reason is required to record a correction")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    corrected = (
        db.query(PatientDisciplineServiceEvent)
        .execution_options(skip_tenant_filter=True)
        .filter(
            PatientDisciplineServiceEvent.id == corrects_event_id,
            PatientDisciplineServiceEvent.discipline_service_id == service.id,
        )
        .one_or_none()
    )
    if corrected is None:
        raise DisciplineServiceError(f"Event {corrects_event_id} not found for this service")

    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.CORRECTION_RECORDED.value,
        from_state=service.current_state,
        to_state=service.current_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        information_source=information_source,
        decision_maker_name=decision_maker_name,
        decision_maker_relationship=decision_maker_relationship,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
        corrects_event_id=corrects_event_id,
    )
    db.add(event)
    _bump_row_version(service)
    db.flush()
    return service, event


# =========================================================
# RN MONITORING
# =========================================================

def assign_rn_monitoring(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    rn_user_id,
    reason: Optional[str] = None,
    correlation_id=None,
    expected_row_version: Optional[int] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    is_change = service.rn_monitoring_assigned_user_id is not None
    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.RN_MONITORING_CHANGED.value if is_change else EventType.RN_MONITORING_ASSIGNED.value,
        from_state=service.current_state,
        to_state=service.current_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        event_metadata={"rn_user_id": str(rn_user_id), "prior_rn_user_id": str(service.rn_monitoring_assigned_user_id) if service.rn_monitoring_assigned_user_id else None},
    )
    db.add(event)
    service.rn_monitoring_assigned_user_id = rn_user_id
    _bump_row_version(service)
    db.flush()
    return service, event


def end_rn_monitoring(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    reason: str,
    expected_row_version: Optional[int] = None,
):
    if not reason:
        raise DisciplineServiceError("reason is required to end RN monitoring")
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.RN_MONITORING_ENDED.value,
        from_state=service.current_state,
        to_state=service.current_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
        event_metadata={"prior_rn_user_id": str(service.rn_monitoring_assigned_user_id) if service.rn_monitoring_assigned_user_id else None},
    )
    db.add(event)
    service.rn_monitoring_assigned_user_id = None
    _bump_row_version(service)
    db.flush()
    return service, event


# =========================================================
# IDG REVIEW LINKAGE
# =========================================================

def request_idg_review(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    idg_review_id=None,
    reason: Optional[str] = None,
    correlation_id=None,
    expected_row_version: Optional[int] = None,
):
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    if idg_review_id:
        review = _load_and_validate_idg_review(
            db, tenant_id=service.tenant_id, patient_id=service.patient_id, idg_review_id=idg_review_id
        )
        # Readmission episode-scoping: when this service belongs to a
        # current admission, the linked review must belong to that same
        # admission. A legacy/admission-unassigned review (admission_id is
        # null) must NOT be allowed to participate in a current-admission
        # workflow -- it is rejected outright, not silently passed through.
        if service.admission_id is not None:
            if review.admission_id is None or review.admission_id != service.admission_id:
                raise DisciplineServiceError(
                    "IDG review is legacy/admission-unassigned or belongs to a different hospice admission; "
                    "cross-admission linkage is rejected"
                )
    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.IDG_REVIEW_REQUESTED.value,
        from_state=service.current_state,
        to_state=service.current_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=reason,
        effective_at=datetime.now(timezone.utc),
        related_idg_review_id=idg_review_id,
        correlation_id=correlation_id,
    )
    db.add(event)
    service.idg_review_required = True
    if idg_review_id:
        service.idg_review_id = idg_review_id
    _bump_row_version(service)
    db.flush()
    return service, event


def complete_idg_review(
    db: Session,
    *,
    service: PatientDisciplineService,
    actor_user_id,
    actor_role: str,
    idg_review_id,
    notes: Optional[str] = None,
    expected_row_version: Optional[int] = None,
):
    """M1 fix: this function already existed but had no API/UI caller,
    making idg_review_required a one-way latch. It is now reachable via
    POST .../idg-review/complete. Validates the review belongs to this
    service's patient/tenant (same H1-style guard as
    create_idg_recommendation) before clearing the flag."""
    _check_permission(service.discipline, actor_role)
    _check_row_version(service, expected_row_version)
    if not idg_review_id:
        raise DisciplineServiceError("idg_review_id is required to complete an IDG review")
    review = _load_and_validate_idg_review(
        db, tenant_id=service.tenant_id, patient_id=service.patient_id, idg_review_id=idg_review_id
    )
    # Readmission episode-scoping: when this service belongs to a current
    # admission, the review must belong to that same admission. A legacy
    # (admission_id is null) review must not be allowed to complete a
    # current-admission service's IDG requirement.
    if service.admission_id is not None:
        if review.admission_id is None or review.admission_id != service.admission_id:
            raise DisciplineServiceError(
                "IDG review is legacy/admission-unassigned or belongs to a different hospice admission; "
                "completion is rejected (readmission episode isolation)"
            )
    event = PatientDisciplineServiceEvent(
        id=uuid.uuid4(),
        tenant_id=service.tenant_id,
        patient_id=service.patient_id,
        discipline_service_id=service.id,
        event_type=EventType.IDG_REVIEW_COMPLETED.value,
        from_state=service.current_state,
        to_state=service.current_state,
        recorded_by_user_id=actor_user_id,
        recorded_by_role=actor_role,
        reason=notes,
        effective_at=datetime.now(timezone.utc),
        related_idg_review_id=idg_review_id,
    )
    db.add(event)
    service.idg_review_required = False
    _bump_row_version(service)
    db.flush()
    return service, event


# =========================================================
# IDG RECOMMENDATIONS (no visit / no billable encounter)
# =========================================================

def create_idg_recommendation(
    db: Session,
    *,
    service: Optional[PatientDisciplineService],
    tenant_id,
    patient_id,
    idg_review_id,
    discipline: str,
    recommendation_type: str,
    recommendation_text: str,
    actor_user_id,
    actor_role: str,
    current_admission_id=None,
    related_patient_issue_id=None,
    requires_poc_change: bool = False,
    linked_poc_problem_id=None,
    linked_poc_goal_id=None,
    linked_poc_intervention_id=None,
) -> IDGRecommendation:
    """MSW and CHAPLAIN may create recommendations without a visit,
    billable encounter, discipline assessment, or face-to-face visit.
    no_direct_visit is always true; the UI must display
    'IDG RECOMMENDATION / NO DIRECT VISIT'. Never creates a visit record
    or billable encounter.

    current_admission_id is the caller's resolved *current* admission for
    this patient (None only when the patient genuinely has no active
    admission at all -- never a client-supplied override). When a current
    admission exists, this is a current-admission workflow: a legacy
    (admission_id is null) or prior-admission IDGReview must be rejected
    outright, never silently passed through, per the no-current-workflow-
    participation rule for admission-unassigned records."""
    canonical_discipline = normalize_continuity_discipline(discipline)
    role = (actor_role or "").strip().upper()
    if role not in _IDG_RECOMMENDATION_AUTHOR_ROLES:
        raise PermissionDeniedError(f"Role '{actor_role}' may not author an IDG recommendation")
    if canonical_discipline not in (ContinuityDiscipline.MSW.value, ContinuityDiscipline.CHAPLAIN.value):
        raise DisciplineServiceError("Only MSW and CHAPLAIN may author IDG recommendations")
    valid_types = {t.value for t in IDGRecommendationType}
    if recommendation_type not in valid_types:
        raise DisciplineServiceError(f"recommendation_type must be one of {sorted(valid_types)}")
    if not recommendation_text:
        raise DisciplineServiceError("recommendation_text is required")

    # H1 fix: reject a recommendation attached to another patient's (or
    # another tenant's) IDG review -- never trust a client-supplied UUID.
    review = _load_and_validate_idg_review(db, tenant_id=tenant_id, patient_id=patient_id, idg_review_id=idg_review_id)

    # Readmission episode-scoping -- current-admission-workflow rule:
    # when the patient has a current admission, this is a current-
    # admission workflow and a legacy (admission_id is null) or prior-
    # admission IDGReview must be rejected outright rather than silently
    # passed through. Admission-unassigned reviews remain valid for
    # historical viewing elsewhere -- just not as the basis for a NEW
    # recommendation. When the patient has no current admission at all
    # (current_admission_id is None), no current-admission context exists
    # to validate against, so legacy behavior is preserved rather than
    # blocking every historical-only patient.
    if current_admission_id is not None:
        if review.admission_id is None:
            raise DisciplineServiceError(
                "IDG review is legacy/admission-unassigned and cannot be used to create a current-admission "
                "recommendation"
            )
        if review.admission_id != current_admission_id:
            raise DisciplineServiceError(
                "IDG review belongs to a different hospice admission; cross-admission recommendation is rejected"
            )
        if service is not None and service.admission_id is not None and service.admission_id != current_admission_id:
            raise DisciplineServiceError(
                "Discipline service belongs to a different hospice admission; cross-admission recommendation "
                "is rejected"
            )

    # Readmission episode-scoping: a recommendation linked to a service
    # must stay within that service's admission. Legacy (admission_id is
    # None) service/review rows are permitted through -- they predate
    # admission-scoping and are not themselves evidence of cross-admission
    # reuse. The resulting recommendation inherits whichever side has a
    # known admission (service takes precedence since it is the
    # continuity-owned record); never cloned/inferred from anywhere else.
    recommendation_admission_id = None
    if service is not None and service.admission_id is not None:
        if review.admission_id is not None and review.admission_id != service.admission_id:
            raise DisciplineServiceError(
                "IDG review belongs to a different hospice admission than the linked discipline service; "
                "cross-admission recommendation is rejected"
            )
        recommendation_admission_id = service.admission_id
    elif review.admission_id is not None:
        recommendation_admission_id = review.admission_id

    # True Plan-of-Care linkage: any supplied POC record must belong to
    # the SAME tenant/patient/current-admission via its PlanOfCare, and
    # goal/intervention must nest correctly under problem/goal. A
    # rejected link raises before any row is added -- no recommendation,
    # no event, no partial state (section 5/19 atomicity requirement).
    if linked_poc_problem_id or linked_poc_goal_id or linked_poc_intervention_id:
        if current_admission_id is None:
            raise DisciplineServiceError(
                "POC linkage requires an active current hospice admission; none exists for this patient"
            )
        _validate_poc_linkage(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            admission_id=current_admission_id,
            poc_problem_id=linked_poc_problem_id,
            poc_goal_id=linked_poc_goal_id,
            poc_intervention_id=linked_poc_intervention_id,
        )

    recommendation = IDGRecommendation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=recommendation_admission_id,
        idg_review_id=idg_review_id,
        discipline_service_id=service.id if service else None,
        discipline=canonical_discipline,
        recommendation_type=recommendation_type,
        recommendation_text=recommendation_text,
        no_direct_visit=True,
        status=IDGRecommendationStatus.PENDING.value,
        related_patient_issue_id=related_patient_issue_id,
        requires_poc_change=bool(requires_poc_change or linked_poc_problem_id or linked_poc_goal_id or linked_poc_intervention_id),
        linked_poc_problem_id=linked_poc_problem_id,
        linked_poc_goal_id=linked_poc_goal_id,
        linked_poc_intervention_id=linked_poc_intervention_id,
        created_by_user_id=actor_user_id,
    )
    db.add(recommendation)
    db.flush()

    if service is not None:
        event = PatientDisciplineServiceEvent(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            discipline_service_id=service.id,
            event_type=EventType.DISCIPLINE_RECOMMENDATION_ADDED.value,
            from_state=service.current_state,
            to_state=service.current_state,
            recorded_by_user_id=actor_user_id,
            recorded_by_role=actor_role,
            reason=recommendation_text,
            effective_at=datetime.now(timezone.utc),
            related_idg_review_id=idg_review_id,
            event_metadata={"recommendation_id": str(recommendation.id), "recommendation_type": recommendation_type},
        )
        db.add(event)
        db.flush()

    return recommendation


def accept_idg_recommendation(db: Session, *, recommendation: IDGRecommendation, actor_user_id, review_notes: Optional[str] = None) -> IDGRecommendation:
    """Marks the recommendation accepted by an authorized clinician. Does
    NOT itself create/modify any POCProblem/POCGoal/POCIntervention --
    POC action is a separate, explicit clinician step."""
    recommendation.status = IDGRecommendationStatus.ACCEPTED.value
    recommendation.reviewed_by_user_id = actor_user_id
    recommendation.reviewed_at = datetime.now(timezone.utc)
    recommendation.review_notes = review_notes
    db.flush()
    return recommendation


def decline_idg_recommendation(db: Session, *, recommendation: IDGRecommendation, actor_user_id, review_notes: Optional[str] = None) -> IDGRecommendation:
    recommendation.status = IDGRecommendationStatus.DECLINED.value
    recommendation.reviewed_by_user_id = actor_user_id
    recommendation.reviewed_at = datetime.now(timezone.utc)
    recommendation.review_notes = review_notes
    db.flush()
    return recommendation
