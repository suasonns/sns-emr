from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.database import DATABASE_URL, get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.main import fastapi_app
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


# ---------------------------------------------------------------------
# HARD DATABASE ISOLATION (do not weaken this)
#
# Incident 2026-08-26: this suite previously ran destructive, tenant-scoped
# DELETE sweeps through app.core.database.SessionLocal -- the SAME session
# the running dev app uses -- and the "test tenant id" it targeted defaulted
# to the REAL Love & Faith Hospice tenant id. Every local test run wiped and
# repopulated that tenant with synthetic fixtures, permanently destroying
# real patient records (including hand-entered test H&P patients) with no
# reliable backup.
#
# Fix: tests get their OWN engine/session bound to a database that is
# PHYSICALLY SEPARATE from DATABASE_URL (see backend/_create_test_db.py,
# which builds "sns_emr_test" from the current models/migrations). The
# guard below refuses to run anything -- loudly, at collection time -- if
# that isolation cannot be verified. A tenant-id mismatch alone is NOT
# trusted as a safety mechanism anymore.
# ---------------------------------------------------------------------


def _derive_test_database_url() -> str:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return override
    parts = urlsplit(DATABASE_URL)
    if not parts.path.lstrip("/"):
        raise RuntimeError(
            "Cannot derive a test database URL: DATABASE_URL has no database name. "
            "Set TEST_DATABASE_URL explicitly."
        )
    return urlunsplit(parts._replace(path="/sns_emr_test"))


TEST_DATABASE_URL = _derive_test_database_url()

_test_engine = create_engine(
    TEST_DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args={"options": "-csearch_path=public -c TimeZone=UTC"},
)

