# app/api/auth_reauth.py

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    """
    Step-up authentication: user must re-enter password to get a short-lived one-time token.
    Dev mode fallback: if current_user.id is None, attach to an existing DB user.
    """
    try:
        # Support dict or object current_user
        user_id = (
            current_user.get("id")
            if isinstance(current_user, dict)
            else getattr(current_user, "id", None)
        )

        # DEV fallback: attach to a real DB user row
        if not user_id:
            row = db.execute(
                text("SELECT id FROM users ORDER BY id LIMIT 1")
            ).mappings().first()

            if not row:
                raise HTTPException(
                    status_code=500,
                    detail="No users exist in DB. Create at least one user row before using /auth/reauth.",
                )

            user_id = str(row["id"])

        # Verify password (dev accepts DEV_REAUTH_PASSWORD='dev')
        if not verify_password(user_id=user_id, password=payload.password, db=db):
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

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # During dev, expose the DB/Python error so you can fix fast
        raise HTTPException(status_code=500, detail=f"Reauth failed: {e}")