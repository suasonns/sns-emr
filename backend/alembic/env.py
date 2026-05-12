from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load environment variables
# Priority:
#   1) .env.local  (local development)
#   2) .env        (fallback)
#   3) OS env      (Azure App Service)
# NOTE: Do NOT print secrets here.
# -------------------------------------------------------------------
load_dotenv(".env.local")
load_dotenv()

# -------------------------------------------------------------------
# Ensure backend/ is on PYTHONPATH so `app.*` imports work
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# -------------------------------------------------------------------
# Alembic Config object
# -------------------------------------------------------------------
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# Import models ONCE using the same path as the application
# -------------------------------------------------------------------
from app.models.base import Base  # noqa: E402
import app.models  # noqa: F401, E402  (loads all models)

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Alembic must use a synchronous SQLAlchemy engine.
    Force psycopg2 when app uses asyncpg.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # Ensure Alembic always uses sync driver
    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    return db_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (no DB connection).
    """
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (real DB connection).
    """
    engine = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()