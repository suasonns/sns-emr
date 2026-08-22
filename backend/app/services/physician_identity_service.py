"""Physician Identity Mapping — User-to-Physician linkage.

Owner directive (2026-08-21): physician_id linkage is an IDENTITY
VERIFICATION model, not the visibility model itself.

    "A role label such as Medical Director, Attending Physician, Hospice
    Physician, NP, or PA does not by itself prove which directory
    provider, patient assignments, orders, or signature obligations
    belong to that user... The authoritative identity relationship must
    be an explicit, verified User-to-Physician linkage."

Fail-closed: a provider-identity-role account (see PROVIDER_IDENTITY_ROLES)
whose linkage is not ACTIVE gets ZERO patient/order visibility and ZERO
signing capability — never an agency-wide fallback, never inferred from
display name/email/free-text provider name/job title/agency membership.

AFTER verification (physician_link_status == "ACTIVE" and physician_id
set), visibility is role-tiered (owner directive):

    - Medical Director / Medical Director Designee (and the legacy "MD"
      literal): tenant-wide oversight visibility.
    - Attending Physician, Hospice Physician, NP, PA: assigned-patient
      visibility only (via the existing PatientAssignment mechanism —
      the same one field clinicians use).

Visibility and signature authority are SEPARATE permissions: identity
verification is necessary for both, but a provider seeing a patient does
not by itself grant sign/certify/approve authority — that is still
independently evaluated by each workflow's own signer-role model
(physician_order_service.is_authorized_order_signer(), CTI's
certification_service, F2F's f2f_service).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.roles import normalize_role
from app.models.physician import Physician
from app.models.user import User
from app.services.audit_logger import log_event

LINK_STATUSES = {"UNLINKED", "PENDING_VERIFICATION", "ACTIVE", "SUSPENDED", "ENDED"}

# Roles whose patient/order/signature access must be gated by a verified
# physician_id linkage. Never inferred from role label alone.
TENANT_WIDE_OVERSIGHT_ROLES = {"MEDICAL_DIRECTOR", "MEDICAL_DIRECTOR_DESIGNEE", "MD"}
ASSIGNED_PATIENT_SCOPED_ROLES = {"ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "NP", "PA"}
PROVIDER_IDENTITY_ROLES = TENANT_WIDE_OVERSIGHT_ROLES | ASSIGNED_PATIENT_SCOPED_ROLES


class PhysicianIdentityError(Exception):
    """Raised for invalid link/unlink requests (e.g. tenant mismatch,
    inactive physician, or attempting to link a physician who already has
    another active linked account)."""


def is_provider_identity_role(role: Optional[str]) -> bool:
    return normalize_role(role) in PROVIDER_IDENTITY_ROLES


def is_tenant_wide_oversight_role(role: Optional[str]) -> bool:
    return normalize_role(role) in TENANT_WIDE_OVERSIGHT_ROLES


def is_identity_verified(user: Optional[User]) -> bool:
    """True only when this account has an ACTIVE, verified linkage to a
    Physician directory record. Never true merely because the role label
    looks like a provider role."""
    if user is None:
        return False
    return bool(user.physician_id) and user.physician_link_status == "ACTIVE"


def link_physician(
    db: Session,
    *,
    tenant_id,
    target_user: User,
    physician: Physician,
    linked_by_user_id,
    reason: str,
) -> User:
    """Administrator action: link+verify a User account to a Physician
    directory record. Fails closed on any mismatch rather than silently
    proceeding — this is the ONLY path that grants provider-identity
    access."""
    if not reason or not reason.strip():
        raise PhysicianIdentityError("A linkage reason is required")
    if str(target_user.tenant_id) != str(tenant_id) or str(physician.tenant_id) != str(tenant_id):
        raise PhysicianIdentityError("User and Physician must belong to the same tenant")
    if (physician.status or "").strip().lower() != "active":
        raise PhysicianIdentityError("Cannot link to an inactive Physician directory record")

    # Prevent two different active accounts from being linked to the same
    # physician at once (governance: "duplicate active account linkage").
    existing_holder = (
        db.query(User)
        .filter(
            User.physician_id == physician.id,
            User.physician_link_status == "ACTIVE",
            User.id != target_user.id,
        )
        .first()
    )
    if existing_holder is not None:
        raise PhysicianIdentityError(
            f"Physician {physician.id} is already actively linked to another user account"
        )

    previous_state = {
        "physician_id": str(target_user.physician_id) if target_user.physician_id else None,
        "physician_link_status": target_user.physician_link_status,
    }

    now = datetime.now(timezone.utc)
    target_user.physician_id = physician.id
    target_user.physician_link_status = "ACTIVE"
    target_user.physician_linked_by_user_id = linked_by_user_id
    target_user.physician_linked_at = now
    target_user.physician_linkage_verified_at = now
    target_user.physician_linkage_reason = reason
    # Re-linking clears any prior unlink record — this is a fresh active link.
    target_user.physician_unlinked_by_user_id = None
    target_user.physician_unlinked_at = None
    target_user.physician_unlink_reason = None
    db.add(target_user)
    db.flush()

    action = "PROVIDER_LINK_CHANGED" if previous_state["physician_id"] else "PROVIDER_LINK_CREATED"
    log_event(
        db=db, tenant_id=str(tenant_id), user_id=str(linked_by_user_id), role=None,
        action=action, entity_type="user_physician_link", entity_id=str(target_user.id),
        metadata={
            "physician_id": str(physician.id),
            "target_user_id": str(target_user.id),
            "previous_state": previous_state,
            "new_state": {"physician_id": str(physician.id), "physician_link_status": "ACTIVE"},
            "reason": reason,
        },
    )
    return target_user


def unlink_physician(
    db: Session,
    *,
    tenant_id,
    target_user: User,
    unlinked_by_user_id,
    reason: str,
) -> User:
    """Administrator action: end an active linkage. Access is revoked
    immediately (is_identity_verified() re-evaluates physician_link_status
    on every check, no caching)."""
    if not reason or not reason.strip():
        raise PhysicianIdentityError("An unlink reason is required")
    if str(target_user.tenant_id) != str(tenant_id):
        raise PhysicianIdentityError("User does not belong to this tenant")

    previous_state = {
        "physician_id": str(target_user.physician_id) if target_user.physician_id else None,
        "physician_link_status": target_user.physician_link_status,
    }

    now = datetime.now(timezone.utc)
    target_user.physician_link_status = "ENDED"
    target_user.physician_unlinked_by_user_id = unlinked_by_user_id
    target_user.physician_unlinked_at = now
    target_user.physician_unlink_reason = reason
    db.add(target_user)
    db.flush()

    log_event(
        db=db, tenant_id=str(tenant_id), user_id=str(unlinked_by_user_id), role=None,
        action="PROVIDER_LINK_REMOVED", entity_type="user_physician_link", entity_id=str(target_user.id),
        metadata={
            "target_user_id": str(target_user.id),
            "previous_state": previous_state,
            "new_state": {"physician_id": previous_state["physician_id"], "physician_link_status": "ENDED"},
            "reason": reason,
        },
    )
    return target_user


def authorized_patient_ids_for_provider(db: Session, *, tenant_id, user: User) -> Optional[set]:
    """Patient-visibility scope for a provider-identity-role user.

    Returns:
        - None: this role is not a provider-identity role (caller should
          apply ordinary RBAC/assignment rules, unaffected by this model),
          OR the role is verified tenant-wide oversight (no restriction).
        - set(): FAIL-CLOSED. Provider-identity role without an ACTIVE
          verified linkage — zero patients, never an agency-wide fallback.
        - set(patient_id, ...): assigned-patient scope for a verified
          Attending Physician/Hospice Physician/NP/PA, via the existing
          PatientAssignment mechanism (same one field clinicians use).
    """
    if not is_provider_identity_role(user.role):
        return None

    if not is_identity_verified(user):
        log_event(
            db=db, tenant_id=str(tenant_id), user_id=str(user.id), role=user.role,
            action="PROVIDER_ACCESS_BLOCKED_UNLINKED", entity_type="user_physician_link",
            entity_id=str(user.id),
            metadata={"physician_link_status": user.physician_link_status},
        )
        return set()

    if is_tenant_wide_oversight_role(user.role):
        return None  # verified oversight — tenant-wide, no restriction

    from app.models.patient_assignment import PatientAssignment

    rows = (
        db.query(PatientAssignment.patient_id)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.user_id == user.id,
            PatientAssignment.active.is_(True),
        )
        .all()
    )
    return {row[0] for row in rows}
