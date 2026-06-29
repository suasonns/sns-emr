from datetime import datetime, timezone


def escalate_idg_warnings(meeting):
    """
    Enterprise-grade IDG escalation logic.

    Purpose:
    - Determine risk level of IDG meeting based on timing
    - Safe for audit and compliance use

    Rules:
    - COMPLETED meetings are not escalated
    - Uses timezone-safe datetime comparisons
    - Handles null safety
    """

    # ✅ Null safety
    if not meeting or not getattr(meeting, "meeting_date", None):
        return "UNKNOWN"

    # ✅ Do not escalate completed meetings
    if getattr(meeting, "status", None) == "COMPLETED":
        return "NONE"

    now = datetime.now(timezone.utc)

    # ✅ Normalize meeting_date to UTC
    meeting_date = meeting.meeting_date

    if meeting_date.tzinfo is None:
        meeting_date = meeting_date.replace(tzinfo=timezone.utc)

    delta = now - meeting_date
    days_old = delta.days

    # ✅ Escalation logic
    if days_old > 3:
        return "CRITICAL"
    elif days_old > 1:
        return "ESCALATED"
    else:
        return "WARNING"
