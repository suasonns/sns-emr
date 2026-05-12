"""add_rare_regulatory_reporting_core

Revision ID: e83a93644f10
Revises: 7b7656d00e1a
Create Date: 2026-05-05 18:59:27.088525
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e83a93644f10'
down_revision: Union[str, Sequence[str], None] = '7b7656d00e1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    # --- ENUMS (SAFE, POSTGRES-COMPLIANT) ---
    reg_report_type_enum = postgresql.ENUM(
        'SIERA_ALERTS',
        'VOLUNTEER_ANNUAL',
        'CMS_ANNUAL',
        name='reg_report_type_enum',
        create_type=False
    )

    reg_report_status_enum = postgresql.ENUM(
        'DRAFT',
        'CERTIFIED',
        'LOCKED',
        name='reg_report_status_enum',
        create_type=False
    )

    reg_artifact_type_enum = postgresql.ENUM(
        'PDF',
        'CSV',
        'JSON',
        name='reg_artifact_type_enum',
        create_type=False
    )

    # Create enum types if missing (your DB already has them, so checkfirst prevents errors)
    reg_report_type_enum.create(op.get_bind(), checkfirst=True)
    reg_report_status_enum.create(op.get_bind(), checkfirst=True)
    reg_artifact_type_enum.create(op.get_bind(), checkfirst=True)

    # --- CORE REPORT HEADER ---
    op.create_table(
        'regulatory_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # IMPORTANT: Use the enum object, not sa.Enum(name=...)
        sa.Column('report_type', reg_report_type_enum, nullable=False),

        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),

        # IMPORTANT: Use the enum object, not sa.Enum(name=...)
        sa.Column('status', reg_report_status_enum, nullable=False),

        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('certified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('certified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('integrity_hash', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
    )

    # --- REPORT SECTIONS ---
    op.create_table(
        'regulatory_report_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'report_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('regulatory_reports.id'),
            nullable=False
        ),
        sa.Column('section_key', sa.Text(), nullable=False),
        sa.Column('section_title', sa.Text(), nullable=False),
        sa.Column('section_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # --- REPORT METRICS ---
    op.create_table(
        'regulatory_report_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'report_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('regulatory_reports.id'),
            nullable=False
        ),
        sa.Column(
            'section_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('regulatory_report_sections.id'),
            nullable=True
        ),
        sa.Column('metric_key', sa.Text(), nullable=False),
        sa.Column('metric_value_numeric', sa.Numeric(), nullable=True),
        sa.Column('metric_value_text', sa.Text(), nullable=True),
        sa.Column('breakdown_json', sa.JSON(), nullable=True),
    )

    # --- REPORT ARTIFACTS ---
    op.create_table(
        'regulatory_report_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'report_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('regulatory_reports.id'),
            nullable=False
        ),

        # IMPORTANT: Use the enum object, not sa.Enum(name=...)
        sa.Column('artifact_type', reg_artifact_type_enum, nullable=False),

        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('checksum', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table('regulatory_report_artifacts')
    op.drop_table('regulatory_report_metrics')
    op.drop_table('regulatory_report_sections')
    op.drop_table('regulatory_reports')
