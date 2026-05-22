"""add_tenant_id_to_survey_access

Revision ID: f115ffe3c4f9
Revises: 9738bc94da79
Create Date: 2026-05-21 14:48:06.276112
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f115ffe3c4f9"
down_revision: Union[str, Sequence[str], None] = "9738bc94da79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # 1) Add tenant_id as NULLABLE (safe for existing rows)
    # ---------------------------------------------------------
    op.add_column(
        "survey_access",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )

    # ---------------------------------------------------------
    # 2) Backfill tenant_id from patients (authoritative source)
    # ---------------------------------------------------------
    op.execute(
        """
        UPDATE public.survey_access sa
        SET tenant_id = p.tenant_id
        FROM public.patients p
        WHERE sa.patient_id = p.id
          AND sa.tenant_id IS NULL
        """
    )

    # ---------------------------------------------------------
    # 3) Enforce NOT NULL after backfill
    # ---------------------------------------------------------
    op.alter_column(
        "survey_access",
        "tenant_id",
        nullable=False,
        schema="public",
    )

    # ---------------------------------------------------------
    # 4) Add FK + index
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_survey_access_tenant",
        "survey_access",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
        source_schema="public",
        referent_schema="public",
    )

    op.create_index(
        "ix_survey_access_tenant_id",
        "survey_access",
        ["tenant_id"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_survey_access_tenant_id",
        table_name="survey_access",
        schema="public",
    )
    op.drop_constraint(
        "fk_survey_access_tenant",
        "survey_access",
        type_="foreignkey",
        schema="public",
    )
    op.drop_column(
        "survey_access",
        "tenant_id",
        schema="public",
    )