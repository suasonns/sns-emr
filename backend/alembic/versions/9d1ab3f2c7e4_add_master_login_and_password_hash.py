"""add master login and password hash

Revision ID: 9d1ab3f2c7e4
Revises: d2c9c7b5e4a1
Create Date: 2026-08-13 20:00:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "9d1ab3f2c7e4"
down_revision = "d2c9c7b5e4a1"
branch_labels = None
depends_on = None


MASTER_TENANT_ID = "01271980-0000-0000-0000-000005101977"
MASTER_USER_ID = "3a0f7c1e-2f49-45d0-bfd0-8d6d7b9f4f1a"
MASTER_PASSWORD_HASH = "$pbkdf2-sha256$29000$b22NkRKitJYyhvC.977Xeg$lRfLPYfQh3rFI9DcVYn.Pq2A73b./PeDjeOYe41d1yA"


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.users
        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
        """
    )

    op.execute(
        """
        ALTER TABLE public.users
        ALTER COLUMN password_hash SET NOT NULL
        """
    )

    op.execute(
        f"""
        INSERT INTO core.tenants (
            id,
            tenant_code,
            display_name,
            schema_name,
            status,
            created_at,
            activated_at,
            billing_organization_id
        )
        SELECT
            '{MASTER_TENANT_ID}'::uuid,
            'SUNRISE_MASTER',
            'Sunrise Hospice Care',
            'public',
            'ACTIVE',
            NOW(),
            NOW(),
            '00000000-0000-0000-0000-632455464000'::uuid
        WHERE NOT EXISTS (
            SELECT 1 FROM core.tenants WHERE id = '{MASTER_TENANT_ID}'::uuid
        )
        """
    )

    op.execute(
        f"""
        INSERT INTO public.users (
            id,
            tenant_id,
            email,
            password_hash,
            full_name,
            role,
            active,
            access_level,
            created_at,
            updated_at
        )
        SELECT
            '{MASTER_USER_ID}'::uuid,
            '{MASTER_TENANT_ID}'::uuid,
            'romel.suason@suasonns.org',
            '{MASTER_PASSWORD_HASH}',
            'Romel Suason',
            'ADMINISTRATOR',
            TRUE,
            'ROLE_BASED',
            NOW(),
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM public.users WHERE tenant_id = '{MASTER_TENANT_ID}'::uuid AND email = 'romel.suason@suasonns.org'
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM public.users
        WHERE email = 'romel.suason@suasonns.org'
          AND tenant_id = '01271980-0000-0000-0000-000005101977'::uuid
        """
    )

    op.execute(
        """
        DELETE FROM core.tenants
        WHERE id = '01271980-0000-0000-0000-000005101977'::uuid
        """
    )

    op.execute(
        """
        ALTER TABLE public.users
        DROP COLUMN IF EXISTS password_hash
        """
    )
