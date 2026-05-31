"""add benefit_periods table

Revision ID: eb76b663ad19
Revises: 52b9a117e2bb
Create Date: 2026-05-29 18:45:50.693693
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "eb76b663ad19"
down_revision: Union[str, Sequence[str], None] = "52b9a117e2bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------
    # 1) Ensure enum exists (safe, idempotent)
    # ------------------------------------------------------------
    benefit_type_enum = postgresql.ENUM(
        "INITIAL",
        "RECERT",
        name="benefit_type_enum",
    )
    benefit_type_enum.create(bind, checkfirst=True)

    # ------------------------------------------------------------
    # 2) Create table ONLY if it does not already exist
    # ------------------------------------------------------------
    if not bind.dialect.has_table(bind, "benefit_periods"):
        benefit_type_enum_no_create = postgresql.ENUM(
            "INITIAL",
            "RECERT",
            name="benefit_type_enum",
            create_type=False,
        )

        op.create_table(
            "benefit_periods",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("benefit_type", benefit_type_enum_no_create, nullable=False),
            sa.Column("period_number", sa.Integer(), nullable=False),
            sa.Column("election_date", sa.Date(), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

        op.create_index("ix_benefit_periods_tenant_id", "benefit_periods", ["tenant_id"])
        op.create_index("ix_benefit_periods_patient_id", "benefit_periods", ["patient_id"])
        op.create_index("ix_benefit_periods_benefit_type", "benefit_periods", ["benefit_type"])
        op.create_index("ix_benefit_periods_start_date", "benefit_periods", ["start_date"])
        op.create_index("ix_benefit_periods_end_date", "benefit_periods", ["end_date"])

def downgrade() -> None:
    op.drop_index("ix_benefit_periods_end_date", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_start_date", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_benefit_type", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_patient_id", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_tenant_id", table_name="benefit_periods")
    op.drop_table("benefit_periods")

    # Forward-only enum: do NOT drop benefit_type_enum