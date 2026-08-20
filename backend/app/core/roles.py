"""
Canonical role handling.

Authorization checks across the API were written against several spellings of
the same role ("ADMIN", "Administrator", "ADMINISTRATOR", "CLINICAL_ADMIN"),
while only the values in VALID_ROLES can actually be issued to a user. Compare
roles through this module so a single stored role satisfies every spelling.

SNS HOSPICE SOLUTIONS MASTER ACCESS CONTROL MODEL
--------------------------------------------------
This module also implements the full department/role taxonomy from the
platform's master access-control design. Existing role names already in use
(OWNER, DPCS_ADMINISTRATOR, DPCS, ADMINISTRATOR, BILLING, RN, LVN, etc.) are
kept exactly as-is — nothing already shipped is renamed. The additional
department roles below (QA, Intake, Scheduling, Billing sub-roles, Clinical
sub-roles, Platform sub-roles) are new, additive role values layered on top.
"""

from __future__ import annotations

from typing import Iterable, Literal

# Every spelling that resolves to the same effective role.
_ALIASES = {
    "ADMIN": "ADMINISTRATOR",
    "ADMINISTRATOR": "ADMINISTRATOR",
    "CLINICAL_ADMIN": "ADMINISTRATOR",
    "DPCS_ADMIN": "DPCS",
    "SUPER_ADMIN": "ADMINISTRATOR",
    "MSW": "SW",
    "LCSW": "SW",
    "LPN": "LVN",
    "BILLER": "BILLING",
    "ALTERNATE_MEDICAL_DIRECTOR": "MEDICAL_DIRECTOR",
    "MEDICAL_DIRECTOR_DESIGNEE": "MEDICAL_DIRECTOR",
}

# =============================================================
# LEVEL 0 — PLATFORM (SNS Hospice Solutions vendor staff)
#
# OWNER is the platform/vendor super-user (SNS Hospice Solutions owner-
# developer account). The additional platform roles below are new
# additive department roles for future SNS staff (support, platform
# billing, operations, AI management, compliance). None of these belong
# to any agency and none may ever automatically gain PHI or clinical
# documentation access.
# =============================================================
PLATFORM_ROLES = {
    "OWNER",
    "PLATFORM_SUPPORT",
    "PLATFORM_BILLING",
    "PLATFORM_OPERATIONS",
    "PLATFORM_AI_MANAGEMENT",
    "PLATFORM_COMPLIANCE",
}

# =============================================================
# LEVEL 1 — TENANT / AGENCY
#
# DPCS_ADMINISTRATOR is a distinct role for an agency principal who holds
# BOTH the DPCS and Administrator titles simultaneously (common in small
# hospice agencies). DPCS and ADMINISTRATOR remain separate, distinct
# titles for accreditation purposes (CoPs distinguish them); this role is
# for the person who legitimately holds both, not a substitute for either.
# =============================================================

# Roles carrying clinical administrative authority; DPCS is always clinical.
#
# OWNER is the platform/vendor super-user and is intentionally EXCLUDED
# here. It must never gain clinical-admin fallback access to tenant PHI,
# IDG, or patient charts.
CLINICAL_ADMIN_ROLES = {"ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR"}

# =============================================================
# LEVEL 2 — CLINICAL DEPARTMENT (new additive sub-roles; MD/DO/NP/PA and
# ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR remain the existing canonical
# clinical/admin roles above and are unchanged).
# =============================================================
CLINICAL_DEPARTMENT_ROLES = {
    "MEDICAL_DIRECTOR",
    "ATTENDING_PHYSICIAN",
    "RN",
    "LVN",
    "CHHA",
    "SW",  # MSW/LCSW/BSW alias to SW
    "CHAPLAIN",
    "VOLUNTEER_COORDINATOR",
    "CLINICAL_SUPERVISOR",
}

# =============================================================
# LEVEL 2 — BILLING DEPARTMENT
#
# BILLING remains the existing canonical billing-only role. The additional
# billing sub-roles below are new, additive department roles that share the
# same financial-only access scope (never clinical documentation).
# =============================================================
BILLING_DEPARTMENT_ROLES = {
    "BILLING",
    "BILLING_MANAGER",
    "BILLING_SPECIALIST",
    "COLLECTIONS",
    "REVENUE_CYCLE",
}

# =============================================================
# LEVEL 2 — QA DEPARTMENT (new; read-only clinical/compliance access,
# never billing management).
# =============================================================
QA_ROLES = {
    "QA_MANAGER",
    "QA_REVIEWER",
    "COMPLIANCE_OFFICER",
}

# =============================================================
# LEVEL 2 — INTAKE DEPARTMENT (new)
# =============================================================
INTAKE_ROLES = {
    "INTAKE_MANAGER",
    "INTAKE_COORDINATOR",
}

# =============================================================
# LEVEL 2 — SCHEDULING DEPARTMENT (new)
# =============================================================
SCHEDULING_ROLES = {
    "SCHEDULER",
    "STAFFING_COORDINATOR",
}

# Financial authority is separate from clinical authority. It belongs to the
# CFO or CEO, or to whoever has been granted that title, plus the billing
# department roles.
#
# OWNER (platform owner/developer) is intentionally EXCLUDED here. Platform
# Owner is not a clinical or financial role — it manages platform operations
# only (tenants, licensing, platform health) and must never be combined with
# billing/financial access, even for convenience. A platform owner and a
# billing/financial admin must always be distinct accounts.
FINANCIAL_ADMIN_ROLES = {"CFO", "CEO", "FINANCIAL_ADMIN"} | BILLING_DEPARTMENT_ROLES

# Roles that make a gate financial rather than clinical.
FINANCIAL_ROLES = FINANCIAL_ADMIN_ROLES


def normalize_role(role: str | None) -> str:
    if not role:
        return ""
    key = str(role).strip().upper()
    return _ALIASES.get(key, key)


def is_platform_role(role: str | None) -> bool:
    """True for SNS platform/vendor staff — never grants tenant/PHI access."""
    return normalize_role(role) in PLATFORM_ROLES


def is_owner_role(role: str | None) -> bool:
    """True only for the platform OWNER role."""
    return normalize_role(role) == "OWNER"


def access_scope_for_role(role: str | None) -> Literal["platform", "billing", "tenant"]:
    """Return the frontend navigation scope for a canonical backend role."""
    normalized = normalize_role(role)
    if normalized in PLATFORM_ROLES:
        return "platform"
    if normalized in FINANCIAL_ADMIN_ROLES:
        return "billing"
    return "tenant"


def role_matches(
    user_role: str | None,
    allowed_roles: Iterable[str] | None,
    *,
    allow_clinical_admin: bool = True,
) -> bool:
    """
    True when the user's role satisfies the gate, ignoring spelling.

    Clinical admins satisfy clinical gates but never financial ones; financial
    admins satisfy financial gates. Platform roles never receive an implicit
    fallback into tenant/clinical/financial gates — they must be explicitly
    listed in `allowed_roles` for a platform-scoped endpoint.
    """
    if allowed_roles is None:
        return True

    normalized_user = normalize_role(user_role)
    if not normalized_user:
        return False

    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    if normalized_user in normalized_allowed:
        return True

    # Platform roles never get an implicit tenant/clinical/financial fallback.
    if normalized_user in PLATFORM_ROLES:
        return False

    is_financial_gate = bool(normalized_allowed & FINANCIAL_ROLES)

    if is_financial_gate:
        return normalized_user in FINANCIAL_ADMIN_ROLES

    if allow_clinical_admin and normalized_user in CLINICAL_ADMIN_ROLES:
        return True

    return False
