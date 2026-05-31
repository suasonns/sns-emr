from __future__ import annotations

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.security import get_current_user


def get_db_tenant(
    user=Depends(get_current_user),
) -> Generator[Session, None, None]:
    """
    Tenant-aware DB session
    """

    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "id", None)

    if not tenant_id or not user_id:
        raise RuntimeError("Authenticated user missing tenant_id or user id")

    db: Session = SessionLocal()

    try:
        db.info["tenant_id"] = tenant_id
        db.info["user_id"] = user_id

        db.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )

        db.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": str(user_id)},
        )

        yield db

    finally:
        db.close()