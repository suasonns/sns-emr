from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

import sqlalchemy as sa
from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ---------------------------------------------------------
# ✅ ENVIRONMENT (MUST BE FIRST)
# ---------------------------------------------------------
load_dotenv(".env.local")
load_dotenv()

# ---------------------------------------------------------
# ✅ PYTHON PATH FIX (ENTERPRISE SAFE)
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
# ✅ IMPORT ALL MODELS (CRITICAL)
# ---------------------------------------------------------
from app.db.base import Base  # noqa: E402

# ✅ IMPORTANT: force full model registry load
import app.models  # noqa: F401

# If you ever split models across modules, explicitly import:
# import app.models.clinical_notes
# import app.models.audit_logs
# import app.models.notifications
# etc.

target_metadata = Base.metadata

# ---------------------------------------------------------
# ✅ DATABASE URL (OWNER-FIRST)
# ---------------------------------------------------------
def get_database_url() -> str:
    url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
    )

    if not url:
        raise RuntimeError("DATABASE URL not configured")

    return url

# ---------------------------------------------------------
# ✅ RUN MIGRATIONS (ONLINE ONLY)
# ---------------------------------------------------------
def run_migrations_online() -> None:
    engine = create_engine(
        get_database_url(),
        future=True,
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as connection:

        # ✅ GLOBAL SCHEMA SAFETY
        connection.execute(
            sa.text("SET search_path TO public, core")
        )

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,  # ✅ prevent tenant schema confusion
        )

        with context.begin_transaction():
            context.run_migrations()

# ---------------------------------------------------------
# ✅ ENTRYPOINT
# ---------------------------------------------------------
run_migrations_online()
