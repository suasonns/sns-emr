"""add structured findings processing state to harvested signals

Revision ID: b6c7d8e9f0a1
Revises: 43ebae4b566d
Create Date: 2026-08-27 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, Sequence[str], None] = '43ebae4b566d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Adds processing-state tracking for the concept-aware structured findings
    pipeline. `structured_findings = []` alone cannot distinguish "never
    attempted" from "attempted, model found nothing", so every row (existing
    and new) is given an explicit status.

    All existing rows default to PENDING: they were harvested before this
    tracking existed, so none of them have been through the concept-aware
    pipeline yet regardless of what their `structured_findings` column
    currently holds. This makes them eligible for reprocessing via
    structured_findings_reprocess_service. New rows created after this
    migration are stamped COMPLETED/FAILED immediately by harvest_service.
    """
    op.add_column(
        "patient_harvested_signals",
        sa.Column(
            "structured_findings_status",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
    )
    op.add_column(
        "patient_harvested_signals",
        sa.Column(
            "structured_findings_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "patient_harvested_signals",
        sa.Column(
            "structured_findings_last_attempted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "patient_harvested_signals",
        sa.Column(
            "structured_findings_last_error",
            sa.Text(),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_harvested_signals_structured_findings_status",
        "patient_harvested_signals",
        ["structured_findings_status"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_harvested_signals_structured_findings_status",
        table_name="patient_harvested_signals",
    )
    op.drop_column("patient_harvested_signals", "structured_findings_last_error")
    op.drop_column("patient_harvested_signals", "structured_findings_last_attempted_at")
    op.drop_column("patient_harvested_signals", "structured_findings_attempts")
    op.drop_column("patient_harvested_signals", "structured_findings_status")
