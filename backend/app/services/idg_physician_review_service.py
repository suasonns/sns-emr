"""
IDG physician review + batch-signature-queue service.

Implements the Hospice IDG Physician Review Workflow:

    1. Each patient discussed in IDG must have a Review Status:
       Reviewed or Deferred (required before closing the discussion).
    2. Only Reviewed patients may enter the Batch Signature Queue.
    3. Deferred patients are automatically excluded from batch-sign.
    4. Batch signing applies individual electronic signatures (via the
       existing physician_order_service.approve_order pipeline) to every
       eligible pending order for each Reviewed patient, each order
       getting its own signature timestamp.
    5. Review Status and Signature Status are separate workflow states —
       this service only ever reads/writes review_status/reviewed_at on
       IDGMeetingPatientReview; actual order signatures are recorded on
       PhysicianOrder by physician_order_service.approve_order.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.idg_meeting import IDGMeeting
from app.models.idg_meeting_patient_review import IDGMeetingPatientReview
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet as PatientFacesheet
from app.models.physician_order import PhysicianOrder
from app.models.task import Task
from app.models.enums import TaskType, TaskOrigin, TaskDiscipline, TaskStatus, CompletionReferenceType
from app.services import physician_order_service as order_svc

VALID_REVIEW_STATUSES = {"PENDING", "REVIEWED", "DEFERRED"}

VALID_DEFER_REASONS = {
    "NEED_MORE_INFORMATION",
    "NEED_TO_REVIEW_CHART",
    "NEED_TO_CONTACT_ATTENDING_PHYSICIAN",
    "NEED_LABS_RESULTS",
    "NEED_FAMILY_CAREGIVER_CLARIFICATION",
    "MEDICATION_ISSUE_UNRESOLVED",
    "OTHER",
}

# Orders in these statuses are the ones a Medical Director signature
# actually advances (drafted/pending sign-off from IDG discussion).
SIGNABLE_ORDER_STATUSES = ("PENDING_HOSPICE_MD_APPROVAL",)


class IDGPhysicianReviewError(Exception):
    """Raised when a review/batch-sign operation is not allowed."""


def _get_meeting_or_raise(db: Session, *, tenant_id, idg_meeting_id) -> IDGMeeting:
    meeting = (
        db.query(IDGMeeting)
        .filter(IDGMeeting.id == idg_meeting_id, IDGMeeting.tenant_id == tenant_id)
        .first()
    )
    if not meeting:
        raise IDGPhysicianReviewError("IDG session not found")
    return meeting


def list_idg_meeting_dates(db: Session, *, tenant_id) -> list[dict]:
    """
    Tenant-wide "IDG Meeting Workspace" list view. IDGMeeting rows are
    scheduled per-patient (see idg_meeting_scheduler.generate_idg_meetings),
    so a shared meeting_date is the de-facto session-grouping key: every
    IDGMeeting sharing a date across the tenant is "one IDG meeting" from
    the facilitator/physician's point of view — e.g. "IDG Meeting: Aug 19
    | 32 Patients".
    """
    rows = (
        db.query(IDGMeeting.meeting_date, func.count(IDGMeeting.id))
        .filter(IDGMeeting.tenant_id == tenant_id)
        .group_by(IDGMeeting.meeting_date)
        .order_by(IDGMeeting.meeting_date.desc())
        .all()
    )
    return [
        {"meeting_date": meeting_date.isoformat(), "patient_count": count}
        for meeting_date, count in rows
    ]


def list_patients_for_meeting_date(db: Session, *, tenant_id, meeting_date) -> list[dict]:
    """
    All patients scheduled for IDG on a given shared meeting_date,
    each with their own per-patient IDGMeeting.id (idg_meeting_id) plus
    their current IDGMeetingPatientReview status (defaults to PENDING
    when no review row exists yet — i.e. not yet opened/discussed).
    """
    meetings = (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.meeting_date == meeting_date,
        )
        .all()
    )
    if not meetings:
        raise IDGPhysicianReviewError("No IDG meetings found for that meeting_date")

    meeting_ids = [m.id for m in meetings]
    patient_ids = [m.patient_id for m in meetings if m.patient_id]

    reviews_by_meeting_id = {
        r.idg_meeting_id: r
        for r in db.query(IDGMeetingPatientReview)
        .filter(IDGMeetingPatientReview.idg_meeting_id.in_(meeting_ids))
        .all()
    }
    facesheets_by_patient_id = {
        f.patient_id: f
        for f in db.query(PatientFacesheet)
        .filter(PatientFacesheet.patient_id.in_(patient_ids))
        .all()
    }
    patients_by_id = {
        p.id: p
        for p in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    }

    results = []
    for meeting in meetings:
        review = reviews_by_meeting_id.get(meeting.id)
        facesheet = facesheets_by_patient_id.get(meeting.patient_id)
        patient = patients_by_id.get(meeting.patient_id)
        display_name = None
        if facesheet and (facesheet.first_name or facesheet.last_name):
            display_name = f"{facesheet.last_name or ''}, {facesheet.first_name or ''}".strip(", ")
        results.append(
            {
                "idg_meeting_id": str(meeting.id),
                "patient_id": str(meeting.patient_id) if meeting.patient_id else None,
                "patient_name": display_name,
                "mrn": patient.mrn if patient else None,
                "meeting_status": meeting.status,
                "review_status": review.review_status if review else "PENDING",
                "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
                "defer_reason": review.defer_reason if review else None,
                "batch_signed_at": review.batch_signed_at.isoformat() if review and review.batch_signed_at else None,
            }
        )
    return results


def get_review(
    db: Session, *, tenant_id, idg_meeting_id, patient_id
) -> Optional[IDGMeetingPatientReview]:
    return (
        db.query(IDGMeetingPatientReview)
        .filter(
            IDGMeetingPatientReview.tenant_id == tenant_id,
            IDGMeetingPatientReview.idg_meeting_id == idg_meeting_id,
            IDGMeetingPatientReview.patient_id == patient_id,
        )
        .first()
    )


def list_reviews_for_session(
    db: Session, *, tenant_id, idg_meeting_id
) -> list[IDGMeetingPatientReview]:
    _get_meeting_or_raise(db, tenant_id=tenant_id, idg_meeting_id=idg_meeting_id)
    return (
        db.query(IDGMeetingPatientReview)
        .filter(
            IDGMeetingPatientReview.tenant_id == tenant_id,
            IDGMeetingPatientReview.idg_meeting_id == idg_meeting_id,
        )
        .order_by(IDGMeetingPatientReview.reviewed_at.desc())
        .all()
    )


def _sync_deferred_md_review_task(db: Session, *, review: IDGMeetingPatientReview) -> None:
    """
    Rule (defer alert): when a patient is Deferred, create/keep-open a
    reminder task assigned to the MD role so the deferral doesn't
    silently disappear — the physician must come back and review/sign
    it later. It is intentionally NOT part of the Batch Signature Queue.
    When the patient is subsequently marked Reviewed (or reverted to
    Pending), auto-complete that task.
    """
    existing_task = (
        db.query(Task)
        .filter(
            Task.reference_type == "IDG_PATIENT_REVIEW",
            Task.reference_id == review.id,
            Task.task_type == TaskType.IDG_DEFERRED_MD_REVIEW,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.OVERDUE]),
        )
        .first()
    )

    if review.review_status == "DEFERRED":
        if existing_task:
            return  # already alerted, avoid duplicate open tasks
        task = Task(
            tenant_id=review.tenant_id,
            patient_id=review.patient_id,
            created_by=review.recorded_by_user_id or review.physician_user_id,
            task_type=TaskType.IDG_DEFERRED_MD_REVIEW,
            origin=TaskOrigin.MANUAL,
            discipline=TaskDiscipline.MD,
            assigned_role="MD",
            status=TaskStatus.PENDING,
            due_at=datetime.now(timezone.utc) + timedelta(days=3),
            reference_type="IDG_PATIENT_REVIEW",
            reference_id=review.id,
            alert_reason=(
                "Patient deferred during IDG — requires physician review and "
                "signature; excluded from batch signing until resolved."
                + (f" Reason: {review.defer_reason}" if review.defer_reason else "")
            ),
        )
        db.add(task)
    else:
        # Moved to REVIEWED or back to PENDING — the defer alert is resolved.
        if existing_task and existing_task.status != TaskStatus.COMPLETED:
            existing_task.status = TaskStatus.COMPLETED
            existing_task.completed_at = datetime.now(timezone.utc)
            existing_task.completion_reference_type = CompletionReferenceType.IDG_PATIENT_REVIEW
            existing_task.completion_reference_id = review.id
            db.add(existing_task)


def set_review_status(
    db: Session,
    *,
    tenant_id,
    idg_meeting_id,
    patient_id,
    physician_user_id,
    review_status: str,
    recorded_by_user_id=None,
    reviewed_by_physician_directly: bool = False,
    review_source: str = "IDG",
    defer_reason: Optional[str] = None,
    defer_note: Optional[str] = None,
    poc_reviewed: bool = False,
    medication_list_reviewed: bool = False,
    medication_reconciliation_reviewed: bool = False,
    orders_reviewed: bool = False,
    discussion_reviewed: bool = False,
    notes: Optional[str] = None,
) -> IDGMeetingPatientReview:
    """
    Rule 1/2/5: record (or update) the physician's Reviewed/Deferred
    decision for one patient in one IDG session. Required before that
    patient's discussion can be considered closed.

    Audit-trail safety: `recorded_by_user_id` is whoever actually clicked
    the button (often the facilitator/RN during IDG). `physician_user_id`
    is the physician of record. `reviewed_by_physician_directly` is only
    True when the physician personally authenticated and clicked it
    themselves — never inferred, never assumed.
    """
    _get_meeting_or_raise(db, tenant_id=tenant_id, idg_meeting_id=idg_meeting_id)

    status = (review_status or "").strip().upper()
    if status not in VALID_REVIEW_STATUSES:
        raise IDGPhysicianReviewError(
            f"review_status must be one of {sorted(VALID_REVIEW_STATUSES)}"
        )

    reason = (defer_reason or "").strip().upper() or None
    if status == "DEFERRED":
        if not reason:
            raise IDGPhysicianReviewError("defer_reason is required when review_status is DEFERRED")
        if reason not in VALID_DEFER_REASONS:
            raise IDGPhysicianReviewError(f"defer_reason must be one of {sorted(VALID_DEFER_REASONS)}")

    review = get_review(
        db, tenant_id=tenant_id, idg_meeting_id=idg_meeting_id, patient_id=patient_id
    )
    now = datetime.now(timezone.utc)

    if review:
        review.review_status = status
        review.physician_user_id = physician_user_id
        review.recorded_by_user_id = recorded_by_user_id
        review.reviewed_by_physician_directly = bool(reviewed_by_physician_directly)
        review.review_source = review_source or "IDG"
        review.reviewed_at = now
        review.notes = notes
        review.defer_reason = reason if status == "DEFERRED" else None
        review.defer_note = defer_note if status == "DEFERRED" else None
        review.poc_reviewed = poc_reviewed
        review.medication_list_reviewed = medication_list_reviewed
        review.medication_reconciliation_reviewed = medication_reconciliation_reviewed
        review.orders_reviewed = orders_reviewed
        review.discussion_reviewed = discussion_reviewed
        # Re-deferring or re-reviewing resets prior batch-sign bookkeeping
        # only when moving away from REVIEWED — leaves an accurate trail.
        if status == "DEFERRED":
            review.batch_signed_at = None
    else:
        review = IDGMeetingPatientReview(
            tenant_id=tenant_id,
            patient_id=patient_id,
            idg_meeting_id=idg_meeting_id,
            physician_user_id=physician_user_id,
            recorded_by_user_id=recorded_by_user_id,
            reviewed_by_physician_directly=bool(reviewed_by_physician_directly),
            review_source=review_source or "IDG",
            review_status=status,
            reviewed_at=now,
            notes=notes,
            defer_reason=reason if status == "DEFERRED" else None,
            defer_note=defer_note if status == "DEFERRED" else None,
            poc_reviewed=poc_reviewed,
            medication_list_reviewed=medication_list_reviewed,
            medication_reconciliation_reviewed=medication_reconciliation_reviewed,
            orders_reviewed=orders_reviewed,
            discussion_reviewed=discussion_reviewed,
        )
        db.add(review)
        db.flush()  # assign review.id before the task references it

    _sync_deferred_md_review_task(db, review=review)

    db.commit()
    db.refresh(review)
    return review


def _signable_orders_for_patient(db: Session, *, tenant_id, patient_id) -> list[PhysicianOrder]:
    return (
        db.query(PhysicianOrder)
        .filter(
            PhysicianOrder.tenant_id == tenant_id,
            PhysicianOrder.patient_id == patient_id,
            PhysicianOrder.status.in_(SIGNABLE_ORDER_STATUSES),
        )
        .order_by(PhysicianOrder.ordered_at.asc())
        .all()
    )


def get_batch_signature_queue(
    db: Session, *, tenant_id, idg_meeting_id
) -> list[dict]:
    """
    Rule 2/3/4: only Reviewed patients (deferred ones automatically
    excluded, per query filter) with pending physician orders.
    """
    _get_meeting_or_raise(db, tenant_id=tenant_id, idg_meeting_id=idg_meeting_id)

    reviewed = (
        db.query(IDGMeetingPatientReview)
        .filter(
            IDGMeetingPatientReview.tenant_id == tenant_id,
            IDGMeetingPatientReview.idg_meeting_id == idg_meeting_id,
            IDGMeetingPatientReview.review_status == "REVIEWED",
        )
        .all()
    )

    queue = []
    for review in reviewed:
        orders = _signable_orders_for_patient(
            db, tenant_id=tenant_id, patient_id=review.patient_id
        )
        if not orders:
            continue
        queue.append(
            {
                "patient_id": str(review.patient_id),
                "review_id": str(review.id),
                "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
                "physician_user_id": str(review.physician_user_id),
                "orders": orders,
            }
        )
    return queue


def batch_sign(
    db: Session,
    *,
    tenant_id,
    idg_meeting_id,
    physician_user_id,
    patient_ids: Optional[Iterable[uuid.UUID]] = None,
    signature_method: str = "ELECTRONIC",
) -> dict:
    """
    Rule 6/7: apply an individual electronic signature to every eligible
    pending order for every Reviewed (never Deferred) patient in the
    session's Batch Signature Queue, each order recording its own
    signature timestamp via physician_order_service.approve_order.
    """
    queue = get_batch_signature_queue(db, tenant_id=tenant_id, idg_meeting_id=idg_meeting_id)

    allowed_patient_ids = None
    if patient_ids is not None:
        allowed_patient_ids = {str(p) for p in patient_ids}

    signed = []
    failed = []
    skipped_patients = 0

    for entry in queue:
        if allowed_patient_ids is not None and entry["patient_id"] not in allowed_patient_ids:
            skipped_patients += 1
            continue

        any_signed_for_patient = False
        for order in entry["orders"]:
            try:
                signed_order = order_svc.approve_order(
                    db,
                    order=order,
                    approved_by=physician_user_id,
                    signature_method=signature_method,
                )
                any_signed_for_patient = True
                signed.append(
                    {
                        "order_id": str(signed_order.id),
                        "patient_id": entry["patient_id"],
                        "signed_at": signed_order.signed_at.isoformat()
                        if signed_order.signed_at
                        else None,
                    }
                )
            except order_svc.PhysicianOrderError as exc:
                failed.append(
                    {
                        "order_id": str(order.id),
                        "patient_id": entry["patient_id"],
                        "error": str(exc),
                    }
                )

        if any_signed_for_patient:
            review = get_review(
                db,
                tenant_id=tenant_id,
                idg_meeting_id=idg_meeting_id,
                patient_id=entry["patient_id"],
            )
            if review:
                review.batch_signed_at = datetime.now(timezone.utc)
                db.add(review)

    db.commit()

    return {
        "signed_count": len(signed),
        "failed_count": len(failed),
        "skipped_patients": skipped_patients,
        "signed": signed,
        "failed": failed,
    }
