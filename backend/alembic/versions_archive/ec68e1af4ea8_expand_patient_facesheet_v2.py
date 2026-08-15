"""expand patient facesheet v2

Revision ID: ec68e1af4ea8
Revises: 9c4f2a7b6e31
Create Date: 2026-07-07 18:43:15.674321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ec68e1af4ea8'
down_revision: Union[str, Sequence[str], None] = '9c4f2a7b6e31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('patient_facesheet', sa.Column('primary_payer', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('primary_policy_number', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('secondary_policy_number', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('requires_prior_authorization', sa.Boolean(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('authorization_required_for', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('authorization_number', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('authorization_status', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('authorization_start_date', sa.Date(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('authorization_end_date', sa.Date(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('current_level_of_care', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('loc_effective_date', sa.Date(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('has_allergies', sa.Boolean(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('current_pos_type', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('current_pos_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('current_pos_address', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('room_number', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('pos_start_date', sa.Date(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('pos_end_date', sa.Date(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('responsible_party_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('responsible_party_relationship', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('responsible_party_phone', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('emergency_contact_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('emergency_contact_relationship', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('emergency_contact_phone', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('attending_physician_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('attending_physician_npi', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('attending_physician_following', sa.Boolean(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('medical_director_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('medical_director_npi', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('medical_director_designee_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('medical_director_designee_npi', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('associate_medical_director_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('associate_medical_director_npi', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('pharmacy_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('pharmacy_phone', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('pharmacy_fax', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('dme_vendor_name', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('dme_vendor_phone', sa.String(), nullable=True))
    op.add_column('patient_facesheet', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.alter_column('patient_facesheet', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.execute("""
            ALTER TABLE patient_facesheet
            ALTER COLUMN created_by
            TYPE UUID
            USING created_by::uuid
            """)
    op.alter_column('patient_facesheet', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.execute("""
            ALTER TABLE patient_facesheet
            ALTER COLUMN updated_by
            TYPE UUID
            USING updated_by::uuid\
            """)
    op.create_index('ix_patient_facesheet_patient_id', 'patient_facesheet', ['patient_id'], unique=False)
    op.create_foreign_key(op.f('fk_patient_facesheet_updated_by_users'), 'patient_facesheet', 'users', ['updated_by'], ['id'])
    op.create_foreign_key(op.f('fk_patient_facesheet_patient_id_patients'), 'patient_facesheet', 'patients', ['patient_id'], ['id'])
    op.create_foreign_key(op.f('fk_patient_facesheet_created_by_users'), 'patient_facesheet', 'users', ['created_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint(op.f('fk_patient_facesheet_created_by_users'), 'patient_facesheet', type_='foreignkey')
    op.drop_constraint(op.f('fk_patient_facesheet_patient_id_patients'), 'patient_facesheet', type_='foreignkey')
    op.drop_constraint(op.f('fk_patient_facesheet_updated_by_users'), 'patient_facesheet', type_='foreignkey')
    op.drop_index('ix_patient_facesheet_patient_id', table_name='patient_facesheet')
    op.alter_column('patient_facesheet', 'updated_by',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    op.alter_column('patient_facesheet', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.alter_column('patient_facesheet', 'created_by',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('patient_facesheet', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.drop_column('patient_facesheet', 'deleted_at')
    op.drop_column('patient_facesheet', 'dme_vendor_phone')
    op.drop_column('patient_facesheet', 'dme_vendor_name')
    op.drop_column('patient_facesheet', 'pharmacy_fax')
    op.drop_column('patient_facesheet', 'pharmacy_phone')
    op.drop_column('patient_facesheet', 'pharmacy_name')
    op.drop_column('patient_facesheet', 'associate_medical_director_npi')
    op.drop_column('patient_facesheet', 'associate_medical_director_name')
    op.drop_column('patient_facesheet', 'medical_director_designee_npi')
    op.drop_column('patient_facesheet', 'medical_director_designee_name')
    op.drop_column('patient_facesheet', 'medical_director_npi')
    op.drop_column('patient_facesheet', 'medical_director_name')
    op.drop_column('patient_facesheet', 'attending_physician_following')
    op.drop_column('patient_facesheet', 'attending_physician_npi')
    op.drop_column('patient_facesheet', 'attending_physician_name')
    op.drop_column('patient_facesheet', 'emergency_contact_phone')
    op.drop_column('patient_facesheet', 'emergency_contact_relationship')
    op.drop_column('patient_facesheet', 'emergency_contact_name')
    op.drop_column('patient_facesheet', 'responsible_party_phone')
    op.drop_column('patient_facesheet', 'responsible_party_relationship')
    op.drop_column('patient_facesheet', 'responsible_party_name')
    op.drop_column('patient_facesheet', 'pos_end_date')
    op.drop_column('patient_facesheet', 'pos_start_date')
    op.drop_column('patient_facesheet', 'room_number')
    op.drop_column('patient_facesheet', 'current_pos_address')
    op.drop_column('patient_facesheet', 'current_pos_name')
    op.drop_column('patient_facesheet', 'current_pos_type')
    op.drop_column('patient_facesheet', 'has_allergies')
    op.drop_column('patient_facesheet', 'loc_effective_date')
    op.drop_column('patient_facesheet', 'current_level_of_care')
    op.drop_column('patient_facesheet', 'authorization_end_date')
    op.drop_column('patient_facesheet', 'authorization_start_date')
    op.drop_column('patient_facesheet', 'authorization_status')
    op.drop_column('patient_facesheet', 'authorization_number')
    op.drop_column('patient_facesheet', 'authorization_required_for')
    op.drop_column('patient_facesheet', 'requires_prior_authorization')
    op.drop_column('patient_facesheet', 'secondary_policy_number')
    op.drop_column('patient_facesheet', 'primary_policy_number')
    op.drop_column('patient_facesheet', 'primary_payer')
    