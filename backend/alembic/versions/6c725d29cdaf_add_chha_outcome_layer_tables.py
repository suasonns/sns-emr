"""add chha outcome layer tables

Revision ID: 6c725d29cdaf
Revises: 44ba6a23278a
Create Date: 2026-06-22 11:13:21.678345
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "6c725d29cdaf"
down_revision: Union[str, Sequence[str], None] = "44ba6a23278a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # CHHA VISIT OUTCOME TABLE (1 ROW PER VISIT)
    # =====================================================
    op.create_table(
        "chha_visit_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id"), nullable=False),

        sa.Column("poc_reference_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Core outcome layer
        sa.Column("tolerance_to_care", sa.String(length=50), nullable=False, server_default="WELL_TOLERATED"),
        sa.Column("condition_during_visit", sa.String(length=50), nullable=False, server_default="STABLE"),
        sa.Column("skin_outcome", sa.String(length=50), nullable=False, server_default="NOT_ASSESSED"),

        sa.Column("pain_or_change_observed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rn_notification_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("rn_notified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rn_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rn_notified_name", sa.String(length=255), nullable=True),

        sa.Column("caregiver_instruction_provided", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("caregiver_understanding_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("exception_narrative", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),

        sa.UniqueConstraint("visit_id", name="uq_chha_visit_outcomes_visit_id"),
    )

    op.create_index("ix_chha_visit_outcomes_tenant_id", "chha_visit_outcomes", ["tenant_id"])
    op.create_index("ix_chha_visit_outcomes_patient_id", "chha_visit_outcomes", ["patient_id"])
    op.create_index("ix_chha_visit_outcomes_visit_id", "chha_visit_outcomes", ["visit_id"])

    # =====================================================
    # CHHA TASK RESULTS TABLE (MULTIPLE ROWS PER VISIT)
    # =====================================================
    op.create_table(
        "chha_visit_task_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chha_visit_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # Task identity
        sa.Column("section_code", sa.String(length=100), nullable=False),
        sa.Column("task_code", sa.String(length=100), nullable=False),

        # Execution result
        sa.Column("was_assigned", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("refused", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("not_done", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        # Optional structured detail
        sa.Column("observation_code", sa.String(length=100), nullable=True),
        sa.Column("result_note", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_chha_visit_task_results_outcome_id",
        "chha_visit_task_results",
        ["outcome_id"],
    )

    op.create_index(
        "ix_chha_visit_task_results_section_code",
        "chha_visit_task_results",
        ["section_code"],
    )

    op.create_index(
        "ix_chha_visit_task_results_task_code",
        "chha_visit_task_results",
        ["task_code"],
    )


def downgrade() -> None:
    # Drop task results first (FK dependency)
    op.drop_index("ix_chha_visit_task_results_task_code", table_name="chha_visit_task_results")
    op.drop_index("ix_chha_visit_task_results_section_code", table_name="chha_visit_task_results")
    op.drop_index("ix_chha_visit_task_results_outcome_id", table_name="chha_visit_task_results")
    op.drop_table("chha_visit_task_results")

    # Drop outcomes
    op.drop_index("ix_chha_visit_outcomes_visit_id", table_name="chha_visit_outcomes")
    op.drop_index("ix_chha_visit_outcomes_patient_id", table_name="chha_visit_outcomes")
    op.drop_index("ix_chha_visit_outcomes_tenant_id", table_name="chha_visit_outcomes")
    op.drop_table("chha_visit_outcomes")