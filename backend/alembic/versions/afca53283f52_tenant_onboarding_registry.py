"""tenant onboarding registry

Revision ID: afca53283f52
Revises: e8ddd8217e52
Create Date: 2026-06-03 08:07:49.622733
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "afca53283f52"
down_revision: Union[str, Sequence[str], None] = "e8ddd8217e52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ✅ SNS Hospice EMR — Tenant Onboarding Registry (Enterprise Safe)

    This migration is intentionally idempotent because:
    - earlier attempts may have partially created objects
    - we must not drop or rewrite history
    - we must still guarantee the required guardrails exist
    """

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ---------------------------------------------------------
    # 1) Ensure enum exists (safe / idempotent)
    # ---------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'tenant_status'
            ) THEN
                CREATE TYPE tenant_status AS ENUM ('ACTIVE', 'SUSPENDED', 'ARCHIVED');
            END IF;
        END$$;
        """
    )

    tenant_status_enum = postgresql.ENUM(
        "ACTIVE",
        "SUSPENDED",
        "ARCHIVED",
        name="tenant_status",
        create_type=False,  # ✅ do not attempt CREATE TYPE
    )

    # ---------------------------------------------------------
    # 2) Create core.tenants only if missing
    # ---------------------------------------------------------
    tenants_exists = inspector.has_table("tenants", schema="core")

    if not tenants_exists:
        op.create_table(
            "tenants",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("schema_name", sa.Text(), nullable=False, unique=True),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("status", tenant_status_enum, nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
            schema="core",
        )

    # ---------------------------------------------------------
    # 3) Guardrail: prevent tenant deletes (function + trigger)
    #    Your screenshot shows NO trigger exists → we enforce it.
    # ---------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION core.prevent_tenant_delete()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Tenants may not be deleted (audit integrity)';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_no_tenant_delete'
                  AND tgrelid = 'core.tenants'::regclass
            ) THEN
                CREATE TRIGGER trg_no_tenant_delete
                BEFORE DELETE ON core.tenants
                FOR EACH ROW
                EXECUTE FUNCTION core.prevent_tenant_delete();
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    """
    ⚠️ Downgrade intentionally blocked.
    Tenant registry is foundational for audit integrity.
    """
    raise RuntimeError("Downgrade not permitted for tenant registry")
