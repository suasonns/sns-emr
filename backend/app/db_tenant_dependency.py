from __future__ import annotations

from typing import Generator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging
import os

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.tenancy.registry import get_tenant_schema_name
from app.tenancy.search_path import set_tenant_search_path

logger = logging.getLogger("sns_emr")

# Optional debug flag (keeps noise out of normal runs)
TENANT_DEBUG = os.getenv("TENANT_DEBUG", "false").lower() == "true"


def get_db_tenant(
    user=Depends(get_current_user),
) -> Generator[Session, None, None]:
    """
    ✅ SINGLE ENFORCEMENT POINT (CANONICAL)

    Controls:
    - tenant scoping
    - search_path switching
    - cross-tenant access
    - system account behavior (Owner + Management)
    """

    db: Session = SessionLocal()

    try:
        # ✅ DEBUG: show DB identity + search_path for this session
        if TENANT_DEBUG:
            who = db.execute(text("SELECT current_user")).scalar_one()
            sp = db.execute(text("SHOW search_path")).scalar_one()
            logger.warning(f"DB WHOAMI current_user={who} search_path={sp}")

        # ---------------------------------------------------
        # STEP 1 — OWNER / SYSTEM ADMIN (SNS Hospice Owner)
        # ---------------------------------------------------
        if getattr(user, "is_superuser", False):
            db.info["user_id"] = str(getattr(user, "id", ""))
            db.info["tenant_id"] = None
            yield db
            return

        # ---------------------------------------------------
        # STEP 2 — MANAGEMENT ACCOUNT (Support / Monitoring)
        # ---------------------------------------------------
        if getattr(user, "is_management", False):
            db.info["user_id"] = str(getattr(user, "id", ""))
            db.info["tenant_id"] = None
            yield db
            return

        # ---------------------------------------------------
        # STEP 3 — NORMAL TENANT USER (Hospice Staff)
        # ---------------------------------------------------
        tenant_id = getattr(user, "tenant_id", None)
        user_id = getattr(user, "id", None)

        if not tenant_id or not user_id:
            raise RuntimeError("Tenant user missing tenant_id or user id")

        tenant_schema = get_tenant_schema_name(db, str(tenant_id))

        db.info["tenant_id"] = str(tenant_id)
        db.info["user_id"] = str(user_id)

        # ✅ Enforce tenant isolation (must be SET search_path, not SET LOCAL)
        set_tenant_search_path(db, tenant_schema)

        # ✅ Optional audit variables (does not enable RLS)
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
        try:
            db.rollback()
        except Exception:
            pass
        raise

    finally:
        # ✅ Prevent pooled connection leakage
        try:
            db.execute(text("SET search_path TO public"))
        except Exception:
            pass
        db.close()