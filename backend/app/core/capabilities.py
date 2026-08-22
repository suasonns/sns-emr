"""
Named clinical/administrative capabilities (owner directives 2026-08-22).

This module is the single source of truth for authorization decisions that
role strings alone cannot express cleanly:

  - ADMINISTRATOR, DPCS, and DPCS_ADMINISTRATOR are ONE clinical-admin access
    group (owner directive, final): identical capabilities everywhere —
    census, patient search, patient chart access, RN ICA, RN visit
    documentation, Plan of Care, IDG, and supervisory workflows. Do not
    create a separate rule per role name; use CLINICAL_ADMIN_ROLES /
    _CLINICAL_ADMIN_CAPS below as the one definition.
  - Regular RN (and CASE_MANAGER) is assignment-scoped: only patients with
    an active PatientAssignment for that user.
  - Physician-only capabilities (sign_physician_order, certify_terminal_
    illness, finalize_f2f) are granted only to verified physician-tier roles
    (MEDICAL_DIRECTOR/ATTENDING_PHYSICIAN/HOSPICE_PHYSICIAN/NP/PA) and are
    NEVER granted to the clinical-admin group — holding "all RN privileges"
    does not make DPCS/Administrator a physician.
"""

from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, status

from app.core.roles import normalize_role
from app.core.security import CurrentUser, get_current_user

# ---------------------------------------------------------------------
# Named capabilities (mandate item D)
# ---------------------------------------------------------------------
VIEW_ALL_TENANT_PATIENTS = "view_all_tenant_patients"
VIEW_ASSIGNED_PATIENTS = "view_assigned_patients"
PERFORM_RN_ASSESSMENT = "perform_rn_assessment"
FINALIZE_RN_DOCUMENTATION = "finalize_rn_documentation"
ADMINISTER_MEDICATION_AS_RN = "administer_medication_as_rn"
MANAGE_PATIENT_ASSIGNMENTS = "manage_patient_assignments"
SUPERVISE_CLINICAL_WORK = "supervise_clinical_work"
SIGN_PHYSICIAN_ORDER = "sign_physician_order"
CERTIFY_TERMINAL_ILLNESS = "certify_terminal_illness"
FINALIZE_F2F = "finalize_f2f"

ALL_CAPABILITIES = {
    VIEW_ALL_TENANT_PATIENTS,
    VIEW_ASSIGNED_PATIENTS,
    PERFORM_RN_ASSESSMENT,
    FINALIZE_RN_DOCUMENTATION,
    ADMINISTER_MEDICATION_AS_RN,
    MANAGE_PATIENT_ASSIGNMENTS,
    SUPERVISE_CLINICAL_WORK,
    SIGN_PHYSICIAN_ORDER,
    CERTIFY_TERMINAL_ILLNESS,
    FINALIZE_F2F,
}

# RN-scope clinical action capabilities — granted to plain RN, and to DPCS/
# DPCS_ADMINISTRATOR DIRECTLY (not via a generic admin fallback), and to
# verified physician-tier roles (a physician may always do at least what an
# RN may do). NEVER granted to plain ADMINISTRATOR.
_RN_SCOPE_CAPS = {
    VIEW_ASSIGNED_PATIENTS,
    PERFORM_RN_ASSESSMENT,
    FINALIZE_RN_DOCUMENTATION,
    ADMINISTER_MEDICATION_AS_RN,
}

# Physician-only capabilities — never granted to DPCS/DPCS_ADMINISTRATOR/
# ADMINISTRATOR regardless of "all RN privileges".
_PHYSICIAN_ONLY_CAPS = {
    SIGN_PHYSICIAN_ORDER,
    CERTIFY_TERMINAL_ILLNESS,
    FINALIZE_F2F,
}

# ---------------------------------------------------------------------
# Explicit role -> capability mapping (mandate item D)
# ---------------------------------------------------------------------
# Owner directive (2026-08-22, superseding the earlier ADMINISTRATOR/DPCS
# split): ADMINISTRATOR, DPCS, and DPCS_ADMINISTRATOR are ONE clinical-admin
# access group with identical authorization — full RN-scope clinical
# privilege, tenant-wide patient visibility, assignment management, and
# clinical supervision. This mirrors app.core.roles.CLINICAL_ADMIN_ROLES;
# do not duplicate a separate rule per role name.
# ---------------------------------------------------------------------
_CLINICAL_ADMIN_CAPS = _RN_SCOPE_CAPS | {
    VIEW_ALL_TENANT_PATIENTS,
    MANAGE_PATIENT_ASSIGNMENTS,
    SUPERVISE_CLINICAL_WORK,
}