TestSessionLocal = sessionmaker(
    bind=_test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def _assert_tests_are_isolated_from_dev_db() -> None:
    dev_parts = urlsplit(DATABASE_URL)
    dev_dbname = dev_parts.path.lstrip("/")

    if TEST_DATABASE_URL == DATABASE_URL:
        raise RuntimeError(
            "REFUSING TO RUN TESTS: TEST_DATABASE_URL is identical to the "
            "application's DATABASE_URL. Tests must run against a physically "
            "separate database. See backend/_create_test_db.py."
        )

    with _test_engine.connect() as conn:
        dbname = conn.execute(text("SELECT current_database()")).scalar()

    if dbname == dev_dbname:
        raise RuntimeError(
            f"REFUSING TO RUN TESTS: the test engine is connected to '{dbname}', "
            f"which is the SAME database name as the app's DATABASE_URL "
            f"('{dev_dbname}'). Tests must never share a database with the app."
        )
    if "test" not in (dbname or "").lower():
        raise RuntimeError(
            f"REFUSING TO RUN TESTS: connected database '{dbname}' does not look "
            "like a dedicated test database (expected a name containing 'test'). "
            "Refusing to run destructive test fixtures against it."
        )


_assert_tests_are_isolated_from_dev_db()


# ---------------------------------------------------------------------
# Redirect EVERY SessionLocal() call, app-wide, to the isolated test engine.
#
# The codebase has ~15 separate ad-hoc "get_db"-style dependencies scattered
# across app/ (db_tenant_dependency.py, tenant_routing_middleware.py,
# api/audit_dashboard.py, api/visits.py, api/routes/forms.py, etc.), each
# doing its own `from app.core.database import SessionLocal` and then
# `SessionLocal()`. Overriding FastAPI's `Depends(get_db)` alone does NOT
# reach any of these -- they bypass dependency_overrides entirely.
#
# All of them share the exact same `SessionLocal` sessionmaker OBJECT
# (Python import binds a reference, not a copy), so reconfiguring that one
# object's bind is the single choke point that redirects every one of them
# to the isolated test database, with no way for a new ad-hoc dependency to
# silently slip through.
# ---------------------------------------------------------------------

from app.core import database as _app_database  # noqa: E402

_app_database.SessionLocal.configure(bind=_test_engine)
_app_database.engine = _test_engine

try:
    from app.core import sync_db as _app_sync_db  # noqa: E402

    _app_sync_db.SyncSessionLocal.configure(bind=_test_engine)
    _app_sync_db.SYNC_ENGINE = _test_engine
except Exception:
    pass


@pytest.fixture(scope="session", autouse=True)
def _route_app_db_dependency_to_test_database():
    """Belt-and-suspenders: also override FastAPI's Depends(get_db) so the
    `client` fixture's HTTP-level tests are explicit about using the test
    session, on top of the sessionmaker-level redirect above."""

    def _test_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _test_get_db
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------
# Audit defaults for fixtures
#
# patients.created_by and admissions.admission_date are NOT NULL because a
# record needs an author and an admission needs a date. Fixtures across the
# suite predate both, so they are filled here rather than weakening the model.
# ---------------------------------------------------------------------

@event.listens_for(Patient, "before_insert")
def _default_patient_created_by(mapper, connection, target) -> None:
    if getattr(target, "created_by", None) is None:
        target.created_by = TEST_USER_ID


@event.listens_for(Admission, "before_insert")
def _default_admission_date(mapper, connection, target) -> None:
    if getattr(target, "admission_date", None) is None:
        target.admission_date = datetime.now(timezone.utc).replace(tzinfo=None)
    if getattr(target, "created_by", None) is None:
        target.created_by = TEST_USER_ID


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
    # Purely a synthetic id local to the isolated sns_emr_test database.
    # This must NEVER match a real tenant id -- see the isolation guard
    # above for why a tenant-id check alone is not trusted as a safeguard.
    return os.getenv("REAL_TENANT_ID", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def login_headers(client: TestClient, user_id: str, role: str) -> dict:
    token = create_access_token(
        user_id=TEST_USER_ID,
        role=role,
        tenant_id=uuid.UUID(_test_tenant_id()),
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

    Bound to the isolated sns_emr_test database (see the isolation guard
    at the top of this file) -- never the app's real DATABASE_URL/tenant.
    Explicitly bypasses tenant ORM enforcement. This does NOT affect
    production behavior.
    """
    session = TestSessionLocal()

    tenant_id = _test_tenant_id()

    # Physician Identity Mapping (owner directive 2026-08-21) added
    # users.physician_id -> physicians.id. "users" is retained across tests
    # (see _RETAINED below) but "physicians" is not, so any lingering link
    # from a prior test would block deleting physicians here. Clear it first.
    #
    # Defect fixed here (traced 2026-08-22): this statement previously
    # nulled physician_id WITHOUT resetting physician_link_status, so a
    # user a prior test had linked (ACTIVE) or unlinked (ENDED) kept that
    # stale status label with physician_id now NULL — reproducing the
    # exact ACTIVE+NULL / ENDED+NULL anomaly found in the shared dev DB
    # across repeated local test runs. Reset both together.
    session.execute(
        text(
            "UPDATE users SET physician_id = NULL, physician_link_status = 'UNLINKED' "
            "WHERE tenant_id = :tenant_id"
        ),
        {"tenant_id": uuid.UUID(tenant_id)},
    )
    session.commit()

    # A handful of tables own tenant-scoped data (patient_payers, etc.)
    # WITHOUT a tenant_id column of their own -- the tenant_id-scoped sweep
    # below can't target them at all, so a leftover row from an earlier
    # test/run survives indefinitely and can block deleting its parent
    # (e.g. a stale patient_payers row blocks deleting its patient, which
    # then collides with a fresh test trying to reuse that MRN). Clean
    # these explicitly first, scoped through their tenant-scoped parent.
    for _sql in (
        "DELETE FROM patient_payers WHERE patient_id IN "
        "(SELECT id FROM patients WHERE tenant_id = :tenant_id)",
    ):
        try:
            session.execute(text(_sql), {"tenant_id": uuid.UUID(tenant_id)})
        except Exception:
            session.rollback()
    session.commit()

    # Delete child rows before parents; the generated schema enforces the FKs
    # that the old hand-built database did not. sorted_tables can't fully
    # topologically order everything (see the physicians<->users cycle
    # warning below), so a single pass may hit an FK violation for tables
    # outside that cycle too (e.g. chha_visit_outcomes / chha_visit_task_
    # results). Retry failed deletes in dependency-agnostic passes -- each
    # pass runs in its own SAVEPOINT so one failure doesn't abort the rest.
    _RETAINED = {"tenants", "users", "roles", "interfaces"}
    _candidates = [
        table
        for table in reversed(Base.metadata.sorted_tables)
        if table.name not in _RETAINED and "tenant_id" in table.c
    ]
    for _pass in range(len(_candidates) + 1):
        if not _candidates:
            break
        remaining = []
        for table in _candidates:
            nested = session.begin_nested()
            try:
                session.execute(
                    table.delete().where(table.c.tenant_id == uuid.UUID(tenant_id))
                )
                nested.commit()
            except Exception:
                nested.rollback()
                remaining.append(table)
        if len(remaining) == len(_candidates):
            # No progress this pass -- give up retrying and let the final
            # commit surface whatever's left.
            break
        _candidates = remaining
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

    # Tests reference this well-known id as created_by/provider; the generated
    # schema enforces the FK to users that the old database lacked.
    if session.get(User, TEST_USER_ID) is None:
        session.add(
            User(
                id=TEST_USER_ID,
                tenant_id=uuid.UUID(tenant_id),
                email="test.user@sns.local",
                full_name="Test User",
                role="RN",
                active=True,
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