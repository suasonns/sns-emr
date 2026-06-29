from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.idg_meeting import IDGMeeting


# =========================================================
# CONFIG
# =========================================================

FRIDAY = 4  # Monday=0 ... Friday=4
MONDAY = 0
BIWEEKLY_INTERVAL_DAYS = 14


# =========================================================
# FIND NEXT FRIDAY
# =========================================================

def get_next_friday(start_date: datetime) -> datetime:
    """
    Returns the next Friday AFTER the given date.
    """

    days_ahead = (FRIDAY - start_date.weekday()) % 7

    if days_ahead == 0:
        days_ahead = 7

    return start_date + timedelta(days=days_ahead)


# =========================================================
# GENERATE BIWEEKLY IDG SCHEDULE
# =========================================================

def generate_idg_meetings(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    start_date: datetime,
    count: int = 12,
    created_by=None,
) -> List[IDGMeeting]:
    """
    Generate IDG meetings every other Friday.
    """

    meetings: List[IDGMeeting] = []

    current_date = get_next_friday(start_date)

    for _ in range(count):
        meeting = IDGMeeting(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            meeting_date=current_date,
            status="SCHEDULED",
            created_by=created_by,
        )

        db.add(meeting)
        meetings.append(meeting)

        current_date = current_date + timedelta(days=BIWEEKLY_INTERVAL_DAYS)

    return meetings


# =========================================================
# GENERIC RESCHEDULE (CORE FUNCTION)
# =========================================================

def reschedule_meeting(
    db: Session,
    *,
    meeting_id,
    new_date: datetime,
    reason: Optional[str] = None,
) -> Optional[IDGMeeting]:
    """
    Move meeting to any new date.
    """

    meeting = (
        db.query(IDGMeeting)
        .filter(IDGMeeting.id == meeting_id)
        .first()
    )

    if not meeting:
        return None

    meeting.rescheduled_from = meeting.meeting_date
    meeting.meeting_date = new_date
    meeting.rescheduled_reason = reason

    return meeting


# =========================================================
# MOVE ANY DATE TO NEXT MONDAY
# =========================================================

def move_to_next_monday(date_value: datetime) -> datetime:
    """
    Move a date to the next Monday.
    """

    days_ahead = (MONDAY - date_value.weekday()) % 7

    if days_ahead == 0:
        days_ahead = 7

    return date_value + timedelta(days=days_ahead)


# =========================================================
# OVERRIDE: FRIDAY → MONDAY
# =========================================================

def override_to_monday(
    db: Session,
    *,
    meeting_id,
    reason: str,
) -> Optional[IDGMeeting]:
    """
    Convenience override: Move meeting to next Monday.
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


# =========================================================
# OPTIONAL: HOLIDAY ADJUSTMENT
# =========================================================

def adjust_for_holidays(
    meeting: IDGMeeting,
    holidays: List[datetime],
    reason: str = "Holiday adjustment",
):
    """
    If meeting falls on a holiday → move to Monday.
    """

    for holiday in holidays:
        if meeting.meeting_date.date() == holiday.date():
            meeting.rescheduled_from = meeting.meeting_date
            meeting.meeting_date = move_to_next_monday(meeting.meeting_date)
            meeting.rescheduled_reason = reason