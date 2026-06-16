from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_tenant_with_request_state
from app.core.deps import get_current_user

from app.services.edi_835_parser import parse_835_file
from app.services.payment_service import post_payments_from_835

router = APIRouter(prefix="/billing/835", tags=["835 Payments"])


@router.post("/upload")
async def upload_835(
    file: UploadFile,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Upload ERA (835) file and post payments.
    """

    content = await file.read()
    text = content.decode()

    parsed = parse_835_file(text)

    created = post_payments_from_835(
        tenant_id=current_user.tenant_id,
        parsed_data=parsed,
    )

    return {
        "processed": len(created),
        "message": "835 file processed successfully",
    }