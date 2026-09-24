"""HOPE J2052C ownership fix: sfv_requirements reason columns + sfv_outcome_corrections

Issue #146. Adds columns to `sfv_requirements` so the CMS J2052C "reason
SFV not completed" outcome is attributed to the clinician who actually
attempted the SFV (via the attempt visit), never the triggering RN
ICA/HUV assessment author. Adds a new, append-only
`sfv_outcome_corrections` table mirroring the SECTION 12
`rnica_amendments` "never destroy, always append" guarantee.

Purely additive: extends the existing `ck_sfv_requirements_status` check
constraint with one new value (NOT_COMPLETED); does not remove or
reinterpret any existing status value, and does not modify any existing
row.

Revision ID: y9z0a1b2c3d4
Revises: f7a8b9c0d1e2
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "y9z0a1b2c3d4"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sfv_requirements", sa.Column("reason_code", sa.String(2), nullable=True))
    op.add_column(
        "sfv_requirements",
        sa.Column("reason_recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column("sfv_requirements", sa.Column("reason_recorded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "sfv_requirements",
        sa.Column(
            "reason_recorded_visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.drop_constraint("ck_sfv_requirements_status", "sfv_requirements", type_="check")
    op.create_check_constraint(
        "ck_sfv_requirements_status",
        "sfv_requirements",
        "status IN ('OPEN', 'COMPLETED', 'OVERDUE', 'CANCELLED', 'NOT_COMPLETED')",
    )
    op.create_check_constraint(
        "ck_sfv_requirements_reason_code",
        "sfv_requirements",
        "reason_code IS NULL OR reason_code IN ('1', '2', '3', '9')",
    )

    op.create_table(
        "sfv_outcome_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sfv_requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sfv_requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prior_reason_code", sa.String(2), nullable=True),
        sa.Column("new_reason_code", sa.String(2), nullable=False),
        sa.Column("correction_reason", sa.Text(), nullable=False),
        sa.Column("corrected_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # BaseModel declares created_by on every model; omitting it here
        # caused a real runtime INSERT failure (UndefinedColumn), caught
        # by Postgres-backed test execution -- not visible via
        # py_compile/import-only verification.
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_sfv_outcome_corrections_tenant_id", "sfv_outcome_corrections", ["tenant_id"])
    op.create_index("ix_sfv_outcome_corrections_patient_id", "sfv_outcome_corrections", ["patient_id"])
    op.create_index(
        "ix_sfv_outcome_corrections_sfv_requirement_id", "sfv_outcome_corrections", ["sfv_requirement_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_sfv_outcome_corrections_sfv_requirement_id", table_name="sfv_outcome_corrections")
    op.drop_index("ix_sfv_outcome_corrections_patient_id", table_name="sfv_outcome_corrections")
    op.drop_index("ix_sfv_outcome_corrections_tenant_id", table_name="sfv_outcome_corrections")
    op.drop_table("sfv_outcome_corrections")

    op.drop_constraint("ck_sfv_requirements_reason_code", "sfv_requirements", type_="check")
    op.drop_constraint("ck_sfv_requirements_status", "sfv_requirements", type_="check")
    op.create_check_constraint(
        "ck_sfv_requirements_status",
        "sfv_requirements",
        "status IN ('OPEN', 'COMPLETED', 'OVERDUE', 'CANCELLED')",
    )

    op.drop_column("sfv_requirements", "reason_recorded_visit_id")
    op.drop_column("sfv_requirements", "reason_recorded_at")
    op.drop_column("sfv_requirements", "reason_recorded_by")
    op.drop_column("sfv_requirements", "reason_code")
