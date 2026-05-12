from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "435a3eb45748"
down_revision: Union[str, Sequence[str], None] = "38516eb3a508"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add IDG_POC_REVIEW to tasks_task_type_enum.

    This supports CMS 42 CFR 418.56(d) – IDG review at least every 15 calendar days.
    """
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'IDG_POC_REVIEW';
        EXCEPTION
            WHEN duplicate_object THEN
                -- enum value already exists; no-op
                NULL;
        END
        $$;
        """
    )


def downgrade() -> None:
    """
    Downgrade is intentionally a no-op.

    PostgreSQL does not safely support removing enum values without
    recreating the enum type, which is not survey-safe.
    """
    pass