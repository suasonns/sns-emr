from __future__ import annotations

"""
California Two-Hour In-Person Licensed-Nurse Response service (issue #143;
Title 22 Section 74820/74848; DPH-18-002E-HospiceAgencies_Text.pdf).

Clock rule (see app.models.patient_response for the full model chain):
  START = PatientResponseEvent.received_at
  STOP  = NurseResponseAssignment.arrived_at (in-person arrival ONLY)

Assignment, reassignment, dispatch, telephone/video interim support, and
IDG notification never start or stop the clock. This module enforces that
by construction: only record_in_person_arrival() ever sets arrived_at, and
response_deadline_at is computed once at event creation and never
recalculated by any other function in this module.
"""

import uuid
from datetime import datetime, timedelta

from app.models.patient_response import (
    InterimPatientSupport,
    NurseResponseAssignment,
    PatientResponseAuditEvent,
    PatientResponseEvent,
    ResponseIntervention,
)

TWO_HOUR_RESPONSE_WINDOW = timedelta(hours=2)


class TwoHourResponseError(RuntimeError):
    pass


def _audit(
    db,
    *,
    tenant_id,
    patient_response_event_id,
    patient_id,
    admission_id,
    event_type,
    actor_user_id=None,
    actor_account_discipline=None,
    prior_value=None,
    new_value=None,
    reason=None,
    correlation_id=None,
):
    row = PatientResponseAuditEvent(
        tenant_id=tenant_id,
        patient_response_event_id=patient_response_event_id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_value,
        new_value=new_value,
        reason=reason,
        correlation_id=correlation_id,
    )
    db.add(row)
    return row


def create_patient_response_event(
    db,
    *,
    tenant_id,
    patient_id,
    admission_id=None,
    benefit_period_id=None,
    event_type: str,
    received_at: datetime,
    received_via: str | None = None,
    reported_by_name: str | None = None,
    description: str,
    created_by_user_id=None,
    actor_account_discipline: str | None = None,
) -> PatientResponseEvent:
    """
    Starts the two-hour clock. received_at must be the real time the
    hospice received the medical-need/safety-concern report -- never a
    later contact/dispatch time. response_deadline_at is computed once
    here (received_at + 2 hours) and is never recalculated afterward by
    assignment, reassignment, or dispatch.
    """
    if event_type not in ("MEDICAL_NEED", "SAFETY_CONCERN"):
        raise TwoHourResponseError("event_type must be MEDICAL_NEED or SAFETY_CONCERN")
    if received_at is None:
        raise TwoHourResponseError("received_at is required (the clock start)")

    event = PatientResponseEvent(
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        benefit_period_id=benefit_period_id,
        event_type=event_type,
        received_at=received_at,
        received_via=received_via,
        reported_by_name=reported_by_name,
        description=description,
        response_deadline_at=received_at + TWO_HOUR_RESPONSE_WINDOW,
        created_by=created_by_user_id,
    )
    db.add(event)
    db.flush()

    _audit(
        db,
        tenant_id=tenant_id,
        patient_response_event_id=event.id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type="REQUIREMENT_CREATED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"event_type": event_type, "received_at": received_at.isoformat()},
    )
    db.flush()
    return event


def assign_nurse(
    db,
    *,
    event: PatientResponseEvent,
    nurse_user_id,
    assigned_at: datetime,
    reassigned_from_assignment_id=None,
    reassignment_reason: str | None = None,
    created_by_user_id=None,
    actor_account_discipline: str | None = None,
) -> NurseResponseAssignment:
    """
    Creates an assignment (or reassignment) row. NEVER modifies
    event.response_deadline_at -- assignment/reassignment does not start
    or restart the clock.
    """
    if reassigned_from_assignment_id is not None and not reassignment_reason:
        raise TwoHourResponseError("reassignment_reason is required when reassigning")

    assignment = NurseResponseAssignment(
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        nurse_user_id=nurse_user_id,
        assigned_at=assigned_at,
        reassigned_from_assignment_id=reassigned_from_assignment_id,
        reassignment_reason=reassignment_reason,
        created_by=created_by_user_id,
    )
    db.add(assignment)
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="REASSIGNED" if reassigned_from_assignment_id else "ASSIGNED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"nurse_user_id": str(nurse_user_id), "assigned_at": assigned_at.isoformat()},
        reason=reassignment_reason,
    )
    db.flush()
    return assignment


def record_dispatch(
    db, *, assignment: NurseResponseAssignment, dispatched_at: datetime, created_by_user_id=None
) -> NurseResponseAssignment:
    """Dispatch does not stop the clock -- only records that dispatch occurred."""
    assignment.dispatched_at = dispatched_at
    db.flush()
    _audit(
        db,
        tenant_id=assignment.tenant_id,
        patient_response_event_id=assignment.patient_response_event_id,
        patient_id=assignment.patient_response_event.patient_id,
        admission_id=assignment.patient_response_event.admission_id,
        event_type="DISPATCHED",
        actor_user_id=created_by_user_id,
        new_value={"dispatched_at": dispatched_at.isoformat()},
    )
    db.flush()
    return assignment


