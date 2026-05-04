"""Add audit fields to BaseModel

Revision ID: f6496a5dc397
Revises: b8699a65514c
Create Date: 2026-04-28 19:03:26.034873
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6496a5dc397'
down_revision: Union[str, Sequence[str], None] = 'b8699a65514c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # amendments
    op.add_column(
        'amendments',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('amendments', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_amendments_created_by'), 'amendments', ['created_by'], unique=False)
    op.create_foreign_key(None, 'amendments', 'users', ['created_by'], ['id'])

    # audit_logs
    op.add_column(
        'audit_logs',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('audit_logs', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_audit_logs_created_by'), 'audit_logs', ['created_by'], unique=False)
    op.create_foreign_key(None, 'audit_logs', 'users', ['created_by'], ['id'])

    # clinical_notes
    op.add_column(
        'clinical_notes',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('clinical_notes', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_clinical_notes_created_by'), 'clinical_notes', ['created_by'], unique=False)
    op.create_foreign_key(None, 'clinical_notes', 'users', ['created_by'], ['id'])

    # idg_meetings
    op.add_column(
        'idg_meetings',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('idg_meetings', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_idg_meetings_created_by'), 'idg_meetings', ['created_by'], unique=False)
    op.create_foreign_key(None, 'idg_meetings', 'users', ['created_by'], ['id'])

    # idg_reviews
    op.add_column(
        'idg_reviews',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('idg_reviews', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_idg_reviews_created_by'), 'idg_reviews', ['created_by'], unique=False)
    op.create_foreign_key(None, 'idg_reviews', 'users', ['created_by'], ['id'])

    # medications
    op.add_column(
        'medications',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('medications', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_medications_created_by'), 'medications', ['created_by'], unique=False)
    op.create_foreign_key(None, 'medications', 'users', ['created_by'], ['id'])

    # patients
    op.add_column(
        'patients',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('patients', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_patients_created_by'), 'patients', ['created_by'], unique=False)
    op.create_foreign_key(None, 'patients', 'users', ['created_by'], ['id'])

    # survey_access
    op.add_column(
        'survey_access',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('survey_access', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_survey_access_created_by'), 'survey_access', ['created_by'], unique=False)
    op.create_foreign_key(None, 'survey_access', 'users', ['created_by'], ['id'])

    # users
    op.add_column(
        'users',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('users', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_users_created_by'), 'users', ['created_by'], unique=False)
    op.create_foreign_key(None, 'users', 'users', ['created_by'], ['id'])

    # visits
    op.add_column(
        'visits',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('visits', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_visits_created_by'), 'visits', ['created_by'], unique=False)
    op.create_foreign_key(None, 'visits', 'users', ['created_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'visits', type_='foreignkey')
    op.drop_index(op.f('ix_visits_created_by'), table_name='visits')
    op.drop_column('visits', 'created_by')
    op.drop_column('visits', 'updated_at')

    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_created_by'), table_name='users')
    op.drop_column('users', 'created_by')
    op.drop_column('users', 'updated_at')

    op.drop_constraint(None, 'survey_access', type_='foreignkey')
    op.drop_index(op.f('ix_survey_access_created_by'), table_name='survey_access')
    op.drop_column('survey_access', 'created_by')
    op.drop_column('survey_access', 'updated_at')

    op.drop_constraint(None, 'patients', type_='foreignkey')
    op.drop_index(op.f('ix_patients_created_by'), table_name='patients')
    op.drop_column('patients', 'created_by')
    op.drop_column('patients', 'updated_at')

    op.drop_constraint(None, 'medications', type_='foreignkey')
    op.drop_index(op.f('ix_medications_created_by'), table_name='medications')
    op.drop_column('medications', 'created_by')
    op.drop_column('medications', 'updated_at')

    op.drop_constraint(None, 'idg_reviews', type_='foreignkey')
    op.drop_index(op.f('ix_idg_reviews_created_by'), table_name='idg_reviews')
    op.drop_column('idg_reviews', 'created_by')
    op.drop_column('idg_reviews', 'updated_at')

    op.drop_constraint(None, 'idg_meetings', type_='foreignkey')
    op.drop_index(op.f('ix_idg_meetings_created_by'), table_name='idg_meetings')
    op.drop_column('idg_meetings', 'created_by')
    op.drop_column('idg_meetings', 'updated_at')

    op.drop_constraint(None, 'clinical_notes', type_='foreignkey')
    op.drop_index(op.f('ix_clinical_notes_created_by'), table_name='clinical_notes')
    op.drop_column('clinical_notes', 'created_by')
    op.drop_column('clinical_notes', 'updated_at')

    op.drop_constraint(None, 'audit_logs', type_='foreignkey')
    op.drop_index(op.f('ix_audit_logs_created_by'), table_name='audit_logs')
    op.drop_column('audit_logs', 'created_by')
    op.drop_column('audit_logs', 'updated_at')

    op.drop_constraint(None, 'amendments', type_='foreignkey')
    op.drop_index(op.f('ix_amendments_created_by'), table_name='amendments')
    op.drop_column('amendments', 'created_by')
    op.drop_column('amendments', 'updated_at')