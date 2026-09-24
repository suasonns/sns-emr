from __future__ import annotations

"""
Clinical Outcome service (issue #143 layer). Tracks whether the patient
was appropriately cared for (primary evaluation criterion) independent of
which discipline performed the work -- discipline identifies who did the
work, it never determines ownership of the patient outcome. IDG remains
responsible for patient outcomes (see app.services.idg_review_service).

Identity rule enforced by construction: every mutating function here only
accepts actor_user_id/actor_account_discipline as explicit parameters
sourced by the caller from the AUTHENTICATED ACCOUNT. This module never
reads a discipline value from visit or task metadata -- callers must not
pass visit/task discipline fields into actor_account_discipline.
"""

import uuid
from datetime import datetime

from app.models.clinical_outcome import ClinicalOutcomeAuditEvent, ClinicalOutcomeRecord
from app.models.record_version import RecordVersion

RECORD_TYPE = "CLINICAL_OUTCOME_RECORD"

# Outcome statuses whose closure/finalization requires remaining_need_identified.
STATUSES_REQUIRING_REMAINING_NEED = ("PERSISTENT", "WORSENED", "CLOSED_WITH_ONGOING_PLAN")

# Statuses that represent IDG follow-up being required/in-flight.
IDG_FOLLOW_UP_STATUSES = ("IDG_FOLLOW_UP_REQUIRED", "IDG_FOLLOW_UP_ASSIGNED", "IDG_FOLLOW_UP_COMPLETED")


class ClinicalOutcomeError(RuntimeError):
    pass


def get_outcome_record(db, *, tenant_id, record_id) -> ClinicalOutcomeRecord:
    """Tenant-scoped lookup -- the only sanctioned way to fetch a record for mutation from an API layer.

    tenant_id is normalized to str() before comparison: callers may pass either a
    uuid.UUID or a str (e.g. a JWT-derived tenant claim), and record.tenant_id is a
    real uuid.UUID once loaded via the ORM -- comparing them directly with `!=`
    would always be "not equal" for a str argument, producing a false not-found.
    """
    record = db.get(ClinicalOutcomeRecord, record_id)
    if record is None or str(record.tenant_id) != str(tenant_id):
        raise ClinicalOutcomeError(f"Clinical outcome record {record_id} not found")
    return record


def _audit(
    db,
    *,
    tenant_id,
    clinical_outcome_record_id,
    patient_id,
    admission_id,
    event_type,
    actor_user_id=None,
    actor_account_discipline=None,
    prior_value=None,
    new_value=None,
    reason=None,
):
    row = ClinicalOutcomeAuditEvent(
        tenant_id=tenant_id,
        clinical_outcome_record_id=clinical_outcome_record_id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(row)
    return row


def _snapshot(record: ClinicalOutcomeRecord) -> dict:
    return {
        "outcome_status": record.outcome_status,
        "patient_appropriately_cared_for": record.patient_appropriately_cared_for,
        "patient_response_status": record.patient_response_status,
        "remaining_need_identified": record.remaining_need_identified,
        "idg_communicated": record.idg_communicated,
        "intervention_timely": record.intervention_timely,
        "documentation_complete": record.documentation_complete,
        "response_recorded_at": record.response_recorded_at.isoformat() if record.response_recorded_at else None,
        "closed_at": record.closed_at.isoformat() if record.closed_at else None,
        "notes": record.notes,
    }


def _require_open(record: ClinicalOutcomeRecord):
    if record.closed_at is not None:
        raise ClinicalOutcomeError(
            "Cannot mutate a finalized clinical outcome record directly -- use correct_outcome() or reopen_outcome()."
        )


def create_outcome_from_patient_response_event(
    db,
    *,
    event,
    actor_user_id,
    actor_account_discipline: str,
    source_task_id=None,
    source_visit_id=None,
) -> ClinicalOutcomeRecord:
    """
    Creates a ClinicalOutcomeRecord linked to a patient/admission/source
    event. actor_account_discipline MUST come from the authenticated
    account -- callers must never pass a discipline value read from visit
    or task metadata; this function has no way to distinguish a
    mislabeled value, so the discipline of the call site is the control.
    """
    if not actor_account_discipline:
        raise ClinicalOutcomeError("actor_account_discipline (from the authenticated account) is required")

    record = ClinicalOutcomeRecord(
        tenant_id=event.tenant_id,
        patient_id=event.patient_id,
        admission_id=event.admission_id,
        benefit_period_id=event.benefit_period_id,
        patient_response_event_id=event.id,
        source_task_id=source_task_id,
        source_visit_id=source_visit_id,
        outcome_status="IDENTIFIED",
        created_by=actor_user_id,
        created_by_account_discipline=actor_account_discipline,
    )
    db.add(record)
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="OUTCOME_CREATED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"outcome_status": "IDENTIFIED", "patient_response_event_id": str(event.id)},
    )
    db.flush()
    return record


