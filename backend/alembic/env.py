from __future__ import annotations

import os
import sys
import hashlib
from logging.config import fileConfig
from pathlib import Path

import sqlalchemy as sa
from alembic import context
from dotenv import load_dotenv
from sqlalchemy import CheckConstraint, create_engine
from sqlalchemy.sql.elements import conv

# ✅ Alembic script access (for validation guard)
from alembic.script import ScriptDirectory


# ---------------------------------------------------------
# ✅ ENVIRONMENT (SAFE + ORDERED)
# ---------------------------------------------------------
# Real environment variables (shell / CI / cloud) always win over dotenv files.
load_dotenv(".env.local", override=False)
load_dotenv(override=False)


# ---------------------------------------------------------
# ✅ PYTHON PATH FIX
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ---------------------------------------------------------
# ✅ ALEMBIC CONFIG
# ---------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------
# ✅ IMPORT BASE
# ---------------------------------------------------------
from app.db.base import Base  # noqa: E402


# ---------------------------------------------------------
# ✅ AUTO-LOAD MODELS (FAIL FAST)
# ---------------------------------------------------------
import pkgutil  # noqa: E402
import importlib  # noqa: E402
import app.models  # noqa: E402

FAILED_IMPORTS: list[tuple[str, str]] = []


def load_all_models():
    for _, module_name, _ in pkgutil.walk_packages(
        app.models.__path__,
        app.models.__name__ + ".",
    ):
        try:
            importlib.import_module(module_name)
        except Exception as e:
            FAILED_IMPORTS.append((module_name, str(e)))


load_all_models()

if FAILED_IMPORTS:
    raise RuntimeError(
        f"Model import failures detected: {FAILED_IMPORTS}"
    )


def normalize_postgresql_check_names() -> None:
    """Match metadata names to PostgreSQL's deterministic 63-byte identifiers."""
    max_identifier_length = 63
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if not isinstance(constraint, CheckConstraint):
                continue
            name = str(constraint.name)
            if len(name) <= max_identifier_length:
                continue
            digest = hashlib.md5(name.encode(), usedforsecurity=False).hexdigest()[-4:]
            constraint.name = conv(f"{name[:max_identifier_length - 8]}_{digest}")


normalize_postgresql_check_names()


# ---------------------------------------------------------
# ✅ TARGET METADATA
# ---------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------
# ✅ BLOCK DESTRUCTIVE AUTOGENERATE (CRITICAL LOCK)
# ---------------------------------------------------------
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        if reflected and compare_to is None:
            return False

    if type_ == "column":
        if reflected and compare_to is None:
            return False

    return True


# ---------------------------------------------------------
# ✅ MIGRATION VALIDATION GUARD (RUNTIME PROTECTION)
# ---------------------------------------------------------
def validate_migration_safety():
    script = ScriptDirectory.from_config(config)

    revision = script.get_current_head()
    rev = script.get_revision(revision)

    if not rev:
        return

    migration_path = Path(rev.module.__file__)
    content = migration_path.read_text()

    # ✅ Extract ONLY upgrade() block
    import re

    upgrade_match = re.search(
        r"def upgrade\(.*?\):(.*?)(def downgrade|$)",
        content,
        re.S,
    )

    if not upgrade_match:
        return

    upgrade_content = upgrade_match.group(1)

    dangerous_ops = [
        "op.drop_table",
        "op.drop_column",
        "op.drop_index",
    ]

    violations = [op for op in dangerous_ops if op in upgrade_content]

    if violations:
        raise RuntimeError(
            f"""
🚨 UNSAFE MIGRATION DETECTED (UPGRADE ONLY)

Revision: {revision}
File: {migration_path}

Blocked operations in upgrade():
{violations}

✅ Fix: Remove destructive operations from upgrade().
"""
        )


# ---------------------------------------------------------
# ✅ DATABASE URL (STRICT)
# ---------------------------------------------------------
def _redact_url(url: str) -> str:
    try:
        return sa.engine.make_url(url).render_as_string(hide_password=True)
    except Exception:
        return "<unparseable-database-url>"


def get_database_url() -> str:
    url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
    )

    if not url:
        raise RuntimeError("DATABASE URL not configured")

    # Guard only applies when an expected database name is declared (local/dev).
    expected_db = os.getenv("EXPECTED_DB", "").strip()

    if expected_db and expected_db not in url:
        raise RuntimeError(
            f"WRONG DATABASE DETECTED: {_redact_url(url)}. Expected {expected_db}"
        )

    print(f"[ALEMBIC] Using DATABASE_URL: {_redact_url(url)}")

    return url


# ---------------------------------------------------------
# ✅ RUN MIGRATIONS (ONLINE ONLY, ENTERPRISE SAFE)
# ---------------------------------------------------------
def run_migrations_online() -> None:
    # BLOCK BAD MIGRATIONS BEFORE EXECUTION
    validate_migration_safety()

    engine = create_engine(
        get_database_url(),
        future=True,
        pool_pre_ping=True,
    )

    with engine.begin() as connection:

        # ✅ FORCE SCHEMA
        connection.exec_driver_sql("SET search_path = public")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
            include_schemas=False,
            version_table_schema="public",
            transaction_per_migration=True,
        )

        try:
            with context.begin_transaction():
                context.run_migrations()

            print(" Alembic migration completed successfully")

        except Exception as e:
            print(" MIGRATION FAILED")
            print(f"Error: {str(e)}")
            raise


# ---------------------------------------------------------
# ✅ ENTRYPOINT
# ---------------------------------------------------------
if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported")

run_migrations_online()