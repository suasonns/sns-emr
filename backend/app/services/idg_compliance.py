from app.models.idg_meeting import IDGMeeting

def get_idg_meeting_warnings(meeting: IDGMeeting):
    warnings = []

    if meeting is None:
        return [{
            "discipline": "IDG",
            "status": "Missing",
            "severity": "Critical",
            "message": "IDG meeting record does not exist"
        }]

    discipline_map = [
        ("RN", meeting.rn_required, meeting.rn_present, "Critical"),
        ("Medical Director / NP", meeting.physician_required, meeting.physician_present, "Critical"),
        ("Social Worker", meeting.social_worker_required, meeting.social_worker_present, "Warning"),
        ("Chaplain", meeting.chaplain_required, meeting.chaplain_present, "Warning"),
    ]

    for name, required, present, severity in discipline_map:
        if required and not present:
            warnings.append({
                "discipline": name,
                "status": "Missing",
                "severity": severity,
                "message": f"{name} participation is required for IDG compliance"
            })

    return warnings