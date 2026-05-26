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
if str(BASE_DIR) not in sys.path:
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
import app.models  # noqa: F401, E402

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Enterprise-safe DB resolution order:

    1) MIGRATION_DATABASE_URL  (DDL / Alembic only)
    2) DATABASE_URL            (application runtime)
    3) alembic.ini fallback    (last resort)
    """
    db_url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )

    if not db_url:
        raise RuntimeError(
            "MIGRATION_DATABASE_URL or DATABASE_URL must be set for Alembic"
        )

    # Force synchronous driver
    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace(
            "postgresql+asyncpg", "postgresql+psycopg2"
        )

    return db_url


# -------------------------------------------------------------------
# SAFETY GUARD — PREVENT MASS DROPS DURING AUTOGENERATE
# -------------------------------------------------------------------
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
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
        # Optional debug: print DB identity
        x_args = context.get_x_argument(as_dictionary=True)
        if x_args.get("check_user") == "true":
            who = connection.execute(
                text("select current_user")
            ).scalar()
            dbn = connection.execute(
                text("select current_database()")
            ).scalar()
            prt = connection.execute(
                text("show port")
            ).scalar()
            print(
                f"ALEMBIC CONNECTED AS: {who} | DB: {dbn} | PORT: {prt}"
            )

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()