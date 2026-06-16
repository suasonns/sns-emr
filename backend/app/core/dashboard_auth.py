from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import UUID

from fastapi import HTTPException

# IMPORTANT:
# Do NOT put Depends(get_current_user) here
# We control flow manually to allow DEV fallback


def resolve_dashboard_user(current_user=None):
    """
    ENTERPRISE AUTH RESOLVER (DEV + PROD)

    Behavior:

    1. If valid authenticated user is passed → use it
    2. If auth fails AND dev bypass is enabled → use dev user
    3. Otherwise → raise 401

    This avoids FastAPI raising early before fallback executes.
    """

    allow_bypass = os.getenv("ALLOW_DEV_DASHBOARD_BYPASS", "false").lower() == "true"

    # ✅ 1. REAL AUTH (PRODUCTION PATH)
    if current_user is not None:
        return current_user

    # ✅ 2. DEV BYPASS MODE
    if allow_bypass:
        tenant_id_raw = os.getenv("DEV_DASHBOARD_TENANT_ID", "").strip()

        if not tenant_id_raw:
            raise HTTPException(
                status_code=500,
                detail="DEV_DASHBOARD_TENANT_ID is not set in .env",
            )

        try:
            tenant_id = UUID(tenant_id_raw)
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="DEV_DASHBOARD_TENANT_ID is not a valid UUID",
            )

        return SimpleNamespace(
            id="dev-user",
            tenant_id=tenant_id,
            role=os.getenv("DEV_DASHBOARD_ROLE", "OWNER"),
            ai_enabled=os.getenv("DEV_DASHBOARD_AI_ENABLED", "true").lower()
            == "true",
        )

    # ❌ 3. NO AUTH
    raise HTTPException(status_code=401, detail="Not authenticated")