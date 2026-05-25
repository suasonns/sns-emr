# SNS EMR – Schema-Only Map

This document lists **schema-defining components only**: database schema, ORM models, and Alembic migrations.

---

## Alembic Migrations

```
backend/alembic/
├── env.py
├── script.py.mako
└── versions/
    ├── *.py   # forward-only migrations
```

Purpose:
- Defines authoritative database schema evolution

---

## ORM Models

```
backend/app/models/
├── base.py
├── tenant.py
├── patient.py
├── visit.py
├── task.py
├── benefit_period.py
├── eligibility_decision.py
├── idg_*.py
├── document_*.py
└── *.py
```

Purpose:
- SQLAlchemy metadata
- Foreign key integrity
- Audit fields

---

## Database Access Layer

```
backend/app/db/
├── base.py       # declarative_base()
├── session.py    # SessionLocal
├── revision.py
└── init_db.py
```

Purpose:
- Connects ORM to database
- No business logic

---

## Compliance Schema Extensions

```
backend/app/compliance/
├── cms/
├── achc/
├── chap/
├── cdph/
├── tjc/
├── registry.py
└── types.py
```

Purpose:
- Regulatory schema overlays
- Task and evidence requirements

---

## Engineering Contract

- All schema changes must be forward-only via Alembic
- ORM models must match DB schema
- No runtime logic belongs in schema layers
