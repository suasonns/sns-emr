# app/api/admin_reminders.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.services.document_reminders import run_document_reminders

router = APIRouter(prefix="/admin/reminders", tags=["Admin"])


@router.post("/run")
def run_reminders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Restrict to admin / system roles
    if current_user.role not in {"ADMIN", "SYSTEM"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    run_document_reminders(
        db,
        tenant_id=str(current_user.tenant_id),
        system_user_id=str(current_user.id),
    )

    db.commit()
    return {"status": "ok"}