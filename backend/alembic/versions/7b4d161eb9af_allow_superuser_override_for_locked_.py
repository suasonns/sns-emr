"""allow_superuser_override_for_locked_reports

Revision ID: 7b4d161eb9af
Revises: 4911a5fe7aab
Create Date: 2026-05-05
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "7b4d161eb9af"
down_revision = "4911a5fe7aab"
branch_labels = None
depends_on = None


def upgrade():
    # Allow SUPERUSER override via session variable:
    #   SET app.superuser_override = 'true';

    # Header trigger (regulatory_reports)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_report_update_when_locked()
        RETURNS trigger AS $$
        BEGIN
            -- Superuser override
            IF current_setting('app.superuser_override', true) = 'true' THEN
                RETURN NEW;
            END IF;

            -- Default behavior: LOCKED is immutable
            IF OLD.status = 'LOCKED' THEN
                RAISE EXCEPTION 'Locked report header cannot be modified';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Child tables trigger (metrics / sections / artifacts)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_child_modification_when_report_locked()
        RETURNS trigger AS $$
        DECLARE
            report_uuid uuid;
        BEGIN
            -- Superuser override
            IF current_setting('app.superuser_override', true) = 'true' THEN
                RETURN COALESCE(NEW, OLD);
            END IF;

            IF TG_OP = 'DELETE' THEN
                report_uuid := OLD.report_id;
            ELSE
                report_uuid := NEW.report_id;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM regulatory_reports
                WHERE id = report_uuid
                  AND status = 'LOCKED'
            ) THEN
                RAISE EXCEPTION 'Report is LOCKED and cannot be modified';
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade():
    # Intentionally no-op (override behavior is additive)
    pass
