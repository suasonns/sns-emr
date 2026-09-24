"""
Shared patient-access authorization helper.

Centralizes the two-layer access check already used by the primary patient
list endpoint (app/api/patients.py:list_patients) so every other
patient-scoped endpoint enforces the SAME rules instead of re-implementing
(or omitting) them:

  1. Tenant isolation — the patient must belong to the caller's tenant.
  2. Intra-tenant care-team scoping — within a tenant, most clinical roles
     (RN/LVN/NP/SC/MSW/etc.) may only access patients they are actively
     assigned to via PatientAssignment. Only ADMIN/DPCS/MD roles, or a
     user explicitly flagged access_level == "FULL_ACCESS", bypass this
     and can access any patient in their own tenant.

Use `get_authorized_patient(...)` from every new patient-scoped router
(Orders Hub, Physician Orders, Fax, etc.) instead of a bare
`db.query(Patient).filter(Patient.id == patient_id).first()`.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.capabilities import VIEW_ALL_TENANT_PATIENTS, has_capability
from app.core.security import CurrentUser
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.services.physician_identity_service import (
    is_identity_verified,
    is_provider_identity_role,
    is_tenant_wide_oversight_role,
)

# Roles that may access any patient within their own tenant, bypassing
# care-team assignment scoping. This is the SAME single clinical-admin
# access group as app.core.roles.CLINICAL_ADMIN_ROLES / VIEW_ALL_TENANT_
# PATIENTS in app.core.capabilities (ADMINISTRATOR, DPCS, DPCS_ADMINISTRATOR
# — one group, identical access, owner directive 2026-08-22). Determined
# explicitly via has_capability(), never via an implicit allow_clinical_admin
# fallback.
# NOTE: "MD"/"MEDICAL_DIRECTOR"/"MEDICAL_DIRECTOR_DESIGNEE" are handled
# separately below via the Physician Identity Mapping gate — they are
# NOT full-access merely by role label; see is_provider_identity_role().


def _as_uuid(value: Any, field_name: str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=403, detail=f"Invalid authenticated {field_name}") from exc


def get_authorized_patient(db: Session, patient_id: uuid.UUID, user: CurrentUser) -> Patient:
    """
    Returns the Patient if it belongs to the caller's tenant AND the
    caller is authorized to access it (full-access role, or an active
    PatientAssignment). Raises 404 otherwise — a 404 (rather than 403)
    is used deliberately so unauthorized callers cannot use this endpoint
    to probe for the existence of patients outside their care team.
    """
    tenant_id = _as_uuid(getattr(user, "tenant_id", None), "tenant")
    user_id = _as_uuid(
        getattr(user, "user_id", None) or getattr(user, "id", None),
        "user",
    )

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.active:
        raise HTTPException(status_code=403, detail="Inactive or missing user")

    access_level = db_user.access_level or "ROLE_BASED"

    # ---------------------------------------------------------------
    # Physician Identity Mapping (owner directive 2026-08-21): a
    # provider-identity role (MD/MEDICAL_DIRECTOR/MEDICAL_DIRECTOR_DESIGNEE/
    # ATTENDING_PHYSICIAN/HOSPICE_PHYSICIAN/NP/PA) never gets patient
    # access from its role label alone. Fail-closed: without an ACTIVE
    # verified physician_id linkage, access is denied entirely — no
    # fallback to the generic assignment/unclaimed-caseload logic below.
    # Once verified: Medical Director/Designee (and legacy "MD") get
    # tenant-wide oversight visibility; Attending Physician/Hospice
    # Physician/NP/PA are scoped to their own PatientAssignment rows only
    # (never the "unclaimed caseload" fallback — that exists for generic
    # clinical onboarding, not provider-identity roles).
    # ---------------------------------------------------------------
    if is_provider_identity_role(user.role):
        if not is_identity_verified(db_user):
            raise HTTPException(status_code=404, detail="Patient not found")

        if is_tenant_wide_oversight_role(user.role):
            return patient

        assignment = (
            db.query(PatientAssignment)
            .filter(
                PatientAssignment.patient_id == patient.id,
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.user_id == user_id,
                PatientAssignment.active.is_(True),
            )
            .first()
        )
        if assignment:
            return patient
        raise HTTPException(status_code=404, detail="Patient not found")

    if has_capability(user.role, VIEW_ALL_TENANT_PATIENTS) or access_level == "FULL_ACCESS":
        return patient

    assignment = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.patient_id == patient.id,
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.user_id == user_id,
            PatientAssignment.active.is_(True),
        )
        .first()
    )
    if assignment:
        return patient

    # "Unclaimed caseload" fallback: if NO ONE has an active assignment to
    # this patient yet (e.g. a brand-new referral/admission before a case
    # manager has been assigned), don't lock every clinical user out —
    # that would make it impossible for anyone to ever perform the very
    # intake/admission step that establishes the first assignment. Once at
    # least one active assignment exists, this patient is "claimed" and
    # only actually-assigned staff (or full-access roles) may access it.
    has_any_active_assignment = (
        db.query(PatientAssignment.id)
        .filter(
            PatientAssignment.patient_id == patient.id,
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.active.is_(True),
        )
        .first()
        is not None
    )
    if not has_any_active_assignment:
        return patient

    raise HTTPException(status_code=404, detail="Patient not found")


# ---------------------------------------------------------------------
# SFV completion authorization capability (P3-SFV continuation directive
# section 9, corrected 2026-09-23 "SFV AUTHORIZATION CORRECTION", refined
# 2026-09-23 "FINAL AUTHORIZATION CORRECTION").
# canCompleteSfv(actor, completionVisit, sfvRequirement).
#
# PRODUCT RULE: an HOPE SFV must be completed by a clinician who:
#   1. Holds a qualifying NURSING credential.
#   2. Is authorized for patient access.
#   3. Is authorized to document the visit.
#   4. Is authorized to authenticate/sign the visit.
#   5. Performs a qualifying, separate SFV encounter
#      (triggerVisitId != completionVisitId).
#
# This is deliberately narrower than both of the naive implementations the
# product directive explicitly rejected:
#
#   - NOT `role == "RN"` alone -- that would incorrectly exclude Nurse
#     Practitioners and other RN-licensure-derived nursing roles.
#   - NOT "any authorized clinician"/"any user with patient access" --
#     that would incorrectly include Social Worker, Chaplain, Bereavement/
#     Volunteer Coordinator, administrative users, and physicians, none
#     of whom hold a qualifying NURSING credential for this purpose, even
#     though several of them can view or otherwise document this patient.
#
# This function therefore does NOT reuse app.core.capabilities'
# PERFORM_RN_ASSESSMENT / FINALIZE_RN_DOCUMENTATION capabilities as the
# gate: those two capabilities are also granted (by explicit owner
# directive, see capabilities.py) to ADMINISTRATOR, DPCS,
# DPCS_ADMINISTRATOR (clinical-admin convenience access, not a nursing
# credential) and to physician-tier roles MEDICAL_DIRECTOR,
# ATTENDING_PHYSICIAN, HOSPICE_PHYSICIAN, NP, PA (so a physician may
# always do at least what an RN can do administratively) -- reusing them
# here would let an Administrator or a Physician Assistant complete an
# SFV, which the product rule explicitly forbids. SFV completion instead
# checks the caller's normalized role directly against a dedicated
# qualifying-nursing-credential roster below.
#
# "CASE MANAGER" IS A JOB TITLE, NOT A CREDENTIAL (2026-09-23 correction):
# `CASE_MANAGER` is NOT included in the direct qualifying-role roster.
# app.core.capabilities documents CASE_MANAGER as RN-scope, but that role
# string alone does not prove the specific account holds a nursing
# license -- a repository could (or already does, per its own comment
# acknowledging ambiguity) use CASE_MANAGER for a non-nursing case
# manager. Accordingly, a CASE_MANAGER-role caller is authorized ONLY
# when their underlying credential (User.discipline, this repository's
# existing free-text nursing-discipline field -- see
# app/api/_compliance_common.py:101 for its established precedent as a
# credential source distinct from `role`) ALSO normalizes to a
# qualifying nursing credential (RN or LVN/LPN; NP Case Manager also
# qualifies if ever used). Examples:
#   RN Case Manager (role=CASE_MANAGER, discipline=RN)             -> PASS
#   LVN Case Manager (role=CASE_MANAGER, discipline=LVN)            -> PASS
#   LPN Case Manager (role=CASE_MANAGER, discipline=LPN, normalizes
#     to LVN)                                                       -> PASS
#   Social Worker Case Manager (role=CASE_MANAGER, discipline=SW)   -> FAIL
#   Non-nursing Case Manager (role=CASE_MANAGER, discipline unset
#     or non-nursing)                                               -> FAIL
#
# ON-CALL / COVERING / PER-DIEM CLARIFICATION: this repository has no
# separate on-call/covering/per-diem role string -- shift/coverage status
# is not modeled as a distinct role or field. Any account holding a
# qualifying nursing role (RN, LVN/LPN, NP) or a qualifying-credentialed
# CASE_MANAGER qualifies regardless of shift/coverage status; on-call
# status is operational routing, never a separate authorization source
# and never a requirement.
#
# AUTHORIZED NURSING CREDENTIAL GROUP:
#   RN            - staff / on-call / covering / per-diem RN.
#   LVN (LPN)     - staff / on-call / covering / per-diem LVN or LPN.
#                    "LPN" normalizes to "LVN" via app.core.roles._ALIASES;
#                    both spellings qualify.
#   NP            - Nurse Practitioner, functioning under RN licensure for
#                    purposes of this rule. NP remains part of the nursing
#                    credential group and must NOT be routed into the
#                    physician exclusion category.
#   CASE_MANAGER  - only when User.discipline ALSO normalizes to RN,
#                    LVN/LPN, or NP (see above). The bare role alone is
#                    never sufficient.
#
# EXCLUDED NON-NURSING ROLES (never sufficient on their own, regardless of
# patient/chart access, RN-scope administrative capability, or job
# title): SW (Social Worker), CHAPLAIN, VOLUNTEER_COORDINATOR (this
# repository's closest existing role to "Bereavement Coordinator"/
# "Volunteer" -- no separate BEREAVEMENT_COORDINATOR or VOLUNTEER role
# exists), CHHA, ADMINISTRATOR, DPCS, DPCS_ADMINISTRATOR (administrative
# users), PA (Physician Assistant -- not a nursing credential), MD, DO,
# MEDICAL_DIRECTOR, ATTENDING_PHYSICIAN, HOSPICE_PHYSICIAN (physicians --
# excluded from HOPE SFV completion OWNERSHIP only; this does not limit a
# physician's ability to participate in symptom management, orders,
# consultation, or clinical direction, which are separate clinical
# activities), CLINICAL_SUPERVISOR, QA_REVIEWER, QA_MANAGER,
# COMPLIANCE_OFFICER, and every billing/intake/scheduling/platform role
# (e.g. CFO, CEO, FINANCIAL_ADMIN, BILLING*).
# ---------------------------------------------------------------------
from app.core.roles import normalize_role  # noqa: E402

_SFV_QUALIFYING_NURSING_CREDENTIALS = {"RN", "LVN", "NP"}
_SFV_CASE_MANAGER_ROLE = "CASE_MANAGER"


def can_complete_sfv(db: Session, patient_id: uuid.UUID, user: CurrentUser) -> Patient:
    """Authorize `user` to complete an SFV requirement for `patient_id`.

    Returns the authorized Patient (mirrors get_authorized_patient) or
    raises HTTPException. Enforces, in order:

      1. Tenant membership + intra-tenant patient access + active-user
         status (via get_authorized_patient -- never bypassed).
      2. The caller holds a qualifying NURSING credential -- either a
         direct qualifying role (RN, LVN/LPN, NP), or role CASE_MANAGER
         whose underlying User.discipline ALSO normalizes to a qualifying
         nursing credential ("Case Manager" is a job title, not itself a
         credential -- see the roster and rationale documented
         immediately above this function). Any other role/credential
         combination, including administrative, physician, and
         non-nursing clinical roles that may otherwise have chart access,
         is rejected.

    Clinician identity (which specific RN/LVN) is intentionally NOT
    checked here -- any appropriately authorized NURSING clinician
    (original nurse, another assigned nurse, an authorized on-call nurse,
    etc.) may complete the follow-up visit. Visit identity, tenant/patient
    access, and nursing-credential control the result, not a specific
    clinician's identity, not a job title, and not general chart access.
    """
    patient = get_authorized_patient(db, patient_id, user)

    role = normalize_role(getattr(user, "role", None))
    if role in _SFV_QUALIFYING_NURSING_CREDENTIALS:
        return patient

    if role == _SFV_CASE_MANAGER_ROLE:
        user_id = _as_uuid(
            getattr(user, "user_id", None) or getattr(user, "id", None),
            "user",
        )
        db_user = db.query(User).filter(User.id == user_id).first()
        underlying_credential = normalize_role(getattr(db_user, "discipline", None)) if db_user else None
        if underlying_credential in _SFV_QUALIFYING_NURSING_CREDENTIALS:
            return patient

    raise HTTPException(status_code=403, detail="Not authorized to complete this SFV requirement")

