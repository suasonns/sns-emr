from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.services.discharge_service import finalize_discharge
from app.auth import get_current_user

router = APIRouter()

@router.post("/discharges/{discharge_id}/finalize")
def finalize_discharge_endpoint(
    discharge_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    return finalize_discharge(db, discharge_id, user.id)
