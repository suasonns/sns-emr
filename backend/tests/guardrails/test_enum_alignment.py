from sqlalchemy import text
from app.models.enums import TaskType


def test_tasktype_enum_matches_database(db_session):
    rows = db_session.execute(
        text("SELECT unnest(enum_range(NULL::tasks_task_type_enum))")
    ).fetchall()

    db_values = {r[0] for r in rows}
    code_values = {e.value for e in TaskType}

    missing_in_code = db_values - code_values

    assert not missing_in_code, (
        f"TaskType enum is missing values present in DB: {missing_in_code}. "
        "Update app.models.enums.TaskType to reflect the database enum."
    )
