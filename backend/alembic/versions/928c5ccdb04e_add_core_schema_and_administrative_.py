"""add core schema and administrative tables

Revision ID: 928c5ccdb04e
Revises: 9d4fccab1558
Create Date: 2026-06-01 11:19:46

This migration introduces the administrative control plane (core schema).
It is intentionally limited to NON-CLINICAL, NON-PHI tables.

NO existing schemas or tables are modified.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "928c5ccdb04e"
down_revision = "9d4fccab1558"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 1) Create core schema (administrative only)
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    # ------------------------------------------------------------------
    # 2) Create enums idempotently (enterprise-safe)
    #    This avoids DuplicateObject errors if types already exist.
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'core' AND t.typname = 'tenant_status'
            ) THEN
                CREATE TYPE core.tenant_status AS ENUM ('PROVISIONING','ACTIVE','SUSPENDED','ARCHIVED');
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'core' AND t.typname = 'user_status'
            ) THEN
                CREATE TYPE core.user_status AS ENUM ('ACTIVE','DISABLED');
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'core' AND t.typname = 'membership_role'
            ) THEN
                CREATE TYPE core.membership_role AS ENUM ('ADMIN','STAFF','READ_ONLY');
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'core' AND t.typname = 'tenant_event_type'
            ) THEN
                CREATE TYPE core.tenant_event_type AS ENUM (
                    'TENANT_CREATED',
                    'SCHEMA_CREATED',
                    'TENANT_ACTIVATED',
                    'TENANT_SUSPENDED',
                    'TENANT_ARCHIVED'
                );
            END IF;
        END$$;
        """
    )

    # ------------------------------------------------------------------
    # 3) core.tenants — Tenant Registry (NON-PHI)
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_code", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("schema_name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PROVISIONING",
                "ACTIVE",
                "SUSPENDED",
                "ARCHIVED",
                name="tenant_status",
                schema="core",
                create_type=False,  # critical: do NOT create type during table create
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        schema="core",
    )

    # ------------------------------------------------------------------
    # 4) core.tenant_events — Administrative Audit Trail
    # ------------------------------------------------------------------
    op.create_table(
        "tenant_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core.tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                "TENANT_CREATED",
                "SCHEMA_CREATED",
                "TENANT_ACTIVATED",
                "TENANT_SUSPENDED",
                "TENANT_ARCHIVED",
                name="tenant_event_type",
                schema="core",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("event_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("details_json", postgresql.JSONB),
        schema="core",
    )

    # ------------------------------------------------------------------
    # 5) core.users — Global Identity (NON-CLINICAL)
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ACTIVE",
                "DISABLED",
                name="user_status",
                schema="core",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        schema="core",
    )

    # ------------------------------------------------------------------
    # 6) core.user_tenants — User ↔ Tenant Membership
    # ------------------------------------------------------------------
    op.create_table(
        "user_tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core.users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core.tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM(
                "ADMIN",
                "STAFF",
                "READ_ONLY",
                name="membership_role",
                schema="core",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant_membership"),
        schema="core",
    )


def downgrade():
    # Downgrade ONLY removes core schema objects. Clinical schemas are never touched.
    op.drop_table("user_tenants", schema="core")
    op.drop_table("users", schema="core")
    op.drop_table("tenant_events", schema="core")
    op.drop_table("tenants", schema="core")

    op.execute("DROP TYPE IF EXISTS core.membership_role")
    op.execute("DROP TYPE IF EXISTS core.user_status")
    op.execute("DROP TYPE IF EXISTS core.tenant_event_type")
    op.execute("DROP TYPE IF EXISTS core.tenant_status")

    op.execute("DROP SCHEMA IF EXISTS core")