def record_intervention(
    db,
    *,
    record: ClinicalOutcomeRecord,
    intervention_timely: bool | None = None,
    actor_user_id,
    actor_account_discipline: str,
    notes: str | None = None,
) -> ClinicalOutcomeRecord:
    """
    Recording an intervention alone never advances the outcome to a
    resolved/closed status and never satisfies patient-response
    requirements -- it only records that intervention activity occurred.
    """
    _require_open(record)
    record.outcome_status = "INTERVENTION_IN_PROGRESS"
    if intervention_timely is not None:
        record.intervention_timely = intervention_timely
    if notes:
        record.notes = notes
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="INTERVENTION_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"outcome_status": "INTERVENTION_IN_PROGRESS", "intervention_timely": intervention_timely},
    )
    db.flush()
    return record


def record_patient_response(
    db,
    *,
    record: ClinicalOutcomeRecord,
    patient_response_status: str,
    response_recorded_at: datetime,
    patient_appropriately_cared_for: bool | None = None,
    remaining_need_identified: bool = False,
    actor_user_id,
    actor_account_discipline: str,
) -> ClinicalOutcomeRecord:
    """
    Records the patient's actual, observed response. This is the only
    function that may set response_recorded_at/patient_response_status --
    task completion and visit completion never satisfy this requirement.
    """
    _require_open(record)
    if patient_response_status in ("PERSISTENT", "WORSENED") and not remaining_need_identified:
        raise ClinicalOutcomeError(
            f"{patient_response_status} requires remaining_need_identified=True"
        )

    record.patient_response_status = patient_response_status
    record.response_recorded_at = response_recorded_at
    record.remaining_need_identified = remaining_need_identified
    if patient_appropriately_cared_for is not None:
        record.patient_appropriately_cared_for = patient_appropriately_cared_for
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="PATIENT_RESPONSE_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "patient_response_status": patient_response_status,
            "response_recorded_at": response_recorded_at.isoformat(),
            "remaining_need_identified": remaining_need_identified,
        },
    )
    if remaining_need_identified:
        _audit(
            db,
            tenant_id=record.tenant_id,
            clinical_outcome_record_id=record.id,
            patient_id=record.patient_id,
            admission_id=record.admission_id,
            event_type="REMAINING_NEED_RECORDED",
            actor_user_id=actor_user_id,
            actor_account_discipline=actor_account_discipline,
            new_value={"remaining_need_identified": True},
        )
    db.flush()
    return record


def change_outcome_status(
    db,
    *,
    record: ClinicalOutcomeRecord,
    new_status: str,
    actor_user_id,
    actor_account_discipline: str,
    reason: str | None = None,
) -> ClinicalOutcomeRecord:
    """
    Changes the controlled outcome_status. Statuses requiring
    remaining_need_identified are enforced here as well as at the DB
    check-constraint layer (defense in depth).
    """
    _require_open(record)
    if new_status not in ClinicalOutcomeRecord.OUTCOME_STATUSES:
        raise ClinicalOutcomeError(f"Unknown outcome_status: {new_status}")
    if new_status in STATUSES_REQUIRING_REMAINING_NEED and not record.remaining_need_identified:
        raise ClinicalOutcomeError(f"{new_status} requires remaining_need_identified=True")

    prior_status = record.outcome_status
    record.outcome_status = new_status
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="OUTCOME_STATUS_CHANGED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value={"outcome_status": prior_status},
        new_value={"outcome_status": new_status},
        reason=reason,
    )
    if new_status == "IDG_FOLLOW_UP_REQUIRED":
        _audit(
            db,
            tenant_id=record.tenant_id,
            clinical_outcome_record_id=record.id,
            patient_id=record.patient_id,
            admission_id=record.admission_id,
            event_type="IDG_FOLLOW_UP_REQUIRED",
            actor_user_id=actor_user_id,
            actor_account_discipline=actor_account_discipline,
        )
    db.flush()
    return record


def record_idg_communication(
    db,
    *,
    record: ClinicalOutcomeRecord,
    idg_communicated_at: datetime,
    idg_review_id=None,
    actor_user_id,
    actor_account_discipline: str,
) -> ClinicalOutcomeRecord:
    """IDG notification is a secondary-criterion signal; it never closes/finalizes the outcome by itself."""
    _require_open(record)
    prior = {"idg_communicated": record.idg_communicated, "idg_communicated_at": None, "idg_review_id": None}
    record.idg_communicated = True
    record.idg_communicated_at = idg_communicated_at
    if idg_review_id is not None:
        record.idg_review_id = idg_review_id
    db.flush()
    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="IDG_COMMUNICATION_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior,
        new_value={
            "idg_communicated": record.idg_communicated,
            "idg_communicated_at": idg_communicated_at.isoformat(),
            "idg_review_id": str(record.idg_review_id) if record.idg_review_id else None,
        },
    )
    db.flush()
    return record


def finalize_outcome(
    db,
    *,
    record: ClinicalOutcomeRecord,
    closed_at: datetime,
    actor_user_id,
    actor_account_discipline: str,
) -> ClinicalOutcomeRecord:
    """
    Finalizes (closes) the outcome record. Rejects finalization unless a
    real patient response has been recorded and, when the outcome is
    persistent/worsened/closed-with-ongoing-plan, a remaining need has
    been identified. Visit completion, task completion, IDG notification
    alone, and note signature alone are never sufficient -- none of those
    set response_recorded_at, so this check structurally rejects them.
    """
    if record.response_recorded_at is None:
        raise ClinicalOutcomeError("Cannot finalize: no patient response has been recorded")
    if record.outcome_status in STATUSES_REQUIRING_REMAINING_NEED and not record.remaining_need_identified:
        raise ClinicalOutcomeError(f"{record.outcome_status} requires remaining_need_identified=True before finalization")
    if record.closed_at is not None:
        raise ClinicalOutcomeError("Outcome record is already finalized")

    record.closed_at = closed_at
    record.closed_by = actor_user_id
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="OUTCOME_FINALIZED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"closed_at": closed_at.isoformat(), "outcome_status": record.outcome_status},
    )
    db.flush()
    return record


def correct_outcome(
    db,
    *,
    record: ClinicalOutcomeRecord,
    corrections: dict,
    correction_reason: str,
    actor_user_id,
    actor_account_discipline: str,
) -> ClinicalOutcomeRecord:
    """
    Applies a correction to a NON-finalized record while preserving the
    original values via a RecordVersion snapshot -- corrections never
    silently overwrite history. Finalized records must be reopened first
    (see reopen_outcome) before they can be corrected.
    """
    if record.closed_at is not None:
        raise ClinicalOutcomeError("Cannot silently correct a finalized outcome record -- reopen it first")
    if not correction_reason:
        raise ClinicalOutcomeError("correction_reason is required")

    prior_snapshot = _snapshot(record)
    existing_version_count = (
        db.query(RecordVersion)
        .filter(
            RecordVersion.tenant_id == record.tenant_id,
            RecordVersion.source_record_type == RECORD_TYPE,
            RecordVersion.source_record_id == record.id,
        )
        .count()
    )
    db.add(
        RecordVersion(
            tenant_id=record.tenant_id,
            source_record_type=RECORD_TYPE,
            source_record_id=record.id,
            version_number=existing_version_count + 1,
            snapshot=prior_snapshot,
            change_reason=correction_reason,
            created_by=actor_user_id,
        )
    )

    for field, value in corrections.items():
        if not hasattr(record, field):
            raise ClinicalOutcomeError(f"Unknown field for correction: {field}")
        setattr(record, field, value)
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="OUTCOME_CORRECTED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_snapshot,
        new_value=_snapshot(record),
        reason=correction_reason,
    )
    db.flush()
    return record


def reopen_outcome(
    db,
    *,
    record: ClinicalOutcomeRecord,
    reopen_reason: str,
    actor_user_id,
    actor_account_discipline: str,
) -> ClinicalOutcomeRecord:
    """Reopens a finalized outcome record. Requires a reason and an authorized actor."""
    if record.closed_at is None:
        raise ClinicalOutcomeError("Cannot reopen: outcome record is not finalized")
    if not reopen_reason:
        raise ClinicalOutcomeError("reopen_reason is required")
    if not actor_user_id:
        raise ClinicalOutcomeError("An authorized actor is required to reopen an outcome record")

    prior_snapshot = _snapshot(record)
    record.reopened_at = datetime.now(record.closed_at.tzinfo) if record.closed_at.tzinfo else datetime.utcnow()
    record.reopened_by = actor_user_id
    record.reopen_reason = reopen_reason
    record.closed_at = None
    record.closed_by = None
    db.flush()

    _audit(
        db,
        tenant_id=record.tenant_id,
        clinical_outcome_record_id=record.id,
        patient_id=record.patient_id,
        admission_id=record.admission_id,
        event_type="OUTCOME_REOPENED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_snapshot,
        new_value=_snapshot(record),
        reason=reopen_reason,
    )
    db.flush()
    return record
