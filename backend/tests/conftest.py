from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.db.base import Base
from app.main import fastapi_app
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


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
    return os.getenv("REAL_TENANT_ID", "01271980-0000-0000-0000-000005101977")


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

    Explicitly bypasses tenant ORM enforcement.
    This does NOT affect production behavior.
    """
    session = SessionLocal()

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