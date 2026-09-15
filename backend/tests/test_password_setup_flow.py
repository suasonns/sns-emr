from __future__ import annotations

"""
End-to-end coverage for the token-based "set your password" workflow
(backend/app/api/auth.py: GET /auth/set-password/validate, POST
/auth/set-password), which previously had no dedicated automated test
anywhere in the suite (see docs/STAFF_MANAGEMENT_GAP_REPORT.md).

Covers, per the Owner Platform completion directive:
  - token generation (via app.api.staff._issue_password_reset_link, the
    same helper used by both the tenant staff and SNS platform staff
    reset-password endpoints)
  - token expiration
  - invalid / unknown token
  - successful password creation
  - password reset validation (GET .../validate) for a valid, expired,
    and unknown token
  - audit logging (PASSWORD_SET_VIA_RESET_LINK)
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from app.api.staff import _issue_password_reset_link
from app.core.protected_tenants import PLATFORM_TENANT_ID
from app.core.security import verify_password_hash
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User

_created_user_ids: list[uuid.UUID] = []


@pytest.fixture(autouse=True)
def _cleanup(db_session):
    _created_user_ids.clear()
    yield
    if _created_user_ids:
        db_session.query(AuditLog).filter(
            AuditLog.entity_id.in_([str(uid) for uid in _created_user_ids])
        ).delete(synchronize_session=False)
        db_session.query(User).filter(User.id.in_(_created_user_ids)).delete(
            synchronize_session=False
        )
        db_session.commit()
    _created_user_ids.clear()


def _ensure_platform_tenant(db_session) -> None:
    if db_session.get(Tenant, PLATFORM_TENANT_ID) is None:
        db_session.add(
            Tenant(
                id=PLATFORM_TENANT_ID,
                legal_name="SNS Hospice Solutions",
                display_name="SNS Hospice Solutions",
                npi="9999999999",
                tenant_type="PRODUCTION",
                status="ACTIVE",
            )
        )
        db_session.commit()


def _make_user(db_session, *, role: str = "PLATFORM_SUPPORT") -> User:
    _ensure_platform_tenant(db_session)
    user = User(
        id=uuid.uuid4(),
        tenant_id=PLATFORM_TENANT_ID,
        email=f"pwtest.{uuid.uuid4().hex[:8]}@sns.internal",
        full_name="Password Setup Test User",
        role=role,
        active=True,
        account_type="HUMAN_STAFF",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _created_user_ids.append(user.id)
    return user


def _token_from_link(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


# ---------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------

def test_issuing_reset_link_sets_a_hashed_single_use_token(db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    db_session.commit()

    token = _token_from_link(link)
    # The raw token is never persisted -- only its SHA-256 hash.
    assert user.password_reset_token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert user.password_reset_expires_at is not None
    assert user.password_reset_expires_at > datetime.now(timezone.utc)


# ---------------------------------------------------------------------
# GET /auth/set-password/validate
# ---------------------------------------------------------------------

def test_validate_accepts_a_fresh_token(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    db_session.commit()
    token = _token_from_link(link)

    resp = client.get("/auth/set-password/validate", params={"token": token})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["valid"] is True
    assert body["email"] == user.email


def test_validate_rejects_unknown_token(client, db_session):
    resp = client.get("/auth/set-password/validate", params={"token": "not-a-real-token"})
    assert resp.status_code == 400


def test_validate_rejects_expired_token(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    token = _token_from_link(link)
    user.password_reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    resp = client.get("/auth/set-password/validate", params={"token": token})
    assert resp.status_code == 400


# ---------------------------------------------------------------------
# POST /auth/set-password
# ---------------------------------------------------------------------

def test_set_password_succeeds_with_a_valid_token(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    db_session.commit()
    token = _token_from_link(link)

    resp = client.post(
        "/auth/set-password",
        json={"token": token, "new_password": "Correct-Horse-Battery-Staple-1"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "ok"}

    db_session.refresh(user)
    assert verify_password_hash("Correct-Horse-Battery-Staple-1", user.password_hash)
    assert user.must_change_password is False
    # Token is single-use: cleared after a successful set.
    assert user.password_reset_token_hash is None
    assert user.password_reset_expires_at is None


def test_set_password_token_cannot_be_reused(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    db_session.commit()
    token = _token_from_link(link)

    first = client.post(
        "/auth/set-password",
        json={"token": token, "new_password": "First-Password-Attempt-1"},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/auth/set-password",
        json={"token": token, "new_password": "Second-Password-Attempt-1"},
    )
    assert second.status_code == 400


def test_set_password_rejects_expired_token(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    token = _token_from_link(link)
    user.password_reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    resp = client.post(
        "/auth/set-password",
        json={"token": token, "new_password": "Expired-Token-Password-1"},
    )
    assert resp.status_code == 400

    db_session.refresh(user)
    # Password must remain unchanged when the token is rejected -- this
    # user never had a password set, so the hash column stays empty.
    assert not user.password_hash


def test_set_password_rejects_unknown_token(client, db_session):
    resp = client.post(
        "/auth/set-password",
        json={"token": "totally-unknown-token", "new_password": "Whatever-Password-1"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------

def test_set_password_writes_an_audit_event(client, db_session):
    user = _make_user(db_session)
    link = _issue_password_reset_link(user)
    db_session.commit()
    token = _token_from_link(link)

    resp = client.post(
        "/auth/set-password",
        json={"token": token, "new_password": "Audited-Password-Change-1"},
    )
    assert resp.status_code == 200, resp.text

    event = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity_type == "auth",
            AuditLog.entity_id == str(user.id),
            AuditLog.action == "PASSWORD_SET_VIA_RESET_LINK",
        )
        .one_or_none()
    )
    assert event is not None
    assert str(event.user_id) == str(user.id)
