"""prevent_modification_when_report_locked

Revision ID: 2bae706344b5
Revises: ab9b61a7b73f
Create Date: 2026-05-05 19:39:44.996359
"""

from alembic import op

revision = '2bae706344b5'
down_revision = 'ab9b61a7b73f'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Child-table protection (metrics, sections, artifacts)
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_child_modification_when_report_locked()
    RETURNS trigger AS $$
    DECLARE
        report_uuid uuid;
    BEGIN
        -- Determine report_id depending on operation
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

        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach to RARE child tables
    op.execute("""
    CREATE TRIGGER trg_block_metrics_on_locked_report
    BEFORE INSERT OR UPDATE OR DELETE
    ON regulatory_report_metrics
    FOR EACH ROW
    EXECUTE FUNCTION prevent_child_modification_when_report_locked();
    """)

    op.execute("""
    CREATE TRIGGER trg_block_sections_on_locked_report
    BEFORE INSERT OR UPDATE OR DELETE
    ON regulatory_report_sections
    FOR EACH ROW
    EXECUTE FUNCTION prevent_child_modification_when_report_locked();
    """)

    op.execute("""
    CREATE TRIGGER trg_block_artifacts_on_locked_report
    BEFORE INSERT OR UPDATE OR DELETE
    ON regulatory_report_artifacts
    FOR EACH ROW
    EXECUTE FUNCTION prevent_child_modification_when_report_locked();
    """)

    # 2) Header immutability (report itself)
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_report_update_when_locked()
    RETURNS trigger AS $$
    BEGIN
        IF OLD.status = 'LOCKED' THEN
            RAISE EXCEPTION 'Locked report header cannot be modified';
        END IF;

        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER trg_block_report_update_when_locked
    BEFORE UPDATE OR DELETE
    ON regulatory_reports
    FOR EACH ROW
    EXECUTE FUNCTION prevent_report_update_when_locked();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_block_metrics_on_locked_report ON regulatory_report_metrics;")
    op.execute("DROP TRIGGER IF EXISTS trg_block_sections_on_locked_report ON regulatory_report_sections;")
    op.execute("DROP TRIGGER IF EXISTS trg_block_artifacts_on_locked_report ON regulatory_report_artifacts;")
    op.execute("DROP TRIGGER IF EXISTS trg_block_report_update_when_locked ON regulatory_reports;")

    op.execute("DROP FUNCTION IF EXISTS prevent_child_modification_when_report_locked;")
    op.execute("DROP FUNCTION IF EXISTS prevent_report_update_when_locked;")