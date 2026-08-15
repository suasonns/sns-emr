# app/api/auth_reauth.py

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class ReauthRequest(BaseModel):
    password: str


@router.post("/reauth", status_code=status.HTTP_200_OK)
def reauthenticate(
    payload: ReauthRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = getattr(current_user, "id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user context is required",
        )

    if not verify_password(user_id, payload.password, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)

    created = db.execute(
        text("""
            INSERT INTO reauth_sessions (user_id, purpose, expires_at)
            VALUES (:uid, 'BULK_PRINT', :exp)
            RETURNING id
        """),
        {"uid": user_id, "exp": expires_at},
    ).fetchone()

    db.commit()

    return {
        "reauth_token": str(created.id),
        "expires_at": expires_at.isoformat(),
    }
