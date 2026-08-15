"""guarded remove patients soc_date

Revision ID: da5ca220d709
Revises: 8a6ea3cc5aca
Create Date: 2026-07-16 15:32:01.178402
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da5ca220d709"
down_revision: Union[str, Sequence[str], None] = "8a6ea3cc5aca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BACKUP_TABLE = "patients_soc_date_backup"


def _column_names(bind, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()

    patient_cols = _column_names(bind, "patients")
    admission_cols = _column_names(bind, "admissions")

    # ---------------------------------------------------------
    # Guard 1: schema must contain both columns before cleanup
    # ---------------------------------------------------------
    if "soc_date" not in patient_cols:
        raise RuntimeError("Guard check failed: patients.soc_date does not exist.")

    if "soc_date" not in admission_cols:
        raise RuntimeError("Guard check failed: admissions.soc_date does not exist.")

    # ---------------------------------------------------------
    # Guard 2: refuse to drop if any patient SOC exists without
    # a matching non-null Admission SOC
    # ---------------------------------------------------------
    missing_admission_soc = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) AS cnt
            FROM patients p
            WHERE p.soc_date IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM admissions a
                  WHERE a.patient_id = p.id
                    AND a.soc_date IS NOT NULL
              )
            """
        )
    ).scalar_one()

    if int(missing_admission_soc or 0) > 0:
        raise RuntimeError(
            f"Guard check failed: {missing_admission_soc} patient rows still have "
            "patients.soc_date with no non-null Admission.soc_date. "
            "Backfill or correct data before dropping the column."
        )

    # ---------------------------------------------------------
    # Guard 3: create backup table once
    # ---------------------------------------------------------
    existing_tables = set(sa.inspect(bind).get_table_names())

    if BACKUP_TABLE not in existing_tables:
        op.create_table(
            BACKUP_TABLE,
            sa.Column("patient_id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "backed_up_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

    # Backup only rows that currently have data and are not already backed up
    bind.execute(
        sa.text(
            f"""
            INSERT INTO {BACKUP_TABLE} (patient_id, soc_date)
            SELECT CAST(p.id AS TEXT), p.soc_date
            FROM patients p
            WHERE p.soc_date IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM {BACKUP_TABLE} b
                  WHERE b.patient_id = CAST(p.id AS TEXT)
              )
            """
        )
    )

    # ---------------------------------------------------------
    # Final action: drop the legacy column
    # ---------------------------------------------------------
    op.drop_column("patients", "soc_date")


def downgrade() -> None:
    bind = op.get_bind()

    patient_cols = _column_names(bind, "patients")

    if "soc_date" not in patient_cols:
        op.add_column(
            "patients",
            sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
        )

    existing_tables = set(sa.inspect(bind).get_table_names())

    # Restore from backup table if present
    if BACKUP_TABLE in existing_tables:
        bind.execute(
            sa.text(
                f"""
                UPDATE patients p
                SET soc_date = b.soc_date
                FROM {BACKUP_TABLE} b
                WHERE CAST(p.id AS TEXT) = b.patient_id
                  AND b.soc_date IS NOT NULL
                """
            )
        )