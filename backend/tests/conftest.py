import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db_session import get_db as real_get_db


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def login_headers(client: TestClient, user_id: str, role: str) -> dict:
    r = client.post("/auth/dev-login", params={"user_id": user_id, "role": role})
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


@pytest.fixture()
def db_session():
    gen = real_get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass