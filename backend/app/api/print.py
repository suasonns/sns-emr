from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.core.bulk_reauth_guard import require_bulk_print_reauth

router = APIRouter(prefix="/print", tags=["Print"])


class BulkPrintRequest(BaseModel):
    document_ids: list[str]
    reauth_token: str | None = None


@router.post("/bulk")
def bulk_print(
    payload: BulkPrintRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["id"]
    document_count = len(payload.document_ids)

    # ✅ THIS IS STEP 2
    if document_count > 1:
        require_bulk_print_reauth(
            reauth_token=payload.reauth_token,
            user_id=user_id,
            db=db,
        )

    # ✅ Continue with actual print logic
    return {
        "status": "PRINT_STARTED",
        "document_count": document_count,
    }

@router.post("/documents/bulk")
def bulk_print_documents(
    payload: BulkPrintRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["id"]
    document_count = len(payload.document_ids)

    if document_count > 1:
        require_bulk_print_reauth(
            reauth_token=payload.reauth_token,
            user_id=user_id,
            db=db,
        )

    # continue with printing