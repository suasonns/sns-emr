from fastapi import APIRouter
from uuid import UUID

from app.services.task_overdue_engine import run_overdue_engine
from app.db.session import SessionLocal

router = APIRouter()


@router.post("/debug/run-overdue")
def run_overdue_debug():
    db = SessionLocal()

    try:
        run_overdue_engine(
            db=db,
            tenant_id=UUID("01271980-0000-0000-0000-000005101977"),
        )
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()