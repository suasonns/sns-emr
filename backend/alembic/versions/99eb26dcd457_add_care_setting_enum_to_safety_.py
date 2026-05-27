"""
Add care_setting enum and safety_responsibility enum to safety_assessments

Revision ID: 99eb26dcd457
Revises: 0cf459de52f2
Create Date: 2026-05-26 10:06:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# Alembic revision identifiers
revision: str = "99eb26dcd457"
down_revision: Union[str, Sequence[str], None] = "0cf459de52f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add care_setting and safety_responsibility columns to safety_assessments.

    Enterprise-grade behavior:
    - Creates PostgreSQL ENUM types explicitly (forward-only).
    - Adds columns only if missing (idempotent in multi-env deploys).
    """

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("safety_assessments")}

    # 1) Create care_setting_enum (forward-only, PostgreSQL-safe)
    care_setting_enum = postgresql.ENUM(
        "HOME",
        "ALF",
        "BOARD_AND_CARE",
        "SNF",
        "HOSPITAL",
        "INPATIENT_HOSPICE",
        "RESIDENTIAL_CARE_FACILITY",
        "CORRECTIONAL_FACILITY",
        "HOMELESS_SHELTER",
        "TEMPORARY_RELOCATION",
        "OTHER",
        name="care_setting_enum",
        create_type=True,
    )
    care_setting_enum.create(bind, checkfirst=True)

    # 2) Create safety_responsibility_enum (forward-only, PostgreSQL-safe)
    safety_responsibility_enum = postgresql.ENUM(
        "HOSPICE_MANAGED",
        "FACILITY_MANAGED",
        name="safety_responsibility_enum",
        create_type=True,
    )
    safety_responsibility_enum.create(bind, checkfirst=True)

    # 3) Add care_setting column if missing
    if "care_setting" not in existing_cols:
        op.add_column(
            "safety_assessments",
            sa.Column("care_setting", care_setting_enum, nullable=False),
        )

    # 4) Add safety_responsibility column if missing
    if "safety_responsibility" not in existing_cols:
        op.add_column(
            "safety_assessments",
            sa.Column("safety_responsibility", safety_responsibility_enum, nullable=False),
        )


def downgrade() -> None:
    """
    Downgrade intentionally omitted.

    PostgreSQL ENUMs are forward-only in production systems.
    """
    pass
