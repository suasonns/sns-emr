"""form_engine_phase1_core_fields

Revision ID: 2f227d63cf1f
Revises: 230ca950caa5
Create Date: 2026-06-23 10:13:19.002920
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f227d63cf1f'
down_revision: Union[str, Sequence[str], None] = '230ca950caa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ✅ Define enum safely (reuse without recreating)
form_type_enum = sa.Enum(
    'AFTER_DEATH',
    'AFTER_HOURS',
    'ANCILLARY_SUPPORT',
    'ASSESS',
    'BEREAVEMENT_VISIT',
    'DEATH_VISIT',
    'DECLINED_VISIT',
    'MISSED_VISIT',
    'OFFICE_HOURS',
    'ON_CALL_TRIAGE',
    'RESPITE_RELIEF',
    'SUPV_VISIT_ONLY',
    'VOLUNTEER_SUPPORT',
    'WEEKENDS',
    'SHORT_FORM',
    'PRE_ADMIT_EVAL',
    name='form_type_enum',
    create_type=False  # 🔒 CRITICAL: prevents duplicate enum creation
)


def upgrade():
    # ✅ Ensure enum exists
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'form_type_enum') THEN
            CREATE TYPE form_type_enum AS ENUM (
                'AFTER_DEATH',
                'AFTER_HOURS',
                'ANCILLARY_SUPPORT',
                'ASSESS',
                'BEREAVEMENT_VISIT',
                'DEATH_VISIT',
                'DECLINED_VISIT',
                'MISSED_VISIT',
                'OFFICE_HOURS',
                'ON_CALL_TRIAGE',
                'RESPITE_RELIEF',
                'SUPV_VISIT_ONLY',
                'VOLUNTEER_SUPPORT',
                'WEEKENDS',
                'SHORT_FORM',
                'PRE_ADMIT_EVAL'
            );
        END IF;
    END$$;
    """)

    # ✅ Add visits.form_type ONLY if missing
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='visits'
            AND column_name='form_type'
        ) THEN
            ALTER TABLE visits ADD COLUMN form_type form_type_enum;
        END IF;
    END$$;
    """)

    # ✅ Add clinical_notes.form_family
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='clinical_notes'
            AND column_name='form_family'
        ) THEN
            ALTER TABLE clinical_notes ADD COLUMN form_family TEXT;
        END IF;
    END$$;
    """)

    # ✅ Add clinical_notes.is_primary
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='clinical_notes'
            AND column_name='is_primary'
        ) THEN
            ALTER TABLE clinical_notes ADD COLUMN is_primary BOOLEAN DEFAULT TRUE NOT NULL;
        END IF;
    END$$;
    """)

    # ✅ Add clinical_notes.parent_note_id
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='clinical_notes'
            AND column_name='parent_note_id'
        ) THEN
            ALTER TABLE clinical_notes ADD COLUMN parent_note_id UUID;
        END IF;
    END$$;
    """)

def downgrade():
    # Reverse order (safe rollback)
    op.drop_column('clinical_notes', 'parent_note_id')
    op.drop_column('clinical_notes', 'is_primary')
    op.drop_column('clinical_notes', 'form_family')
    op.drop_column('visits', 'form_type')

    # ❌ DO NOT drop enum (safety — preserves shared dependencies)