"""add_dx_primary_policy_table

Revision ID: 11fee75738cb19:02:46.279253Revision ID: 11fee75738cb
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "11fee75738cb"
down_revision: Union[str, Sequence[str], None] = "515c21f1f8de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure UUID support
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "dx_primary_policy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code_pattern", sa.String(length=16), nullable=False),
        sa.Column(
            "pattern_type",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'LIKE'"),
        ),
        sa.Column(
            "allow_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "allow_secondary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "code_pattern",
            "pattern_type",
            name="uq_dx_primary_policy_tenant_pattern",
        ),
    )

    op.create_index(
        "ix_dx_primary_policy_tenant",
        "dx_primary_policy",
        ["tenant_id"],
    )
    op.create_index(
        "ix_dx_primary_policy_pattern",
        "dx_primary_policy",
        ["code_pattern"],
    )

    dx_policy = sa.table(
        "dx_primary_policy",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("tenant_id", postgresql.UUID(as_uuid=True)),
        sa.column("code_pattern", sa.String),
        sa.column("pattern_type", sa.String),
        sa.column("allow_primary", sa.Boolean),
        sa.column("allow_secondary", sa.Boolean),
        sa.column("reason", sa.Text),
    )

    op.bulk_insert(
        dx_policy,
        [
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "F%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "Mental/behavioral codes not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "R%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "Signs/symptoms not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "V%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "External cause codes not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "W%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "External cause codes not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "X%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "External cause codes not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "Y%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "External cause codes not allowed as hospice primary dx",
            },
            {
                "id": uuid.uuid4(),
                "tenant_id": None,
                "code_pattern": "Z%",
                "pattern_type": "LIKE",
                "allow_primary": False,
                "allow_secondary": True,
                "reason": "Encounter/status Z codes not allowed as hospice primary dx",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_dx_primary_policy_pattern", table_name="dx_primary_policy")
    op.drop_index("ix_dx_primary_policy_tenant", table_name="dx_primary_policy")
    op.drop_table("dx_primary_policy")

