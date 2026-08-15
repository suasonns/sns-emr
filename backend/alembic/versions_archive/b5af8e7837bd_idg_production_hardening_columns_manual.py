"""idg_production_hardening_columns_manual

Revision ID: b5af8e7837bd
Revises: 1ebaf6300150
Create Date: 2026-08-04 17:44:58.418003

Manual scoped IDG production hardening migration.

DO NOT AUTOGENERATE.
DO NOT TOUCH unrelated tables.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b5af8e7837bd"
down_revision: Union[str, Sequence[str], None] = "1ebaf6300150"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # idg_notes
    # ---------------------------------------------------------

    op.execute("""
        ALTER TABLE idg_notes
        ADD COLUMN IF NOT EXISTS role_label VARCHAR(100);
    """)

    op.execute("""
        ALTER TABLE idg_notes
        ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'COMPLETED';
    """)

    op.execute("""
        ALTER TABLE idg_notes
        ADD COLUMN IF NOT EXISTS entered_by UUID;
    """)

    op.execute("""
        ALTER TABLE idg_notes
        ADD COLUMN IF NOT EXISTS entered_by_name VARCHAR(255);
    """)

    op.execute("""
        ALTER TABLE idg_notes
        ADD COLUMN IF NOT EXISTS updated_by UUID;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_notes_status
        ON idg_notes (status);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_notes_created_at
        ON idg_notes (created_at);
    """)

    # ---------------------------------------------------------
    # idg_signatures
    # ---------------------------------------------------------

    op.execute("""
        ALTER TABLE idg_signatures
        ADD COLUMN IF NOT EXISTS patient_id UUID;
    """)

    op.execute("""
        ALTER TABLE idg_signatures
        ADD COLUMN IF NOT EXISTS discipline VARCHAR(50);
    """)

    op.execute("""
        ALTER TABLE idg_signatures
        ADD COLUMN IF NOT EXISTS signed BOOLEAN NOT NULL DEFAULT false;
    """)

    op.execute("""
        ALTER TABLE idg_signatures
        ADD COLUMN IF NOT EXISTS signature_note TEXT;
    """)

    op.execute("""
        ALTER TABLE idg_signatures
        ADD COLUMN IF NOT EXISTS updated_by UUID;
    """)

    op.execute("""
        UPDATE idg_signatures
        SET signed = is_signed
        WHERE signed IS DISTINCT FROM is_signed;
    """)

    op.execute("""
        UPDATE idg_signatures s
        SET patient_id = r.patient_id
        FROM idg_reviews r
        WHERE s.idg_review_id = r.id
          AND s.patient_id IS NULL;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_signatures_patient_id
        ON idg_signatures (patient_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_signatures_discipline
        ON idg_signatures (discipline);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_signatures_signed_at
        ON idg_signatures (signed_at);
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_idg_signature_review_user'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM idg_signatures
                WHERE idg_review_id IS NOT NULL
                GROUP BY idg_review_id, user_id
                HAVING COUNT(*) > 1
            ) THEN
                ALTER TABLE idg_signatures
                ADD CONSTRAINT uq_idg_signature_review_user
                UNIQUE (idg_review_id, user_id);
            END IF;
        END $$;
    """)

    # ---------------------------------------------------------
    # idg_md_attestations
    # ---------------------------------------------------------

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS patient_id UUID;
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'PENDING';
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS attested BOOLEAN NOT NULL DEFAULT false;
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS attested_by UUID;
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS physician_role VARCHAR(100);
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS attested_at TIMESTAMP WITH TIME ZONE;
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS attestation_note TEXT;
    """)

    op.execute("""
        ALTER TABLE idg_md_attestations
        ADD COLUMN IF NOT EXISTS updated_by UUID;
    """)

    op.execute("""
        UPDATE idg_md_attestations md
        SET patient_id = r.patient_id
        FROM idg_reviews r
        WHERE md.idg_review_id = r.id
          AND md.patient_id IS NULL;
    """)

    op.execute("""
        UPDATE idg_md_attestations
        SET attested = is_signed
        WHERE attested IS DISTINCT FROM is_signed;
    """)

    op.execute("""
        UPDATE idg_md_attestations
        SET attested_at = signed_at
        WHERE attested_at IS NULL
          AND signed_at IS NOT NULL;
    """)

    op.execute("""
        UPDATE idg_md_attestations
        SET attested_by = physician_id
        WHERE attested_by IS NULL
          AND is_signed = true;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_md_attestations_patient_id
        ON idg_md_attestations (patient_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_md_attestations_attested_by
        ON idg_md_attestations (attested_by);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_md_attestations_attested_at
        ON idg_md_attestations (attested_at);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_idg_md_attestations_status
        ON idg_md_attestations (status);
    """)

    # ---------------------------------------------------------
    # family_concern_categories
    # ---------------------------------------------------------

    op.execute("""
        ALTER TABLE family_concern_categories
        ADD COLUMN IF NOT EXISTS description TEXT;
    """)


def downgrade() -> None:
    # Forward-only. Do not drop production hardening columns automatically.
    pass