def record_in_person_arrival(
    db,
    *,
    event: PatientResponseEvent,
    assignment: NurseResponseAssignment,
    arrived_at: datetime,
    variance_reason: str | None = None,
    created_by_user_id=None,
    actor_account_discipline: str | None = None,
) -> NurseResponseAssignment:
    """
    The ONLY function in this module that stops the clock. Telephone/video
    contact must never call this -- use record_interim_support instead.
    """
    is_late = arrived_at > event.response_deadline_at
    if is_late and not variance_reason:
        raise TwoHourResponseError(
            "variance_reason is required when in-person arrival is after the two-hour deadline"
        )

    assignment.arrived_at = arrived_at
    assignment.is_late = is_late
    assignment.variance_reason = variance_reason
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="ARRIVED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"arrived_at": arrived_at.isoformat(), "is_late": is_late},
        reason=variance_reason,
    )
    if is_late:
        _audit(
            db,
            tenant_id=event.tenant_id,
            patient_response_event_id=event.id,
            patient_id=event.patient_id,
            admission_id=event.admission_id,
            event_type="DEADLINE_MISSED",
            actor_user_id=created_by_user_id,
            reason=variance_reason,
        )
    db.flush()
    return assignment


def record_interim_support(
    db,
    *,
    event: PatientResponseEvent,
    support_type: str,
    provided_at: datetime,
    provided_by_user_id=None,
    notes: str | None = None,
) -> InterimPatientSupport:
    """
    Telephone/video/caregiver-coaching support while awaiting in-person
    arrival. Never sets arrived_at and never satisfies the in-person
    arrival requirement.
    """
    support = InterimPatientSupport(
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        support_type=support_type,
        provided_at=provided_at,
        provided_by_user_id=provided_by_user_id,
        notes=notes,
        created_by=provided_by_user_id,
    )
    db.add(support)
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="INTERIM_SUPPORT_RECORDED",
        actor_user_id=provided_by_user_id,
        new_value={"support_type": support_type, "provided_at": provided_at.isoformat()},
    )
    db.flush()
    return support


def record_intervention(
    db,
    *,
    event: PatientResponseEvent,
    assignment: NurseResponseAssignment | None,
    intervention_type: str,
    description: str,
    performed_at: datetime,
    performed_by_user_id=None,
) -> ResponseIntervention:
    """Assessment/intervention performed once the nurse has arrived in person."""
    intervention = ResponseIntervention(
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        nurse_response_assignment_id=assignment.id if assignment else None,
        intervention_type=intervention_type,
        description=description,
        performed_at=performed_at,
        performed_by_user_id=performed_by_user_id,
        created_by=performed_by_user_id,
    )
    db.add(intervention)
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="INTERVENTION_RECORDED",
        actor_user_id=performed_by_user_id,
        new_value={"intervention_type": intervention_type},
    )
    db.flush()
    return intervention


def record_patient_response(
    db,
    *,
    event: PatientResponseEvent,
    intervention: ResponseIntervention,
    patient_response_recorded_at: datetime,
    patient_response_summary: str,
    actor_user_id=None,
) -> ResponseIntervention:
    """
    Records the patient's response to the intervention. Task completion or
    visit completion alone does NOT satisfy this -- callers must supply a
    real, observed patient response.
    """
    intervention.patient_response_recorded_at = patient_response_recorded_at
    intervention.patient_response_summary = patient_response_summary
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="PATIENT_RESPONSE_RECORDED",
        actor_user_id=actor_user_id,
        new_value={
            "patient_response_recorded_at": patient_response_recorded_at.isoformat(),
            "patient_response_summary": patient_response_summary,
        },
    )
    db.flush()
    return intervention


def record_idg_notification(
    db, *, event: PatientResponseEvent, intervention: ResponseIntervention, idg_notified_at: datetime, actor_user_id=None
) -> ResponseIntervention:
    """IDG notification never stops the clock and never substitutes for patient response."""
    intervention.idg_notified_at = idg_notified_at
    db.flush()
    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="IDG_NOTIFIED",
        actor_user_id=actor_user_id,
        new_value={"idg_notified_at": idg_notified_at.isoformat()},
    )
    db.flush()
    return intervention


def close_patient_response_event(
    db, *, event: PatientResponseEvent, closed_at: datetime, actor_user_id=None
) -> PatientResponseEvent:
    """
    Clinical closure requires:
      - at least one in-person arrival (an assignment with arrived_at set), and
      - (when closure_requires_patient_response, the default) at least one
        intervention with a recorded patient response.
    Task completion or visit completion alone is never sufficient.
    """
    has_arrival = any(a.arrived_at is not None for a in event.assignments)
    if not has_arrival:
        raise TwoHourResponseError("Cannot close: no in-person nurse arrival has been recorded")

    if event.closure_requires_patient_response:
        has_patient_response = any(i.patient_response_recorded_at is not None for i in event.interventions)
        if not has_patient_response:
            raise TwoHourResponseError("Cannot close: no patient response has been recorded")

    event.closed_at = closed_at
    db.flush()

    _audit(
        db,
        tenant_id=event.tenant_id,
        patient_response_event_id=event.id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        event_type="RECORD_FINALIZED",
        actor_user_id=actor_user_id,
        new_value={"closed_at": closed_at.isoformat()},
    )
    db.flush()
    return event
