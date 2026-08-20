from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token


security = HTTPBearer(auto_error=False)


# =========================================================
# CONSTANTS
# =========================================================

VALID_ROLES = {
    # Clinical roles.
    "RN",
    "LVN",
    "LPN",
    "MD",
    "DO",
    "NP",
    "PA",
    "SW",
    "CHHA",
    "CHAPLAIN",
    "MEDICAL_DIRECTOR",
    "ALTERNATE_MEDICAL_DIRECTOR",
    "MEDICAL_DIRECTOR_DESIGNEE",
    "ATTENDING_PHYSICIAN",
    "VOLUNTEER_COORDINATOR",
    "CLINICAL_SUPERVISOR",
    # Agency/tenant business roles.
    "ADMINISTRATOR",
    "DPCS",
    # An agency principal who holds BOTH the DPCS and Administrator titles.
    "DPCS_ADMINISTRATOR",
    # Financial/billing roles.
    "CFO",
    "CEO",
    "FINANCIAL_ADMIN",
    "BILLING",
    "BILLING_MANAGER",
    "BILLING_SPECIALIST",
    "COLLECTIONS",
    "REVENUE_CYCLE",
    # QA department.
    "QA_MANAGER",
    "QA_REVIEWER",
    "COMPLIANCE_OFFICER",
    # Intake department.
    "INTAKE_MANAGER",
    "INTAKE_COORDINATOR",
    # Scheduling department.
    "SCHEDULER",
    "STAFFING_COORDINATOR",
    # Platform owner; required by require_owner and the owner dashboard.
    # This is the SNS Hospice Solutions vendor super-user and must never be
    # granted clinical/tenant PHI access (see CLINICAL_ADMIN_ROLES in roles.py).
    "OWNER",
    # Additional SNS platform department roles — never granted PHI access.
    "PLATFORM_SUPPORT",
    "PLATFORM_BILLING",
    "PLATFORM_OPERATIONS",
    "PLATFORM_AI_MANAGEMENT",
    "PLATFORM_COMPLIANCE",
}


# =========================================================
# USER CONTEXT
# =========================================================

@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    role: str
    tenant_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    is_system: bool = False

    @property
    def user_id(self) -> uuid.UUID:
        return self.id


# =========================================================
# TOKEN DECODE
# =========================================================

def _decode_token(token: str) -> dict:
    return decode_access_token(token)


# =========================================================
# DEPENDENCY
# =========================================================

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    payload = _decode_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        )

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid role: {role}",
        )

    try:
        return CurrentUser(
            id=uuid.UUID(user_id),
            role=str(role),
            tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
            email=payload.get("email"),
            is_system=False,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token values",
        )