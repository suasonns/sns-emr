from __future__ import annotations

"""
IDG patient-outcome follow-up service (issue #143 layer). Extends the
existing idg_reviews table (does NOT create a second idg_follow_ups
table) -- distinct from app.services.idg_review_service, which handles
IDGMeeting-driven POC finalization and ICA task auto-completion. This
module only concerns follow-up tracking added for the Clinical
Outcome/IDG compliance work.

The IDG owns coordinated patient care -- no single discipline is ever
stored as the sole "owner" of a patient outcome; individuals may receive
assigned follow-up actions, but assigned-action ownership is not patient
ownership.
"""

from datetime import datetime

from app.models.idg_review import IDGReview, IDGReviewAuditEvent
from app.models.record_version import RecordVersion

RECORD_TYPE = "IDG_REVIEW"


class IDGFollowUpError(RuntimeError):
    pass


def _audit(
    db,
    *,
    tenant_id,
    idg_review_id,
    patient_id,
    admission_id,
    event_type,
    actor_user_id=None,
    actor_account_discipline=None,
    prior_value=None,
    new_value=None,
    reason=None,
):
    row = IDGReviewAuditEvent(
        tenant_id=tenant_id,
        idg_review_id=idg_review_id,
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


def _snapshot(review: IDGReview) -> dict:
    return {
        "follow_up_status": review.follow_up_status,
        "follow_up_assigned_to_user_id": str(review.follow_up_assigned_to_user_id)
        if review.follow_up_assigned_to_user_id
        else None,
        "follow_up_assigned_at": review.follow_up_assigned_at.isoformat() if review.follow_up_assigned_at else None,
        "desired_patient_outcome": review.desired_patient_outcome,
        "follow_up_action": review.follow_up_action,
        "follow_up_due_date": review.follow_up_due_date.isoformat() if review.follow_up_due_date else None,
        "continuing_plan": review.continuing_plan,
        "closure_summary": review.closure_summary,
    }


def get_idg_follow_up(db, *, tenant_id, idg_review_id) -> IDGReview:
    """tenant_id is normalized to str() -- see clinical_outcome_service.get_outcome_record for why."""
    review = db.get(IDGReview, idg_review_id)
    if review is None or str(review.tenant_id) != str(tenant_id):
        raise IDGFollowUpError(f"IDG review {idg_review_id} not found")
    return review


def create_idg_follow_up(
    db,
    *,
    tenant_id,
    patient_id,
    benefit_period_id=None,
    desired_patient_outcome: str,
    follow_up_action: str,
    follow_up_due_date: datetime,
    source_patient_response_event_id=None,
    source_clinical_outcome_record_id=None,
    created_by_user_id,
    actor_account_discipline: str | None = None,
) -> IDGReview:
    """
    Creates the IDG follow-up record (reuses idg_reviews rather than a
    second parallel table). desired_patient_outcome, follow_up_action,
    and follow_up_due_date are required -- a follow-up is not actionable
    without them. Must originate from a response event or clinical
    outcome record.
    """
    if not desired_patient_outcome:
        raise IDGFollowUpError("desired_patient_outcome is required")
    if not follow_up_action:
        raise IDGFollowUpError("follow_up_action is required")
    if follow_up_due_date is None:
        raise IDGFollowUpError("follow_up_due_date is required")
    if source_patient_response_event_id is None and source_clinical_outcome_record_id is None:
        raise IDGFollowUpError("A follow-up must be linked to a source response event or clinical outcome record")

    review = IDGReview(
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        follow_up_required=True,
        follow_up_status=None,
        desired_patient_outcome=desired_patient_outcome,
        follow_up_action=follow_up_action,
        follow_up_due_date=follow_up_due_date,
        source_patient_response_event_id=source_patient_response_event_id,
        source_clinical_outcome_record_id=source_clinical_outcome_record_id,
        created_by=created_by_user_id,
    )
    db.add(review)
    db.flush()

    _audit(
        db,
        tenant_id=tenant_id,
        idg_review_id=review.id,
        patient_id=patient_id,
        admission_id=None,
        event_type="IDG_FOLLOW_UP_CREATED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "desired_patient_outcome": desired_patient_outcome,
            "follow_up_action": follow_up_action,
            "follow_up_due_date": follow_up_due_date.isoformat(),
        },
    )
    db.flush()
    return review


def record_idg_recommendation(
    db, *, review: IDGReview, summary: str, actor_user_id, actor_account_discipline: str | None = None
) -> IDGReview:
    """Multiple disciplines may each contribute a recommendation; this never assigns sole ownership."""
    review.summary = summary
    db.flush()
    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="IDG_RECOMMENDATION_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"summary": summary},
    )
    db.flush()
    return review


