# api/core/dashboard_auth.py

from __future__ import annotations

import os
import uuid
from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status

from app.core.security import CurrentUser


# =========================================================
# CONFIG
# =========================================================

ALLOW_DEV_BYPASS = os.getenv("ALLOW_DEV_DASHBOARD_BYPASS", "false").lower() == "true"

ALLOWED_DASHBOARD_ROLES = {
    "OWNER",
    "ADMINISTRATOR",
    "DPCS",
    "RN",
}


# =========================================================
# RESOLVER
# =========================================================

def resolve_dashboard_user(current_user: Optional[CurrentUser] = None) -> CurrentUser:
    """
    ENTERPRISE DASHBOARD AUTH RESOLVER

    Rules:

    1. If valid authenticated user → use it ✅
    2. DEV bypass allowed → controlled fallback ✅
    3. Otherwise → reject ❌

    Guarantees:
    ✅ Always returns a consistent CurrentUser object
    ✅ Enforces role validation
    ✅ Marks dev bypass clearly (for audit)
    ✅ Prevents silent production misuse
    """

    # -----------------------------------------------------
    # 1. AUTHENTICATED USER (PRODUCTION PATH)
    # -----------------------------------------------------
    if current_user is not None:
        if current_user.role not in ALLOWED_DASHBOARD_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized for dashboard access",
            )
        return current_user

    # -----------------------------------------------------
    # 2. DEV BYPASS MODE
    # -----------------------------------------------------
    if ALLOW_DEV_BYPASS:
        tenant_id_raw = os.getenv("DEV_DASHBOARD_TENANT_ID", "").strip()

        if not tenant_id_raw:
            raise HTTPException(
                status_code=500,
                detail="DEV_DASHBOARD_TENANT_ID is not configured",
            )

        try:
            tenant_id = UUID(tenant_id_raw)
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="DEV_DASHBOARD_TENANT_ID must be a valid UUID",
            )

        role = os.getenv("DEV_DASHBOARD_ROLE", "OWNER")

        if role not in ALLOWED_DASHBOARD_ROLES:
            raise HTTPException(
                status_code=500,
                detail="DEV_DASHBOARD_ROLE is not valid",
            )

        # ✅ RETURN REAL CurrentUser (NOT SimpleNamespace)
        return CurrentUser(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            role=role,
            tenant_id=tenant_id,
            email="dev-dashboard@sns.local",
        )

    # -----------------------------------------------------
    # 3. NO AUTH → REJECT
    # -----------------------------------------------------
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )