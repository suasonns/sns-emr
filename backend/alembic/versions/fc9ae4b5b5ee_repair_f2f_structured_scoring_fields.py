"""repair f2f structured scoring fields

Revision ID: fc9ae4b5b5ee
Revises: 5dd64799f776
Create Date: 2026-06-22

"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = "fc9ae4b5b5ee"
down_revision = "5dd64799f776"
branch_labels = None
depends_on = None


def upgrade():
    """
    REPAIR MIGRATION ONLY.

    The F2F structured scoring fields were already added manually in the
    target PostgreSQL database before this Alembic revision was run.

    Therefore, this migration intentionally performs NO schema mutation.
    Its purpose is to align Alembic revision history to the already-correct
    database schema without rewriting migration history.
    """
    pass


def downgrade():
    """
    No-op downgrade.

    This revision is a repair/stamp alignment migration only.
    """
    pass