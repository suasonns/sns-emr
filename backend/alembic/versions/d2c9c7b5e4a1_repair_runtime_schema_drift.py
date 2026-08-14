"""repair runtime schema drift

Revision ID: d2c9c7b5e4a1
Revises: a1184c1c1d5f
Create Date: 2026-08-13 11:24:06.653000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d2c9c7b5e4a1"
down_revision: Union[str, Sequence[str], None] = "a1184c1c1d5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refusals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("discipline", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("refused_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("was_reoffered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reoffered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_refusals_tenant_id", "refusals", ["tenant_id"])
    op.create_index("ix_refusals_patient_id", "refusals", ["patient_id"])
    op.create_index("ix_refusals_discipline", "refusals", ["discipline"])
    op.create_index("ix_refusals_refused_at", "refusals", ["refused_at"])

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'visits' AND column_name = 'start_time'
            ) THEN
                ALTER TABLE visits ADD COLUMN start_time TIMESTAMP WITH TIME ZONE;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'visits' AND column_name = 'end_time'
            ) THEN
                ALTER TABLE visits ADD COLUMN end_time TIMESTAMP WITH TIME ZONE;
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'notifications' AND column_name = 'title'
            ) THEN
                ALTER TABLE notifications ADD COLUMN title TEXT;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'notifications' AND column_name = 'is_read'
            ) THEN
                ALTER TABLE notifications ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'notifications' AND column_name = 'read_at'
            ) THEN
                ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END$$;
        """
    )

    op.execute("UPDATE notifications SET title = COALESCE(title, message, '')")
    op.execute("UPDATE notifications SET is_read = COALESCE(is_read, seen_at IS NOT NULL, FALSE)")
    op.execute("UPDATE notifications SET read_at = COALESCE(read_at, seen_at)")
    op.execute("ALTER TABLE notifications ALTER COLUMN title SET DEFAULT ''")
    op.execute("ALTER TABLE notifications ALTER COLUMN title SET NOT NULL")

    for column_name, column_type in [
        ("kps_score", "INTEGER"),
        ("pps_score_previous", "INTEGER"),
        ("pps_score_current", "INTEGER"),
        ("fast_score", "VARCHAR"),
        ("nyha_class", "VARCHAR"),
        ("adl_dependency_level", "VARCHAR"),
        ("is_bedbound", "BOOLEAN"),
        ("weight_loss_lbs", "NUMERIC"),
        ("oral_intake_decline", "BOOLEAN"),
        ("dysphagia", "BOOLEAN"),
        ("hospitalizations_30d", "INTEGER"),
        ("oxygen_lpm_previous", "NUMERIC"),
        ("oxygen_lpm_current", "NUMERIC"),
        ("primary_diagnosis", "TEXT"),
        ("secondary_conditions", "TEXT"),
        ("clinical_decline_summary", "TEXT"),
    ]:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'f2f_encounters' AND column_name = '{column_name}'
                ) THEN
                    ALTER TABLE f2f_encounters ADD COLUMN {column_name} {column_type};
                END IF;
            END$$;
            """
        )


def downgrade() -> None:
    op.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS read_at")
    op.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS is_read")
    op.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS title")
    op.execute("ALTER TABLE visits DROP COLUMN IF EXISTS end_time")
    op.execute("ALTER TABLE visits DROP COLUMN IF EXISTS start_time")

    for column_name in [
        "clinical_decline_summary",
        "secondary_conditions",
        "primary_diagnosis",
        "oxygen_lpm_current",
        "oxygen_lpm_previous",
        "hospitalizations_30d",
        "dysphagia",
        "oral_intake_decline",
        "is_bedbound",
        "adl_dependency_level",
        "nyha_class",
        "fast_score",
        "pps_score_current",
        "pps_score_previous",
        "kps_score",
    ]:
        op.execute(f"ALTER TABLE f2f_encounters DROP COLUMN IF EXISTS {column_name}")

    op.drop_index("ix_refusals_refused_at", table_name="refusals")
    op.drop_index("ix_refusals_discipline", table_name="refusals")
    op.drop_index("ix_refusals_patient_id", table_name="refusals")
    op.drop_index("ix_refusals_tenant_id", table_name="refusals")
    op.drop_table("refusals")
