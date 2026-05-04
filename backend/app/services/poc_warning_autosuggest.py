from sqlalchemy.orm import Session
from app.models.task import Task


def suggest_close_poc_noncompliant_structure_tasks(
    *,
    db: Session,
    patient_id,
    corrected_note_id,
):
    """
    Auto-suggest closure by attaching the corrected POC_UPDATE note as evidence
    to existing open POC_NONCOMPLIANT_STRUCTURE tasks (RN/NP/MD).
    Does NOT mark tasks as COMPLETED.
    """
    open_tasks = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == "POC_NONCOMPLIANT_STRUCTURE")
        .filter(Task.status != "COMPLETED")
        .all()
    )

    updated = 0
    for t in open_tasks:
        # Only fill if empty, so we don't overwrite human selections
        if t.completion_reference_type is None and not t.completion_reference_id:
            t.completion_reference_type = "NOTE"
            t.completion_reference_id = str(corrected_note_id)
            updated += 1

    return updated