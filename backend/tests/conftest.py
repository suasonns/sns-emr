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
    """TEST_DATABASE_URL is now REQUIRED, with no fallback -- see the
    2026-09-03 incident where every session silently defaulting to the same
    shared 'sns_emr_test' database caused cross-session schema collisions
    (tables vanishing mid-run, migration deadlocks). Use
    `backend/scripts/run_isolated_tests.py` to get one automatically."""
    override = os.getenv("TEST_DATABASE_URL")
    if not override:
        raise RuntimeError(
            "TEST_DATABASE_URL_REQUIRED: Tests must use an explicitly "
            "isolated database. Run tests via "
            "`python backend/scripts/run_isolated_tests.py -- <pytest args>` "
            "instead of invoking pytest directly."
        )
    return override


TEST_DATABASE_URL = _derive_test_database_url()

_SNS_TEST_WORKTREE_ID = os.getenv("SNS_TEST_WORKTREE_ID", "unknown")
_SNS_TEST_RUN_ID = os.getenv("SNS_TEST_RUN_ID", "unknown")
_TEST_APPLICATION_NAME = (
    f"sns-emr-test:{_SNS_TEST_WORKTREE_ID}:{_SNS_TEST_RUN_ID}:{os.getpid()}"
)

_test_engine = create_engine(
    TEST_DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args={
        "options": "-csearch_path=public -c TimeZone=UTC",
        "application_name": _TEST_APPLICATION_NAME,
    },
)

TestSessionLocal = sessionmaker(
    bind=_test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def _assert_tests_are_isolated_from_dev_db() -> None:
    dev_parts = urlsplit(DATABASE_URL)
    dev_dbname = dev_parts.path.lstrip("/")

    if TEST_DATABASE_URL == DATABASE_URL:
        raise RuntimeError(
            "TEST_DATABASE_ISOLATION_VIOLATION: DATABASE_URL and "
            "TEST_DATABASE_URL resolve to the same database."
        )

    with _test_engine.connect() as conn:
        dbname = conn.execute(text("SELECT current_database()")).scalar()

    if dbname == dev_dbname:
        raise RuntimeError(
            f"TEST_DATABASE_ISOLATION_VIOLATION: the test engine is "
            f"connected to '{dbname}', which is the SAME database name as "
            f"the app's DATABASE_URL ('{dev_dbname}'). Tests must never "
            "share a database with the app."
        )
    from scripts.test_db_identity import UnsafeTestDatabaseNameError, validate_database_name

    try:
        validate_database_name(dbname or "")
    except UnsafeTestDatabaseNameError as exc:
        raise RuntimeError(str(exc)) from exc


_assert_tests_are_isolated_from_dev_db()


# ---------------------------------------------------------------------
# Automated catalog seed data (form_modules / form_registry /
# form_package_modules)
#
# backend/seed_catalog.sql has, since 4ba6a9a, contained the reference
# catalog rows (including the RN_ASSESS and HHA_VISIT form_key entries)
# that form_resolution_service.resolve_form_package() requires -- but no
# automated test-setup path ever loaded it, so any test exercising visit
# creation for a discipline/event_type that resolves to one of these
# form_keys failed with "Configured form_key '...' does not exist or is
# inactive" against an empty form_registry table. seed_catalog.sql uses
# native psql `COPY ... FROM stdin` syntax (no psql CLI is available in
# this environment), so parse its COPY blocks here and load them via
# psycopg2's copy_expert against the isolated test engine.
#
# Safe to run every session: none of these 3 tables have a tenant_id
# column, so they are never touched by db_session's per-test tenant-scoped
# cleanup sweep, and this loader only inserts when a table is empty.
# ---------------------------------------------------------------------

def _load_seed_catalog_data() -> None:
    import io
    import re
    from pathlib import Path

    seed_path = Path(__file__).resolve().parents[1] / "seed_catalog.sql"
    if not seed_path.exists():
        return

    sql_text = seed_path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"COPY (public\.\w+) \(([^)]*)\) FROM stdin;\n(.*?)\n\\\.",
        sql_text,
        flags=re.DOTALL,
    )
    if not blocks:
        return

    raw_conn = _test_engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        for table, columns_raw, data in blocks:
            table_name = table.split(".", 1)[-1]
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            (existing,) = cursor.fetchone()
            if existing:
                continue

            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s",
                (table_name,),
            )
            real_columns = {row[0] for row in cursor.fetchall()}

            seed_columns = [c.strip() for c in columns_raw.split(",")]
            keep_indexes = [
                i for i, col in enumerate(seed_columns) if col in real_columns
            ]
            if not keep_indexes:
                continue

            kept_columns = ", ".join(seed_columns[i] for i in keep_indexes)
            display_order_pos = None
            if "display_order" in real_columns:
                try:
                    display_order_pos = seed_columns.index("display_order")
                except ValueError:
                    display_order_pos = None

            filtered_lines = []
            for row_num, line in enumerate(data.split("\n"), start=1):
                if not line:
                    continue
                fields = line.split("\t")
                # form_package_modules.display_order is NOT NULL in the
                # current schema, but seed_catalog.sql predates that
                # constraint and stores \N (NULL) for every row. Fill in a
                # synthetic sequential value rather than dropping the row.
                if display_order_pos is not None and fields[display_order_pos] == "\\N":
                    fields[display_order_pos] = str(row_num)
                filtered_lines.append(
                    "\t".join(fields[i] for i in keep_indexes)
                )
            filtered_data = "\n".join(filtered_lines) + "\n"

            # Each block runs in its own savepoint: form_package_modules'
            # seed rows predate a display_order NOT NULL tightening and can
            # legitimately fail to load without that dooming the
            # form_registry rows the visit-creation tests actually need.
            cursor.execute("SAVEPOINT seed_block")
            try:
                cursor.copy_expert(
                    f"COPY {table} ({kept_columns}) FROM STDIN",
                    io.StringIO(filtered_data),
                )
            except Exception as exc:
                cursor.execute("ROLLBACK TO SAVEPOINT seed_block")
                print(f"[seed] Skipped {table_name} seed data: {exc}")
            else:
                cursor.execute("RELEASE SAVEPOINT seed_block")
                print(f"[seed] Loaded catalog seed data into {table_name}.")
        raw_conn.commit()
    finally:
        raw_conn.close()


_load_seed_catalog_data()


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