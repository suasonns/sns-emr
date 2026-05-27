from __future__ import annotations

from dataclasses import dataclass
import pytest
from fastapi.testclient import TestClient

from app.main import fastapi_app
from app.core.database import SessionLocal


# ---------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    return TestClient(fastapi_app)


# ---------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------

def login_headers(client: TestClient, user_id: str, role: str) -> dict:
    r = client.post(
        "/auth/dev-login",
        json={
            "user_id": user_id,
            "role": role,
            "tenant_id": "01271980-0000-0000-0000-000005101977",
        },
    )
    assert r.status_code == 200, r.text

    token = r.json().get("access_token")
    assert token, f"dev-login returned no access_token: {r.json()}"

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
# Database Session (TEST‑ONLY BYPASS)
# ---------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """
    Test database session.

    Explicitly bypasses tenant ORM enforcement.
    This does NOT affect production behavior.
    """
    session = SessionLocal()

    # ✅ REQUIRED FOR UNIT TESTS
    session.info["skip_tenant_filter"] = True
    session.info["tenant_id"] = "01271980-0000-0000-0000-000005101977"

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
    return _TestTenant(
        id="01271980-0000-0000-0000-000005101977"
    )