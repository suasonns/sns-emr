"""allow PLATFORM and BILLING tenant_type values

Revision ID: v6w7x8y9z0a1
Revises: u5v6w7x8y9z0
Create Date: 2026-08-22 22:35:00.000000

SNS Hospice Solutions (the vendor/platform organization that owns OWNER-role
staff: executives, compliance, QA, support, developers, implementation) and
SNS Billing Services (the separate billing organization that owns BILLING-
role staff) are real, permanent organizations distinct from any hospice
agency tenant (Love & Faith / Angela / Silva). tenant_id remains required
(NOT NULL) on users; these two organizations get their own tenant rows
instead of a nullable tenant_id, per the locked-in decision to keep
tenant_id required and control access via tenant + domain + role.

This migration only widens the existing ck_tenant_type_valid CHECK
constraint to accept 'PLATFORM' and 'BILLING' in addition to the existing
'PRODUCTION', 'TRAINING', 'DEV' values. It does not touch any existing row.
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "v6w7x8y9z0a1"
down_revision = "u5v6w7x8y9z0"
branch_labels = None
depends_on = None

OLD_CONSTRAINT = "tenant_type IN ('PRODUCTION', 'TRAINING', 'DEV')"
NEW_CONSTRAINT = (
    "tenant_type IN ('PRODUCTION', 'TRAINING', 'DEV', 'PLATFORM', 'BILLING')"
)


def upgrade() -> None:
    op.drop_constraint("ck_tenant_type_valid", "tenants", type_="check")
    op.create_check_constraint("ck_tenant_type_valid", "tenants", NEW_CONSTRAINT)


def downgrade() -> None:
    op.drop_constraint("ck_tenant_type_valid", "tenants", type_="check")
    op.create_check_constraint("ck_tenant_type_valid", "tenants", OLD_CONSTRAINT)
