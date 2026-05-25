# SNS EMR – FULL BACKEND FILESYSTEM MAP (AUTHORITATIVE)

**Purpose**
This document is the authoritative, complete filesystem map for the SNS EMR backend.
It includes **all folders regardless of whether they are currently empty**, so that
future development restores files into an already-established structure.

This file is documentation-only and does not change runtime behavior.

---

## Repository Root: `SNS EMR/`

```
SNS EMR/
├── .gitignore
├── alembic_revision_ids.txt
├── *.bundle                          # git bundle backups
├── backend/
└── docs/
```

---

## Documentation: `SNS EMR/docs/`

```
docs/
├── Enterprise Ownership + Default Privileges Script.txt
├── README.md
├── SNS_EMR_BACKEND_MAP_COMPLETE.md
└── (other markdown / text references)
```

---

## Backend Root: `SNS EMR/backend/`

```
backend/
├── __pycache__/
├── alembic/
├── app/
├── schemas/
├── services/
├── tenants/
├── tenancy/
├── utils/
├── tests/
├── venv/
├── .env
├── .env.local
├── alembic.ini
├── requirements.txt
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## Alembic: `backend/alembic/`

```
alembic/
├── __pycache__/
├── env.py
├── README
├── script.py.mako
└── versions/
```

### Alembic Versions: `backend/alembic/versions/`

```
versions/
├── <forward-only migration files>.py
```

---

## Application Package: `backend/app/`

```
app/
├── __pycache__/
├── api/
├── compliance/
├── core/
├── db/
├── models/
├── __init__.py
└── main.py
```

---

## API Layer: `backend/app/api/`

```
api/
├── __pycache__/
├── __init__.py
├── auth.py
├── auth_whoami.py
├── patients.py
├── visits.py
├── tasks.py
├── internal_tasks.py
├── internal_training.py
├── internal_superuser.py
├── reports.py
└── registry.py
```

---

## Compliance Engine: `backend/app/compliance/`

```
compliance/
├── __pycache__/
├── achc/
│   ├── __init__.py
│   └── documentation_timeliness.py
├── cdph/
│   ├── __init__.py
│   └── california_specific.py
├── chap/
│   ├── __init__.py
│   └── chap_core.py
├── cms/
│   ├── __init__.py
│   ├── evidence.py
│   └── poc_update.py
├── tjc/
│   ├── __init__.py
│   └── survey_tracers.py
├── registry.py
├── types.py
└── __init__.py
```

---

## Core Infrastructure: `backend/app/core/`

```
core/
├── __pycache__/
├── env.py
├── audit_middleware.py
├── security.py
├── db.py
├── sync_db.py
└── (additional core utilities)
```

---

## Database Layer: `backend/app/db/`

```
db/
├── __pycache__/
├── base.py
├── session.py
├── revision.py
└── init_db.py
```

---

## ORM Models: `backend/app/models/`

```
models/
├── __pycache__/
├── base.py
├── tenant.py
├── patient.py
├── visit.py
├── task.py
├── benefit_period.py
├── eligibility_decision.py
├── idg_*.py
├── document_*.py
└── (additional model files)
```

---

## Schemas: `backend/schemas/` (intentionally present)

```
schemas/
├── __pycache__/
```

---

## Services Layer: `backend/services/`

```
services/
├── __pycache__/
├── admission_guardrail_service.py
├── audit_logger.py
├── benefit_period_service.py
├── chart_service.py
├── dx_primary_policy_service.py
├── eligibility_service.py
├── idg_service.py
├── poc_update_engine.py
├── task_completion.py
├── task_engine.py
├── task_generation_engine.py
├── visit_finalize_service.py
├── visit_service.py
└── (additional service modules)
```

---

## Tenancy Runtime Logic: `backend/tenancy/`

```
tenancy/
├── __pycache__/
├── dependencies.py
└── registry.py
```

---

## Tenant Fixtures / Data: `backend/tenants/`

```
tenants/
├── __pycache__/
├── love_and_faith/
└── test.py
```

---

## Utilities: `backend/utils/`

```
utils/
├── __pycache__/
├── diff_utils.py
├── text_normalization.py
└── test_text_normalization.py
```

---

## Engineering Contract

- This file is the authoritative filesystem map
- All folders listed here are intentional
- Empty folders must not be removed
- Files may be added, but folder structure is preserved
- This document may be used for future restoration
