
# SNS EMR – Backend System Baseline Map

**Purpose**  
This document is the authoritative daily baseline map for the SNS EMR backend.  
It is uploaded to Copilot before development begins to prevent architectural, schema, or compliance drift.

---

## System Status (Baseline)

- **System State:** Stable
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Alembic Current:** `104cd74a907d (head)`
- **Alembic Heads:** `104cd74a907d (head)`
- **Schema Drift:** None detected

---

## Backend Folder Structure

```
SNS EMR/
└── backend/
    ├── alembic/
    │   ├── versions/
    │   ├── env.py
    │   └── README
    │
    ├── apps/
    │   └── tenants/
    │       ├── local_dev/
    │       └── test.py
    │
    ├── utils/
    │   ├── base_utils.py
    │   ├── data_normalization.py
    │   └── test_data_normalization.py
    │
    ├── scripts/
    │   ├── init_db.py
    │   ├── load_mock_data.py
    │   ├── seed_tasks.py
    │   └── setup_db.ps1
    │
    ├── tests/
    │   ├── api/
    │   ├── compliance/
    │   ├── integration/
    │   ├── services/
    │   │   ├── test_admission_guardrails_determination.py
    │   │   └── test_idg_policy.py
    │   ├── conftest.py
    │   ├── test_db.py
    │   ├── test_task_engine.py
    │   ├── test_task_engine_supervisory.py
    │   ├── test_idg_reviews.py
    │   ├── test_poc_updates.py
    │   └── test_visit_transitions.py
    │
    └── docs/
        ├── compliance/
        ├── api-overview.md
        ├── assessment.md
        ├── consent_forms.md
        ├── care_plans.md
        ├── eligibility.md
        ├── enterprise_ownership - Default Privileges.docx
        ├── Read_Me.md
        ├── SNS_HOSPICE_EMR_FLOW.md
        ├── SNS_EMR_FINAL_RISK_MAP.md
        ├── SNS_EMR_SCHEDULING_MAP.md
        └── survey_workflow_map.md
```

---

## Folder Responsibilities & Guardrails

### alembic/
- Owns all database schema changes
- Forward-only migrations
- `current` must always equal `head`
- No manual DB changes

### apps/tenants/
- Tenant isolation logic
- Environment-specific behavior
- No shared global state

### utils/
- Shared helper logic only
- Normalization and validation
- No database writes
- No workflow orchestration

### scripts/
- Developer tooling only
- Local/dev/test usage
- Must never auto-run in production

### tests/
- Compliance evidence
- Regression protection
- Survey-defensible proof of behavior

### docs/
- Human-readable system intent
- Survey walkthroughs
- Risk and workflow maps

---

## Daily Upload Template

```
SNS EMR – Daily System Snapshot

Date:
Alembic Current: 104cd74a907d (head)
Alembic Heads:   104cd74a907d (head)
DB State:        In sync
System Status:   Stable

Changes Today:
- None / (list files changed)

Notes:
- No schema drift
- Core workflows intact
```

---

## Compliance Intent

This structure supports:
- CMS Hospice Conditions of Participation
- ACHC / CHAP / Joint Commission readiness
- Immutable audit trails
- Task-to-evidence traceability
- Survey-defensible workflows

---

**This document must be updated only when structure or schema changes occur.**

---
## 2026-05-28 — Architectural Decisions Update

- Single UI and codebase for all tenants
- Behavioral differences via subscription + tenant config
- Multi-tenant user support with per-tenant roles
- Sensitive HR data masked and tenant-configurable enforcement
- Owner-level platform dashboard confirmed
- Tenant hardening required before clinical workflows
