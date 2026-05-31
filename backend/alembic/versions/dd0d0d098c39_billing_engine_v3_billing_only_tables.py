"""billing engine v3 billing-only tables

Revision ID: dd0d0d098c39
Revises: fb42cc46ea2b
Create Date: 2026-05-30 15:40:30.395055

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dd0d0d098c39"
down_revision: Union[str, Sequence[str], None] = "fb42cc46ea2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "authorization_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("payer_name", sa.String(), nullable=False),
        sa.Column("auth_status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_authorization_records"),
    )

    op.create_table(
        "billing_cycles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_billing_cycles"),
    )

    op.create_table(
        "billing_snapshot",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_billing_snapshot"),
    )

    op.create_table(
        "billing_summary",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("billing_cycle_id", sa.String(), nullable=False),
        sa.Column("total_units", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_billing_summary"),
    )

    op.create_table(
        "continuous_care_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_continuous_care_events"),
    )

    op.create_table(
        "gip_periods",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_gip_periods"),
    )

    op.create_table(
        "orders_snapshot",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("discipline", sa.String(), nullable=False),
        sa.Column("visits_per_week", sa.Integer(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_orders_snapshot"),
    )

    op.create_table(
        "patient_payers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("payer_name", sa.String(), nullable=False),
        sa.Column("payer_type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_patient_payers"),
    )

    op.create_table(
        "patient_pos",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("pos_type", sa.String(), nullable=False),
        sa.Column("facility_name", sa.String(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_patient_pos"),
    )

    op.create_table(
        "payer_contracts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("payer_name", sa.String(), nullable=False),
        sa.Column("has_contract", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_payer_contracts"),
    )

    op.create_table(
        "respite_periods",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_respite_periods"),
    )

    op.create_table(
        "visit_minutes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("visit_id", sa.String(), nullable=False),
        sa.Column("discipline", sa.String(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_visit_minutes"),
    )

    op.create_index(
        "ix_authorization_records_patient_id",
        "authorization_records",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_cycles_tenant_id",
        "billing_cycles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_snapshot_patient_id",
        "billing_snapshot",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_summary_billing_cycle_id",
        "billing_summary",
        ["billing_cycle_id"],
        unique=False,
    )
    op.create_index(
        "ix_billing_summary_patient_id",
        "billing_summary",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_continuous_care_events_patient_id",
        "continuous_care_events",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_gip_periods_patient_id",
        "gip_periods",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_orders_snapshot_patient_id",
        "orders_snapshot",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_payers_patient_id",
        "patient_payers",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_pos_patient_id",
        "patient_pos",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_payer_contracts_tenant_id",
        "payer_contracts",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_respite_periods_patient_id",
        "respite_periods",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_visit_minutes_visit_id",
        "visit_minutes",
        ["visit_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_visit_minutes_visit_id", table_name="visit_minutes")
    op.drop_index("ix_respite_periods_patient_id", table_name="respite_periods")
    op.drop_index("ix_payer_contracts_tenant_id", table_name="payer_contracts")
    op.drop_index("ix_patient_pos_patient_id", table_name="patient_pos")
    op.drop_index("ix_patient_payers_patient_id", table_name="patient_payers")
    op.drop_index("ix_orders_snapshot_patient_id", table_name="orders_snapshot")
    op.drop_index("ix_gip_periods_patient_id", table_name="gip_periods")
    op.drop_index(
        "ix_continuous_care_events_patient_id",
        table_name="continuous_care_events",
    )
    op.drop_index(
        "ix_billing_summary_patient_id",
        table_name="billing_summary",
    )
    op.drop_index(
        "ix_billing_summary_billing_cycle_id",
        table_name="billing_summary",
    )
    op.drop_index(
        "ix_billing_snapshot_patient_id",
        table_name="billing_snapshot",
    )
    op.drop_index(
        "ix_billing_cycles_tenant_id",
        table_name="billing_cycles",
    )
    op.drop_index(
        "ix_authorization_records_patient_id",
        table_name="authorization_records",
    )

    op.drop_table("visit_minutes")
    op.drop_table("respite_periods")
    op.drop_table("payer_contracts")
    op.drop_table("patient_pos")
    op.drop_table("patient_payers")
    op.drop_table("orders_snapshot")
    op.drop_table("gip_periods")
    op.drop_table("continuous_care_events")
    op.drop_table("billing_summary")
    op.drop_table("billing_snapshot")
    op.drop_table("billing_cycles")
    op.drop_table("authorization_records")
