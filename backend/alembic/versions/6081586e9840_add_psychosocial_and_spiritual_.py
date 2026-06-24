from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6081586e9840"
down_revision: Union[str, Sequence[str], None] = "28394d291963"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add discipline-specific completion reference types.

    This is a forward-only PostgreSQL enum extension.
    Safe to run multiple times due to IF NOT EXISTS.
    """

    op.execute(
        "ALTER TYPE tasks_completion_ref_enum ADD VALUE IF NOT EXISTS 'PSYCHOSOCIAL_NOTE';"
    )

    op.execute(
        "ALTER TYPE tasks_completion_ref_enum ADD VALUE IF NOT EXISTS 'SPIRITUAL_NOTE';"
    )


def downgrade() -> None:
    """
    PostgreSQL enums are forward-only in practice.

    We DO NOT remove enum values because:
    - existing rows may depend on them
    - PostgreSQL does not support safe removal
    """
    pass
