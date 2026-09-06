"""add facility payment visibility tables

Revision ID: g1h2i3j4k5l6
Revises: f5a6b7c8d9e0
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facility_payment_expectations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_pos_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_pos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("facility_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("residence_type_snapshot", sa.String(length=50), nullable=True),
        sa.Column("room_number_snapshot", sa.String(length=64), nullable=True),
        sa.Column("residence_start_date_snapshot", sa.Date(), nullable=True),
        sa.Column("residence_end_date_snapshot", sa.Date(), nullable=True),
        sa.Column("expected_funding_source_snapshot", sa.String(length=64), nullable=True),
        sa.Column("expected_payer_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("primary_payer_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("secondary_payer_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("responsibility_category", sa.String(length=64), nullable=False),
        sa.Column("expected_funding_source", sa.String(length=64), nullable=False, server_default=sa.text("'NOT_VERIFIED'")),
        sa.Column("expected_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("frequency", sa.String(length=64), nullable=True),
        sa.Column("service_period_start", sa.Date(), nullable=False),
        sa.Column("service_period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("authorization_reference", sa.String(length=255), nullable=True),
        sa.Column("share_of_cost_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("supersedes_expectation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("superseded_by_expectation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'MANUAL'")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reconciliation_status", sa.String(length=32), nullable=False, server_default=sa.text("'NOT_VERIFIED'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("expected_amount >= 0", name="ck_facility_payment_expectation_expected_amount_nonnegative"),
        sa.CheckConstraint("service_period_end >= service_period_start", name="ck_facility_payment_expectation_service_period_valid"),
    )
    op.create_index("ix_facility_payment_expectations_tenant_id", "facility_payment_expectations", ["tenant_id"], unique=False)
    op.create_index("ix_facility_payment_expectations_patient_id", "facility_payment_expectations", ["patient_id"], unique=False)
    op.create_index("ix_facility_payment_expectations_patient_pos_id", "facility_payment_expectations", ["patient_pos_id"], unique=False)
    op.create_index("ix_facility_payment_expectations_responsibility_category", "facility_payment_expectations", ["responsibility_category"], unique=False)
    op.create_index("ix_facility_payment_expectations_expected_funding_source", "facility_payment_expectations", ["expected_funding_source"], unique=False)
    op.create_index("ix_facility_payment_expectations_service_period_start", "facility_payment_expectations", ["service_period_start"], unique=False)
    op.create_index("ix_facility_payment_expectations_service_period_end", "facility_payment_expectations", ["service_period_end"], unique=False)
    op.create_index("ix_facility_payment_expectations_due_date", "facility_payment_expectations", ["due_date"], unique=False)
    op.create_index("ix_facility_payment_expectations_status", "facility_payment_expectations", ["status"], unique=False)
    op.create_index("ix_facility_payment_expectations_reconciliation_status", "facility_payment_expectations", ["reconciliation_status"], unique=False)
    op.create_index("ix_facility_payment_expectation_tenant_patient", "facility_payment_expectations", ["tenant_id", "patient_id"], unique=False)
    op.create_index("ix_facility_payment_expectation_tenant_status", "facility_payment_expectations", ["tenant_id", "status"], unique=False)
    op.create_index("ix_facility_payment_expectation_tenant_reconciliation_status", "facility_payment_expectations", ["tenant_id", "reconciliation_status"], unique=False)

    op.create_table(
        "facility_payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("facility_payment_expectation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facility_payment_expectations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("remittance_advice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remittance_advices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payment_adjustment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_adjustments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payer_name", sa.String(length=255), nullable=True),
        sa.Column("amount_applied", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_date", sa.String(length=16), nullable=True),
        sa.Column("allocation_status", sa.String(length=32), nullable=False, server_default=sa.text("'PROPOSED'")),
        sa.Column("match_basis", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reconciled_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_facility_payment_allocations_tenant_id", "facility_payment_allocations", ["tenant_id"], unique=False)
    op.create_index("ix_facility_payment_allocations_facility_payment_expectation_id", "facility_payment_allocations", ["facility_payment_expectation_id"], unique=False)
    op.create_index("ix_facility_payment_allocations_allocation_status", "facility_payment_allocations", ["allocation_status"], unique=False)
    op.create_index("ix_facility_payment_allocation_tenant_expectation", "facility_payment_allocations", ["tenant_id", "facility_payment_expectation_id"], unique=False)
    op.create_index("ix_facility_payment_allocation_payment_id", "facility_payment_allocations", ["payment_id"], unique=False)

    op.create_table(
        "facility_collection_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("facility_payment_expectation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("expected_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("received_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("outstanding_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("days_outstanding", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution_evidence", sa.Text(), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_facility_collection_alerts_tenant_id", "facility_collection_alerts", ["tenant_id"], unique=False)
    op.create_index("ix_facility_collection_alerts_patient_id", "facility_collection_alerts", ["patient_id"], unique=False)
    op.create_index("ix_facility_collection_alerts_facility_payment_expectation_id", "facility_collection_alerts", ["facility_payment_expectation_id"], unique=False)
    op.create_index("ix_facility_collection_alerts_alert_type", "facility_collection_alerts", ["alert_type"], unique=False)
    op.create_index("ix_facility_collection_alerts_status", "facility_collection_alerts", ["status"], unique=False)

    op.create_table(
        "facility_collection_alert_thresholds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("threshold_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("threshold_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "alert_type", name="uq_facility_collection_alert_threshold_tenant_alert"),
    )
    op.create_index("ix_facility_collection_alert_thresholds_tenant_id", "facility_collection_alert_thresholds", ["tenant_id"], unique=False)
    op.create_index("ix_facility_collection_alert_threshold_tenant_alert", "facility_collection_alert_thresholds", ["tenant_id", "alert_type"], unique=False)

    op.create_table(
        "facility_payment_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("supporting_reference", sa.Text(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_facility_payment_audit_log_tenant_id", "facility_payment_audit_log", ["tenant_id"], unique=False)
    op.create_index("ix_facility_payment_audit_log_entity_id", "facility_payment_audit_log", ["entity_id"], unique=False)
    op.create_index("ix_facility_payment_audit_tenant_entity", "facility_payment_audit_log", ["tenant_id", "entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_facility_payment_audit_tenant_entity", table_name="facility_payment_audit_log")
    op.drop_index("ix_facility_payment_audit_log_entity_id", table_name="facility_payment_audit_log")
    op.drop_index("ix_facility_payment_audit_log_tenant_id", table_name="facility_payment_audit_log")
    op.drop_table("facility_payment_audit_log")

    op.drop_index("ix_facility_collection_alert_threshold_tenant_alert", table_name="facility_collection_alert_thresholds")
    op.drop_index("ix_facility_collection_alert_thresholds_tenant_id", table_name="facility_collection_alert_thresholds")
    op.drop_table("facility_collection_alert_thresholds")

    op.drop_index("ix_facility_collection_alerts_status", table_name="facility_collection_alerts")
    op.drop_index("ix_facility_collection_alerts_alert_type", table_name="facility_collection_alerts")
    op.drop_index("ix_facility_collection_alerts_facility_payment_expectation_id", table_name="facility_collection_alerts")
    op.drop_index("ix_facility_collection_alerts_patient_id", table_name="facility_collection_alerts")
    op.drop_index("ix_facility_collection_alerts_tenant_id", table_name="facility_collection_alerts")
    op.drop_table("facility_collection_alerts")

    op.drop_index("ix_facility_payment_allocation_payment_id", table_name="facility_payment_allocations")
    op.drop_index("ix_facility_payment_allocation_tenant_expectation", table_name="facility_payment_allocations")
    op.drop_index("ix_facility_payment_allocations_allocation_status", table_name="facility_payment_allocations")
    op.drop_index("ix_facility_payment_allocations_facility_payment_expectation_id", table_name="facility_payment_allocations")
    op.drop_index("ix_facility_payment_allocations_tenant_id", table_name="facility_payment_allocations")
    op.drop_table("facility_payment_allocations")

    op.drop_index("ix_facility_payment_expectation_tenant_reconciliation_status", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectation_tenant_status", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectation_tenant_patient", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_reconciliation_status", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_status", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_due_date", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_service_period_end", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_service_period_start", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_expected_funding_source", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_responsibility_category", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_patient_pos_id", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_patient_id", table_name="facility_payment_expectations")
    op.drop_index("ix_facility_payment_expectations_tenant_id", table_name="facility_payment_expectations")
    op.drop_table("facility_payment_expectations")
