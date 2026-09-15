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
    # Discovered in live data (2026-08-22 role audit): a designee acting
    # with DPCS authority is DPCS for authorization purposes, same pattern
    # as MEDICAL_DIRECTOR_DESIGNEE above.
    "DPCS_DESIGNEE": "DPCS",
    # "SUPERVISOR" is the persisted spelling for the existing
    # CLINICAL_SUPERVISOR canonical role — same role, different spelling.
    "SUPERVISOR": "CLINICAL_SUPERVISOR",
    # Generic "MD" role label used in several legacy require_roles(...)
    # lists; treat as the physician-tier ATTENDING_PHYSICIAN role for
    # capability purposes (assignment-scoped, not tenant-wide oversight —
    # that stays exclusive to MEDICAL_DIRECTOR).
    "MD": "ATTENDING_PHYSICIAN",
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
    # ---------------------------------------------------------------
    # SNS Staff & Access RBAC foundation (Phase UM-1). Additive only —
    # nothing above this line is renamed or removed. These give the
    # remaining approved SNS Staff & Access job functions (see
    # docs/ACCESS_CONTROL_MODEL.md) their own role string so they can
    # carry distinct permissions instead of sharing OWNER's blanket
    # access or a role with no enforced permissions at all.
    # ---------------------------------------------------------------
    "PLATFORM_ADMIN",
    "PLATFORM_SECURITY",
    "PLATFORM_DEVELOPER",
    "PLATFORM_DEVOPS",
    "PLATFORM_IMPLEMENTATION",
    "PLATFORM_CUSTOMER_SERVICE",
    "PLATFORM_QA",
    "PLATFORM_AUDITOR",
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
    "CASE_MANAGER",
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


# =============================================================
# SNS STAFF & ACCESS — RBAC FOUNDATION (Phase UM-1)
#
# This is the single authoritative permission model for the "SNS Staff &
# Access" platform-owner surface (backend/app/api/owner_admin.py). It is
# additive to, and reuses, everything above: PLATFORM_ROLES for scope,
# is_owner_role/is_platform_role for the existing OWNER-only and
# platform-only gates. Do not duplicate this mapping elsewhere — extend it
# here and consume it via role_can()/require_platform_permission().
# =============================================================

# Derived (never independently stored/edited) display tier per role, used
# only for the "Access Level" column on the SNS staff roster. Purely
# presentational — actual authorization always goes through
# PLATFORM_PERMISSION_MATRIX / role_can(), never this tier.
ACCESS_LEVEL_FOR_ROLE: dict[str, str] = {
    "OWNER": "LEVEL_1_OWNER",
    "PLATFORM_ADMIN": "LEVEL_2_ADMINISTRATOR",
    "PLATFORM_SECURITY": "LEVEL_3_SPECIALIZED_ADMINISTRATOR",
    "PLATFORM_COMPLIANCE": "LEVEL_3_SPECIALIZED_ADMINISTRATOR",
    "PLATFORM_BILLING": "LEVEL_3_SPECIALIZED_ADMINISTRATOR",
    "PLATFORM_AI_MANAGEMENT": "LEVEL_3_SPECIALIZED_ADMINISTRATOR",
    "PLATFORM_OPERATIONS": "LEVEL_4_OPERATIONAL_STAFF",
    "PLATFORM_DEVELOPER": "LEVEL_4_OPERATIONAL_STAFF",
    "PLATFORM_DEVOPS": "LEVEL_4_OPERATIONAL_STAFF",
    "PLATFORM_IMPLEMENTATION": "LEVEL_4_OPERATIONAL_STAFF",
    "PLATFORM_QA": "LEVEL_4_OPERATIONAL_STAFF",
    "PLATFORM_SUPPORT": "LEVEL_5_LIMITED_SUPPORT",
    "PLATFORM_CUSTOMER_SERVICE": "LEVEL_5_LIMITED_SUPPORT",
    "PLATFORM_AUDITOR": "LEVEL_6_READ_ONLY",
}


def access_level_for_role(role: str | None) -> str:
    """Derived privilege-tier label for display only (see module docstring)."""
    return ACCESS_LEVEL_FOR_ROLE.get(normalize_role(role), "LEVEL_6_READ_ONLY")


