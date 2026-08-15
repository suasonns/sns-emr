"""
align_task_enums_with_model

Revision ID: f0fb92c66b9a
Revises: c6af768ae7e9
Create Date: 2026-08-13 02:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f0fb92c66b9a"
down_revision: Union[str, Sequence[str], None] = "c6af768ae7e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'tasks_status_enum' AND e.enumlabel = 'IN_PROGRESS'
                ) THEN
                    ALTER TYPE tasks_status_enum ADD VALUE 'IN_PROGRESS';
                END IF;
            END $$;
            """
        )
    )

    for value in ["POC_UPDATE", "IDG_REVIEW", "CERTIFICATION", "RECERTIFICATION", "CONDITION_TRIGGER"]:
        op.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum e
                        JOIN pg_type t ON e.enumtypid = t.oid
                        WHERE t.typname = 'tasks_regulatory_basis_enum' AND e.enumlabel = '{value}'
                    ) THEN
                        ALTER TYPE tasks_regulatory_basis_enum ADD VALUE '{value}';
                    END IF;
                END $$;
                """
            )
        )

    for value in ["LVN", "CHHA", "MSW", "BSW", "LCSW", "SC"]:
        op.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum e
                        JOIN pg_type t ON e.enumtypid = t.oid
                        WHERE t.typname = 'tasks_discipline_enum' AND e.enumlabel = '{value}'
                    ) THEN
                        ALTER TYPE tasks_discipline_enum ADD VALUE '{value}';
                    END IF;
                END $$;
                """
            )
        )


def downgrade() -> None:
    # Postgres does not support removing enum values safely in-place.
    # This is a forward-only repair migration, so downgrade is intentionally no-op.
    pass