ROLE_CAPABILITIES: dict[str, set[str]] = {
    # Single clinical-admin access group — ADMINISTRATOR, DPCS, and
    # DPCS_ADMINISTRATOR all get the exact same capability set. NOT
    # physician-only capabilities (see item 6: DPCS/Administrator never
    # gain physician signing authority merely from this role).
    "ADMINISTRATOR": _CLINICAL_ADMIN_CAPS,
    "DPCS": _CLINICAL_ADMIN_CAPS,
    "DPCS_ADMINISTRATOR": _CLINICAL_ADMIN_CAPS,
    # Regular RN: assignment-scoped clinical role only.
    "RN": {
        VIEW_ASSIGNED_PATIENTS,
        PERFORM_RN_ASSESSMENT,
        FINALIZE_RN_DOCUMENTATION,
        ADMINISTER_MEDICATION_AS_RN,
    },
    # Physician-tier roles: RN-scope actions a physician may always perform,
    # PLUS physician-only capabilities. Tenant-wide oversight visibility
    # mirrors the existing Physician Identity Mapping gate
    # (is_tenant_wide_oversight_role) for MEDICAL_DIRECTOR.
    "MEDICAL_DIRECTOR": _RN_SCOPE_CAPS
    | _PHYSICIAN_ONLY_CAPS
    | {VIEW_ALL_TENANT_PATIENTS, SUPERVISE_CLINICAL_WORK},
    "ATTENDING_PHYSICIAN": _RN_SCOPE_CAPS | _PHYSICIAN_ONLY_CAPS,
    "HOSPICE_PHYSICIAN": _RN_SCOPE_CAPS | _PHYSICIAN_ONLY_CAPS,
    "NP": _RN_SCOPE_CAPS | {SIGN_PHYSICIAN_ORDER},
    "PA": _RN_SCOPE_CAPS | {SIGN_PHYSICIAN_ORDER},
    # QA / compliance: read-only tenant-wide visibility, no clinical action
    # capabilities.
    "QA_REVIEWER": {VIEW_ALL_TENANT_PATIENTS},
    "QA_MANAGER": {VIEW_ALL_TENANT_PATIENTS, SUPERVISE_CLINICAL_WORK},
    "COMPLIANCE_OFFICER": {VIEW_ALL_TENANT_PATIENTS},
    # Discovered in live data (2026-08-22 role audit), not yet covered by an
    # explicit owner rule — mapped conservatively so existing accounts don't
    # silently lose access; confirm/adjust with the owner as a follow-up.
    # CLINICAL_SUPERVISOR ("SUPERVISOR" alias): oversees multiple RNs'
    # caseloads, so tenant-wide view + supervision, but NOT RN-scope
    # documentation/signing on a patient's behalf.
    "CLINICAL_SUPERVISOR": {VIEW_ALL_TENANT_PATIENTS, SUPERVISE_CLINICAL_WORK},
    # CASE_MANAGER: hospice case managers are RN-scope, assignment-scoped
    # like regular RN.
    "CASE_MANAGER": {
        VIEW_ASSIGNED_PATIENTS,
        PERFORM_RN_ASSESSMENT,
        FINALIZE_RN_DOCUMENTATION,
        ADMINISTER_MEDICATION_AS_RN,
    },
}


def role_capabilities(role: str | None) -> set[str]:
    """Return the capability set for a (possibly non-canonical) role string."""
    return set(ROLE_CAPABILITIES.get(normalize_role(role), set()))


def has_capability(role: str | None, capability: str) -> bool:
    return capability in role_capabilities(role)


def has_any_capability(role: str | None, capabilities: Iterable[str]) -> bool:
    caps = role_capabilities(role)
    return any(c in caps for c in capabilities)


def require_capability(capability: str):
    """FastAPI dependency: 403s unless the caller's role maps to `capability`."""

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_capability(user.role, capability):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' lacks capability '{capability}'",
            )
        return user

    return dependency


def require_any_capability(*capabilities: str):
    """FastAPI dependency: 403s unless the caller's role maps to ANY of the given capabilities."""

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_any_capability(user.role, capabilities):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' lacks required capability (any of {sorted(capabilities)})",
            )
        return user

    return dependency
