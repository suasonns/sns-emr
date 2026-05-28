"""repair_create_foundation_tables_autocommit

Revision ID: f5ee8cb51e19
Revises: de6941fcac1d
Create Date: 2026-05-27 18:55:44.576512

Forward-only repair migration.

Ensures foundational tables exist in sns_emr_dev_clean.public:
- tenants
- roles
- interfaces

Runs DDL in AUTOCOMMIT after explicitly ending Alembic's active transaction.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f5ee8cb51e19"
down_revision = "de6941fcac1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Alembic/SQLAlchemy may already have an open transaction.
    # We must end it before changing isolation_level.
    try:
        if bind.in_transaction():
            bind.commit()
    except Exception:
        # If commit isn't allowed for any reason, rollback safely.
        try:
            bind.rollback()
        except Exception:
            pass

    # Now we can safely use AUTOCOMMIT for DDL.
    conn = bind.execution_options(isolation_level="AUTOCOMMIT")

    # Create tables defensively
    conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS public.tenants (
            id uuid PRIMARY KEY,
            name varchar(200) NOT NULL DEFAULT 'DEV',
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp NOT NULL DEFAULT now(),
            created_by uuid
        );
    """)

    conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS public.roles (
            id uuid PRIMARY KEY,
            name varchar(100) NOT NULL,
            created_at timestamp NOT NULL DEFAULT now()
        );
    """)

    conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS public.interfaces (
            id uuid PRIMARY KEY,
            name varchar(120) NOT NULL,
            created_at timestamp NOT NULL DEFAULT now()
        );
    """)

    # Create indexes defensively
    conn.exec_driver_sql("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_roles_name
        ON public.roles(name);
    """)

    conn.exec_driver_sql("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_interfaces_name
        ON public.interfaces(name);
    """)


def downgrade() -> None:
    # Forward-only repair migration
    pass
