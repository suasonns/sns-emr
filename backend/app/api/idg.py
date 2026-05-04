@router.get("/meeting/{meeting_id}/warnings", summary="IDG discipline compliance warnings")
def idg_meeting_warnings(
    meeting_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Administrator"])
    ),
):
    meeting = db.query(IDGMeeting).filter(IDGMeeting.id == meeting_id).first()
    warnings = get_idg_meeting_warnings(meeting)

    return {
        "meeting_date": meeting.meeting_date,
        "warnings": warnings,
    }
