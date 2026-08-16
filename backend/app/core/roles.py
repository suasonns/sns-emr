"""
Canonical role handling.

Authorization checks across the API were written against several spellings of
the same role ("ADMIN", "Administrator", "ADMINISTRATOR", "CLINICAL_ADMIN"),
while only the values in VALID_ROLES can actually be issued to a user. Compare
roles through this module so a single stored role satisfies every spelling.
"""

from __future__ import annotations

from typing import Iterable

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
}

# Roles carrying clinical administrative authority; DPCS is always clinical.
CLINICAL_ADMIN_ROLES = {"ADMINISTRATOR", "DPCS"}

# Financial authority is separate from clinical authority. It belongs to the
# CFO or CEO, or to whoever has been granted that title.
FINANCIAL_ADMIN_ROLES = {"CFO", "CEO", "FINANCIAL_ADMIN"}

# Roles that make a gate financial rather than clinical.
FINANCIAL_ROLES = FINANCIAL_ADMIN_ROLES | {"BILLING"}


def normalize_role(role: str | None) -> str:
    if not role:
        return ""
    key = str(role).strip().upper()
    return _ALIASES.get(key, key)


def role_matches(
    user_role: str | None,
    allowed_roles: Iterable[str] | None,
    *,
    allow_clinical_admin: bool = True,
) -> bool:
    """
    True when the user's role satisfies the gate, ignoring spelling.

    Clinical admins satisfy clinical gates but never financial ones; financial
    admins satisfy financial gates.
    """
    if allowed_roles is None:
        return True

    normalized_user = normalize_role(user_role)
    if not normalized_user:
        return False

    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    if normalized_user in normalized_allowed:
        return True

    is_financial_gate = bool(normalized_allowed & FINANCIAL_ROLES)

    if is_financial_gate:
        return normalized_user in FINANCIAL_ADMIN_ROLES

    if allow_clinical_admin and normalized_user in CLINICAL_ADMIN_ROLES:
        return True

    return False
