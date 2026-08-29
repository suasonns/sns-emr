"""Build/rebuild the isolated `sns_emr_test` database from the current
Alembic migrations (the true source of truth for production schema).

conftest.py's docstring has referenced this script since the 2026-08-26
DB-isolation incident, but it never actually existed in the repo — so the
test database's schema silently drifted out of sync with migrations/models
(missing columns such as `client_request_id`, and later `field_provenance`,
`processing_status`) and dozens of tests failed for infrastructure reasons
unrelated to any code under test.

This script is intentionally NOT run automatically by pytest. Run it by hand
(or wire it into CI) whenever migrations change and test failures look like
missing-column/missing-table/missing-type errors rather than real assertion
failures:

    python backend/_create_test_db.py

Implementation note: this previously used SQLAlchemy's
`Base.metadata.create_all()`, but several models (e.g. IDGMeeting's
`idg_status_enum`) declare `create_type=False` because their Postgres ENUM
types are created by a migration, not by SQLAlchemy metadata -- so
`create_all()` alone can never fully reconstruct the schema. Running the
real Alembic migration chain (`alembic upgrade head`) against the test
database is both correct (it's exactly what production runs) and complete.

Safety: refuses to run against anything that isn't named like a test
database, mirroring the guard in tests/conftest.py.
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.database import DATABASE_URL


def _derive_test_database_url() -> str:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return override
    parts = urlsplit(DATABASE_URL)
    return urlunsplit(parts._replace(path="/sns_emr_test"))


def main() -> None:
    test_url = _derive_test_database_url()
    dbname = urlsplit(test_url).path.lstrip("/")

    if "test" not in dbname.lower():
        raise RuntimeError(
            f"REFUSING TO REBUILD '{dbname}': does not look like a test "
            "database (expected a name containing 'test')."
        )

    engine = create_engine(test_url, future=True)

    with engine.connect() as conn:
        actual_dbname = conn.execute(text("SELECT current_database()")).scalar()
        if "test" not in (actual_dbname or "").lower():
            raise RuntimeError(
                f"REFUSING TO REBUILD: connected database is '{actual_dbname}', "
                "which does not look like a test database."
            )

    # Base.metadata.drop_all() only drops tables it knows about, in FK-aware
    # order -- it doesn't know about (and can't CASCADE through) plain SQL
    # views like patient_face_sheet_view that depend on those tables, or
    # types/enums outside metadata. Drop and recreate the whole public schema
    # instead so leftover views/objects/types from prior schema versions can
    # never block the rebuild.
    print(f"[rebuild] Dropping and recreating schema 'public' in '{dbname}'...")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    print(f"[rebuild] Running Alembic migrations against '{dbname}'...")
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    os.environ["MIGRATION_DATABASE_URL"] = test_url
    # env.py's load_dotenv(override=False) will re-populate EXPECTED_DB from
    # .env if we merely pop it, so set it to a value that matches the test
    # DB instead of trying to unset it.
    os.environ["EXPECTED_DB"] = dbname
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        os.environ.pop("MIGRATION_DATABASE_URL", None)
    print("[rebuild] Done. Schema now matches current Alembic migrations.")


if __name__ == "__main__":
    main()