# =============================================================
# SNS OWNER PLATFORM AUTHORITY HIERARCHY (approved 2026-09-15)
#
# Single source of truth for platform-role seniority. Lower number = more
# senior. This is the ONLY place platform-role seniority is expressed; the
# assignment-ceiling checks in role_can() below are derived entirely from
# this table (rank comparison) instead of hardcoded role-name checks, so
# there is no code-level "if role == OWNER" shortcut around the ceiling
# logic. OWNER occupies rank 0 and is therefore always senior to (or, for
# the OWNER-tier itself, equal to) every other platform role — this makes
# "Platform Owner remains highest authority" a data fact, not a bypass.
#
# Customer Service and Support are intentionally ranked below every
# specialized administrator and every technical department role
# (Security, Compliance, Billing, Implementation, Developer, DevOps, QA),
# per the approved hierarchy.
# =============================================================
ROLE_AUTHORITY_RANK: dict[str, int] = {
    "OWNER": 0,
    "PLATFORM_ADMIN": 1,
    "PLATFORM_SECURITY": 2,
    "PLATFORM_COMPLIANCE": 3,
    "PLATFORM_BILLING": 4,
    "PLATFORM_IMPLEMENTATION": 5,
    "PLATFORM_DEVELOPER": 6,
    "PLATFORM_DEVOPS": 7,
    # Not part of the newly-approved hierarchy list, but pre-existing,
    # additive platform roles from an earlier phase; kept at the same
    # operational tier as the other technical department roles above
    # (matches their existing LEVEL_4_OPERATIONAL_STAFF access-level tier)
    # rather than inventing an unapproved seniority.
    "PLATFORM_AI_MANAGEMENT": 7,
    "PLATFORM_OPERATIONS": 7,
    "PLATFORM_QA": 8,
    "PLATFORM_CUSTOMER_SERVICE": 9,
    "PLATFORM_SUPPORT": 10,
    "PLATFORM_AUDITOR": 11,
}


# The assignment/target ceiling in role_can() below only protects the
# ranks at or above this threshold (OWNER=0, PLATFORM_ADMIN=1). Every rank
# above the threshold has no ceiling among peers; authority there is
# governed purely by capability grants. This matches the pre-existing,
# approved design and is expressed as data so role_can() never needs a
# literal "OWNER"/"PLATFORM_ADMIN" string comparison for it.
_PROTECTED_TIER_MAX_RANK = 1


def role_authority_rank(role: str | None) -> int | None:
    """Seniority rank for a platform role, or None if the role is not a
    recognized platform role (callers must treat None as "no authority")."""
    return ROLE_AUTHORITY_RANK.get(normalize_role(role))


# SNS platform-staff lifecycle status (Phase UM-3). Distinct from, and
# synced into, the global `users.active` boolean -- see app.models.user.
# platform_staff_status for why the two columns are kept separate.
PLATFORM_STAFF_STATUSES = {"ACTIVE", "SUSPENDED", "DISABLED", "REMOVED"}


def normalize_platform_staff_status(value: str | None) -> str:
    normalized = (value or "").strip().upper()
    return normalized if normalized in PLATFORM_STAFF_STATUSES else "ACTIVE"


# SNS Staff & Access capability names. These are namespaced (`staff.*`) so
# they can never be confused with the separate Tenant Management /
# Biller Management / Revenue Intelligence / Licensing & Billing capability
# namespaces approved for later phases — this file only ever grants
# `staff.*` capabilities today.
STAFF_CAPABILITIES = {
    "staff.view",
    "staff.create",
    "staff.invite",
    "staff.edit_profile",
    "staff.assign_role",
    "staff.assign_owner_role",
    "staff.activate",
    "staff.suspend",
    "staff.disable",
    "staff.revoke_access",
    "staff.remove",
    "staff.reset_password",
    "staff.view_audit",
    "staff.manage_service_accounts",
    "staff.manage_api_clients",
}

