"""create guardrail_policies

Revision ID: 959032ecd284
Revises: 84a63a08a99d
Create Date: 2026-06-26 13:13:41.694319
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "959032ecd284"
down_revision: Union[str, Sequence[str], None] = "84a63a08a99d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "guardrail_policies"


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(index_name: str, table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx.get("name") == index_name for idx in indexes)


def upgrade():
    # ---------------------------------------------------------
    # Create table only if missing
    # ---------------------------------------------------------
    if not _table_exists(TABLE_NAME):
        op.create_table(
            TABLE_NAME,
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("policy_key", sa.String(length=128), nullable=False),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "value_type",
                sa.String(length=16),
                nullable=False,
                server_default="STRING",
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "effective_date",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.PrimaryKeyConstraint("id", name="pk_guardrail_policies"),
            sa.CheckConstraint(
                "value_type IN ('STRING', 'INTEGER', 'BOOLEAN', 'JSON')",
                name="ck_guardrail_policies_value_type",
            ),
        )

    # ---------------------------------------------------------
    # Indexes / uniqueness
    # ---------------------------------------------------------
    if not _index_exists("uq_guardrail_policies_tenant_key", TABLE_NAME):
        op.create_index(
            "uq_guardrail_policies_tenant_key",
            TABLE_NAME,
            ["tenant_id", "policy_key"],
            unique=True,
        )

    if not _index_exists("ix_guardrail_policies_tenant_id", TABLE_NAME):
        op.create_index(
            "ix_guardrail_policies_tenant_id",
            TABLE_NAME,
            ["tenant_id"],
            unique=False,
        )

    if not _index_exists("ix_guardrail_policies_is_active", TABLE_NAME):
        op.create_index(
            "ix_guardrail_policies_is_active",
            TABLE_NAME,
            ["is_active"],
            unique=False,
        )

    # ---------------------------------------------------------
    # Auto-update updated_at on UPDATE
    # ---------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_guardrail_policies_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        f"""
        DROP TRIGGER IF EXISTS trg_guardrail_policies_updated_at ON {TABLE_NAME};
        CREATE TRIGGER trg_guardrail_policies_updated_at
        BEFORE UPDATE ON {TABLE_NAME}
        FOR EACH ROW
        EXECUTE FUNCTION update_guardrail_policies_updated_at();
        """
    )

    # ---------------------------------------------------------
    # Seed default policy rows for all existing tenants
    # ---------------------------------------------------------
    op.execute(
        f"""
        INSERT INTO {TABLE_NAME} (
            tenant_id,
            policy_key,
            value,
            description,
            value_type,
            is_active,
            effective_date,
            created_at,
            updated_at
        )
        SELECT
            t.id,
            seed.policy_key,
            seed.value,
            seed.description,
            seed.value_type,
            true,
            now(),
            now(),
            now()
        FROM tenants t
        CROSS JOIN (
            VALUES
                (
                    'MIN_NARRATIVE_LENGTH',
                    '200',
                    'Minimum characters required for clinical eligibility narrative',
                    'INTEGER'
                ),
                (
                    'REQUIRE_MEASURABLE_DECLINE',
                    'true',
                    'Require documented measurable evidence of decline for admission support',
                    'BOOLEAN'
                ),
                (
                    'ENFORCE_LCD_RULES',
                    'true',
                    'Apply LCD/documentation consistency rules during admission guardrail evaluation',
                    'BOOLEAN'
                ),
                (
                    'GUARDRAIL_MODE',
                    'GUIDANCE',
                    'Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT',
                    'STRING'
                )
        ) AS seed(policy_key, value, description, value_type)
        ON CONFLICT (tenant_id, policy_key) DO NOTHING;
        """
    )


def downgrade():
    # ---------------------------------------------------------
    # Drop trigger + function
    # ---------------------------------------------------------
    op.execute(
        "DROP TRIGGER IF EXISTS trg_guardrail_policies_updated_at ON guardrail_policies;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS update_guardrail_policies_updated_at();"
    )

    # ---------------------------------------------------------
    # Drop indexes if table exists
    # ---------------------------------------------------------
    if _table_exists(TABLE_NAME):
        if _index_exists("ix_guardrail_policies_is_active", TABLE_NAME):
            op.drop_index("ix_guardrail_policies_is_active", table_name=TABLE_NAME)

        if _index_exists("ix_guardrail_policies_tenant_id", TABLE_NAME):
            op.drop_index("ix_guardrail_policies_tenant_id", table_name=TABLE_NAME)

        if _index_exists("uq_guardrail_policies_tenant_key", TABLE_NAME):
            op.drop_index("uq_guardrail_policies_tenant_key", table_name=TABLE_NAME)

        # ---------------------------------------------------------
        # Drop table
        # ---------------------------------------------------------
        op.drop_table(TABLE_NAME)