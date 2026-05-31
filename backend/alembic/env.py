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
# Load environment variables
# ---------------------------------------------------------
load_dotenv(".env.local")
load_dotenv()

# ---------------------------------------------------------
# Ensure backend path
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ---------------------------------------------------------
# Alembic config
# ---------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------
# Import models
# ---------------------------------------------------------
from app.db.base import Base  # noqa
import app.models  # noqa

target_metadata = Base.metadata


# ---------------------------------------------------------
# DB URL
# ---------------------------------------------------------
def get_database_url() -> str:
    url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
    )
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


# ---------------------------------------------------------
# RUN MIGRATIONS ONLINE (FINAL FIX)
# ---------------------------------------------------------
def run_migrations_online() -> None:
    engine = create_engine(
        get_database_url(),
        future=True,
        isolation_level="AUTOCOMMIT",  # 🔥 KEY FIX
    )

    with engine.connect() as connection:
        connection.execute(sa.text("SET search_path TO public"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        context.run_migrations()


# ---------------------------------------------------------
# ENTRY
# ---------------------------------------------------------
run_migrations_online()
