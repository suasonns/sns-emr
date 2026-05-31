"""create benefit periods table

Revision ID: eb851de9e5e1
Revises: 924041973331
Create Date: 2026-04-30 12:40:19.663958
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "eb851de9e5e1"
down_revision = "924041973331"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enterprise-safe migration:
    - Idempotent for PostgreSQL
    - Safe in online and offline Alembic modes
    - Does not depend on op.get_bind()
    - Does not depend on users table for created_by FK
    """

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS benefit_periods (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES patients(id),
            benefit_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NULL,
            is_current BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            created_by UUID NULL
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_benefit_periods_patient_id
        ON benefit_periods (patient_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_benefit_periods_start_date
        ON benefit_periods (start_date);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_benefit_periods_end_date
        ON benefit_periods (end_date);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_benefit_periods_is_current
        ON benefit_periods (is_current);
        """
    )


def downgrade() -> None:
    """
    Safe rollback for development / controlled environments.
    """
    op.execute("DROP INDEX IF EXISTS ix_benefit_periods_is_current;")
    op.execute("DROP INDEX IF EXISTS ix_benefit_periods_end_date;")
    op.execute("DROP INDEX IF EXISTS ix_benefit_periods_start_date;")
    op.execute("DROP INDEX IF EXISTS ix_benefit_periods_patient_id;")
    op.execute("DROP TABLE IF EXISTS benefit_periods;")