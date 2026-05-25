# SNS EMR – Runtime vs Structural Folders

This document classifies backend folders by **runtime responsibility** versus **structural / organizational purpose**.

---

## Runtime-Critical Folders (Loaded or Executed at Runtime)

These folders directly affect application behavior when FastAPI is running.

```
backend/app/api/          # FastAPI routers (Swagger surface)
backend/app/core/         # security, audit, env loading, DB facade
backend/app/db/           # SQLAlchemy Base, session, DB access
backend/app/models/       # ORM models (metadata, FK integrity)
backend/app/services/     # business logic, task engines, workflows
backend/app/compliance/   # compliance logic invoked by services
backend/app/tenancy/      # tenant resolution and guards
backend/alembic/          # migrations when alembic is executed
```

Impact:
- Changes here affect runtime behavior
- Must be validated with app startup and API tests

---

## Structural / Organizational Folders (Not Executed Directly)

These folders provide organization, documentation, or future scaffolding.

```
backend/schemas/          # placeholder for request/response schemas
backend/utils/            # helper utilities
backend/tests/            # test suite
backend/tenants/          # fixtures / seed data
backend/venv/             # local virtual environment
backend/__pycache__/      # runtime cache
backend/app/__pycache__/  # runtime cache
```

Impact:
- Safe to evolve independently
- Do not affect production runtime directly

---

## Documentation & Governance

```
docs/                     # architecture, runbooks, maps
*.bundle                  # git backups
alembic_revision_ids.txt  # reference artifact
```

---

## Engineering Rule

- Runtime folders require review, tests, and migrations
- Structural folders should never be deleted once established
