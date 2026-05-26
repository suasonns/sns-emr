from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.dependencies.tenant import inject_tenant
from app.core.security_deps import get_current_user_id


def get_db_tenant(
    request: Request,
    tenant_id: str = Depends(inject_tenant),
    user_id: str = Depends(get_current_user_id),
) -> Generator[Session, None, None]:
    """
    Enterprise tenant-aware DB session.

    Sets BOTH:
    1) Postgres session vars (for RLS): app.tenant_id + app.user_id
    2) SQLAlchemy session info (for ORM filters): db.info["tenant_id"] + db.info["user_id"]
    """

    db = SessionLocal()
    try:
        # -----------------------------
        # ORM-level tenant context
        # -----------------------------
        db.info["tenant_id"] = str(tenant_id)
        db.info["user_id"] = str(user_id)

        # -----------------------------
        # DB-level tenant context (RLS)
        # -----------------------------
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