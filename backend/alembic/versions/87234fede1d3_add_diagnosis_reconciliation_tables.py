"""add diagnosis reconciliation tables

Revision ID: 87234fede1d3
Revises: cac43cdc0c6b
Create Date: 2026-05-06 10:21:46.935039
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "87234fede1d3"
down_revision: Union[str, Sequence[str], None] = "cac43cdc0c6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Login / actor table (staff + vendors + billers, etc.)
USER_TABLE = "accounts"


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    # Ensure UUID support for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ======================================================
    # Ensure accounts exists (MINIMAL bootstrap for FK targets)
    # ======================================================
    if not insp.has_table(USER_TABLE):
        op.create_table(
            USER_TABLE,
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    # ======================================================
    # diagnosis_sources
    # ======================================================
    if not insp.has_table("diagnosis_sources"):
        op.create_table(
            "diagnosis_sources",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "patient_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("source", sa.Text(), nullable=False),
            sa.Column("dx_type", sa.Text(), nullable=False),
            sa.Column("icd_code", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column(
                "documented_by_account_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(f"{USER_TABLE}.id"),
                nullable=True,
            ),
            sa.Column(
                "documented_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.CheckConstraint(
                "source IN ('REFERRAL','RN_IA','CTI')",
                name="ck_dx_source",
            ),
            sa.CheckConstraint(
                "dx_type IN ('PRIMARY','RELATED','SECONDARY')",
                name="ck_dx_type",
            ),
        )

        op.create_index(
            "ix_dx_patient_active",
            "diagnosis_sources",
            ["patient_id", "is_active"],
        )
        op.create_index(
            "ix_dx_patient_source_type",
            "diagnosis_sources",
            ["patient_id", "source", "dx_type"],
        )
        op.create_index(
            "uq_dx_active_primary_per_source",
            "diagnosis_sources",
            ["patient_id", "source"],
            unique=True,
            postgresql_where=sa.text(
                "is_active = true AND dx_type = 'PRIMARY'"
            ),
        )

    # ======================================================
    # diagnosis_discrepancies
    # ======================================================
    if not insp.has_table("diagnosis_discrepancies"):
        op.create_table(
            "diagnosis_discrepancies",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "patient_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("referral_primary", sa.Text(), nullable=True),
            sa.Column("rn_primary", sa.Text(), nullable=True),
            sa.Column("cti_primary", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'OPEN'"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.CheckConstraint(
                "status IN ('OPEN','ACKNOWLEDGED','RESOLVED')",
                name="ck_dx_disc_status",
            ),
        )

        op.create_index(
            "ix_dx_disc_patient_status",
            "diagnosis_discrepancies",
            ["patient_id", "status"],
        )

    # ======================================================
    # diagnosis_reconciliations
    # ======================================================
    if not insp.has_table("diagnosis_reconciliations"):
        op.create_table(
            "diagnosis_reconciliations",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "discrepancy_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(
                    "diagnosis_discrepancies.id",
                    ondelete="CASCADE",
                ),
                nullable=False,
            ),
            sa.Column("resolution_choice", sa.Text(), nullable=False),
            sa.Column("narrative", sa.Text(), nullable=True),
            sa.Column(
                "attested_by_account_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(f"{USER_TABLE}.id"),
                nullable=False,
            ),
            sa.Column(
                "attested_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.CheckConstraint(
                "resolution_choice IN ("
                "'RN_MORE_ACCURATE_TERMINAL',"
                "'CTI_TERMINAL_EVENT_RN_UNDERLYING',"
                "'CONDITION_CHANGED',"
                "'BOTH_RELEVANT_PRIMARY_VS_CONTRIBUTING',"
                "'OTHER'"
                ")",
                name="ck_dx_recon_choice",
            ),
        )

        op.create_index(
            "ix_dx_recon_discrepancy",
            "diagnosis_reconciliations",
            ["discrepancy_id"],
        )


def downgrade():
    # Forward-only by policy, but safe best-effort cleanup
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("diagnosis_reconciliations"):
        op.drop_index(
            "ix_dx_recon_discrepancy",
            table_name="diagnosis_reconciliations",
        )
        op.drop_table("diagnosis_reconciliations")

    if insp.has_table("diagnosis_discrepancies"):
        op.drop_index(
            "ix_dx_disc_patient_status",
            table_name="diagnosis_discrepancies",
        )
        op.drop_table("diagnosis_discrepancies")

    if insp.has_table("diagnosis_sources"):
        op.drop_index(
            "uq_dx_active_primary_per_source",
            table_name="diagnosis_sources",
        )
        op.drop_index(
            "ix_dx_patient_source_type",
            table_name="diagnosis_sources",
        )
        op.drop_index(
            "ix_dx_patient_active",
            table_name="diagnosis_sources",
        )
        op.drop_table("diagnosis_sources")

    # Optional cleanup: do not drop accounts here (shared actor table)