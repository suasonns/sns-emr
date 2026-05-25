# SNS Hospice EMR – Backend Filesystem Map (Complete Scaffold)
**Status: Minimum Production‑Stable Baseline**

This document is the authoritative filesystem and architecture map for the
SNS Hospice EMR backend. It includes **all folders**, even when empty, so future
work can restore files without changing structure.

---

## Project Root

```
backend/
├── app/
│   ├── api/
│   ├── auth/                # compatibility shim (may be empty initially)
│   ├── compliance/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── tenancy/
│   ├── __init__.py
│   └── main.py
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── docs/
├── venv/
├── .env
├── .env.local
├── alembic.ini
└── requirements.txt
```

---

## API Layer (Swagger Visibility)

```
app/api/
├── __init__.py          # canonical tenant-scoped router
├── auth.py
├── auth_whoami.py
├── patients.py
├── visits.py
├── tasks.py
├── internal_tasks.py
├── internal_superuser.py
├── internal_training.py
├── reports.py
├── registry.py
└── __pycache__/         # runtime
```

---

## ORM / Models (SQLAlchemy)

```
app/models/
├── __init__.py          # RESTORE MODE registry (FK-safe)
├── base.py              # BaseModel + audit fields
├── tenant.py
├── patient.py
├── visit.py
├── task.py
├── benefit_period.py
├── eligibility_decision.py
├── idg/                 # IDG domain (folder may be empty initially)
├── documents/           # document domain (folder may be empty initially)
└── __pycache__/
```

---

## Database Layer (NON-NEGOTIABLE)

```
app/db/
├── base.py              # declarative_base() SINGLE SOURCE
├── session.py           # engine + SessionLocal
├── init_db.py
├── revision.py
└── __pycache__/
```

---

## Core Infrastructure

```
app/core/
├── env.py               # dotenv loader
├── audit_middleware.py
├── security.py
├── db.py                # facade (Base, get_db)
├── permissions.py
├── tenancy_guard.py
└── __pycache__/
```

---

## Services (Business Logic)

```
app/services/
├── task_engine.py
├── task_completion.py
├── poc_update_engine.py
├── visit_finalize.py
├── eligibility_engine.py
├── reporting/           # future services
└── __pycache__/
```

---

## Tenancy

```
app/tenancy/
├── dependencies.py      # require_valid_tenant
├── guards.py
└── __pycache__/
```

---

## Compliance (Read-Only Runtime)

```
app/compliance/
├── cms/
├── chap/
├── cdph/
├── achc/
├── types.py
├── registry.py
└── __pycache__/
```

---

## Verified System State

- App boots cleanly
- Swagger loads
- GET /patients → 200
- POST /patients → 201 / 409
- ORM metadata: ['eligibility_decisions', 'patients', 'tenants']
- FK integrity restored

---

## Engineering Contract

- This file is authoritative
- Folder structure is immutable
- Files may be added but folders are not removed
- No downgrade to "minimum running"
- All changes are forward-only
