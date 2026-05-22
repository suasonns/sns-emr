# scripts/test_overdue_task.py

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# -------------------------------------------------------------------
# Ensure project imports work when running from scripts/ on Windows
# -------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parents[1]  # ...\backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.task_overdue_engine import evaluate_task_timeliness


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")

# Optional: allow overriding selection from env
TASK_ID_ENV = os.environ.get("TASK_ID")  # UUID string
TENANT_ID_ENV = os.environ.get("TENANT_ID")  # UUID string

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _pick_task_and_tenant(db) -> tuple[UUID, UUID]:
    """
    Pick a real task row and its tenant_id from the database for testing.
    Prefers OPEN/PENDING/OVERDUE tasks with non-null tenant_id.
    """

    if TASK_ID_ENV:
        task_id = UUID(TASK_ID_ENV)
        row = db.execute(
            text("""
                SELECT id, tenant_id
                FROM tasks
                WHERE id = :id
                LIMIT 1
            """),
            {"id": str(task_id)},
        ).fetchone()
        if not row:
            raise RuntimeError(f"TASK_ID not found in DB: {task_id}")
        tenant_id = UUID(str(row.tenant_id))
        return task_id, tenant_id

    row = db.execute(
        text("""
            SELECT id, tenant_id, status
            FROM tasks
            WHERE tenant_id IS NOT NULL
              AND status IN ('OPEN','PENDING','OVERDUE')
            ORDER BY created_at DESC
            LIMIT 1
        """)
    ).fetchone()

    if not row:
        raise RuntimeError(
            "No eligible tasks found (OPEN/PENDING/OVERDUE with tenant_id). "
            "Create a task first or relax selection."
        )

    task_id = UUID(str(row.id))
    tenant_id = UUID(str(row.tenant_id))
    return task_id, tenant_id


def main() -> None:
    db = SessionLocal()
    try:
        # Confirm DB identity
        db_name, schema_name = db.execute(text("select current_database(), current_schema()")).fetchone()
        print("Connected to:", db_name, "schema:", schema_name)

        task_id, tenant_id = _pick_task_and_tenant(db)
        print("Using task_id:", task_id)
        print("Using tenant_id:", tenant_id)

        # Move due_at into the past (10 days) with SQL to avoid ORM model mismatch.
        # NOTE: Your DB may enforce audit attribution; if so, you must include attribution columns.
        # We'll attempt a minimal update first; if blocked, you'll see the DB error.
        db.execute(
            text("""
                UPDATE tasks
                SET due_at = now() - interval '10 days'
                WHERE id = :id
            """),
            {"id": str(task_id)},
        )
        db.commit()

        # Run the overdue engine
        result = evaluate_task_timeliness(db=db, tenant_id=tenant_id, as_of=date.today())
        db.commit()
        print("evaluate_task_timeliness result:", result)

        # Verify task state in DB
        after = db.execute(
            text("""
                SELECT id, status, due_at, overdue_at, escalated_at
                FROM tasks
                WHERE id = :id
            """),
            {"id": str(task_id)},
        ).fetchone()

        print("Task after:")
        print("  id:", after.id)
        print("  status:", after.status)
        print("  due_at:", after.due_at)
        print("  overdue_at:", after.overdue_at)
        print("  escalated_at:", after.escalated_at)

    finally:
        db.close()


if __name__ == "__main__":
    main()