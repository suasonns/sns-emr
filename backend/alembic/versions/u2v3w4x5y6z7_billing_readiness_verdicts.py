"""Eligibility Traceability Epic Workstream 3: billing readiness persistence.

Adds billing_readiness_verdicts -- an immutable, append-only history of
every check_patient_billing_readiness() evaluation. Closes the confirmed
Chronology Gap: "why was this patient billable on DATE X" previously had
no answer beyond re-deriving today's live state.

Additive only. The underlying eligibility-rule logic in
check_patient_billing_readiness() is unchanged by this migration; the
service gains one additional persistence step (see
app/billing/services/billing_readiness_service.py) that writes to this
table using the same computed result it was already returning.

Revision ID: u2v3w4x5y6z7
Revises: t1u2v3w4x5y6
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "u2v3w4x5y6z7"
down_revision: Union[str, Sequence[str], None] = "t1u2v3w4x5y6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_readiness_verdicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_ready", sa.Boolean(), nullable=False),
        sa.Column("blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("benefit_periods.id"), nullable=True),
        sa.Column("certification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("certifications.id"), nullable=True),
        sa.Column("triggered_by", sa.String(length=32), server_default="MANUAL_CHECK", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_readiness_verdicts")),
    )
    op.create_index("ix_billing_readiness_verdicts_tenant_id", "billing_readiness_verdicts", ["tenant_id"])
    op.create_index("ix_billing_readiness_verdicts_patient_id", "billing_readiness_verdicts", ["patient_id"])
    op.create_index("ix_billing_readiness_verdicts_evaluated_at", "billing_readiness_verdicts", ["evaluated_at"])
    op.create_index("ix_billing_readiness_verdicts_benefit_period_id", "billing_readiness_verdicts", ["benefit_period_id"])
    op.create_index("ix_billing_readiness_verdicts_certification_id", "billing_readiness_verdicts", ["certification_id"])
    op.create_index(
        "ix_brv_patient_evaluated_at", "billing_readiness_verdicts", ["patient_id", "evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_brv_patient_evaluated_at", table_name="billing_readiness_verdicts")
    op.drop_index("ix_billing_readiness_verdicts_certification_id", table_name="billing_readiness_verdicts")
    op.drop_index("ix_billing_readiness_verdicts_benefit_period_id", table_name="billing_readiness_verdicts")
    op.drop_index("ix_billing_readiness_verdicts_evaluated_at", table_name="billing_readiness_verdicts")
    op.drop_index("ix_billing_readiness_verdicts_patient_id", table_name="billing_readiness_verdicts")
    op.drop_index("ix_billing_readiness_verdicts_tenant_id", table_name="billing_readiness_verdicts")
    op.drop_table("billing_readiness_verdicts")
