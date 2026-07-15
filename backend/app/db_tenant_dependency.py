from __future__ import annotations

import logging
import os
from typing import Generator, Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user, CurrentUser
from app.tenancy.registry import get_tenant_schema_name
from app.tenancy.search_path import set_tenant_search_path

logger = logging.getLogger("sns_emr")

TENANT_DEBUG = os.getenv("TENANT_DEBUG", "false").lower() == "true"


def get_db_tenant(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Generator[Session, None, None]:
    """
    ✅ ENTERPRISE TENANT DB DEPENDENCY (PRODUCTION SAFE)
    """

    db: Session = SessionLocal()

    try:
        # ✅ ALWAYS START CLEAN
        try:
            db.rollback()
        except Exception:
            pass

        if TENANT_DEBUG:
            try:
                who = db.execute(text("SELECT current_user")).scalar_one()
                sp = db.execute(text("SHOW search_path")).scalar_one()

                logger.warning(
                    f"[TENANT_DEBUG] current_user={who} search_path={sp}"
                )

                logger.warning(
                    f"[TENANT_DEBUG] auth_user user_id={getattr(user, 'user_id', None)} "
                    f"tenant_id={getattr(user, 'tenant_id', None)} "
                    f"role={getattr(user, 'role', None)} "
                    f"is_system={getattr(user, 'is_system', None)}"
                )
            except Exception:
                logger.warning("TENANT_DEBUG failed", exc_info=True)

        # ---------------------------------------------------
        # SYSTEM ACCESS (NO TENANT SCOPING)
        # ---------------------------------------------------
        if getattr(user, "is_system", False):
            db.info["user_id"] = str(getattr(user, "user_id", ""))
            db.info["tenant_id"] = None
            yield db
            return

        # ---------------------------------------------------
        # TENANT USER
        # ---------------------------------------------------
        tenant_id = getattr(user, "tenant_id", None)
        user_id = getattr(user, "user_id", None)

        if tenant_id is None or user_id is None:
            raise RuntimeError("Tenant user missing tenant_id or user_id")

        tenant_id_str = str(tenant_id)
        user_id_str = str(user_id)

        # ✅ RESOLVE SCHEMA (CANONICAL)
        tenant_schema = get_tenant_schema_name(db, tenant_id_str)

        db.info["tenant_id"] = tenant_id_str
        db.info["user_id"] = user_id_str

        # ✅ SAFE SCHEMA SWITCH
        try:
            set_tenant_search_path(db, tenant_schema)
        except Exception as exc:
            db.rollback()
            logger.exception("Failed to set tenant search_path")
            raise RuntimeError("Tenant schema enforcement failed") from exc

        # ✅ AUDIT CONTEXT
        try:
            db.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id_str},
            )
            db.execute(
                text("SELECT set_config('app.user_id', :user_id, true)"),
                {"user_id": user_id_str},
            )
        except Exception:
            logger.warning("Failed to set session audit context", exc_info=True)

        yield db

    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

        logger.error("Tenant DB dependency error", exc_info=True)
        raise

    finally:
        # ✅ CLEAN RESET (SAFE)
        try:
            db.execute(text("SET search_path TO public"))
        except Exception:
            pass

        db.close()