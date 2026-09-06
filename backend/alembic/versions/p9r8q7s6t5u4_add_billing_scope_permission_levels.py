"""add permission level to billing provider service scopes

Revision ID: p9r8q7s6t5u4
Revises: n8m7b6v5c4x3
Create Date: 2026-09-06 11:55:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p9r8q7s6t5u4"
down_revision: Union[str, Sequence[str], None] = "n8m7b6v5c4x3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "billing_provider_agency_service_scopes",
        sa.Column(
            "permission_level",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'VIEW'"),
        ),
    )
    op.create_check_constraint(
        "ck_billing_provider_assignment_permission_level_valid",
        "billing_provider_agency_service_scopes",
        "permission_level IN ('VIEW', 'EDIT')",
    )


def downgrade() -> None:
    raise NotImplementedError("Forward-only migration")
