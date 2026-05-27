"""add assessments references and discrepancies

Revision ID: 81d8dfcde545
Revises: 99eb26dcd457
Create Date: 2026-05-26 14:37:15.421408

"""
from typing import Sequence, Union, Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "81d8dfcde545"
down_revision: Union[str, Sequence[str], None] = "99eb26dcd457"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_pk_column(table_name: str, schema: str = "public") -> Optional[str]:
    """
    Returns the primary key column name for a given table, or None if not found.
    """
    bind = op.get_bind()
    sql = sa.text(
        """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = :schema
          AND tc.table_name = :table
          AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY kcu.ordinal_position
        LIMIT 1
        """
    )
    return bind.execute(sql, {"schema": schema, "table": table_name}).scalar()


def _table_exists(table_name: str, schema: str = "public") -> bool:
    bind = op.get_bind()
    sql = sa.text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_name = :table
        LIMIT 1
        """
    )
    return bind.execute(sql, {"schema": schema, "table": table_name}).scalar() is not None


def upgrade() -> None:
    # Enterprise-safe: enable uuid extension for server-side UUID defaults.
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Detect PKs (do NOT assume "id" exists everywhere)
    patients_pk = _get_pk_column("patients")
    idg_meetings_pk = _get_pk_column("idg_meetings") if _table_exists("idg_meetings") else None

    # 1) assessments
    op.create_table(
        "assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Create as plain UUID column first; add FK after creation (safer)
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("discipline", sa.String(length=16), nullable=False),
        sa.Column("assessment_type", sa.String(length=64), nullable=False),

        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),

        # Enterprise-safe default: quoted literal
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'DRAFT'")),

        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=True),

        sa.Column(
            "data_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_assessments_patient_type_status",
        "assessments",
        ["patient_id", "assessment_type", "status"],
    )

    # SIGNED must have signed_at (audit-proof)
    op.create_check_constraint(
        "ck_assessments_signed_requires_signed_at",
        "assessments",
        "(status <> 'SIGNED') OR (signed_at IS NOT NULL)",
    )

    # Add patient FK AFTER creation (prevents failures if PK name differs)
    if patients_pk:
        op.create_foreign_key(
            "fk_assessments_patient",
            "assessments",
            "patients",
            ["patient_id"],
            [patients_pk],
            source_schema="public",
            referent_schema="public",
            ondelete="RESTRICT",
        )

    # 2) assessment_references
    op.create_table(
        "assessment_references",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("referenced_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("reference_kind", sa.String(length=32), nullable=False),  # RN_BASELINE
        sa.Column("reviewed_ack", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_assessment_references_assessment_id", "assessment_references", ["assessment_id"])
    op.create_index("ix_assessment_references_referenced_id", "assessment_references", ["referenced_assessment_id"])

    # FKs to assessments
    op.create_foreign_key(
        "fk_assessment_references_assessment",
        "assessment_references",
        "assessments",
        ["assessment_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_assessment_references_referenced",
        "assessment_references",
        "assessments",
        ["referenced_assessment_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="CASCADE",
    )

    # Enterprise: if reviewed_ack is true, reviewed_at must be present
    op.create_check_constraint(
        "ck_assessment_references_ack_requires_reviewed_at",
        "assessment_references",
        "(reviewed_ack = false) OR (reviewed_at IS NOT NULL)",
    )

    # 3) assessment_discrepancies
    op.create_table(
        "assessment_discrepancies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Create plain columns first; add FKs after creation
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("domain", sa.String(length=50), nullable=False),

        sa.Column("baseline_assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("comparing_assessment_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("discrepancy_summary", sa.Text(), nullable=True),

        sa.Column("requires_idg_reconciliation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("resolved_in_idg_meeting_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_assessment_discrepancies_patient_resolved_domain",
        "assessment_discrepancies",
        ["patient_id", "resolved", "domain"],
    )

    # FKs to patients + assessments
    if patients_pk:
        op.create_foreign_key(
            "fk_discrepancies_patient",
            "assessment_discrepancies",
            "patients",
            ["patient_id"],
            [patients_pk],
            source_schema="public",
            referent_schema="public",
            ondelete="RESTRICT",
        )

    op.create_foreign_key(
        "fk_discrepancies_baseline_assessment",
        "assessment_discrepancies",
        "assessments",
        ["baseline_assessment_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_discrepancies_comparing_assessment",
        "assessment_discrepancies",
        "assessments",
        ["comparing_assessment_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )

    # FK to idg_meetings only if table exists and PK is known (prevents your error)
    if idg_meetings_pk:
        op.create_foreign_key(
            "fk_discrepancies_resolved_in_idg_meeting",
            "assessment_discrepancies",
            "idg_meetings",
            ["resolved_in_idg_meeting_id"],
            [idg_meetings_pk],
            source_schema="public",
            referent_schema="public",
            ondelete="SET NULL",
        )

    # Enterprise: if resolved=true then resolved_at must exist
    op.create_check_constraint(
        "ck_discrepancies_resolved_requires_resolved_at",
        "assessment_discrepancies",
        "(resolved = false) OR (resolved_at IS NOT NULL)",
    )


def downgrade() -> None:
    # Drop constraints / indexes in reverse order
    op.drop_constraint("ck_discrepancies_resolved_requires_resolved_at", "assessment_discrepancies", type_="check")

    # FKs created with explicit names
    if _table_exists("assessment_discrepancies"):
        # Some FKs may not exist depending on environment, so drop defensively
        for fk_name in [
            "fk_discrepancies_resolved_in_idg_meeting",
            "fk_discrepancies_comparing_assessment",
            "fk_discrepancies_baseline_assessment",
            "fk_discrepancies_patient",
        ]:
            try:
                op.drop_constraint(fk_name, "assessment_discrepancies", type_="foreignkey")
            except Exception:
                pass

    op.drop_index("ix_assessment_discrepancies_patient_resolved_domain", table_name="assessment_discrepancies")
    op.drop_table("assessment_discrepancies")

    op.drop_constraint("ck_assessment_references_ack_requires_reviewed_at", "assessment_references", type_="check")
    for fk_name in ["fk_assessment_references_referenced", "fk_assessment_references_assessment"]:
        try:
            op.drop_constraint(fk_name, "assessment_references", type_="foreignkey")
        except Exception:
            pass

    op.drop_index("ix_assessment_references_referenced_id", table_name="assessment_references")
    op.drop_index("ix_assessment_references_assessment_id", table_name="assessment_references")
    op.drop_table("assessment_references")

    # Drop assessments patient FK if present
    try:
        op.drop_constraint("fk_assessments_patient", "assessments", type_="foreignkey")
    except Exception:
        pass

    op.drop_constraint("ck_assessments_signed_requires_signed_at", "assessments", type_="check")
    op.drop_index("ix_assessments_patient_type_status", table_name="assessments")
    op.drop_table("assessments")
