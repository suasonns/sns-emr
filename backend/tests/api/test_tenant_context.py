# tests/api/test_tenant_context.py

from types import SimpleNamespace

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.tenancy.context import set_tenant_context, require_valid_tenant
from app.db_tenant_dependency import get_db_tenant


def test_set_tenant_context_sets_db_info_unit():
    """
    Unit proof: the tenant context initializer sets db.info keys.
    """

    class DummyDB:
        def __init__(self):
            self.info = {}

    dummy_db = DummyDB()
    dummy_user = SimpleNamespace(tenant_id="tenant-123", id="user-456")

    # Call function directly with explicit args.
    # Depends() is resolved only by FastAPI at runtime.
    set_tenant_context(db=dummy_db, user=dummy_user)

    assert dummy_db.info["tenant_id"] == "tenant-123"
    assert dummy_db.info["user_id"] == "user-456"


def test_router_dependency_executes_and_sets_context_runtime():
    """
    Runtime proof: router-level dependency executes on request
    and populates db.info via set_tenant_context.
    """

    app = FastAPI()

    # Fake DB session with .info
    class DummyDB:
        def __init__(self):
            self.info = {}

    dummy_db = DummyDB()

    # Override DB dependency
    app.dependency_overrides[get_db_tenant] = lambda: dummy_db

    # Override tenant guard to bypass auth
    app.dependency_overrides[require_valid_tenant] = lambda: SimpleNamespace(
        tenant_id="tenant-abc",
        id="user-def",
        role="ADMIN",
    )

    @app.get("/_tenant_context_probe", dependencies=[Depends(set_tenant_context)])
    def probe(db=Depends(get_db_tenant)):
        return {
            "tenant_id": db.info.get("tenant_id"),
            "user_id": db.info.get("user_id"),
        }

    client = TestClient(app)
    response = client.get("/_tenant_context_probe")

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-abc"
    assert response.json()["user_id"] == "user-def"