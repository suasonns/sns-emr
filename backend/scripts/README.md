\# Scripts Directory



Purpose:

This directory contains utility and operational scripts used for

development, maintenance, onboarding, and compliance support.



Guidelines:

\- Scripts here must NOT modify database schema.

\- All schema changes are managed exclusively via Alembic migrations.

\- Scripts may be used for:

&#x20; - data inspection

&#x20; - reference data loading

&#x20; - administrative tasks

&#x20; - survey or audit support



If a script becomes part of core application behavior,

it should be moved into the main codebase.

## Development login provisioning

`python scripts/seed_login_accounts.py` provisions the DPCS/Administrator,
platform OWNER, and BILLING development identities from environment variables.
The same idempotent service runs during application startup.

Copy `backend/.env.example` to an ignored local environment file and set
generated values for:

- `DEV_TENANT_ID` for the agency DPCS/Administrator and BILLING identities.
- `DEV_PLATFORM_TENANT_ID` for the isolated platform OWNER identity.
- `DEV_DPCS_ADMIN_EMAIL` and `DEV_DPCS_ADMIN_PASSWORD`.
- `DEV_PLATFORM_OWNER_EMAIL` and `DEV_PLATFORM_OWNER_PASSWORD`.
- `DEV_BILLING_EMAIL` and `DEV_BILLING_PASSWORD`.

Passwords must be at least 12 characters. An existing identity's role, tenant,
and active status are reconciled when its email is configured. Its password is
changed only when the matching password variable is present. Public password
reset is disabled; signed-in users change their own password through
`POST /auth/change-password`.


