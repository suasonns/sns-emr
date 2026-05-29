"""
Compatibility wrapper for database session dependencies.

This project defines the canonical SQLAlchemy SessionLocal in app.core.db.
This module re-exports a non-tenant-scoped get_db() dependency so that:

- Legacy imports do not break
- Compliance guardrail tests can execute without tenant/auth headers
- Production tenant enforcement remains explicit and opt-in

IMPORTANT:
- Do NOT add auth or tenant enforcement here
- Tenant-safe endpoints must use get_db_tenant instead
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.db import SessionLocal  # canonical session factory


def get_db() -> Generator[Session, None, None]:
    """
    Non-tenant-scoped DB session dependency.

    Intended use:
    - Compliance guardrail tests
    - System-level endpoints where auth/tenant is optional
    - Internal utilities that must not enforce tenant context

    DO NOT:
    - Enforce authentication
    - Enforce tenant headers
    - Inject request context

    Tenant-safe endpoints must explicitly depend on get_db_tenant.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()