"""Staff Management API (Insights > HR).

Replaces the hardcoded mock roster in AnalyticsHR.jsx with real data backed
by the `users` table. Scope: Personal Information, Professional Information,
and Access/Account Setting only — no pay rate and no license/document
expiration tracking (owner directive: not needed for this phase). SSN is
deliberately not collected (needs an encryption-at-rest plan first).

Only clinical admins (ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR) may create or
edit staff records; any authenticated tenant user may view the roster.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.patients import get_db_with_request_state, require_tenant_user, _tenant_id_uuid
from app.core.crypto import decrypt_ssn, encrypt_ssn, mask_ssn
from app.core.roles import CLINICAL_ADMIN_ROLES, role_matches
from app.core.security import hash_password
from app.models.user import User
from app.services.audit_logger import log_event

router = APIRouter(prefix="/staff", tags=["staff"])

VALID_STAFF_TYPES = {"C", "A", "X", "Y"}  # Clinical / Administrative / Contracted / Referral Source

# How long an admin-issued password set/reset link stays valid.
RESET_LINK_TTL = timedelta(hours=72)


def _generate_temp_password() -> str:
    """5-digit numeric temporary password (staff must change it at login)."""
    return str(secrets.randbelow(90000) + 10000)


def _frontend_base_url() -> str:
    return (
        os.getenv("FRONTEND_URL")
        or os.getenv("APP_URL")
        or "http://localhost:5173"
    ).rstrip("/")


def _issue_password_reset_link(staff: User) -> str:
    """Generate a single-use, expiring "set your password" link.

    Only the SHA-256 hash of the token is persisted (never the raw value),
    same principle as password_hash. The raw token is embedded in the
    returned link and shown once — today the admin copies/relays it
    manually; once email sending is wired up, this exact link is what gets
    emailed, with no backend changes needed.
    """
    raw_token = secrets.token_urlsafe(32)
    staff.password_reset_token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    staff.password_reset_expires_at = datetime.now(timezone.utc) + RESET_LINK_TTL
    return f"{_frontend_base_url()}/set-password?token={raw_token}"


class StaffWrite(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    middle_name: str | None = None
    role: str
    active: bool = True

    # Personal information
    date_of_birth: date | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    phone: str | None = None
    home_phone: str | None = None
    # Write-only: 9 digits (any formatting accepted). Omit/leave blank to
    # leave the stored SSN unchanged; never returned back in plaintext.
    ssn: str | None = None

    # Professional information
    job_title: str | None = None
    discipline: str | None = None
    license_number: str | None = None
    npi: str | None = None
    employment_date: date | None = None
    employment_end_date: date | None = None

    # Access / account setting
    staff_type: str | None = None
    access_level: str | None = None


def _require_staff_admin(user=Depends(require_tenant_user)):
    if not role_matches(getattr(user, "role", None), CLINICAL_ADMIN_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an agency administrator can manage staff records",
        )
    return user


def _actor_id(user) -> uuid.UUID:
    raw_actor_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    if not raw_actor_id:
        raise HTTPException(status_code=500, detail="Invalid user identity")
    return uuid.UUID(str(raw_actor_id))


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = str(value).strip()
    return trimmed or None


def _display_full_name(staff: User) -> str:
    structured = " ".join(
        part for part in [staff.first_name, staff.middle_name, staff.last_name] if part
    ).strip()
    return structured or (staff.full_name or "").strip() or staff.email


def _serialize_staff(staff: User) -> dict[str, Any]:
    return {
        "id": str(staff.id),
        "tenant_id": str(staff.tenant_id),
        "email": staff.email,
        "full_name": _display_full_name(staff),
        "first_name": staff.first_name,
        "middle_name": staff.middle_name,
        "last_name": staff.last_name,
        "role": staff.role,
        "active": staff.active,
        "date_of_birth": staff.date_of_birth,
        "address_street": staff.address_street,
        "address_city": staff.address_city,
        "address_state": staff.address_state,
        "address_zip": staff.address_zip,
        "phone": staff.phone,
        "home_phone": staff.home_phone,
        "job_title": staff.job_title,
        "discipline": staff.discipline,
        "license_number": staff.license_number,
        "npi": staff.npi,
        "employment_date": staff.employment_date,
        "employment_end_date": staff.employment_end_date,
        "staff_type": staff.staff_type,
        "access_level": staff.access_level,
        "must_change_password": bool(staff.must_change_password),
        "ssn_masked": mask_ssn(staff.ssn_last4),
        "has_ssn": bool(staff.ssn_encrypted),
        "created_at": staff.created_at,
        "updated_at": staff.updated_at,
    }


def _apply_staff_payload(staff: User, payload: StaffWrite, *, is_create: bool) -> None:
    first_name = _normalize_optional_string(payload.first_name)
    last_name = _normalize_optional_string(payload.last_name)
    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="First and last name are required")

    staff.first_name = first_name
    staff.last_name = last_name
    staff.middle_name = _normalize_optional_string(payload.middle_name)
    staff.full_name = " ".join(
        part for part in [first_name, staff.middle_name, last_name] if part
    )

    email = _normalize_optional_string(payload.email)
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    staff.email = email.lower()

    role = _normalize_optional_string(payload.role)
    if not role:
        raise HTTPException(status_code=400, detail="Role is required")
    staff.role = role

    staff.active = bool(payload.active)

    staff.date_of_birth = payload.date_of_birth
    staff.address_street = _normalize_optional_string(payload.address_street)
    staff.address_city = _normalize_optional_string(payload.address_city)
    staff.address_state = _normalize_optional_string(payload.address_state)
    staff.address_zip = _normalize_optional_string(payload.address_zip)
    staff.phone = _normalize_optional_string(payload.phone)
    staff.home_phone = _normalize_optional_string(payload.home_phone)

    ssn = _normalize_optional_string(payload.ssn)
    if ssn:
        try:
            ciphertext, last4, lookup_hash = encrypt_ssn(ssn)
        except ValueError:
            raise HTTPException(status_code=400, detail="SSN must be 9 digits")
        staff.ssn_encrypted = ciphertext
        staff.ssn_last4 = last4
        staff.ssn_lookup_hash = lookup_hash
    # Blank/omitted SSN on update leaves the existing value untouched --
    # there's no "clear" affordance since a staff record shouldn't lose a
    # collected SSN by accident when an admin edits an unrelated field.

    staff.job_title = _normalize_optional_string(payload.job_title)
    staff.discipline = _normalize_optional_string(payload.discipline)
    staff.license_number = _normalize_optional_string(payload.license_number)
    staff.npi = _normalize_optional_string(payload.npi)
    staff.employment_date = payload.employment_date
    staff.employment_end_date = payload.employment_end_date

    normalized_staff_type = _normalize_optional_string(payload.staff_type)
    if normalized_staff_type:
        normalized_staff_type = normalized_staff_type.upper()
        if normalized_staff_type not in VALID_STAFF_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid staff type. Must be one of: {sorted(VALID_STAFF_TYPES)}",
            )
    staff.staff_type = normalized_staff_type

    access_level = _normalize_optional_string(payload.access_level)
    if access_level:
        staff.access_level = access_level.upper()
    elif is_create:
        staff.access_level = "ROLE_BASED"


@router.get("")
def list_staff(
    status_filter: str = Query("active", alias="status"),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    query = db.query(User).filter(User.tenant_id == tenant_id)

    normalized_status = (status_filter or "active").strip().lower()
    if normalized_status == "active":
        query = query.filter(User.active.is_(True))
    elif normalized_status == "inactive":
        query = query.filter(User.active.is_(False))
    elif normalized_status != "both":
        raise HTTPException(status_code=400, detail="Invalid status filter")

    staff_members = query.order_by(User.last_name.asc(), User.first_name.asc()).all()
    return [_serialize_staff(member) for member in staff_members]


@router.post("", status_code=201)
def create_staff(
    payload: StaffWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(_require_staff_admin),
):
    tenant_id = _tenant_id_uuid(user)
    actor_id = _actor_id(user)

    normalized_email = _normalize_optional_string(payload.email)
    if normalized_email:
        existing = (
            db.query(User)
            .filter(User.tenant_id == tenant_id, func.lower(User.email) == normalized_email.lower())
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="A staff member with this email already exists")

    staff = User(
        tenant_id=tenant_id,
        created_by=actor_id,
        must_change_password=True,
    )
    temp_password = _generate_temp_password()
    staff.password_hash = hash_password(temp_password)
    _apply_staff_payload(staff, payload, is_create=True)
    reset_link = _issue_password_reset_link(staff)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    result = _serialize_staff(staff)
    # Only returned once, at creation, so the admin can hand it to the new
    # hire. Never persisted or re-shown in plaintext after this response.
    # Two ways to onboard: log in directly with the temp password, or click
    # the reset link to set their own password immediately — both enforce
    # must_change_password until a real password is chosen.
    result["temporary_password"] = temp_password
    result["reset_link"] = reset_link
    return result


@router.get("/{staff_id}")
def get_staff(
    staff_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.tenant_id == tenant_id)
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return _serialize_staff(staff)


@router.patch("/{staff_id}")
def update_staff(
    staff_id: uuid.UUID,
    payload: StaffWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(_require_staff_admin),
):
    tenant_id = _tenant_id_uuid(user)
    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.tenant_id == tenant_id)
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    normalized_email = _normalize_optional_string(payload.email)
    if normalized_email:
        existing = (
            db.query(User)
            .filter(
                User.tenant_id == tenant_id,
                func.lower(User.email) == normalized_email.lower(),
                User.id != staff_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="A staff member with this email already exists")

    _apply_staff_payload(staff, payload, is_create=False)
    staff.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(staff)
    return _serialize_staff(staff)


@router.post("/{staff_id}/reset-password")
def reset_staff_password(
    staff_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(_require_staff_admin),
):
    """Admin-issued password reset. Returns a new temporary password the
    admin can hand to the staff member directly (no email delivery yet).
    The staff member is forced to change it on their next login."""
    tenant_id = _tenant_id_uuid(user)
    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.tenant_id == tenant_id)
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    temp_password = _generate_temp_password()
    staff.password_hash = hash_password(temp_password)
    staff.must_change_password = True
    reset_link = _issue_password_reset_link(staff)
    staff.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "id": str(staff.id),
        "email": staff.email,
        "temporary_password": temp_password,
        "reset_link": reset_link,
    }


@router.get("/{staff_id}/ssn")
def reveal_staff_ssn(
    staff_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(_require_staff_admin),
):
    """Decrypts and returns the full SSN. Admin-only and audit-logged --
    every reveal is recorded (who, when, whose record) since this is the
    most sensitive field on the staff record."""
    tenant_id = _tenant_id_uuid(user)
    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.tenant_id == tenant_id)
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    if not staff.ssn_encrypted:
        raise HTTPException(status_code=404, detail="No SSN on file for this staff member")

    try:
        ssn = decrypt_ssn(staff.ssn_encrypted)
    except ValueError:
        raise HTTPException(status_code=500, detail="Unable to decrypt SSN")

    log_event(
        user_id=str(_actor_id(user)),
        tenant_id=str(tenant_id),
        role=str(getattr(user, "role", None)),
        action="staff.ssn.reveal",
        entity_type="user",
        entity_id=str(staff.id),
        db=db,
    )

    return {"id": str(staff.id), "ssn": ssn}
