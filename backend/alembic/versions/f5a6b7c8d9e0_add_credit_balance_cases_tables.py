"""add credit_balance_cases and credit_balance_case_events tables

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credit_balance_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'POTENTIAL'")),
        sa.Column("medicare_classification", sa.String(length=32), nullable=False, server_default=sa.text("'UNKNOWN'")),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("credit_amount_at_detection", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_repaid", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("amount_recouped", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("amount_reallocated", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("repayment_method", sa.String(length=64), nullable=True),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("review_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("identified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repayment_due_at", sa.Date(), nullable=True),
        sa.Column("repaid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recouped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reallocated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_credit_balance_cases_tenant_id", "credit_balance_cases", ["tenant_id"], unique=False)
    op.create_index("ix_credit_balance_cases_claim_id", "credit_balance_cases", ["claim_id"], unique=False)
    op.create_index("ix_credit_balance_cases_patient_id", "credit_balance_cases", ["patient_id"], unique=False)
    op.create_index("ix_credit_balance_cases_status", "credit_balance_cases", ["status"], unique=False)
    op.create_index("ix_credit_balance_cases_medicare_classification", "credit_balance_cases", ["medicare_classification"], unique=False)
    op.create_index("ix_credit_balance_case_tenant_status", "credit_balance_cases", ["tenant_id", "status"], unique=False)
    op.create_index("ix_credit_balance_case_claim", "credit_balance_cases", ["claim_id"], unique=False)

    op.create_table(
        "credit_balance_case_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("credit_balance_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("performed_by", sa.String(length=255), nullable=False),
        sa.Column("source_transaction_reference", sa.String(length=255), nullable=True),
        sa.Column("amount_before", sa.Numeric(12, 2), nullable=True),
        sa.Column("amount_after", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_balance_case_events_case_id", "credit_balance_case_events", ["case_id"], unique=False)
    op.create_index("ix_credit_balance_case_event_case", "credit_balance_case_events", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_credit_balance_case_event_case", table_name="credit_balance_case_events")
    op.drop_index("ix_credit_balance_case_events_case_id", table_name="credit_balance_case_events")
    op.drop_table("credit_balance_case_events")

    op.drop_index("ix_credit_balance_case_claim", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_case_tenant_status", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_cases_medicare_classification", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_cases_status", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_cases_patient_id", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_cases_claim_id", table_name="credit_balance_cases")
    op.drop_index("ix_credit_balance_cases_tenant_id", table_name="credit_balance_cases")
    op.drop_table("credit_balance_cases")
