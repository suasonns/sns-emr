# services/idg_meeting_scheduler.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.idg_meeting import IDGMeeting


FRIDAY = 4
MONDAY = 0
BIWEEKLY_INTERVAL_DAYS = 14


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_next_friday(start_date: datetime) -> datetime:
    """
    Return the next Friday after start_date.

    If start_date is already Friday, this returns the Friday one week later.
    """
    start_date = _as_aware_utc(start_date)
    days_ahead = FRIDAY - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def move_to_next_monday(date_value: datetime) -> datetime:
    """
    Move date_value to the next Monday.

    If date_value is already Monday, this returns the Monday one week later.
    """
    date_value = _as_aware_utc(date_value)
    days_ahead = MONDAY - date_value.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return date_value + timedelta(days=days_ahead)


def generate_idg_meetings(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    benefit_period_id: Optional[UUID],
    start_date: datetime,
    count: int = 12,
    created_by: Optional[UUID] = None,
) -> List[IDGMeeting]:
    """
    Generate biweekly IDG meeting records for one patient.

    This function is idempotent by patient, tenant, benefit period, and meeting date.
    It does not create IDG reviews.
    It does not modify POC.
    It only creates scheduled IDG meeting records when missing.
    """
    if count <= 0:
        return []

    first_meeting_date = get_next_friday(start_date)
    meetings: List[IDGMeeting] = []

    for index in range(count):
        meeting_date = first_meeting_date + timedelta(
            days=BIWEEKLY_INTERVAL_DAYS * index
        )

        existing = (
            db.query(IDGMeeting)
            .filter(
                IDGMeeting.tenant_id == tenant_id,
                IDGMeeting.patient_id == patient_id,
                IDGMeeting.benefit_period_id == benefit_period_id,
                IDGMeeting.meeting_date == meeting_date,
            )
            .first()
        )

        if existing:
            meetings.append(existing)
            continue

        meeting = IDGMeeting(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            meeting_date=meeting_date,
            status="SCHEDULED",
            created_by=created_by,
        )
        db.add(meeting)
        meetings.append(meeting)

    return meetings


def reschedule_meeting(
    db: Session,
    *,
    meeting_id: UUID,
    new_date: datetime,
    reason: Optional[str] = None,
) -> Optional[IDGMeeting]:
    """
    Reschedule an existing IDG meeting.

    This preserves the original date in rescheduled_from.
    """
    meeting = (
        db.query(IDGMeeting)
        .filter(IDGMeeting.id == meeting_id)
        .first()
    )
    if not meeting:
        return None

    meeting.rescheduled_from = meeting.meeting_date
    meeting.meeting_date = _as_aware_utc(new_date)
    meeting.rescheduled_reason = reason
    return meeting


def override_to_monday(
    db: Session,
    *,
    meeting_id: UUID,
    reason: str,
) -> Optional[IDGMeeting]:
    """
    Convenience override for moving an IDG date to the next Monday.
    """
    meeting = (
        db.query(IDGMeeting)
        .filter(IDGMeeting.id == meeting_id)
        .first()
    )
    if not meeting:
        return None

    new_date = move_to_next_monday(meeting.meeting_date)
    return reschedule_meeting(
        db=db,
        meeting_id=meeting_id,
        new_date=new_date,
        reason=reason,
    )


def adjust_for_holidays(
    meeting: IDGMeeting,
    holidays: List[datetime],
    reason: str = "Holiday adjustment",
) -> IDGMeeting:
    """
    If the meeting falls on a holiday date, move it to the next Monday.

    This mutates the provided meeting object but does not commit.
    """
    if not meeting or not meeting.meeting_date:
        return meeting

    meeting_date = _as_aware_utc(meeting.meeting_date)
    holiday_dates = {
        _as_aware_utc(value).date()
        for value in holidays
        if value is not None
    }

    if meeting_date.date() in holiday_dates:
        meeting.rescheduled_from = meeting.meeting_date
        meeting.meeting_date = move_to_next_monday(meeting_date)
        meeting.rescheduled_reason = reason

    return meeting