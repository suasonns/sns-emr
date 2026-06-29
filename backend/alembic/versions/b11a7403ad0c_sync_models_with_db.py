"""sync models with db

Revision ID: b11a7403ad0c
Revises: 6ddbc98ac54b
Create Date: 2026-06-28 15:08:41.385225
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b11a7403ad0c"
down_revision: Union[str, Sequence[str], None] = "6ddbc98ac54b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    cols = _inspector().get_columns(table_name)
    return any(col["name"] == column_name for col in cols)


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    indexes = _inspector().get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if _has_table(table_name) and not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if _has_table(table_name) and not _has_column(table_name, column.name):
        op.add_column(table_name, column)


# ---------------------------------------------------------
# UPGRADE
# ---------------------------------------------------------

def upgrade() -> None:
    """
    Forward-only, additive migration.

    Safety rules:
    - create missing tables
    - add missing columns only
    - do not drop/rename here
    - billing_cycles.id is live VARCHAR, so all new billing_cycle_id
      references must also be VARCHAR for now
    """

    # ---------------------------------------------------------
    # CREATE MISSING TABLES
    # ---------------------------------------------------------

    if not _has_table("payers"):
        op.create_table(
            "payers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=True),
            sa.Column("payer_type", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_payers_name", "payers", ["name"], unique=False)
        op.create_index("ix_payers_tenant_id", "payers", ["tenant_id"], unique=False)
        op.create_index("ix_payers_code", "payers", ["code"], unique=False)

    if not _has_table("billing_summaries"):
        op.create_table(
            "billing_summaries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            # IMPORTANT: billing_cycles.id is VARCHAR in live DB
            sa.Column("billing_cycle_id", sa.String(), sa.ForeignKey("billing_cycles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("total_units", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("risk_score", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.UniqueConstraint("patient_id", "billing_cycle_id", name="uq_billing_summary_patient_cycle"),
        )
        op.create_index("ix_billing_summary_patient_status", "billing_summaries", ["patient_id", "status"], unique=False)
        op.create_index("ix_billing_summary_cycle", "billing_summaries", ["billing_cycle_id"], unique=False)

    if not _has_table("billing_snapshots"):
        op.create_table(
            "billing_snapshots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            # IMPORTANT: billing_cycles.id is VARCHAR in live DB
            sa.Column("billing_cycle_id", sa.String(), sa.ForeignKey("billing_cycles.id", ondelete="SET NULL"), nullable=True),
            sa.Column("snapshot_type", sa.String(length=50), nullable=False),
            sa.Column("version", sa.String(length=50), nullable=True),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_billing_snapshot_patient_created", "billing_snapshots", ["patient_id", "created_at"], unique=False)
        op.create_index("ix_billing_snapshot_tenant_type", "billing_snapshots", ["tenant_id", "snapshot_type"], unique=False)

    if not _has_table("orders_snapshots"):
        op.create_table(
            "orders_snapshots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("discipline", sa.String(length=32), nullable=False),
            sa.Column("visits_per_week", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
            sa.Column("effective_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("snapshot_type", sa.String(length=50), nullable=False, server_default="ORDERS"),
            sa.Column("version", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.CheckConstraint("end_date IS NULL OR end_date >= effective_date", name="ck_orders_snapshot_dates"),
        )
        op.create_index("ix_orders_snapshot_patient_date", "orders_snapshots", ["patient_id", "effective_date"], unique=False)
        op.create_index("ix_orders_snapshot_tenant", "orders_snapshots", ["tenant_id"], unique=False)

    if not _has_table("claim_export_logs"):
        op.create_table(
            "claim_export_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            # IMPORTANT: billing_cycles.id is VARCHAR in live DB
            sa.Column("billing_cycle_id", sa.String(), sa.ForeignKey("billing_cycles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("export_type", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="SUCCESS"),
            sa.Column("override_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("override_reason", sa.String(), nullable=True),
            sa.Column("override_approved_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_claim_export_patient_cycle", "claim_export_logs", ["patient_id", "billing_cycle_id"], unique=False)
        op.create_index("ix_claim_export_status", "claim_export_logs", ["status"], unique=False)

    # ---------------------------------------------------------
    # ADD MISSING COLUMNS TO EXISTING TABLES
    # ---------------------------------------------------------

    # billing_cycles
    _add_column_if_missing(
        "billing_cycles",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
    )
    _add_column_if_missing(
        "billing_cycles",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    _add_column_if_missing(
        "billing_cycles",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "billing_cycles",
        sa.Column("created_by", sa.String(length=255), nullable=True),
    )
    _create_index_if_missing("ix_billing_cycle_tenant_dates", "billing_cycles", ["tenant_id", "start_date", "end_date"])

    # patient_pos
    _add_column_if_missing("patient_pos", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("patient_pos", sa.Column("status", sa.String(length=32), nullable=True, server_default="ACTIVE"))
    _add_column_if_missing("patient_pos", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("patient_pos", sa.Column("created_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_patient_pos_patient_date", "patient_pos", ["patient_id", "effective_date"])
    _create_index_if_missing("ix_patient_pos_tenant", "patient_pos", ["tenant_id"])

    # gip_periods
    _add_column_if_missing("gip_periods", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("gip_periods", sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("gip_periods", sa.Column("service_level", sa.String(length=50), nullable=True, server_default="GIP"))
    _add_column_if_missing("gip_periods", sa.Column("status", sa.String(length=32), nullable=True, server_default="ACTIVE"))
    _add_column_if_missing("gip_periods", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("gip_periods", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("gip_periods", sa.Column("created_by", sa.String(length=255), nullable=True))
    _add_column_if_missing("gip_periods", sa.Column("updated_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_gip_period_patient_service_dates", "gip_periods", ["patient_id", "service_level", "start_date", "end_date"])

    # respite_periods
    _add_column_if_missing("respite_periods", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("respite_periods", sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("respite_periods", sa.Column("service_level", sa.String(length=50), nullable=True, server_default="RESPITE"))
    _add_column_if_missing("respite_periods", sa.Column("status", sa.String(length=32), nullable=True, server_default="ACTIVE"))
    _add_column_if_missing("respite_periods", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("respite_periods", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("respite_periods", sa.Column("created_by", sa.String(length=255), nullable=True))
    _add_column_if_missing("respite_periods", sa.Column("updated_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_respite_period_patient_service_dates", "respite_periods", ["patient_id", "service_level", "start_date", "end_date"])

    # continuous_care_events
    _add_column_if_missing("continuous_care_events", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("continuous_care_events", sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("continuous_care_events", sa.Column("service_level", sa.String(length=50), nullable=True, server_default="CONTINUOUS_CARE"))
    _add_column_if_missing("continuous_care_events", sa.Column("status", sa.String(length=32), nullable=True, server_default="ACTIVE"))
    _add_column_if_missing("continuous_care_events", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("continuous_care_events", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("continuous_care_events", sa.Column("created_by", sa.String(length=255), nullable=True))
    _add_column_if_missing("continuous_care_events", sa.Column("updated_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_continuous_care_patient_service_dates", "continuous_care_events", ["patient_id", "service_level", "start_date", "end_date"])

    # visit_minutes
    _add_column_if_missing("visit_minutes", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("visit_minutes", sa.Column("service_date", sa.Date(), nullable=True))
    _add_column_if_missing("visit_minutes", sa.Column("status", sa.String(length=32), nullable=True, server_default="DRAFT"))
    _add_column_if_missing("visit_minutes", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("visit_minutes", sa.Column("created_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_visit_minutes_visit_date", "visit_minutes", ["visit_id", "service_date"])
    _create_index_if_missing("ix_visit_minutes_tenant", "visit_minutes", ["tenant_id"])

    # authorization_records
    _add_column_if_missing("authorization_records", sa.Column("authorization_number", sa.String(length=100), nullable=True))
    _add_column_if_missing("authorization_records", sa.Column("service_type", sa.String(length=50), nullable=True))
    _add_column_if_missing("authorization_records", sa.Column("status", sa.String(length=32), nullable=True, server_default="PENDING"))
    _add_column_if_missing("authorization_records", sa.Column("created_by", sa.String(length=255), nullable=True))

    if _has_table("authorization_records") and _has_column("authorization_records", "auth_status") and _has_column("authorization_records", "status"):
        op.execute(
            sa.text(
                """
                UPDATE authorization_records
                SET status = auth_status
                WHERE status IS NULL AND auth_status IS NOT NULL
                """
            )
        )

    # payer_contracts
    _add_column_if_missing("payer_contracts", sa.Column("payer_id", postgresql.UUID(as_uuid=True), nullable=True))
    _add_column_if_missing("payer_contracts", sa.Column("contract_number", sa.String(length=100), nullable=True))
    _add_column_if_missing("payer_contracts", sa.Column("status", sa.String(length=32), nullable=True, server_default="ACTIVE"))
    _add_column_if_missing("payer_contracts", sa.Column("start_date", sa.Date(), nullable=True))
    _add_column_if_missing("payer_contracts", sa.Column("end_date", sa.Date(), nullable=True))
    _add_column_if_missing("payer_contracts", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    _add_column_if_missing("payer_contracts", sa.Column("created_by", sa.String(length=255), nullable=True))
    _create_index_if_missing("ix_contract_payer", "payer_contracts", ["payer_id"])


# ---------------------------------------------------------
# DOWNGRADE
# ---------------------------------------------------------

def downgrade() -> None:
    raise NotImplementedError(
        "Forward-only migration: downgrade intentionally disabled."
    )