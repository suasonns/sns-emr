from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.security import CurrentUser

from app.services.certification_service import create_or_finalize_cert

router = APIRouter(prefix="/certifications", tags=["Certifications"])


@router.post("/", summary="Finalize certification/recertification and complete task")
def finalize_cert_endpoint(
    patient_id: str,
    benefit_period_id: str,
    signed_by_role: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["NP", "MD", "Administrator"])),
):
    cert = create_or_finalize_cert(
        db,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        signed_by_role=signed_by_role,
        signed_by_user_id=user.user_id,
    )
    return {"id": str(cert.id), "cert_type": cert.cert_type, "signed_at": str(cert.signed_at)}