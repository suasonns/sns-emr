from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.role_guards import require_owner
from app.core.user_session_reference_store import get_user_session_reference
from app.core.audit_events import log_support_lookup
from app.core.db import get_db

router = APIRouter(prefix="/support", tags=["Support"])


@router.get("/user-session/{ref}")
def lookup_user_session_reference(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    OWNER-only support lookup (MFA required).
    Audited.
    """
    require_owner(user)

    data = get_user_session_reference(ref)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="User Session Reference not found or expired",
        )

    # ✅ AUDIT ENTRY
    log_support_lookup(
        db=db,
        actor_id=str(user.id),
        session_reference=ref,
        ip_address=request.client.host if request.client else None,
    )

    return data