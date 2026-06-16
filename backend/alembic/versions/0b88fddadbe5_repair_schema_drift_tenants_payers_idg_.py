
"""repair schema drift: tenants/payers/idg/audit + notification tables

Revision ID: 0b88fddadbe5
Revises: 7a1fa136d905
Create Date: 2026-06-04 21:05:06.791241
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0b88fddadbe5"
down_revision: Union[str, Sequence[str], None] = "7a1fa136d905"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure UUID generator available (safe if already installed)
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # -------------------------
    # tenants
    # -------------------------
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type VARCHAR;")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS environment_tag VARCHAR;")

    # -------------------------
    # patient_payers
    # -------------------------
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS subscriber_id VARCHAR;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS subscriber_id_type VARCHAR;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS facility_name VARCHAR;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS effective_start_date DATE;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS end_date DATE;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS is_primary BOOLEAN;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE patient_payers ADD COLUMN IF NOT EXISTS created_by UUID;")

    # -------------------------
    # audit_logs
    # -------------------------
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id UUID;")

    # -------------------------
    # patient_assignments
    # -------------------------
    op.execute("ALTER TABLE patient_assignments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE patient_assignments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE patient_assignments ADD COLUMN IF NOT EXISTS created_by UUID;")

    # -------------------------
    # IDG tables
    # -------------------------
    op.execute("ALTER TABLE idg_meetings ADD COLUMN IF NOT EXISTS id UUID;")

    op.execute("ALTER TABLE idg_reviews ADD COLUMN IF NOT EXISTS idg_meeting_id UUID;")
    op.execute("ALTER TABLE idg_reviews ADD COLUMN IF NOT EXISTS tenant_id UUID;")
    op.execute("ALTER TABLE idg_reviews ADD COLUMN IF NOT EXISTS is_finalized BOOLEAN;")
    op.execute("ALTER TABLE idg_reviews ADD COLUMN IF NOT EXISTS finalized_by UUID;")

    op.execute("ALTER TABLE idg_notes ADD COLUMN IF NOT EXISTS id UUID;")
    op.execute("ALTER TABLE idg_notes ADD COLUMN IF NOT EXISTS note_text TEXT;")

    op.execute("ALTER TABLE idg_signatures ADD COLUMN IF NOT EXISTS idg_meeting_id UUID;")
    op.execute("ALTER TABLE idg_md_attestations ADD COLUMN IF NOT EXISTS id UUID;")

    # -------------------------
    # drug_aliases
    # -------------------------
    op.execute("ALTER TABLE drug_aliases ADD COLUMN IF NOT EXISTS id UUID;")

    # -------------------------
    # Unique indexes (safe, optional)
    # -------------------------
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_idg_meetings_id ON idg_meetings (id) WHERE id IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_idg_notes_id ON idg_notes (id) WHERE id IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_idg_md_attestations_id ON idg_md_attestations (id) WHERE id IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_drug_aliases_id ON drug_aliases (id) WHERE id IS NOT NULL;")

    # -------------------------
    # Missing tables
    # -------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            patient_id UUID NULL,
            user_id UUID NULL,
            notification_type VARCHAR NULL,
            status VARCHAR NULL,
            payload JSONB NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NULL,
            created_by UUID NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS communications_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            patient_id UUID NULL,
            channel VARCHAR NULL,
            direction VARCHAR NULL,
            subject VARCHAR NULL,
            body TEXT NULL,
            status VARCHAR NULL,
            external_reference VARCHAR NULL,
            sent_at TIMESTAMP WITHOUT TIME ZONE NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            created_by UUID NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            document_id UUID NULL,
            notification_id UUID NULL,
            status VARCHAR NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            created_by UUID NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS external_substances (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            patient_id UUID NULL,
            substance_name VARCHAR NULL,
            category VARCHAR NULL,
            notes TEXT NULL,
            recorded_at TIMESTAMP WITHOUT TIME ZONE NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            created_by UUID NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS service_coverage_decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            patient_id UUID NULL,
            payer_id UUID NULL,
            service_type VARCHAR NULL,
            decision VARCHAR NULL,
            effective_start_date DATE NULL,
            effective_end_date DATE NULL,
            rationale TEXT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            created_by UUID NULL
        );
        """
    )


def downgrade() -> None:
    """
    Downgrade reverses this repair migration.
    Not recommended in production due to potential data loss.
    """

    op.execute("DROP TABLE IF EXISTS service_coverage_decisions;")
    op.execute("DROP TABLE IF EXISTS external_substances;")
    op.execute("DROP TABLE IF EXISTS document_notifications;")
    op.execute("DROP TABLE IF EXISTS communications_logs;")
    op.execute("DROP TABLE IF EXISTS notifications;")

    op.execute("DROP INDEX IF EXISTS ux_drug_aliases_id;")
    op.execute("DROP INDEX IF EXISTS ux_idg_md_attestations_id;")
    op.execute("DROP INDEX IF EXISTS ux_idg_notes_id;")
    op.execute("DROP INDEX IF EXISTS ux_idg_meetings_id;")

    op.execute("ALTER TABLE drug_aliases DROP COLUMN IF EXISTS id;")

    op.execute("ALTER TABLE idg_md_attestations DROP COLUMN IF EXISTS id;")
    op.execute("ALTER TABLE idg_signatures DROP COLUMN IF EXISTS idg_meeting_id;")
    op.execute("ALTER TABLE idg_notes DROP COLUMN IF EXISTS note_text;")
    op.execute("ALTER TABLE idg_notes DROP COLUMN IF EXISTS id;")

    op.execute("ALTER TABLE idg_reviews DROP COLUMN IF EXISTS finalized_by;")
    op.execute("ALTER TABLE idg_reviews DROP COLUMN IF EXISTS is_finalized;")
    op.execute("ALTER TABLE idg_reviews DROP COLUMN IF EXISTS tenant_id;")
    op.execute("ALTER TABLE idg_reviews DROP COLUMN IF EXISTS idg_meeting_id;")

    op.execute("ALTER TABLE idg_meetings DROP COLUMN IF EXISTS id;")

    op.execute("ALTER TABLE patient_assignments DROP COLUMN IF EXISTS created_by;")
    op.execute("ALTER TABLE patient_assignments DROP COLUMN IF EXISTS updated_at;")
    op.execute("ALTER TABLE patient_assignments DROP COLUMN IF EXISTS created_at;")

    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS tenant_id;")

    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS created_by;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS updated_at;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS created_at;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS is_primary;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS end_date;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS effective_start_date;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS facility_name;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS subscriber_id_type;")
    op.execute("ALTER TABLE patient_payers DROP COLUMN IF EXISTS subscriber_id;")

    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS environment_tag;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS tenant_type;")
