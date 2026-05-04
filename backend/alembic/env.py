from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models.base import Base
import app.models

target_metadata = Base.metadata

import sys
from pathlib import Path

# -------------------------------------------------------------------
# Ensure backend/ is on PYTHONPATH so `app.*` imports work
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# -------------------------------------------------------------------
# Alembic config
# -------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# Import models ONCE using the same path as the application
# -------------------------------------------------------------------
from app.models.base import Base
import app.models  # <-- loads all models via app/models/__init__.py

# Metadata for autogenerate
target_metadata = Base.metadata

# -------------------------------------------------------------------
# Offline migrations
# -------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# -------------------------------------------------------------------
# Online migrations
# -------------------------------------------------------------------
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()