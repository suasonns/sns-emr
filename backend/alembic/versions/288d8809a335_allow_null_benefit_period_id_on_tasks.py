"""allow_null_benefit_period_id_on_tasks

Revision ID: 288d8809a335
Revises: 1a965fb41bc2
Create Date: 2026-05-28 16:33:20.019364

Forward-only repair migration.
Allows tasks.benefit_period_id to be NULL.
"""

from typing import Sequence, Union
from alembic import op

revision: str = "288d8809a335"
down_revision: Union[str, Sequence[str], None] = "1a965fb41bc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.tasks ALTER COLUMN benefit_period_id DROP NOT NULL;")


def downgrade() -> None:
    # forward-only
    pass
