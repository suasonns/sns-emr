from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import get_current_user as get_core_current_user
from app.core.security import verify_password_hash
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    tenant_id: str
    role: str


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    user = get_core_current_user(credentials=creds)
    return CurrentUser(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )


def verify_password(user_id: str, password: str, db: Session) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not getattr(user, "password_hash", None):
        return False

    return verify_password_hash(password, user.password_hash)
