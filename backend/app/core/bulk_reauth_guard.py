from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text


def require_bulk_print_reauth(
    *,
    reauth_token: str | None,
    user_id: str,
    db: Session,
):
    if not reauth_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Re-authentication required for bulk print/export.",
        )

    row = db.execute(
        text("""
            SELECT id, expires_at, used_at
            FROM reauth_sessions
            WHERE id = :id
              AND user_id = :uid
              AND purpose = 'BULK_PRINT'
        """),
        {"id": reauth_token, "uid": user_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid re-authentication token.",
        )

    now = datetime.now(timezone.utc)
    exp = row["expires_at"]

    # normalize naive timestamps
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp is None or exp < now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Re-authentication token expired.",
        )

    if row["used_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Re-authentication token already used.",
        )

    # mark token as used
    db.execute(
        text("""
            UPDATE reauth_sessions
            SET used_at = now()
            WHERE id = :id
        """),
        {"id": row["id"]},
    )
    db.commit()
