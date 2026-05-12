from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.jobs.idg_overdue_job import run_idg_overdue_job
from app.core.security import get_current_user

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin"],
)


def require_admin_user(user=Depends(get_current_user)):
    """
    Admin gate.
    Adjust logic if your user model differs.
    """
    role = getattr(user, "role", None)
    is_admin = getattr(user, "is_admin", False)

    if is_admin or role in {"ADMIN", "DPCS", "CLINICAL_ADMIN"}:
        return user

    raise HTTPException(status_code=403, detail="Admin privileges required")


@router.post("/run-idg-overdue")
def run_idg_overdue_job_endpoint(
    db: Session = Depends(get_db),
    admin_user=Depends(require_admin_user),
):
    """
    Admin-only manual trigger for:
      - marking IDG tasks overdue
      - inserting overdue alerts (idempotent)
    """
    result = run_idg_overdue_job(db)
    return {
        "status": "ok",
        "job": "IDG_OVERDUE",
        "result": result,
    }