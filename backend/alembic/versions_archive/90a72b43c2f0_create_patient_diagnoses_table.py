"""create patient diagnoses table

Revision ID: 90a72b43c2f0
Revises: ec68e1af4ea8
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "90a72b43c2f0"
down_revision: Union[str, Sequence[str], None] = "ec68e1af4ea8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


diagnosis_type_enum = postgresql.ENUM(
    "PRIMARY",
    "SECONDARY",
    "COMORBIDITY",
    name="patient_diagnosis_type_enum",
    create_type=False,
)

diagnosis_status_enum = postgresql.ENUM(
    "PROPOSED",
    "ACTIVE",
    "REJECTED",
    "HISTORICAL",
    name="patient_diagnosis_status_enum",
    create_type=False,
)

diagnosis_source_enum = postgresql.ENUM(
    "REFERRAL",
    "RN_ICA",
    "SPECIALIST",
    "ATTENDING_PHYSICIAN",
    "MEDICAL_DIRECTOR",
    "CTI",
    "RECERT",
    "MD",
    name="patient_diagnosis_source_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "PRIMARY",
        "SECONDARY",
        "COMORBIDITY",
        name="patient_diagnosis_type_enum",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "PROPOSED",
        "ACTIVE",
        "REJECTED",
        "HISTORICAL",
        name="patient_diagnosis_status_enum",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "REFERRAL",
        "RN_ICA",
        "SPECIALIST",
        "ATTENDING_PHYSICIAN",
        "MEDICAL_DIRECTOR",
        "CTI",
        "RECERT",
        "MD",
        name="patient_diagnosis_source_enum",
    ).create(bind, checkfirst=True)

    op.create_table(
        "patient_diagnoses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "diagnosis_type",
            diagnosis_type_enum,
            nullable=False,
        ),
        sa.Column(
            "status",
            diagnosis_status_enum,
            server_default=sa.text("'PROPOSED'"),
            nullable=False,
        ),
        sa.Column(
            "source",
            diagnosis_source_enum,
            nullable=False,
        ),
        sa.Column(
            "icd10_code",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "diagnosis_description",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "is_terminal",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_related_to_terminal",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "resolved_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "rejected_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "length(trim(icd10_code)) > 0",
            name="ck_patient_diagnoses_icd10_code_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(diagnosis_description)) > 0",
            name="ck_patient_diagnoses_description_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(display_name)) > 0",
            name="ck_patient_diagnoses_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "resolved_date IS NULL OR effective_date IS NULL OR resolved_date >= effective_date",
            name="ck_patient_diagnoses_resolved_after_effective",
        ),
        sa.CheckConstraint(
            "(status != 'REJECTED') OR (rejected_reason IS NOT NULL AND length(trim(rejected_reason)) > 0)",
            name="ck_patient_diagnoses_rejected_requires_reason",
        ),
    )

    op.create_index(
        "ix_patient_diagnoses_tenant_id",
        "patient_diagnoses",
        ["tenant_id"],
    )

    op.create_index(
        "ix_patient_diagnoses_patient_id",
        "patient_diagnoses",
        ["patient_id"],
    )

    op.create_index(
        "ix_patient_diagnoses_icd10_code",
        "patient_diagnoses",
        ["icd10_code"],
    )

    op.create_index(
        "ix_patient_diagnoses_created_by",
        "patient_diagnoses",
        ["created_by"],
    )

    op.create_index(
        "ix_patient_diagnoses_patient_type_status",
        "patient_diagnoses",
        ["patient_id", "diagnosis_type", "status"],
    )

    op.create_index(
        "ix_patient_diagnoses_tenant_patient_active",
        "patient_diagnoses",
        ["tenant_id", "patient_id", "active"],
    )

    op.create_index(
        "uq_patient_diagnoses_one_active_primary",
        "patient_diagnoses",
        ["tenant_id", "patient_id"],
        unique=True,
        postgresql_where=sa.text(
            "diagnosis_type = 'PRIMARY' "
            "AND status = 'ACTIVE' "
            "AND active = true "
            "AND resolved_date IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_patient_diagnoses_one_active_primary",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_tenant_patient_active",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_patient_type_status",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_created_by",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_icd10_code",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_patient_id",
        table_name="patient_diagnoses",
    )

    op.drop_index(
        "ix_patient_diagnoses_tenant_id",
        table_name="patient_diagnoses",
    )

    op.drop_table("patient_diagnoses")

    postgresql.ENUM(
        name="patient_diagnosis_source_enum",
    ).drop(op.get_bind(), checkfirst=True)

    postgresql.ENUM(
        name="patient_diagnosis_status_enum",
    ).drop(op.get_bind(), checkfirst=True)

    postgresql.ENUM(
        name="patient_diagnosis_type_enum",
    ).drop(op.get_bind(), checkfirst=True)