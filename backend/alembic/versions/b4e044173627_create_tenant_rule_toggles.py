"""create tenant_rule_toggles

Revision ID: b4e044173627
Revises: cad04af9916b
Create Date: 2026-05-22 18:52:23.236100
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b4e044173627"
down_revision: Union[str, Sequence[str], None] = "cad04af9916b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # If table already exists (manual create), do nothing.
    # Alembic will still stamp the revision as applied.
    if "tenant_rule_toggles" in inspector.get_table_names(schema="public"):
        return

    op.create_table(
        "tenant_rule_toggles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "workflow",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_tenant_rule_toggles_tenant",
        "tenant_rule_toggles",
        ["tenant_id"],
    )
    op.create_index(
        "ix_tenant_rule_toggles_workflow",
        "tenant_rule_toggles",
        ["workflow"],
    )
    op.create_index(
        "ix_tenant_rule_toggles_rule_id",
        "tenant_rule_toggles",
        ["rule_id"],
    )

    op.create_unique_constraint(
        "uq_tenant_rule_toggle_one",
        "tenant_rule_toggles",
        ["tenant_id", "workflow", "rule_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tenant_rule_toggle_one",
        "tenant_rule_toggles",
        type_="unique",
    )
    op.drop_index(
        "ix_tenant_rule_toggles_rule_id",
        table_name="tenant_rule_toggles",
    )
    op.drop_index(
        "ix_tenant_rule_toggles_workflow",
        table_name="tenant_rule_toggles",
    )
    op.drop_index(
        "ix_tenant_rule_toggles_tenant",
        table_name="tenant_rule_toggles",
    )
    op.drop_table("tenant_rule_toggles")