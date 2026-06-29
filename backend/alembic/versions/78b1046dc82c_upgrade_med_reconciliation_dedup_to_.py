"""
upgrade med reconciliation dedup to signature-based index

Revision ID: 78b1046dc82c
Revises: decda975ef9e
Create Date: 2026-06-25
"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "78b1046dc82c"
down_revision = "decda975ef9e"
branch_labels = None
depends_on = None


OLD_INDEX_NAME = "uq_med_recon_active_patient_mednorm"
NEW_INDEX_NAME = "uq_med_recon_active_patient_signature"


def upgrade():
    """
    Upgrade from med-name-only active dedup to full normalized-signature active dedup.

    Old rule:
      - one active PENDING row per patient + med_name_normalized

    New rule:
      - one active PENDING row per patient + normalized signature:
          med_name_normalized + dose_normalized + route_normalized + frequency_normalized

    This allows:
      - same medication name with different doses/routes/frequencies
    while still blocking:
      - true duplicates of the same normalized signature
    """

    # ---------------------------------------------------------
    # Drop both indexes defensively so this migration can recover
    # from partial/manual DB changes without rewriting history.
    # ---------------------------------------------------------
    op.execute(
        f"""
        DROP INDEX IF EXISTS {OLD_INDEX_NAME};
        """
    )

    op.execute(
        f"""
        DROP INDEX IF EXISTS {NEW_INDEX_NAME};
        """
    )

    # ---------------------------------------------------------
    # Recreate the signature-based partial unique index
    # ---------------------------------------------------------
    op.execute(
        f"""
        CREATE UNIQUE INDEX {NEW_INDEX_NAME}
        ON med_reconciliation_items (
            patient_id,
            lower(med_name_normalized),
            lower(coalesce(dose_normalized, '')),
            lower(coalesce(route_normalized, '')),
            lower(coalesce(frequency_normalized, ''))
        )
        WHERE review_status = 'PENDING'
          AND med_name_normalized IS NOT NULL;
        """
    )


def downgrade():
    """
    Downgrade from signature-based dedup back to med-name-only dedup.

    IMPORTANT:
    This downgrade can fail if the database currently contains multiple active
    PENDING rows for the same patient + med_name_normalized with different
    dose/route/frequency values.

    To protect data integrity, we explicitly check for that condition and fail
    loudly instead of creating a broken downgrade.
    """

    conn = op.get_bind()

    conflict = conn.execute(
        text(
            """
            SELECT
                patient_id,
                lower(med_name_normalized) AS med_name_key,
                COUNT(*) AS active_count
            FROM med_reconciliation_items
            WHERE review_status = 'PENDING'
              AND med_name_normalized IS NOT NULL
            GROUP BY
                patient_id,
                lower(med_name_normalized)
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).fetchone()

    if conflict is not None:
        raise RuntimeError(
            "Cannot downgrade med reconciliation dedup index: "
            "multiple active PENDING rows now exist for the same patient + "
            "med_name_normalized under the signature-based rule. "
            "Resolve or collapse those rows first before downgrading."
        )

    op.execute(
        f"""
        DROP INDEX IF EXISTS {NEW_INDEX_NAME};
        """
    )

    op.execute(
        f"""
        CREATE UNIQUE INDEX {OLD_INDEX_NAME}
        ON med_reconciliation_items (
            patient_id,
            lower(med_name_normalized)
        )
        WHERE review_status = 'PENDING'
          AND med_name_normalized IS NOT NULL;
        """
    )
