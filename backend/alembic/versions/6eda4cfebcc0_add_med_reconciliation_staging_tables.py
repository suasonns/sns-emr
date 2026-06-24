"""add med reconciliation staging tables

Revision ID: 6eda4cfebcc0
Revises: 6081586e9840
Create Date: 2026-06-18 20:04:02.545817
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6eda4cfebcc0"
down_revision: Union[str, Sequence[str], None] = "6081586e9840"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # =========================================================
    # med_reconciliation_imports
    # =========================================================
    op.create_table(
        "med_reconciliation_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_context", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'PENDING_REVIEW'"),
        ),
        sa.Column("source_file_name", sa.String(length=255), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_med_reconciliation_imports"),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
            name="fk_med_reconciliation_imports_patient_id_patients",
        ),
        sa.CheckConstraint(
            "source_type IN ('PDF', 'CCD', 'C-CDA', 'SCANNED_DOC', 'MANUAL')",
            name="ck_med_reconciliation_imports_source_type",
        ),
        sa.CheckConstraint(
            "source_context IN ('HOSPITAL_DISCHARGE', 'ED_VISIT', 'INPATIENT_STAY', 'OTHER')",
            name="ck_med_reconciliation_imports_source_context",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING_REVIEW', 'PARTIALLY_REVIEWED', 'FINALIZED')",
            name="ck_med_reconciliation_imports_status",
        ),
    )

    op.create_index(
        "ix_med_reconciliation_imports_tenant_id",
        "med_reconciliation_imports",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_imports_patient_id",
        "med_reconciliation_imports",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_imports_status",
        "med_reconciliation_imports",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_imports_uploaded_at",
        "med_reconciliation_imports",
        ["uploaded_at"],
        unique=False,
    )

    # =========================================================
    # med_reconciliation_items
    # =========================================================
    op.create_table(
        "med_reconciliation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("list_type", sa.String(length=32), nullable=False),
        sa.Column("med_name_raw", sa.String(length=255), nullable=False),
        sa.Column("med_name_normalized", sa.String(length=255), nullable=True),

        sa.Column("dose", sa.String(length=128), nullable=True),
        sa.Column("route", sa.String(length=64), nullable=True),
        sa.Column("frequency", sa.String(length=128), nullable=True),
        sa.Column("indication", sa.String(length=255), nullable=True),

        sa.Column("reaction_description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=True),
        sa.Column("reaction_category_suggested", sa.String(length=32), nullable=True),
        sa.Column("reaction_category_final", sa.String(length=32), nullable=True),

        sa.Column(
            "is_discharge_candidate",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_immediate_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_critical_reaction",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "review_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.PrimaryKeyConstraint("id", name="pk_med_reconciliation_items"),
        sa.ForeignKeyConstraint(
            ["import_id"],
            ["med_reconciliation_imports.id"],
            ondelete="CASCADE",
            name="fk_med_reconciliation_items_import_id_imports",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
            name="fk_med_reconciliation_items_patient_id_patients",
        ),
        sa.CheckConstraint(
            "list_type IN ('INPATIENT_HISTORY', 'DISCHARGE_LIST')",
            name="ck_med_reconciliation_items_list_type",
        ),
        sa.CheckConstraint(
            "(severity IS NULL) OR (severity IN ('MILD', 'MODERATE', 'SEVERE'))",
            name="ck_med_reconciliation_items_severity",
        ),
        sa.CheckConstraint(
            "(reaction_category_suggested IS NULL) OR (reaction_category_suggested IN ('POSSIBLE_ALLERGY', 'POSSIBLE_SIDE_EFFECT', 'POSSIBLE_INTOLERANCE', 'UNKNOWN'))",
            name="ck_med_reconciliation_items_reaction_category_suggested",
        ),
        sa.CheckConstraint(
            "(reaction_category_final IS NULL) OR (reaction_category_final IN ('ALLERGY', 'SIDE_EFFECT', 'INTOLERANCE'))",
            name="ck_med_reconciliation_items_reaction_category_final",
        ),
        sa.CheckConstraint(
            "review_status IN ('PENDING', 'REVIEWED', 'ACCEPTED', 'REJECTED')",
            name="ck_med_reconciliation_items_review_status",
        ),
    )

    op.create_index(
        "ix_med_reconciliation_items_import_id",
        "med_reconciliation_items",
        ["import_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_items_tenant_id",
        "med_reconciliation_items",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_items_patient_id",
        "med_reconciliation_items",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_items_review_status",
        "med_reconciliation_items",
        ["review_status"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_items_is_critical_reaction",
        "med_reconciliation_items",
        ["is_critical_reaction"],
        unique=False,
    )
    op.create_index(
        "ix_med_reconciliation_items_import_list_type",
        "med_reconciliation_items",
        ["import_id", "list_type"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_med_reconciliation_items_import_list_type",
        table_name="med_reconciliation_items",
    )
    op.drop_index(
        "ix_med_reconciliation_items_is_critical_reaction",
        table_name="med_reconciliation_items",
    )
    op.drop_index(
        "ix_med_reconciliation_items_review_status",
        table_name="med_reconciliation_items",
    )
    op.drop_index(
        "ix_med_reconciliation_items_patient_id",
        table_name="med_reconciliation_items",
    )
    op.drop_index(
        "ix_med_reconciliation_items_tenant_id",
        table_name="med_reconciliation_items",
    )
    op.drop_index(
        "ix_med_reconciliation_items_import_id",
        table_name="med_reconciliation_items",
    )

    op.drop_table("med_reconciliation_items")

    op.drop_index(
        "ix_med_reconciliation_imports_uploaded_at",
        table_name="med_reconciliation_imports",
    )
    op.drop_index(
        "ix_med_reconciliation_imports_status",
        table_name="med_reconciliation_imports",
    )
    op.drop_index(
        "ix_med_reconciliation_imports_patient_id",
        table_name="med_reconciliation_imports",
    )
    op.drop_index(
        "ix_med_reconciliation_imports_tenant_id",
        table_name="med_reconciliation_imports",
    )

    op.drop_table("med_reconciliation_imports")