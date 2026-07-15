"""
Tenant routing middleware (Phase 3)

Enterprise guarantees:
- Feature-flagged
- NO transaction contamination
- STRICT isolation
- Safe fallback
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import TENANT_ROUTING_ENABLED, SessionLocal
from app.core.tenant_schema_context import set_current_tenant_schema
from app.core.tenant_context import set_current_tenant

logger = logging.getLogger("sns_emr")


# =========================================================
# UTIL
# =========================================================

def _normalize_tenant_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    return value.upper() if value else None


# =========================================================
# RESOLVER (SAFE)
# =========================================================

def resolve_tenant_context(
    tenant_code: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve tenant_id and schema_name from tenant_code.

    ✅ FIXED:
    - Uses public.tenants (canonical)
    - NO manual transactions
    - Safe rollback on error
    """

    if not tenant_code:
        return None, None

    db: Session = SessionLocal()

    try:
        db.rollback()

        row = db.execute(
            text("""
                SELECT id, schema_name
                FROM public.tenants
                WHERE UPPER(tenant_code) = :code
                LIMIT 1
            """),
            {"code": tenant_code},
        ).fetchone()

        if not row:
            return None, None

        return str(row[0]), row[1] or "public"

    except Exception:
        db.rollback()
        logger.exception("Tenant resolver failed (tenant_code=%s)", tenant_code)
        raise

    finally:
        db.close()


# =========================================================
# MIDDLEWARE
# =========================================================

class TenantRoutingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if not TENANT_ROUTING_ENABLED:
            return await call_next(request)

        tenant_code = _normalize_tenant_code(
            request.headers.get("X-Tenant-Code")
        )

        try:
            tenant_id, schema_name = resolve_tenant_context(tenant_code)

            # ✅ APPLY CONTEXT
            set_current_tenant_schema(schema_name)
            set_current_tenant(tenant_id)

            response = await call_next(request)
            return response

        except Exception:
            logger.exception("Tenant routing failed")

            # ✅ SAFE RESET
            set_current_tenant_schema(None)
            set_current_tenant(None)
            raise

        finally:
            # ✅ GUARANTEED CLEANUP
            set_current_tenant_schema(None)
            set_current_tenant(None)


# =========================================================
# DB DEPENDENCY
# =========================================================

def get_db():
    """
    ✅ SAFE DB SESSION (NO LEAKS)
    """

    db = SessionLocal()

    try:
        db.rollback()
        yield db

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()