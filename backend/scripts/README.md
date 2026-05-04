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



