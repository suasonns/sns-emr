"""add finalization role and interface snapshots

Revision ID: 34064ee66034
Revises: d6039fa93bd2
Create Date: 2026-05-07 09:44:17.453662
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# -------------------------------------------------------------------
# Alembic revision identifiers
# -------------------------------------------------------------------
revision: str = "34064ee66034"
down_revision: Union[str, Sequence[str], None] = "d6039fa93bd2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# -------------------------------------------------------------------
# Upgrade
# -------------------------------------------------------------------
def upgrade() -> None:
    # -------------------------------------------------------------
    # VISITS — finalized authorization snapshot
    # -------------------------------------------------------------
    op.add_column(
        "visits",
        sa.Column(
            "finalized_role_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "visits",
        sa.Column(
            "finalized_interface_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # -------------------------------------------------------------
    # CLINICAL NOTES — finalized authorization snapshot
    # -------------------------------------------------------------
    op.add_column(
        "clinical_notes",
        sa.Column(
            "finalized_role_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "clinical_notes",
        sa.Column(
            "finalized_interface_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # -------------------------------------------------------------
    # Foreign keys (snapshot-only, nullable by design)
    # -------------------------------------------------------------
    op.create_foreign_key(
        "fk_visits_finalized_role",
        "visits",
        "roles",
        ["finalized_role_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_visits_finalized_interface",
        "visits",
        "interfaces",
        ["finalized_interface_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_notes_finalized_role",
        "clinical_notes",
        "roles",
        ["finalized_role_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_notes_finalized_interface",
        "clinical_notes",
        "interfaces",
        ["finalized_interface_id"],
        ["id"],
    )

# -------------------------------------------------------------------
# Downgrade (included for completeness only)
# -------------------------------------------------------------------
def downgrade() -> None:
    op.drop_constraint(
        "fk_notes_finalized_interface",
        "clinical_notes",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notes_finalized_role",
        "clinical_notes",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_visits_finalized_interface",
        "visits",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_visits_finalized_role",
        "visits",
        type_="foreignkey",
    )

    op.drop_column("clinical_notes", "finalized_interface_id")
    op.drop_column("clinical_notes", "finalized_role_id")
    op.drop_column("visits", "finalized_interface_id")
    op.drop_column("visits", "finalized_role_id")