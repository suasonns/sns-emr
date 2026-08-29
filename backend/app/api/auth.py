from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.names import format_person_name
from app.core.roles import access_scope_for_role
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, hash_password, verify_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit_logger import log_event


def _client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    # Set on the second call once the user has picked an agency from the
    # requires_agency_selection response below (same email+password valid
    # in more than one tenant).
    tenant_id: str | None = None


class SwitchAgencyRequest(BaseModel):
    target_user_id: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class SetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


def _user_payload(user: User, tenant: Tenant | None = None) -> dict[str, object]:
    # Prefer the structured first/middle/last name; fall back to the
    # legacy full_name column (e.g. seeded admin accounts that only ever
    # had full_name set); only fall back to email if neither is present.
    # Previously this always fell back straight to email, which is why
    # the sidebar showed the login address instead of the staff name.
    display_name = (
        format_person_name(user, None)
        or (user.full_name or "").strip()
        or user.email
    )
    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": str(user.role),
        "email": user.email,
        "full_name": display_name,
        "tenant_name": getattr(tenant, "display_name", None) or getattr(tenant, "legal_name", None),
        "ai_enabled": bool(getattr(tenant, "ai_enabled", False)),
        "billing_enabled": bool(getattr(tenant, "billing_enabled", False)),
        "access_scope": access_scope_for_role(user.role),
        "must_change_password": bool(getattr(user, "must_change_password", False)),
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    query = db.query(User).filter(func.lower(User.email) == payload.email.lower())
    if payload.tenant_id:
        query = query.filter(User.tenant_id == payload.tenant_id)
    candidates = query.filter(User.active.is_(True)).all()

    if not candidates:
        # No account at all for this email (in this tenant, if narrowed) --
        # nothing to attribute the failed attempt to (audit_logs.tenant_id
        # is a required FK), so this case is intentionally not persisted.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # The same email can exist as separate accounts in more than one
    # agency/tenant (uq_users_tenant_email is scoped per-tenant, not
    # global). Each account may have its own password, so we check the
    # given password against every candidate rather than assuming the
    # first row found is the right one.
    matches = [
        user
        for user in candidates
        if user.password_hash and verify_password_hash(payload.password, user.password_hash)
    ]

    if not matches:
        # Email matched one or more real accounts but the password was
        # wrong for all of them -- log the failed attempt against each
        # candidate's tenant so a compromised-password / brute-force
        # pattern shows up per-agency in the owner audit trail.
        for candidate in candidates:
            log_event(
                user_id=str(candidate.id),
                tenant_id=str(candidate.tenant_id),
                role=str(candidate.role),
                action="LOGIN_FAILED",
                entity_type="auth",
                entity_id=str(candidate.id),
                ip=ip,
                metadata={"email": payload.email},
                db=db,
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if payload.tenant_id:
        # Second call after the user picked a specific agency from the
        # requires_agency_selection list below. tenant_id already narrowed
        # candidates to that one tenant, so a password match here means
        # this is the account for that agency -- log in directly, even if
        # its password differs from whatever was typed on the first call.
        user = matches[0]
        tenant = db.get(Tenant, user.tenant_id)
        if tenant is not None and tenant.status != "ACTIVE":
            log_event(
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                role=str(user.role),
                action="LOGIN_FAILED",
                entity_type="auth",
                entity_id=str(user.id),
                ip=ip,
                metadata={"email": user.email, "reason": "tenant_not_active", "tenant_status": tenant.status},
                db=db,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This agency's platform access is currently suspended")
        token = create_access_token(
            user_id=user.id,
            role=str(user.role),
            tenant_id=user.tenant_id,
            email=user.email,
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            role=str(user.role),
            tenant_id=user.tenant_id,
            email=user.email,
        )
        log_event(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=str(user.role),
            action="LOGIN_SUCCESS",
            entity_type="auth",
            entity_id=str(user.id),
            ip=ip,
            metadata={"email": user.email, "agency_selected": True},
            db=db,
        )
        return {
            "access_token": token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _user_payload(user, tenant),
        }

    # No tenant chosen yet. Don't stop at "which accounts share this exact
    # password" -- also pull in every other agency this same physical
    # person is identity-linked to (SSN primary, name+DOB+license
    # fallback; possibly a different email and almost certainly a
    # different password there). Show all of them together so the user
    # never has to know in advance which password unlocks which agency;
    # picking one and, if needed, entering its own password (second call
    # with tenant_id) is all that's required.
    merged: dict[str, User] = {str(user.id): user for user in matches}
    for linked in _find_linked_users(db, matches[0]):
        merged.setdefault(str(linked.id), linked)

    if len(merged) > 1:
        agencies = []
        for user in merged.values():
            tenant = db.get(Tenant, user.tenant_id)
            agencies.append(
                {
                    "tenant_id": str(user.tenant_id),
                    "tenant_name": (
                        getattr(tenant, "display_name", None)
                        or getattr(tenant, "legal_name", None)
                        or "Unknown agency"
                    ),
                    # The account at this agency may use a different email
                    # than the one just typed in (e.g. one email per
                    # agency) -- return it so the second login call can
                    # target the right row instead of assuming the
                    # original email applies everywhere.
                    "email": user.email,
                }
            )
        return {"requires_agency_selection": True, "agencies": agencies}

    user = matches[0]
    tenant = db.get(Tenant, user.tenant_id)

    if tenant is not None and tenant.status != "ACTIVE":
        log_event(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=str(user.role),
            action="LOGIN_FAILED",
            entity_type="auth",
            entity_id=str(user.id),
            ip=ip,
            metadata={"email": user.email, "reason": "tenant_not_active", "tenant_status": tenant.status},
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This agency's platform access is currently suspended")

    token = create_access_token(
        user_id=user.id,
        role=str(user.role),
        tenant_id=user.tenant_id,
        email=user.email,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        role=str(user.role),
        tenant_id=user.tenant_id,
        email=user.email,
    )

    log_event(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=str(user.role),
        action="LOGIN_SUCCESS",
        entity_type="auth",
        entity_id=str(user.id),
        ip=ip,
        metadata={"email": user.email, "agency_selected": False},
        db=db,
    )

    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_payload(user, tenant),
    }


@router.post("/refresh")
def refresh_access_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Exchanges a still-valid refresh token for a new access token (and a
    rotated refresh token) without requiring the password again. This is
    what lets a long clinical encounter (e.g. an in-progress visit
    recording) survive the access token's shorter expiry -- the frontend
    calls this transparently on a 401 instead of forcing a re-login.
    Re-validates the user/tenant are still active on every call so a
    deactivated account or suspended agency can't keep refreshing forever.
    """
    token_payload = decode_refresh_token(payload.refresh_token)

    try:
        user_id = _uuid_from_claim(token_payload.get("sub"))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(User, user_id)
    if user is None or not getattr(user, "active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")

    tenant = db.get(Tenant, user.tenant_id)
    if tenant is not None and tenant.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This agency's platform access is currently suspended",
        )

    new_access_token = create_access_token(
        user_id=user.id,
        role=str(user.role),
        tenant_id=user.tenant_id,
        email=user.email,
    )
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        role=str(user.role),
        tenant_id=user.tenant_id,
        email=user.email,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": _user_payload(user, tenant),
    }


def _uuid_from_claim(value: object) -> UUID:
    if not value:
        raise ValueError("missing claim")
    return UUID(str(value))


@router.get("/me")
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, current_user.id)
    if user is None or not getattr(user, "active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    tenant = db.get(Tenant, user.tenant_id)
    if tenant is not None and tenant.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This agency's platform access is currently suspended")
    return _user_payload(user, tenant)


def _find_linked_users(db: Session, user: User) -> list[User]:
    """Other User rows (any tenant, any email/password) that identity-match
    this person -- powers the "agencies you're also connected to" list shown
    after login. SSN match (deterministic lookup hash) is the primary,
    most reliable signal since it's a real unique identifier; name + DOB +
    license number is a fallback for staff without an SSN on file yet."""
    candidates: dict[str, User] = {}

    if getattr(user, "ssn_lookup_hash", None):
        for match in (
            db.query(User)
            .filter(User.ssn_lookup_hash == user.ssn_lookup_hash)
            .filter(User.id != user.id)
            .filter(User.active.is_(True))
            .all()
        ):
            candidates[str(match.id)] = match

    first = (user.first_name or "").strip().lower()
    last = (user.last_name or "").strip().lower()
    if first and last and user.date_of_birth and user.license_number:
        license_norm = user.license_number.strip().lower()
        for match in (
            db.query(User)
            .filter(func.lower(User.first_name) == first)
            .filter(func.lower(User.last_name) == last)
            .filter(User.date_of_birth == user.date_of_birth)
            .filter(func.lower(User.license_number) == license_norm)
            .filter(User.id != user.id)
            .filter(User.active.is_(True))
            .all()
        ):
            candidates[str(match.id)] = match

    return list(candidates.values())


@router.get("/linked-agencies")
def linked_agencies(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists every other agency (tenant) this same physical person has a
    staff account in -- discovered by identity match (SSN primary; name +
    DOB + license as fallback), independent of whether that account uses a
    different email and/or password. Switching into one still requires
    that agency's own password (see /auth/switch-agency)."""
    user = db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    agencies = []
    for match in _find_linked_users(db, user):
        tenant = db.get(Tenant, match.tenant_id)
        agencies.append(
            {
                "user_id": str(match.id),
                "tenant_id": str(match.tenant_id),
                "tenant_name": (
                    getattr(tenant, "display_name", None)
                    or getattr(tenant, "legal_name", None)
                    or "Unknown agency"
                ),
                "email": match.email,
                "role": str(match.role),
            }
        )
    return {"agencies": agencies}


@router.post("/switch-agency")
def switch_agency(
    payload: SwitchAgencyRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Completes a switch into another agency found via /auth/linked-agencies.
    Requires that target account's own password -- an identity match
    (SSN/name/DOB/license) proves it's the same person, but does not bypass
    that agency's own credential, by design."""
    user = db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target = db.query(User).filter(User.id == payload.target_user_id).first()
    if target is None or not getattr(target, "active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Re-derive the linked set server-side instead of trusting the client's
    # target_user_id blindly -- prevents an authenticated user from probing
    # arbitrary user ids that don't actually match their own identity.
    linked_ids = {str(match.id) for match in _find_linked_users(db, user)}
    if str(target.id) not in linked_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="That account is not linked to your identity",
        )

    if not target.password_hash or not verify_password_hash(payload.password, target.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tenant = db.get(Tenant, target.tenant_id)
    token = create_access_token(
        user_id=target.id,
        role=str(target.role),
        tenant_id=target.tenant_id,
        email=target.email,
    )
    refresh_token = create_refresh_token(
        user_id=target.id,
        role=str(target.role),
        tenant_id=target.tenant_id,
        email=target.email,
    )
    log_event(
        user_id=str(target.id),
        tenant_id=str(target.tenant_id),
        role=str(target.role),
        action="SWITCH_AGENCY",
        entity_type="auth",
        entity_id=str(target.id),
        ip=_client_ip(request),
        metadata={"from_user_id": str(user.id), "from_tenant_id": str(user.tenant_id)},
        db=db,
    )
    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_payload(target, tenant),
    }


@router.post("/reset-password")
def reset_password():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Public password reset is disabled. Contact an administrator; "
            "authenticated users may use /auth/change-password."
        ),
    )


@router.get("/set-password/validate")
def validate_set_password_token(token: str, db: Session = Depends(get_db)):
    """Lets the frontend check a reset-link token before rendering the
    "set your password" form, so an expired/used link shows a clear
    message instead of a failed submit."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = db.query(User).filter(User.password_reset_token_hash == token_hash).first()
    if (
        user is None
        or user.password_reset_expires_at is None
        or user.password_reset_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This link is invalid or has expired.")
    return {"email": user.email, "valid": True}


@router.post("/set-password")
def set_password(payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Public endpoint backing the "set your password" link sent to new
    hires / issued on a password reset. No current password required —
    possession of the (single-use, expiring, unguessable) token is the
    proof of identity. This is also the endpoint an email-based reset
    flow will call once email sending is wired up; no backend changes
    will be needed there, only how the link gets delivered."""
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    user = db.query(User).filter(User.password_reset_token_hash == token_hash).first()
    if (
        user is None
        or user.password_reset_expires_at is None
        or user.password_reset_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This link is invalid or has expired.")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=str(user.role),
        action="PASSWORD_SET_VIA_RESET_LINK",
        entity_type="auth",
        entity_id=str(user.id),
        ip=_client_ip(request),
        db=db,
    )

    return {"status": "ok"}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.password_hash or not verify_password_hash(
        payload.current_password, user.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=str(user.role),
        action="CHANGE_PASSWORD",
        entity_type="auth",
        entity_id=str(user.id),
        ip=_client_ip(request),
        db=db,
    )

    return {"status": "ok"}
