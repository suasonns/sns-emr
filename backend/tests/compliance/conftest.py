"""
Compliance test scaffolding.

These tests are guardrail tests designed to prevent regression
against /docs/compliance/core_rules.md.

Rules:
- Keep tests fast
- Deterministic only
- Use xfail for unimplemented enforcement
- FK-safe fixtures (Patient exists before Visit insert)
"""

import uuid
import pytest
from datetime import datetime, timezone, date

from fastapi.testclient import TestClient
from sqlalchemy import String, Integer, Boolean, Date, DateTime, text
from sqlalchemy.sql.sqltypes import Enum as SAEnum

try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
except Exception:
    PG_UUID = None
    JSONB = None

# IMPORTANT: FastAPI instance is app.main:api (not app.main:app)
import app.main as main_module
from fastapi import FastAPI

# Resolve FastAPI instance without guessing variable names
app = None

for attr in ("app", "api", "application", "fastapi_app"):
    candidate = getattr(main_module, attr, None)
    if isinstance(candidate, FastAPI):
        app = candidate
        break

# Factory pattern support
if app is None and hasattr(main_module, "create_app"):
    candidate = main_module.create_app()
    if isinstance(candidate, FastAPI):
        app = candidate

if app is None:
    raise RuntimeError(
        "Could not locate FastAPI application instance in app.main. "
        "Expected one of: app, api, application, fastapi_app, or create_app()."
    )

from app.models.visit import Visit
from app.models.user import User
from app.models.patient import Patient
from app.models.enums import VisitFormType

# ---------------------------------------------------------
# Deterministic helpers (enterprise-grade)
# ---------------------------------------------------------

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")
FIXED_NOW_UTC = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


def require_visit_attr(attr_name: str):
    if not hasattr(Visit, attr_name):
        pytest.xfail(f"Visit.{attr_name} not implemented yet.")


def _default_for_column(col, provider_user_id=None):
    """
    Produce a safe default for NOT NULL columns when no default/server_default exists.
    Test scaffolding only.
    """
    if col.name in ("created_by", "updated_by") and provider_user_id:
        return provider_user_id

    if PG_UUID is not None:
        impl = getattr(col.type, "impl", col.type)
        if isinstance(impl, PG_UUID):
            return uuid.uuid5(_UUID_NS, f"fixture:{col.name}")

    if JSONB is not None and isinstance(col.type, JSONB):
        return {}

    if isinstance(col.type, String):
        return "TEST"
    if isinstance(col.type, Boolean):
        return False
    if isinstance(col.type, Integer):
        return 0
    if isinstance(col.type, Date):
        return date(1950, 1, 1)
    if isinstance(col.type, DateTime):
        return FIXED_NOW_UTC

    return "TEST"


def _pick_patient_status(db_session, preferred="ACTIVE"):
    """
    Determine a valid patients.status value without guessing.
    Works for Postgres ENUMs. Falls back to preferred string.
    """
    try:
        rows = db_session.execute(
            text(
                """
                SELECT e.enumlabel
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_type t ON t.oid = a.atttypid
                JOIN pg_enum e ON e.enumtypid = t.oid
                WHERE c.relname = 'patients'
                  AND a.attname = 'status'
                ORDER BY e.enumsortorder;
                """
            )
        ).fetchall()

        labels = [r[0] for r in rows]
        if not labels:
            return preferred
        if preferred in labels:
            return preferred
        return labels[0]
    except Exception:
        return preferred


# ---------------------------------------------------------
# Pytest markers
# ---------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "core_rule(section): marks a test as covering a core_rules.md section",
    )
    config.addinivalue_line(
        "markers",
        "requires_impl(name): test requires implementation to exist",
    )