def assign_follow_up(
    db,
    *,
    review: IDGReview,
    assigned_to_user_id,
    assigned_at: datetime,
    actor_user_id,
    actor_account_discipline: str | None = None,
    reassignment_reason: str | None = None,
) -> IDGReview:
    """
    Assigns (or reassigns) the follow-up action to an individual staff
    member or a team account (both stored via the same
    follow_up_assigned_to_user_id field). Assignment is an operational
    action-owner, never a patient-outcome owner. Reassignment requires a
    reason and preserves the prior assignment via a RecordVersion
    snapshot.
    """
    is_reassignment = review.follow_up_assigned_to_user_id is not None
    if is_reassignment and not reassignment_reason:
        raise IDGFollowUpError("reassignment_reason is required when reassigning an existing follow-up")

    prior_snapshot = _snapshot(review)
    if is_reassignment:
        existing_version_count = (
            db.query(RecordVersion)
            .filter(
                RecordVersion.tenant_id == review.tenant_id,
                RecordVersion.source_record_type == RECORD_TYPE,
                RecordVersion.source_record_id == review.id,
            )
            .count()
        )
        db.add(
            RecordVersion(
                tenant_id=review.tenant_id,
                source_record_type=RECORD_TYPE,
                source_record_id=review.id,
                version_number=existing_version_count + 1,
                snapshot=prior_snapshot,
                change_reason=reassignment_reason,
                created_by=actor_user_id,
            )
        )

    review.follow_up_assigned_to_user_id = assigned_to_user_id
    review.follow_up_assigned_at = assigned_at
    if review.follow_up_status != "COMPLETED":
        review.follow_up_status = "ASSIGNED"
    db.flush()

    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="FOLLOW_UP_REASSIGNED" if is_reassignment else "FOLLOW_UP_ASSIGNED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_snapshot if is_reassignment else None,
        new_value={"assigned_to_user_id": str(assigned_to_user_id), "assigned_at": assigned_at.isoformat()},
        reason=reassignment_reason,
    )
    db.flush()
    return review


def record_progress(
    db, *, review: IDGReview, notes: str, actor_user_id, actor_account_discipline: str | None = None
) -> IDGReview:
    review.follow_up_status = "IN_PROGRESS"
    review.poc_action = notes
    db.flush()
    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="FOLLOW_UP_PROGRESS_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"follow_up_status": "IN_PROGRESS", "notes": notes},
    )
    db.flush()
    return review


def link_patient_response(
    db,
    *,
    review: IDGReview,
    clinical_outcome_record_id,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> IDGReview:
    """Links the clinical-outcome record carrying the recorded patient response -- the clinical completion criterion."""
    review.source_clinical_outcome_record_id = clinical_outcome_record_id
    db.flush()
    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="PATIENT_RESPONSE_LINKED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"clinical_outcome_record_id": str(clinical_outcome_record_id)},
    )
    db.flush()
    return review


def complete_follow_up(
    db,
    *,
    review: IDGReview,
    closure_summary: str,
    completed_at: datetime,
    remaining_need: bool = False,
    continuing_plan: str | None = None,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> IDGReview:
    """
    Rejects completion unless: a clinical outcome record is linked (the
    caller is responsible for having verified the linked record's
    response_recorded_at/patient_response_status via
    clinical_outcome_service before calling this), the desired outcome is
    documented, and a closure_summary is supplied. Persistent/worsening
    need requires a continuing_plan.
    """
    if review.source_clinical_outcome_record_id is None:
        raise IDGFollowUpError("Cannot complete follow-up: no linked clinical outcome record")
    if not review.desired_patient_outcome:
        raise IDGFollowUpError("Cannot complete follow-up: desired_patient_outcome is not documented")
    if not closure_summary:
        raise IDGFollowUpError("closure_summary is required to complete a follow-up")
    if remaining_need and not continuing_plan:
        raise IDGFollowUpError("Persistent/worsening need requires a continuing_plan before completion")

    review.follow_up_status = "COMPLETED"
    review.follow_up_completed_at = completed_at
    review.closure_summary = closure_summary
    if continuing_plan:
        review.continuing_plan = continuing_plan
    db.flush()

    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="FOLLOW_UP_COMPLETED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"closure_summary": closure_summary, "completed_at": completed_at.isoformat()},
    )
    db.flush()
    return review


def reopen_follow_up(
    db,
    *,
    review: IDGReview,
    reopen_reason: str,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> IDGReview:
    if review.follow_up_status != "COMPLETED":
        raise IDGFollowUpError("Cannot reopen: follow-up is not COMPLETED")
    if not reopen_reason:
        raise IDGFollowUpError("reopen_reason is required")
    if not actor_user_id:
        raise IDGFollowUpError("An authorized actor is required to reopen a follow-up")

    prior_snapshot = _snapshot(review)
    review.reopened_at = datetime.utcnow()
    review.reopened_by = actor_user_id
    review.reopen_reason = reopen_reason
    review.follow_up_status = "IN_PROGRESS"
    review.follow_up_completed_at = None
    db.flush()

    _audit(
        db,
        tenant_id=review.tenant_id,
        idg_review_id=review.id,
        patient_id=review.patient_id,
        admission_id=None,
        event_type="FOLLOW_UP_REOPENED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_snapshot,
        new_value=_snapshot(review),
        reason=reopen_reason,
    )
    db.flush()
    return review
