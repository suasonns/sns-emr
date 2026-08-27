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
