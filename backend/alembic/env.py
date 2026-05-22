from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool, text
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load environment variables
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
    db_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not db_url:
        raise RuntimeError("DATABASE_URL or sqlalchemy.url must be set")

    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    return db_url


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
        future=True,
    )

    with engine.connect() as connection:
        # Optional debug: print DB user when requested
        x_args = context.get_x_argument(as_dictionary=True)
        if x_args.get("check_user") == "true":
            who = connection.execute(text("select current_user")).scalar()
            dbn = connection.execute(text("select current_database()")).scalar()
            prt = connection.execute(text("show port")).scalar()
            print(f"ALEMBIC DB USER: {who} | DB: {dbn} | PORT: {prt}")

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
