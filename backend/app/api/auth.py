from fastapi import APIRouter
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login")
def dev_login(user_id: str, role: str):
    """
    Development-only login endpoint.
    DO NOT use in production.
    """
    token = create_access_token(subject=user_id, role=role)
    return {
        "access_token": token,
        "token_type": "bearer"
    }