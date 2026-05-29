from __future__ import annotations

from typing import Generator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user


def get_db_tenant(
    user=Depends(get_current_user),
) -> Generator[Session, None, None]:
    """
    Enterprise tenant-aware DB session derived ONLY from authenticated identity.

    Guarantees:
    1) ORM-level tenant context (db.info) using typed UUIDs
    2) Postgres session tenant context (set_config) for RLS/audit
    3) User attribution for audit

    Transaction hygiene:
    - If an exception escapes the endpoint, rollback the session so the pooled
      connection does not retain a failed transaction state.
    """
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "id", None)

    if not tenant_id or not user_id:
        raise RuntimeError("Authenticated user missing tenant_id or user id")

    db: Session = SessionLocal()
    try:
        # ORM context MUST be UUID objects (not strings)
        db.info["tenant_id"] = tenant_id
        db.info["user_id"] = user_id

        # Postgres session variables are strings (OK)
        db.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
        db.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": str(user_id)},
        )

        yield db

    except Exception:
        # ✅ enterprise-grade cleanup: never return a failed transaction to the pool
        try:
            db.rollback()
        except Exception:
            pass
        raise

    finally:
        db.close()