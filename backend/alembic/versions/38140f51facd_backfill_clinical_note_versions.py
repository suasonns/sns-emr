"""backfill clinical note versions from legacy clinical_notes content

Revision ID: 38140f51facd
Revises: 36cf26b0088f
Create Date: 2026-06-16

Purpose:
- Backfill version 1 rows into clinical_note_versions for all pre-existing clinical_notes
- Set clinical_notes.current_version_id to the active version row
- Preserve full history without overwriting legacy note content

Important:
- Forward-only migration
- Safe to run multiple times (idempotent)
"""

from alembic import op
import sqlalchemy as sa


revision = "38140f51facd"
down_revision = "36cf26b0088f"
branch_labels = None
depends_on = None


def upgrade():
    # ✅ STEP 1 — Backfill version 1 rows (ONLY if not already exists)
    op.execute(sa.text("""
        INSERT INTO clinical_note_versions (
            id,
            clinical_note_id,
            version_number,
            content,
            amend_reason,
            created_at,
            created_by,
            is_active
        )
        SELECT
            gen_random_uuid(),
            cn.id,
            1,
            cn.content,
            NULL,
            COALESCE(cn.created_at, now()),
            cn.created_by,
            true
        FROM clinical_notes cn
        WHERE NOT EXISTS (
            SELECT 1
            FROM clinical_note_versions cnv
            WHERE cnv.clinical_note_id = cn.id
        )
    """))

    # ✅ STEP 2 — Set pointer to active version
    op.execute(sa.text("""
        UPDATE clinical_notes cn
        SET current_version_id = cnv.id
        FROM clinical_note_versions cnv
        WHERE cnv.clinical_note_id = cn.id
          AND cnv.version_number = 1
          AND cnv.is_active = true
          AND cn.current_version_id IS NULL
    """))


def downgrade():
    # Safe partial rollback only for version 1 rows
    op.execute(sa.text("""
        DELETE FROM clinical_note_versions cnv
        USING clinical_notes cn
        WHERE cn.current_version_id = cnv.id
          AND cnv.clinical_note_id = cn.id
          AND cnv.version_number = 1
          AND cnv.amend_reason IS NULL
    """))

    op.execute(sa.text("""
        UPDATE clinical_notes
        SET current_version_id = NULL
        WHERE current_version_id IS NOT NULL
    """))
