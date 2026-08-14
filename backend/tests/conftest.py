from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import fastapi_app
from app.models.tenant import Tenant


# ---------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    return TestClient(fastapi_app)


# ---------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------

def _test_tenant_id() -> str:
    return os.getenv("REAL_TENANT_ID", "01271980-0000-0000-0000-000005101977")


def login_headers(client: TestClient, user_id: str, role: str) -> dict:
    token = create_access_token(
        subject=str(uuid.uuid4()),
        role=role,
        tenant_id=_test_tenant_id(),
        email=f"{user_id}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def rn_headers(client):
    return login_headers(client, user_id="nurse_test", role="RN")


@pytest.fixture()
def chha_headers(client):
    return login_headers(client, user_id="aide_test", role="CHHA")


@pytest.fixture()
def volunteer_headers(client):
    return login_headers(client, user_id="vol_test", role="VOLUNTEER")


# ---------------------------------------------------------------------
# Database Session (TEST-ONLY BYPASS)
# ---------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """
    Test database session.

    Explicitly bypasses tenant ORM enforcement.
    This does NOT affect production behavior.
    """
    session = SessionLocal()

    tenant_id = _test_tenant_id()

    session.execute(text("DELETE FROM tasks WHERE tenant_id = CAST(:tenant_id AS UUID)"), {"tenant_id": tenant_id})
    session.execute(text("DELETE FROM patients WHERE tenant_id = CAST(:tenant_id AS UUID)"), {"tenant_id": tenant_id})
    session.commit()

    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        session.add(
            Tenant(
                id=tenant_id,
                legal_name="Love & Faith Hospice",
                display_name="Love & Faith",
                npi="1234567890",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        session.commit()

    session.info["skip_tenant_filter"] = True
    session.info["tenant_id"] = tenant_id

    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------
# Canonical Tenant Fixture (OBJECT, NOT STRING)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class _TestTenant:
    id: str


@pytest.fixture()
def tenant():
    return _TestTenant(id=_test_tenant_id())