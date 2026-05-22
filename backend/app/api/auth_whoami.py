from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/whoami", operation_id="auth_whoami")
def whoami(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "role": (current_user.role or ""),
    }