# Full capability grant per role, expressed entirely as data. OWNER holds
# every staff.* capability -- this is now a matrix entry like every other
# role's grant, not a code-level bypass, so OWNER's authorization flows
# through the exact same capability lookup and assignment-ceiling
# (ROLE_AUTHORITY_RANK) logic as every other role in role_can() below.
PLATFORM_PERMISSION_MATRIX: dict[str, set[str]] = {
    "OWNER": set(STAFF_CAPABILITIES),
    "PLATFORM_ADMIN": {
        "staff.view",
        "staff.create",
        "staff.invite",
        "staff.edit_profile",
        "staff.assign_role",
        "staff.activate",
        "staff.suspend",
        "staff.disable",
        "staff.revoke_access",
        "staff.remove",
        "staff.reset_password",
        "staff.view_audit",
    },
    "PLATFORM_SECURITY": {
        "staff.view",
        "staff.suspend",
        "staff.revoke_access",
        "staff.view_audit",
    },
    "PLATFORM_COMPLIANCE": {
        "staff.view",
        "staff.view_audit",
        # Compliance stays read-only + audit by default (established RBAC
        # boundary). A compliance-motivated suspension is granted via an
        # explicit, revocable delegated permission grant (Phase UM-3
        # responsibility-ownership model) rather than a default bundle
        # change, so this does not widen Compliance's baseline authority.
    },
    "PLATFORM_OPERATIONS": {
        "staff.view",
    },
    "PLATFORM_BILLING": {
        "staff.view",
    },
    "PLATFORM_AI_MANAGEMENT": {
        "staff.view",
    },
    "PLATFORM_DEVELOPER": {
        "staff.view",
    },
    "PLATFORM_DEVOPS": {
        "staff.view",
    },
    "PLATFORM_IMPLEMENTATION": {
        "staff.view",
    },
    "PLATFORM_SUPPORT": {
        "staff.view",
        # Default bundle addition (responsibility-ownership model, Phase
        # UM-3): password reset is the quintessential "routine support
        # function" -- the account-recovery action a support desk performs
        # constantly, without needing Administrator escalation for every
        # ticket. Does not include suspend/disable/remove/role-assignment.
        "staff.reset_password",
    },
    "PLATFORM_CUSTOMER_SERVICE": set(),
    "PLATFORM_QA": {
        "staff.view",
    },
    "PLATFORM_AUDITOR": {
        "staff.view",
        "staff.view_audit",
    },
}


def _role_grants(role: str | None) -> set[str]:
    """Role-default capabilities, from the data-driven matrix only -- no
    role-name special case (OWNER's grant is the "OWNER" matrix entry
    above, like every other role)."""
    return PLATFORM_PERMISSION_MATRIX.get(normalize_role(role), set())


# Capabilities that can NEVER be delegated through the direct-grant
# mechanism below, regardless of who is doing the delegating. Ownership
# Continuity (Assign Additional Owner / Transfer Ownership / anything that
# can create another OWNER) stays exclusively OWNER-only -- role_can()
# already denies this to every non-OWNER actor unconditionally; this set
# additionally blocks it from ever being handed out as a delegated grant.
NON_DELEGABLE_CAPABILITIES = {"staff.assign_owner_role"}

# Roles that may delegate an operational capability they already hold to
# another eligible SNS platform identity ("problems escalate upward, work
# delegates downward" -- Phase UM-3). OWNER is listed explicitly (as data,
# not a code-level special case) alongside Platform Administrator, the
# only other role with delegation authority per the approved operating
# model -- specialized roles perform delegated work, they do not further
# re-delegate it.
DELEGATION_AUTHORITY_ROLES = {"OWNER", "PLATFORM_ADMIN"}


def effective_capabilities_for_role(
    role: str | None, direct_grants: Iterable[str] | None = None
) -> set[str]:
    """Role-default capabilities UNIONED with any active delegated direct
    grants for this specific account. `direct_grants` should already be
    filtered by the caller to non-revoked, non-expired
    StaffPermissionGrant rows for this user (see
    app.api.owner_admin._active_grant_capabilities). Never includes a
    NON_DELEGABLE_CAPABILITIES entry from direct_grants -- those can only
    ever come from the OWNER's unconditional grant, never a delegated row."""
    normalized = normalize_role(role)
    base = set(_role_grants(normalized))
    if direct_grants:
        base |= {
            capability
            for capability in direct_grants
            if capability in STAFF_CAPABILITIES and capability not in NON_DELEGABLE_CAPABILITIES
        }
    return base


def capabilities_for_role(role: str | None, direct_grants: Iterable[str] | None = None) -> list[str]:
    """Public, sorted view of the real `staff.*` capabilities a platform
    role is granted -- the same source of truth role_can() enforces
    server-side. Used to render the SNS Staff & Access "Effective
    Permissions Summary" (Access tab) and to gate primary-action buttons
    in the frontend without ever hardcoding a duplicate permission list.
    Pass `direct_grants` to include this specific account's active
    delegated capabilities in the effective set."""
    return sorted(effective_capabilities_for_role(role, direct_grants))