# ---------------------------------------------------------
# Shared compliance fixtures
# ---------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def provider_user(db_session):
    """
    Deterministic user required by Visit.provider_id FK -> users.id
    """
    user_id = stable_uuid("user:provider")

    existing = db_session.get(User, user_id)
    if existing:
        return existing

    user = User(
        id=user_id,
        tenant_id=db_session.info.get("tenant_id"),
        email="provider.test@sns.local",
        full_name="Compliance Test Provider",
        role="RN",
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def ensure_patient(db_session, provider_user):
    """
    FK-safe patient creator that adapts to the real Patient model.
    Ensures required DB constraints are satisfied (including patients.status and uq_patients_tenant_mrn).
    """
    def _ensure(patient_id: uuid.UUID):
        existing = db_session.get(Patient, patient_id)
        if existing:
            return existing

        cols = {c.name: c for c in Patient.__table__.columns}
        kwargs = {}

        if "id" in cols:
            kwargs["id"] = patient_id

        if "tenant_id" in cols:
            kwargs["tenant_id"] = db_session.info.get("tenant_id")

        # Fill remaining NOT NULL columns that lack defaults
        for name, col in cols.items():
            if name in kwargs:
                continue
            if col.default is not None or col.server_default is not None:
                continue
            if col.nullable:
                continue
            if col.primary_key and getattr(col, "autoincrement", False):
                continue

            kwargs[name] = _default_for_column(col, provider_user_id=getattr(provider_user, "id", None))

        # Critical: patients.status NOT NULL
        if "status" in cols and "status" not in kwargs and not cols["status"].nullable:
            status_col = cols["status"]
            if isinstance(status_col.type, SAEnum) and getattr(status_col.type, "enums", None):
                enums = list(status_col.type.enums)
                kwargs["status"] = "ACTIVE" if "ACTIVE" in enums else enums[0]
            else:
                kwargs["status"] = _pick_patient_status(db_session, preferred="ACTIVE")

        # Critical: uq_patients_tenant_mrn
        if "mrn" in cols:
            kwargs["mrn"] = f"MRN-{str(patient_id)[:8]}"

        # Optional: stable full_name for readability
        if "full_name" in cols and "full_name" not in kwargs:
            kwargs["full_name"] = f"TEST PATIENT {str(patient_id)[:8]}"

        patient = Patient(**kwargs)
        db_session.add(patient)
        db_session.flush()
        return patient

    return _ensure


@pytest.fixture
def routine_rn_visit(db_session, provider_user, ensure_patient):
    patient_id = stable_uuid("patient:routine_rn")
    ensure_patient(patient_id)

    visit_id = stable_uuid("visit:routine_rn")

    existing = db_session.get(Visit, visit_id)
    if existing:
        existing.form_type = VisitFormType.ASSESS.value
        db_session.commit()
        db_session.refresh(existing)
        return existing

    visit = Visit(
        id=visit_id,
        tenant_id=db_session.info.get("tenant_id"),
        patient_id=patient_id,
        provider_id=provider_user.id,
        visit_type="RN",
        visit_discipline="RN",
        form_type=VisitFormType.ASSESS.value,
        acuity_state_at_visit="ROUTINE",
        is_supervisory=False,
        visit_datetime=FIXED_NOW_UTC,
        status="DRAFT",
        visit_mode="IN_PERSON",
    )
    
    db_session.add(visit)
    db_session.commit()
    return visit

@pytest.fixture
def administrative_visit(db_session, provider_user, ensure_patient):
    patient_id = stable_uuid("patient:administrative")
    ensure_patient(patient_id)

    visit_id = stable_uuid("visit:administrative")

    existing = db_session.get(Visit, visit_id)
    if existing:
        return existing

    visit = Visit(
        id=visit_id,
        tenant_id=db_session.info.get("tenant_id"),
        patient_id=patient_id,
        provider_id=provider_user.id,
        visit_type="ADMINISTRATIVE",
        visit_discipline="ADMINISTRATIVE",
        acuity_state_at_visit=None,
        is_supervisory=False,
        visit_datetime=FIXED_NOW_UTC,
        status="DRAFT",
        visit_mode="IN_PERSON",
    )
    db_session.add(visit)
    db_session.commit()
    return visit

@pytest.fixture
def telephone_rn_visit(db_session, provider_user, ensure_patient):
    require_visit_attr("visit_mode")

    patient_id = stable_uuid("patient:telephone_rn")
    ensure_patient(patient_id)

    visit_id = stable_uuid("visit:telephone_rn")

    existing = db_session.get(Visit, visit_id)
    if existing:
        return existing

    visit = Visit(
        id=visit_id,
        tenant_id=db_session.info.get("tenant_id"),
        patient_id=patient_id,
        provider_id=provider_user.id,
        visit_type="RN",
        visit_discipline="RN",
        visit_mode="TELEPHONE",
        acuity_state_at_visit="ROUTINE",
        is_supervisory=True,
        visit_datetime=FIXED_NOW_UTC,
        status="DRAFT",
    )
    db_session.add(visit)
    db_session.commit()
    return visit