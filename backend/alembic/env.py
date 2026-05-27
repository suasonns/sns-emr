from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import engine_from_config, pool

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------
load_dotenv(".env.local")
load_dotenv()

# -------------------------------------------------------------------
# Ensure backend/ is on PYTHONPATH so app.* imports work
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# -------------------------------------------------------------------
# Alembic Config object
# -------------------------------------------------------------------
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# Import canonical Base + import models for metadata registration
# -------------------------------------------------------------------
from app.db.base import Base  # noqa: E402,F401
import app.models  # noqa: E402,F401

target_metadata = Base.metadata

# -------------------------------------------------------------------
# Enterprise-safe DB URL resolution (MIGRATION DATABASE FIRST)
# -------------------------------------------------------------------
def get_database_url() -> str:
    url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
    )
    if not url:
        raise RuntimeError("Database URL not found. Set MIGRATION_DATABASE_URL or DATABASE_URL.")
    return url

# -------------------------------------------------------------------
# SCOPE GUARD: only autogenerate for ORM tables
# -------------------------------------------------------------------
def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in target_metadata.tables
    return True

# -------------------------------------------------------------------
# Normalize server defaults to reduce drift noise
# -------------------------------------------------------------------
def _normalize_default(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    s = s.replace(" ", "")
    s = s.replace("::character varying", "")
    s = s.replace("::text", "")
    return s

def compare_server_default(
    context_,
    inspected_column,
    metadata_column,
    inspected_default,
    metadata_default,
    rendered_metadata_default,
):
    left = _normalize_default(inspected_default)
    right = _normalize_default(rendered_metadata_default)
    return left != right

# -------------------------------------------------------------------
# Migration runners
# -------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=compare_server_default,
        include_object=include_object,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    # Force Alembic connections to use public schema
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
        connect_args={"options": "-csearch_path=public"},
    )

    with connectable.connect() as connection:
        # Belt + suspenders: ensure search_path is correct even if connect_args changes
        connection.execute(sa.text("SET search_path TO public"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=compare_server_default,
            include_object=include_object,
            version_table_schema="public",
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
