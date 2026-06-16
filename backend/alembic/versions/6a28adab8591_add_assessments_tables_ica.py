"""add assessments tables (ICA) — REBUILD-SAFE

Revision ID: 6a28adab8591
Revises: bba772574147
Create Date: 2026-06-02 12:04:07.972181
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6a28adab8591"
down_revision: Union[str, Sequence[str], None] = "bba772574147"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =========================================================
# ENUM DEFINITIONS (REUSE ONLY — DO NOT AUTO-CREATE)
# =========================================================

discipline_enum = postgresql.ENUM(
    "RN",
    "MSW",
    "SC",
    "MD",
    "NP",
    "LVN",
    "CHHA",
    name="assessment_discipline_enum",
    create_type=False,
)

assessment_type_enum = postgresql.ENUM(
    "RN_ICA",
    "MSW_ICA",
    "SC_ICA",
    "RN_BEREAVEMENT_BASELINE",
    "BEREAVEMENT_ASSESSMENT",
    name="assessment_type_enum",
    create_type=False,
)

status_enum = postgresql.ENUM(
    "DRAFT",
    "SIGNED",
    "VOIDED",
    name="assessment_status_enum",
    create_type=False,
)

risk_level_enum = postgresql.ENUM(
    "LOW",
    "MODERATE",
    "HIGH",
    name="assessment_risk_level_enum",
    create_type=False,
)


# =========================================================
# Helpers (idempotent / rebuild-safe)
# =========================================================

def _table_exists(inspector, table_name: str, schema: str = "public") -> bool:
    return table_name in inspector.get_table_names(schema=schema)


def _constraint_exists(
    bind,
    table_name: str,
    constraint_name: str,
    schema: str = "public",
) -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = :schema
          AND t.relname = :table_name
          AND c.conname = :constraint_name
        """
    )
    return bind.execute(
        sql,
        {
            "schema": schema,
            "table_name": table_name,
            "constraint_name": constraint_name,
        },
    ).first() is not None


def _index_exists(
    bind,
    table_name: str,
    index_name: str,
    schema: str = "public",
) -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = :schema
          AND tablename = :table_name
          AND indexname = :index_name
        """
    )
    return bind.execute(
        sql,
        {
            "schema": schema,
            "table_name": table_name,
            "index_name": index_name,
        },
    ).first() is not None


# =========================================================
# Upgrade
# =========================================================

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # =====================================================
    # CREATE ENUMS SAFELY (ONLY IF MISSING)
    # =====================================================
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'assessment_discipline_enum'
            ) THEN
                CREATE TYPE assessment_discipline_enum AS ENUM (
                    'RN', 'MSW', 'SC', 'MD', 'NP', 'LVN', 'CHHA'
                );
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'assessment_type_enum'
            ) THEN
                CREATE TYPE assessment_type_enum AS ENUM (
                    'RN_ICA',
                    'MSW_ICA',
                    'SC_ICA',
                    'RN_BEREAVEMENT_BASELINE',
                    'BEREAVEMENT_ASSESSMENT'
                );
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'assessment_status_enum'
            ) THEN
                CREATE TYPE assessment_status_enum AS ENUM (
                    'DRAFT',
                    'SIGNED',
                    'VOIDED'
                );
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'assessment_risk_level_enum'
            ) THEN
                CREATE TYPE assessment_risk_level_enum AS ENUM (
                    'LOW',
                    'MODERATE',
                    'HIGH'
                );
            END IF;
        END$$;
        """
    )

    # =====================================================
    # assessments
    # =====================================================
    if not _table_exists(inspector, "assessments"):
        op.create_table(
            "assessments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discipline", discipline_enum, nullable=False),
            sa.Column("assessment_type", assessment_type_enum, nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "status",
                status_enum,
                nullable=False,
                server_default=sa.text("'DRAFT'"),
            ),
            sa.Column("risk_score", sa.Integer(), nullable=True),
            sa.Column("risk_level", risk_level_enum, nullable=True),
            sa.Column(
                "data_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )

    if _table_exists(inspector, "assessments"):
        if not _constraint_exists(bind, "assessments", "ck_assessment_signed_requires_fields"):
            op.create_check_constraint(
                "ck_assessment_signed_requires_fields",
                "assessments",
                """
                status <> 'SIGNED'
                OR (
                    signed_at IS NOT NULL
                    AND signed_by IS NOT NULL
                )
                """,
            )

        if not _constraint_exists(bind, "assessments", "ck_rn_baseline_must_be_rn"):
            op.create_check_constraint(
                "ck_rn_baseline_must_be_rn",
                "assessments",
                """
                assessment_type <> 'RN_BEREAVEMENT_BASELINE'
                OR discipline = 'RN'
                """,
            )

        if not _index_exists(bind, "assessments", "ix_assessments_patient_id"):
            op.create_index(
                "ix_assessments_patient_id",
                "assessments",
                ["patient_id"],
                unique=False,
            )

        if not _index_exists(bind, "assessments", "ix_assessments_assessment_type"):
            op.create_index(
                "ix_assessments_assessment_type",
                "assessments",
                ["assessment_type"],
                unique=False,
            )

        if not _index_exists(bind, "assessments", "ix_assessments_discipline"):
            op.create_index(
                "ix_assessments_discipline",
                "assessments",
                ["discipline"],
                unique=False,
            )

    # refresh inspector after possible create
    inspector = inspect(bind)

    # =====================================================
    # assessment_references
    # =====================================================
    if not _table_exists(inspector, "assessment_references"):
        op.create_table(
            "assessment_references",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("referenced_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reference_kind", sa.String(length=100), nullable=False),
            sa.Column("reviewed_ack", sa.Boolean(), nullable=False),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )

    if _table_exists(inspector, "assessment_references"):
        if not _index_exists(bind, "assessment_references", "ix_assessment_references_assessment_id"):
            op.create_index(
                "ix_assessment_references_assessment_id",
                "assessment_references",
                ["assessment_id"],
                unique=False,
            )

        if not _index_exists(bind, "assessment_references", "ix_assessment_references_referenced_assessment_id"):
            op.create_index(
                "ix_assessment_references_referenced_assessment_id",
                "assessment_references",
                ["referenced_assessment_id"],
                unique=False,
            )

    inspector = inspect(bind)

    # =====================================================
    # assessment_discrepancies
    # =====================================================
    if not _table_exists(inspector, "assessment_discrepancies"):
        op.create_table(
            "assessment_discrepancies",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("domain", sa.String(length=100), nullable=False),
            sa.Column("baseline_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("comparing_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discrepancy_summary", sa.Text(), nullable=True),
            sa.Column(
                "requires_idg_reconciliation",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "resolved",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_in_idg_meeting_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("resolution_note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )

    if _table_exists(inspector, "assessment_discrepancies"):
        if not _index_exists(bind, "assessment_discrepancies", "ix_assessment_discrepancies_patient_id"):
            op.create_index(
                "ix_assessment_discrepancies_patient_id",
                "assessment_discrepancies",
                ["patient_id"],
                unique=False,
            )

        if not _index_exists(bind, "assessment_discrepancies", "ix_assessment_discrepancies_resolved"):
            op.create_index(
                "ix_assessment_discrepancies_resolved",
                "assessment_discrepancies",
                ["resolved"],
                unique=False,
            )


def downgrade() -> None:
    # Forward-only migration for compliance/audit safety.
    pass