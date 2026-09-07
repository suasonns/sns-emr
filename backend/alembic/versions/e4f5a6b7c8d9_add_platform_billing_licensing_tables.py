"""create platform billing/licensing tables (subscription_plans, tenant_subscriptions, platform_invoices, platform_payments, license_allocations)

Revision ID: e4f5a6b7c8d9
Revises: c1d4e5f6a7b8
Create Date: 2026-09-05

Note (hotfix/alembic-graph-reconciliation): this migration originally
declared down_revision = "d2e3f4a5b6c7" (add_contact_harvesting_attribution),
assuming feature/patient-contact-harvesting would merge to main first. It
never did, leaving that revision id unresolvable on main and splitting the
graph into two disconnected heads. Repointed to c1d4e5f6a7b8, the actual
main-line head at the time this migration was authored. No schema changes;
forward-only graph reconciliation only.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "c1d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # subscription_plans (SNS's own plan catalog -- NOT tenant scoped)
    # ---------------------------------------------------------------
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_code", sa.String(length=64), nullable=False),
        sa.Column("plan_label", sa.String(length=255), nullable=False),
        sa.Column("monthly_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("seat_allowance", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_unique_constraint("uq_subscription_plans_plan_code", "subscription_plans", ["plan_code"])
    op.create_index("ix_subscription_plans_status", "subscription_plans", ["status"], unique=False)

    # ---------------------------------------------------------------
    # tenant_subscriptions (one tenant's subscription to a plan)
    # ---------------------------------------------------------------
    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'TRIAL'")),
        sa.Column("seats_licensed", sa.Integer(), nullable=True),
        sa.Column("monthly_rate_override", sa.Numeric(12, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_tenant_subscriptions_tenant_id", "tenant_subscriptions", ["tenant_id"], unique=False)
    op.create_index("ix_tenant_subscriptions_plan_id", "tenant_subscriptions", ["plan_id"], unique=False)
    op.create_index("ix_tenant_subscriptions_tenant_status", "tenant_subscriptions", ["tenant_id", "status"], unique=False)
    op.create_index("ix_tenant_subscriptions_renewal_date", "tenant_subscriptions", ["renewal_date"], unique=False)

    # ---------------------------------------------------------------
    # platform_invoices (SNS -> tenant invoices)
    # ---------------------------------------------------------------
    op.create_table(
        "platform_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_number", sa.String(length=64), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_unique_constraint("uq_platform_invoices_invoice_number", "platform_invoices", ["invoice_number"])
    op.create_index("ix_platform_invoices_tenant_id", "platform_invoices", ["tenant_id"], unique=False)
    op.create_index("ix_platform_invoices_subscription_id", "platform_invoices", ["subscription_id"], unique=False)
    op.create_index("ix_platform_invoices_tenant_status", "platform_invoices", ["tenant_id", "status"], unique=False)
    op.create_index("ix_platform_invoices_due_date", "platform_invoices", ["due_date"], unique=False)

    # ---------------------------------------------------------------
    # platform_payments (tenant -> SNS payments against an invoice)
    # ---------------------------------------------------------------
    op.create_table(
        "platform_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platform_invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_platform_payments_tenant_id", "platform_payments", ["tenant_id"], unique=False)
    op.create_index("ix_platform_payments_invoice_id", "platform_payments", ["invoice_id"], unique=False)
    op.create_index("ix_platform_payments_tenant_status", "platform_payments", ["tenant_id", "status"], unique=False)
    op.create_index("ix_platform_payments_occurred_at", "platform_payments", ["occurred_at"], unique=False)

    # ---------------------------------------------------------------
    # license_allocations (per-tenant, per-plan-tier seat usage snapshot)
    # ---------------------------------------------------------------
    op.create_table(
        "license_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("plan_label", sa.String(length=255), nullable=False),
        sa.Column("seats_used", sa.Integer(), nullable=True),
        sa.Column("seats_total", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_license_allocations_tenant_id", "license_allocations", ["tenant_id"], unique=False)
    op.create_index("ix_license_allocations_subscription_id", "license_allocations", ["subscription_id"], unique=False)
    op.create_index("ix_license_allocations_tenant_plan", "license_allocations", ["tenant_id", "plan_label"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_license_allocations_tenant_plan", table_name="license_allocations")
    op.drop_index("ix_license_allocations_subscription_id", table_name="license_allocations")
    op.drop_index("ix_license_allocations_tenant_id", table_name="license_allocations")
    op.drop_table("license_allocations")

    op.drop_index("ix_platform_payments_occurred_at", table_name="platform_payments")
    op.drop_index("ix_platform_payments_tenant_status", table_name="platform_payments")
    op.drop_index("ix_platform_payments_invoice_id", table_name="platform_payments")
    op.drop_index("ix_platform_payments_tenant_id", table_name="platform_payments")
    op.drop_table("platform_payments")

    op.drop_index("ix_platform_invoices_due_date", table_name="platform_invoices")
    op.drop_index("ix_platform_invoices_tenant_status", table_name="platform_invoices")
    op.drop_index("ix_platform_invoices_subscription_id", table_name="platform_invoices")
    op.drop_index("ix_platform_invoices_tenant_id", table_name="platform_invoices")
    op.drop_constraint("uq_platform_invoices_invoice_number", "platform_invoices", type_="unique")
    op.drop_table("platform_invoices")

    op.drop_index("ix_tenant_subscriptions_renewal_date", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_tenant_status", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_plan_id", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_tenant_id", table_name="tenant_subscriptions")
    op.drop_table("tenant_subscriptions")

    op.drop_index("ix_subscription_plans_status", table_name="subscription_plans")
    op.drop_constraint("uq_subscription_plans_plan_code", "subscription_plans", type_="unique")
    op.drop_table("subscription_plans")