def role_can(
    actor_role: str | None,
    capability: str,
    *,
    target_role: str | None = None,
    actor_direct_grants: Iterable[str] | None = None,
) -> bool:
    """
    Authoritative SNS Staff & Access permission check. Fully policy-driven:
    every actor role (including OWNER) is evaluated against the same
    PLATFORM_PERMISSION_MATRIX capability lookup and the same
    ROLE_AUTHORITY_RANK assignment-ceiling comparison below. There is no
    role-name shortcut that returns True before these checks run.

    Deny-by-default: an unrecognized actor role or capability is always
    denied. When `target_role` is supplied, this also enforces the
    assignment/target-hierarchy ceiling, derived from ROLE_AUTHORITY_RANK:
      - An actor may act on a target only if the actor's rank is strictly
        more senior than the target's rank, EXCEPT the OWNER tier (rank 0)
        may act on an OWNER target (ownership-continuity actions such as
        transferring/assigning ownership stay possible for the actual
        Platform Owner) -- no other rank may act on a same-rank target,
        which is what keeps e.g. Platform Administrator from acting on
        another Platform Administrator.
      - `staff.assign_owner_role` is never evaluated with a target_role by
        any current caller; if one is supplied anyway this is denied
        defensively, since assigning the OWNER role is not a
        target-relative action.

    `actor_direct_grants` (Phase UM-3) is the actor's own active delegated
    StaffPermissionGrant capabilities, if any -- an actor who was
    individually delegated a capability (e.g. PLATFORM_SUPPORT delegated
    staff.suspend for a specific escalation) is treated exactly as if
    their role granted it, for this check only. It never bypasses the
    target-hierarchy ceiling below and never grants a
    NON_DELEGABLE_CAPABILITIES entry (effective_capabilities_for_role
    already filters those out).
    """
    normalized_actor = normalize_role(actor_role)
    if capability not in STAFF_CAPABILITIES:
        return False
    if not is_platform_role(normalized_actor):
        return False

    if capability not in effective_capabilities_for_role(normalized_actor, actor_direct_grants):
        return False

    if target_role is not None:
        if capability == "staff.assign_owner_role":
            return False

        normalized_target = normalize_role(target_role)
        actor_rank = ROLE_AUTHORITY_RANK.get(normalized_actor)
        target_rank = ROLE_AUTHORITY_RANK.get(normalized_target)
        # Unrecognized role on either side of the check: deny by default.
        if actor_rank is None or target_rank is None:
            return False
        # The assignment ceiling only protects the two most senior tiers
        # (OWNER, rank 0, and PLATFORM_ADMIN, rank 1) -- consistent with
        # the pre-existing, approved design: every other role's authority
        # over a peer is governed entirely by its capability grant (least
        # privilege), not by an additional seniority ceiling. A target in
        # the protected tier may only be acted on by a strictly more
        # senior actor, except OWNER retains authority over the OWNER
        # tier itself (ownership-continuity actions).
        if target_rank <= _PROTECTED_TIER_MAX_RANK:
            if actor_rank < target_rank:
                pass
            elif actor_rank == 0 and target_rank == 0:
                pass
            else:
                return False

    return True




def can_delegate_capability(
    actor_role: str | None,
    capability: str,
    *,
    target_role: str | None = None,
    actor_direct_grants: Iterable[str] | None = None,
) -> bool:
    """
    Authoritative check for handing a `staff.*` capability to someone else
    as a delegated grant (Phase UM-3, "work delegates downward").

    An actor may delegate a capability only when ALL of:
      - the capability is delegable at all (not in NON_DELEGABLE_CAPABILITIES
        -- Ownership Continuity can never be delegated this way);
      - the actor holds delegation authority, i.e. their role is in
        DELEGATION_AUTHORITY_ROLES (OWNER and PLATFORM_ADMIN today -- a
        plain data-membership check, not a role-name special case);
      - the actor themselves currently holds the capability (via role
        default or their own active direct grant) for that target, i.e.
        role_can() already passes for the actor/capability/target -- an
        actor can never delegate authority they do not themselves have,
        and never above their own assignment-ceiling on the target.
    """
    normalized_actor = normalize_role(actor_role)
    if capability not in STAFF_CAPABILITIES or capability in NON_DELEGABLE_CAPABILITIES:
        return False
    if normalized_actor not in DELEGATION_AUTHORITY_ROLES:
        return False
    return role_can(
        normalized_actor,
        capability,
        target_role=target_role,
        actor_direct_grants=actor_direct_grants,
    )
