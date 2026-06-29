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
# ✅ AUTO-LOAD ALL MODELS (HARDENED VERSION)
# ---------------------------------------------------------
import pkgutil
import importlib
import app.models


FAILED_IMPORTS = []


def load_all_models():
    for _, module_name, _ in pkgutil.walk_packages(
        app.models.__path__,
        app.models.__name__ + "."
    ):
        try:
            importlib.import_module(module_name)
        except Exception as e:
            FAILED_IMPORTS.append((module_name, str(e)))


load_all_models()

# ✅ DEBUG OUTPUT (CRITICAL)
print("\n================ MODEL LOAD DEBUG ================\n")

if FAILED_IMPORTS:
    print("❌ FAILED IMPORTS:")
    for name, err in FAILED_IMPORTS:
        print(f" - {name}: {err}")
else:
    print("✅ ALL MODELS IMPORTED SUCCESSFULLY")

print("\n✅ LOADED TABLES:")
print(sorted(Base.metadata.tables.keys()))

print("\n=================================================\n")

# ---------------------------------------------------------
# ✅ TARGET METADATA
# ---------------------------------------------------------
target_metadata = Base.metadata

# ---------------------------------------------------------
# ✅ DATABASE URL
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
        connection.execute(sa.text("SET search_path TO public, core"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()

# ---------------------------------------------------------
# ✅ ENTRYPOINT
# ---------------------------------------------------------
if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported")

run_migrations_online()