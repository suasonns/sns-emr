"""add rn recert assessments

Revision ID: d45cb3f73cac
Revises: 49b83daaa248
Create Date: 2026-06-22 22:06:26.862010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d45cb3f73cac"
down_revision: Union[str, Sequence[str], None] = "49b83daaa248"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rn_recert_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column("form_type", sa.String(length=50), nullable=False, server_default="RECERT"),
        sa.Column("form_family", sa.String(length=50), nullable=False, server_default="CLINICAL"),
        sa.Column("discipline", sa.String(length=50), nullable=False, server_default="RN"),

        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("pps_score", sa.Integer(), nullable=True),
        sa.Column("kps_score", sa.Integer(), nullable=True),
        sa.Column("fast_stage", sa.String(length=50), nullable=True),
        sa.Column("nyha_class", sa.String(length=50), nullable=True),

        sa.Column("adl_level", sa.String(length=50), nullable=True),
        sa.Column("adl_dependency_count", sa.Integer(), nullable=True),

        sa.Column("primary_diagnosis", sa.Text(), nullable=True),
        sa.Column("eligibility_recommendation", sa.String(length=20), nullable=False, server_default="UNDECIDED"),

        sa.Column(
            "raw_observations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "clarification_items_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "normalized_observations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "translation_output_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "translation_source_map_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "interpretation_output_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column("translation_mode_used", sa.String(length=20), nullable=False, server_default="DETERMINISTIC"),
        sa.Column("translation_reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("translation_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("translation_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attesting_provider_user_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_rn_recert_assessments_patient_id_patients"),
        ),
        sa.ForeignKeyConstraint(
            ["benefit_period_id"],
            ["benefit_periods.id"],
            name=op.f("fk_rn_recert_assessments_benefit_period_id_benefit_periods"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_rn_recert_assessments_created_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["translation_reviewed_by"],
            ["users.id"],
            name=op.f("fk_rn_recert_assessments_translation_reviewed_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["attesting_provider_user_id"],
            ["users.id"],
            name=op.f("fk_rn_recert_assessments_attesting_provider_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rn_recert_assessments")),
    )

    op.create_index(
        op.f("ix_rn_recert_assessments_patient_id"),
        "rn_recert_assessments",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rn_recert_assessments_benefit_period_id"),
        "rn_recert_assessments",
        ["benefit_period_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rn_recert_assessments_created_by_user_id"),
        "rn_recert_assessments",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rn_recert_assessments_status"),
        "rn_recert_assessments",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_rn_recert_assessments_status"), table_name="rn_recert_assessments")
    op.drop_index(op.f("ix_rn_recert_assessments_created_by_user_id"), table_name="rn_recert_assessments")
    op.drop_index(op.f("ix_rn_recert_assessments_benefit_period_id"), table_name="rn_recert_assessments")
    op.drop_index(op.f("ix_rn_recert_assessments_patient_id"), table_name="rn_recert_assessments")
    op.drop_table("rn_recert_assessments")