"""add_unique_dx_primary_policy_per_tenant

Revision ID: ea4bb89ea152
Revises: b329f852f3bb
Create Date: 2026-05-20 16:28:18.469766
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ea4bb89ea152"
down_revision: Union[str, Sequence[str], None] = "b329f852f3bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce one dx_primary_policy row per tenant per ICD-10 prefix.

    This prevents duplicate CMS rules from being seeded multiple times.
    """

    op.create_unique_constraint(
        "uq_dx_primary_policy_tenant_code_pattern",
        "dx_primary_policy",
        ["tenant_id", "code_pattern"],
    )


def downgrade() -> None:
    # Forward-only by design (compliance stabilization)
    pass