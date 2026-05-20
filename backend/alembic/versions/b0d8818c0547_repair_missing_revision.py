"""Repair: restore missing Alembic revision b0d8818c0547

No-op repair migration added to restore Alembic continuity.
The database is already stamped at b0d8818c0547, but the revision file
was missing from the repository, preventing `alembic current` from running.

Forward-only. No schema changes.
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# --- Alembic identifiers ---
revision = "b0d8818c0547"
down_revision = "d0524c53226e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: repair migration only
    pass


def downgrade() -> None:
    # No-op: repair migration only
    pass
