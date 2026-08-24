from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

MIN_PASSWORD_LENGTH = 12

DEV_TENANT_ID_ENV = "DEV_TENANT_ID"
DEV_PLATFORM_TENANT_ID_ENV = "DEV_PLATFORM_TENANT_ID"
DEV_BILLING_TENANT_ID_ENV = "DEV_BILLING_TENANT_ID"


@dataclass(frozen=True)
class DevelopmentIdentity:
    email_env: str
    password_env: str
    tenant_env: str
    full_name: str
    role: str


DEVELOPMENT_IDENTITIES = (
    DevelopmentIdentity(
        email_env="DEV_DPCS_ADMIN_EMAIL",
        password_env="DEV_DPCS_ADMIN_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development DPCS Administrator",
        role="DPCS_ADMINISTRATOR",
    ),
    DevelopmentIdentity(
        email_env="DEV_PLATFORM_OWNER_EMAIL",
        password_env="DEV_PLATFORM_OWNER_PASSWORD",
        tenant_env=DEV_PLATFORM_TENANT_ID_ENV,
        full_name="Development Platform Owner",
        role="OWNER",
    ),
    DevelopmentIdentity(
        email_env="DEV_BILLING_EMAIL",
        password_env="DEV_BILLING_PASSWORD",
        tenant_env=DEV_BILLING_TENANT_ID_ENV,
        full_name="Development Billing",
        role="BILLING",
    ),
    # ---------------------------------------------------------------
    # Owner-acceptance test identities (Angela Hospice / Silva Hospice
    # training tenants only). One synthetic, non-PHI account per role
    # needed to exercise the RN ICA -> Plan of Care -> orders ->
    # signature -> IDG -> finalization workflow end-to-end in the
    # browser. No implicit secrets: each account is a no-op unless its
    # *_EMAIL/*_PASSWORD env vars are explicitly configured.
    # ---------------------------------------------------------------
    DevelopmentIdentity(
        email_env="DEV_RN_EMAIL",
        password_env="DEV_RN_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development RN",
        role="RN",
    ),
    DevelopmentIdentity(
        email_env="DEV_MEDICAL_DIRECTOR_EMAIL",
        password_env="DEV_MEDICAL_DIRECTOR_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development Medical Director",
        role="MEDICAL_DIRECTOR",
    ),
    DevelopmentIdentity(
        email_env="DEV_MSW_EMAIL",
        password_env="DEV_MSW_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development MSW",
        role="SW",
    ),
    DevelopmentIdentity(
        email_env="DEV_CHAPLAIN_EMAIL",
        password_env="DEV_CHAPLAIN_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development Spiritual Counselor",
        role="CHAPLAIN",
    ),
    DevelopmentIdentity(
        email_env="DEV_QA_REVIEWER_EMAIL",
        password_env="DEV_QA_REVIEWER_PASSWORD",
        tenant_env=DEV_TENANT_ID_ENV,
        full_name="Development Read-Only Reviewer",
        role="QA_REVIEWER",
    ),
)


def _configured_uuid(env_name: str) -> uuid.UUID:
    value = os.getenv(env_name)
    if not value:
        raise RuntimeError(f"{env_name} is required when a related development identity is configured")
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise RuntimeError(f"{env_name} must be a valid UUID") from exc


def _ensure_tenant(db: Session, tenant_id: uuid.UUID, *, platform: bool) -> None:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            legal_name="SNS Development Platform" if platform else "SNS Development Agency",
            display_name="Development Platform" if platform else "Development Agency",
            npi="0000000000",
            ein=None if platform else "000000000",
            ptan=None if platform else "DEVELOPMENT",
            tenant_type="DEV",
            environment_tag="DEVELOPMENT",
            status="ACTIVE",
            ai_enabled=True,
            billing_enabled=not platform,
        )
        db.add(tenant)
        db.flush()
        return

    tenant.status = "ACTIVE"
    tenant.ai_enabled = True
    # Only force billing_enabled=False when we just created a brand-new
    # placeholder "SNS Development Platform" tenant above (the `return`
    # in that branch means we never reach here for a fresh tenant). If a
    # caller points DEV_PLATFORM_TENANT_ID_ENV at an existing real tenant
    # (e.g. to give an OWNER-role login access to a production agency),
    # we must not silently mutate that tenant's billing configuration.


def provision_development_logins(
    db: Session, *, roles: Optional[Iterable[str]] = None
) -> int:
    """Create/update configured development identities without implicit secrets.

    ``roles`` scopes which of the module-level ``DEVELOPMENT_IDENTITIES`` are
    processed on this call, matched against ``DevelopmentIdentity.role``.

    - ``roles=None`` (the default) preserves the existing, unscoped bootstrap
      behavior: every globally configured identity is reconciled. This is what
      real startup (``app/main.py``) and the operator script
      (``scripts/seed_login_accounts.py``) rely on, and it must keep working
      unchanged.
    - Passing an explicit ``roles`` iterable (e.g. ``{"DPCS_ADMINISTRATOR",
      "OWNER", "BILLING"}``) restricts processing to only those roles. This
      lets a caller — in particular a test — provision a small, explicit set
      of identities without silently reconciling every other globally
      configured identity (including acceptance identities such as
      MEDICAL_DIRECTOR) onto whatever tenant the caller happens to have
      configured for its own test run.
    """
    provisioned = 0
    role_filter = set(roles) if roles is not None else None

    for identity in DEVELOPMENT_IDENTITIES:
        if role_filter is not None and identity.role not in role_filter:
            continue
        email = (os.getenv(identity.email_env) or "").strip().lower()
        password = os.getenv(identity.password_env)

        if not email and not password:
            continue
        if not email:
            raise RuntimeError(f"{identity.email_env} is required when {identity.password_env} is configured")
        if password is not None and len(password) < MIN_PASSWORD_LENGTH:
            raise RuntimeError(
                f"{identity.password_env} must be at least {MIN_PASSWORD_LENGTH} characters"
            )

        tenant_id = _configured_uuid(identity.tenant_env)
        # Scope the lookup by tenant too, not just email: uq_users_tenant_email
        # is a per-tenant unique constraint, so the same email can now
        # legitimately exist as separate rows across multiple tenants (see
        # the cross-agency account linking feature). Filtering by email
        # alone would raise MultipleResultsFound as soon as that happens.
        user = (
            db.query(User)
            .filter(func.lower(User.email) == email, User.tenant_id == tenant_id)
            .one_or_none()
        )
        if user is None and password is None:
            continue

        _ensure_tenant(
            db,
            tenant_id,
            platform=identity.tenant_env == DEV_PLATFORM_TENANT_ID_ENV,
        )

        if user is None:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=email,
                full_name=identity.full_name,
                role=identity.role,
                access_level="FULL_ACCESS",
                active=True,
            )
            db.add(user)
        else:
            user.tenant_id = tenant_id
            user.email = email
            user.full_name = identity.full_name
            user.role = identity.role
            user.access_level = "FULL_ACCESS"
            user.active = True

        if password is not None:
            user.password_hash = hash_password(password)

        provisioned += 1

    if provisioned:
        db.commit()
    return provisioned
