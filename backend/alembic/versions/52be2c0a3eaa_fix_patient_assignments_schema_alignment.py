"""fix patient_assignments schema alignment

Revision ID: 52be2c0a3eaa
Revises: 1ba7178f0f4c
Create Date: 2026-06-22 23:21:35.504177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52be2c0a3eaa'
down_revision: Union[str, Sequence[str], None] = '1ba7178f0f4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()

    bind.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assignment_discipline_enum') THEN
                CREATE TYPE assignment_discipline_enum AS ENUM (
                    'MD', 'DO', 'MEDICAL_DIRECTOR', 'ATTENDING_PHYSICIAN', 'NP', 'PA',
                    'RN', 'LVN', 'LPN', 'CHHA', 'AIDE',
                    'SW', 'MSW', 'BSW', 'LCSW', 'SC', 'CHAPLAIN',
                    'BEREAVEMENT_COORDINATOR', 'PHARMACIST', 'DIETITIAN',
                    'RESPIRATORY_THERAPIST', 'ADMIN', 'EXECUTIVE_DIRECTOR', 'ADMINISTRATOR',
                    'DIRECTOR', 'CLINICAL_DIRECTOR', 'DPCS', 'INTAKE', 'CASE_MANAGER',
                    'SURVEYOR', 'CONSULTANT', 'VOLUNTEER_COORDINATOR', 'VOLUNTEER',
                    'DRIVER', 'INTERPRETER', 'HOUSEKEEPER'
                );
            END IF;
        END $$;
    """))

    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("patient_assignments")}

    # =========================================
    # 1. RENAME COLUMN staff_user_id → user_id
    # =========================================
    if "staff_user_id" in columns and "user_id" not in columns:
        op.alter_column(
            "patient_assignments",
            "staff_user_id",
            new_column_name="user_id"
        )

    # =========================================
    # 2. CONVERT discipline → ENUM
    # =========================================
    if "discipline" in columns:
        discipline_type = bind.execute(
            sa.text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'patient_assignments' AND column_name = 'discipline'
                LIMIT 1
                """
            )
        ).scalar()

        if discipline_type != "USER-DEFINED":
            op.execute("""
                ALTER TABLE patient_assignments
                ALTER COLUMN discipline TYPE assignment_discipline_enum
                USING discipline::text::assignment_discipline_enum
            """)


def downgrade():
    # reverse if needed
    op.alter_column(
        "patient_assignments",
        "user_id",
        new_column_name="staff_user_id"
    )

    op.execute("""
        ALTER TABLE patient_assignments
        ALTER COLUMN discipline TYPE VARCHAR(16)
    """)
