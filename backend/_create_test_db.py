"""Build/rebuild the isolated `sns_emr_test` database from the current
SQLAlchemy models.

conftest.py's docstring has referenced this script since the 2026-08-26
DB-isolation incident, but it never actually existed in the repo — so the
test database's schema silently drifted out of sync with migrations/models
(missing columns such as `client_request_id`, and later `field_provenance`)
and 45+ RNICA tests failed for infrastructure reasons unrelated to any code
under test.

This script is intentionally NOT run automatically by pytest. Run it by hand
(or wire it into CI) whenever the models change and test failures look like
missing-column/missing-table errors rather than real assertion failures:

    python backend/_create_test_db.py

Safety: refuses to run against anything that isn't named like a test
database, mirroring the guard in tests/conftest.py.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine, text

from app.core.database import DATABASE_URL
from app.db.base import Base

# Import every model module so its tables register on Base.metadata before
# create_all runs. (Base.metadata only knows about classes that have been
# imported somewhere.)
import app.models  # noqa: F401,E402


def _derive_test_database_url() -> str:
    import os

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

    print(f"[rebuild] Dropping all tables in '{dbname}'...")
    Base.metadata.drop_all(bind=engine)
    print(f"[rebuild] Creating all tables in '{dbname}' from current models...")
    Base.metadata.create_all(bind=engine)
    print("[rebuild] Done. Schema now matches current SQLAlchemy models.")


if __name__ == "__main__":
    main()
