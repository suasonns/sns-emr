"""add guardrail policies

Revision ID: 1d5baf814a70
Revises: c8679f4206f8
Create Date: 2026-08-03 13:41:38.297657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1d5baf814a70'
down_revision: Union[str, Sequence[str], None] = 'c8679f4206f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guardrail_policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "policy_key",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "policy_key",
            name="uq_guardrail_policy_tenant_key",
        ),
    )

    op.create_index(
        "ix_guardrail_policies_tenant_id",
        "guardrail_policies",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_guardrail_policies_policy_key",
        "guardrail_policies",
        ["policy_key"],
        unique=False,
    )

    op.create_index(
        "ix_guardrail_policies_tenant_key",
        "guardrail_policies",
        ["tenant_id", "policy_key"],
        unique=False,
    )

    op.create_index(
        "ix_guardrail_policies_enabled",
        "guardrail_policies",
        ["enabled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_guardrail_policies_enabled",
        table_name="guardrail_policies",
    )

    op.drop_index(
        "ix_guardrail_policies_tenant_key",
        table_name="guardrail_policies",
    )

    op.drop_index(
        "ix_guardrail_policies_policy_key",
        table_name="guardrail_policies",
    )

    op.drop_index(
        "ix_guardrail_policies_tenant_id",
        table_name="guardrail_policies",
    )

    op.drop_table("guardrail_policies")