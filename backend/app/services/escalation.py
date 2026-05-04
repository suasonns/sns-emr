from datetime import date, timedelta

def escalate_idg_warnings(meeting):
    days_old = (date.today() - meeting.meeting_date).days

    if days_old > 3:
        return "Critical"
    elif days_old > 1:
        return "Escalated"
    else:
        return "Warning"
