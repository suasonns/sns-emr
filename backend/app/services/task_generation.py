from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.task import Task

HUV_DISCIPLINES = {"RN", "MD", "NP"}
SFV_DISCIPLINES = {"AIDE", "SW", "CHAPLAIN"}


def generate_tasks_for_benefit_period(
    db: Session,
    *,
    patient_id,
    benefit_period,
    frequency_map: dict,  # e.g. {"RN": 2, "AIDE": 5}
    created_by=None,
):
    """
    Auto-generate HUV/SFV compliance tasks for a benefit period.
    Safe to re-run (clears prior PERIODIC tasks).
    """

    # 🔐 SAFETY: remove prior auto-generated tasks for this BP
    db.query(Task).filter(
        Task.patient_id == patient_id,
        Task.benefit_period_id == benefit_period.id,
        Task.origin == "PERIODIC",
    ).delete(synchronize_session=False)

    start = benefit_period.start_date
    end = benefit_period.end_date

    current = start
    tasks: list[Task] = []

    while current <= end:
        for discipline, visits_per_week in frequency_map.items():
            task_type = "HUV" if discipline in HUV_DISCIPLINES else "SFV"

            for _ in range(visits_per_week):
                tasks.append(
                    Task(
                        patient_id=patient_id,
                        benefit_period_id=benefit_period.id,
                        discipline=discipline,
                        task_type=task_type,
                        origin="PERIODIC",
                        regulatory_basis="VISIT_FREQUENCY",
                        due_date=current,
                        status="PENDING",
                        created_by=created_by,
                    )
                )

        current += timedelta(weeks=1)

    db.add_all(tasks)
    db.commit()
    return tasks