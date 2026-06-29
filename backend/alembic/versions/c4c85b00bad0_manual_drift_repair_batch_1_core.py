"""manual drift repair batch 1 core

Revision ID: c4c85b00bad0
Revises: 812c85c3d276
Create Date: 2026-06-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text


revision: str = "c4c85b00bad0"
down_revision: Union[str, Sequence[str], None] = "812c85c3d276"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def _fk_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fks = {fk["name"] for fk in inspector.get_foreign_keys(table_name)}
    return fk_name in fks


def upgrade() -> None:
    # ---------------------------------------------------------
    # PATIENTS
    # ---------------------------------------------------------
    if not _column_exists("patients", "deleted_at"):
        op.add_column(
            "patients",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ---------------------------------------------------------
    # PATIENT ASSIGNMENTS
    # ---------------------------------------------------------
    if not _column_exists("patient_assignments", "deactivated_at"):
        op.add_column(
            "patient_assignments",
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ---------------------------------------------------------
    # PATIENT INSURANCES
    # ---------------------------------------------------------
    if not _column_exists("patient_insurances", "verified_at"):
        op.add_column(
            "patient_insurances",
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists("patient_insurances", "verified_by"):
        op.add_column(
            "patient_insurances",
            sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _column_exists("patient_insurances", "created_by"):
        op.add_column(
            "patient_insurances",
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _fk_exists("patient_insurances", "fk_patient_insurances_verified_by_users"):
        op.create_foreign_key(
            "fk_patient_insurances_verified_by_users",
            "patient_insurances",
            "users",
            ["verified_by"],
            ["id"],
        )

    if not _fk_exists("patient_insurances", "fk_patient_insurances_created_by_users"):
        op.create_foreign_key(
            "fk_patient_insurances_created_by_users",
            "patient_insurances",
            "users",
            ["created_by"],
            ["id"],
        )

    # ---------------------------------------------------------
    # MED RECONCILIATION IMPORTS
    # ---------------------------------------------------------
    if not _column_exists("med_reconciliation_imports", "created_by"):
        op.add_column(
            "med_reconciliation_imports",
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _fk_exists("med_reconciliation_imports", "fk_med_reconciliation_imports_created_by_users"):
        op.create_foreign_key(
            "fk_med_reconciliation_imports_created_by_users",
            "med_reconciliation_imports",
            "users",
            ["created_by"],
            ["id"],
        )

    # ---------------------------------------------------------
    # MED RECONCILIATION ITEMS
    # ---------------------------------------------------------
    if not _column_exists("med_reconciliation_items", "created_by"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _fk_exists("med_reconciliation_items", "fk_med_reconciliation_items_created_by_users"):
        op.create_foreign_key(
            "fk_med_reconciliation_items_created_by_users",
            "med_reconciliation_items",
            "users",
            ["created_by"],
            ["id"],
        )

    # ---------------------------------------------------------
    # MEDICATIONS
    # ---------------------------------------------------------
    if not _column_exists("medications", "is_active"):
        op.add_column(
            "medications",
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=text("true"),
                nullable=False,
            ),
        )

    if not _column_exists("medications", "is_prn"):
        op.add_column(
            "medications",
            sa.Column(
                "is_prn",
                sa.Boolean(),
                server_default=text("false"),
                nullable=False,
            ),
        )

    if not _column_exists("medications", "discontinued_at"):
        op.add_column(
            "medications",
            sa.Column("discontinued_at", sa.Date(), nullable=True),
        )

    # ---------------------------------------------------------
    # AUTHORIZATION RECORDS
    # ---------------------------------------------------------
    # NOTE:
    # tenant_id is added nullable first for safe forward repair.
    # You can backfill and tighten later.
    if not _column_exists("authorization_records", "tenant_id"):
        op.add_column(
            "authorization_records",
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _column_exists("authorization_records", "created_at"):
        op.add_column(
            "authorization_records",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if not _column_exists("authorization_records", "updated_at"):
        op.add_column(
            "authorization_records",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

    if not _fk_exists("authorization_records", "fk_authorization_records_tenant_id_tenants"):
        op.create_foreign_key(
            "fk_authorization_records_tenant_id_tenants",
            "authorization_records",
            "tenants",
            ["tenant_id"],
            ["id"],
        )


def downgrade() -> None:
    # ---------------------------------------------------------
    # AUTHORIZATION RECORDS
    # ---------------------------------------------------------
    if _fk_exists("authorization_records", "fk_authorization_records_tenant_id_tenants"):
        op.drop_constraint(
            "fk_authorization_records_tenant_id_tenants",
            "authorization_records",
            type_="foreignkey",
        )

    if _column_exists("authorization_records", "updated_at"):
        op.drop_column("authorization_records", "updated_at")

    if _column_exists("authorization_records", "created_at"):
        op.drop_column("authorization_records", "created_at")

    if _column_exists("authorization_records", "tenant_id"):
        op.drop_column("authorization_records", "tenant_id")

    # ---------------------------------------------------------
    # MEDICATIONS
    # ---------------------------------------------------------
    if _column_exists("medications", "discontinued_at"):
        op.drop_column("medications", "discontinued_at")

    if _column_exists("medications", "is_prn"):
        op.drop_column("medications", "is_prn")

    if _column_exists("medications", "is_active"):
        op.drop_column("medications", "is_active")

    # ---------------------------------------------------------
    # MED RECONCILIATION ITEMS
    # ---------------------------------------------------------
    if _fk_exists("med_reconciliation_items", "fk_med_reconciliation_items_created_by_users"):
        op.drop_constraint(
            "fk_med_reconciliation_items_created_by_users",
            "med_reconciliation_items",
            type_="foreignkey",
        )

    if _column_exists("med_reconciliation_items", "created_by"):
        op.drop_column("med_reconciliation_items", "created_by")

    # ---------------------------------------------------------
    # MED RECONCILIATION IMPORTS
    # ---------------------------------------------------------
    if _fk_exists("med_reconciliation_imports", "fk_med_reconciliation_imports_created_by_users"):
        op.drop_constraint(
            "fk_med_reconciliation_imports_created_by_users",
            "med_reconciliation_imports",
            type_="foreignkey",
        )

    if _column_exists("med_reconciliation_imports", "created_by"):
        op.drop_column("med_reconciliation_imports", "created_by")

    # ---------------------------------------------------------
    # PATIENT INSURANCES
    # ---------------------------------------------------------
    if _fk_exists("patient_insurances", "fk_patient_insurances_created_by_users"):
        op.drop_constraint(
            "fk_patient_insurances_created_by_users",
            "patient_insurances",
            type_="foreignkey",
        )

    if _fk_exists("patient_insurances", "fk_patient_insurances_verified_by_users"):
        op.drop_constraint(
            "fk_patient_insurances_verified_by_users",
            "patient_insurances",
            type_="foreignkey",
        )

    if _column_exists("patient_insurances", "created_by"):
        op.drop_column("patient_insurances", "created_by")

    if _column_exists("patient_insurances", "verified_by"):
        op.drop_column("patient_insurances", "verified_by")

    if _column_exists("patient_insurances", "verified_at"):
        op.drop_column("patient_insurances", "verified_at")

    # ---------------------------------------------------------
    # PATIENT ASSIGNMENTS
    # ---------------------------------------------------------
    if _column_exists("patient_assignments", "deactivated_at"):
        op.drop_column("patient_assignments", "deactivated_at")

    # ---------------------------------------------------------
    # PATIENTS
    # ---------------------------------------------------------
    if _column_exists("patients", "deleted_at"):
        op.drop_column("patients", "deleted_at")