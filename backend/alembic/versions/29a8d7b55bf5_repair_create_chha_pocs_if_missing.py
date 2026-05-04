"""repair create chha_pocs if missing

Revision ID: 29a8d7b55bf5
Revises: 282649a795c2
Create Date: 2026-05-02 10:02:46.610208
"""

from alembic import op

revision = "29a8d7b55bf5"
down_revision = "282649a795c2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS chha_pocs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        patient_id UUID NOT NULL REFERENCES patients(id),

        status VARCHAR NOT NULL DEFAULT 'draft',

        effective_start DATE NULL,
        effective_end DATE NULL,

        frequency VARCHAR NULL,
        adl_scope TEXT NULL,
        instructions TEXT NULL,
        safety_precautions TEXT NULL,

        finalized_at TIMESTAMP NULL,
        finalized_by UUID NULL REFERENCES users(id),

        created_by UUID NULL REFERENCES users(id),
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_chha_pocs_patient_id ON chha_pocs(patient_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chha_pocs_status ON chha_pocs(status);")


def downgrade():
    # forward-only repair migration
    pass
