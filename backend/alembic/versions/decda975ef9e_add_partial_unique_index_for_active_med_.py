"""
add partial unique index for active med reconciliation dedup

Revision ID: decda975ef9e
Revises: cb5114e26ded
Create Date: 2026-06-25 22:06:50.322255
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "decda975ef9e"
down_revision = "cb5114e26ded"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_med_recon_active_patient_mednorm"


def upgrade():
    """
    Create a PostgreSQL partial unique index enforcing:
    - Only one active (PENDING) med reconciliation item per patient + normalized medication name
    - Historical records (REVIEWED / REJECTED / ACCEPTED) remain unrestricted

    Notes:
    - lower(med_name_normalized) ensures case-insensitive dedup
    - med_name_normalized IS NOT NULL prevents null conflicts
    """

    # ✅ Defensive drop (ensures re-run safety in broken environments)
    op.execute(f"""
        DROP INDEX IF EXISTS {INDEX_NAME};
    """)

    # ✅ Create index
    op.execute(f"""
        CREATE UNIQUE INDEX {INDEX_NAME}
        ON med_reconciliation_items (
            patient_id,
            lower(med_name_normalized)
        )
        WHERE review_status = 'PENDING'
          AND med_name_normalized IS NOT NULL;
    """)


def downgrade():
    """
    Drop the partial unique index.
    """
    op.execute(f"""
        DROP INDEX IF EXISTS {INDEX_NAME};
    """)