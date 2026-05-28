# SNS EMR — Model ↔ DB Discrepancy Report (Tasks & Visits)

**Purpose:** Provide a complete, survey-defensible discrepancy inventory between **PostgreSQL schema** and **SQLAlchemy models** for `tasks` and `visits`, plus a forward-only remediation plan and verification checklist.

**Scope:**
- DB tables: `public.tasks`, `public.visits`
- ORM models: `app.models.task.Task`, `app.models.visit.Visit`
- Integrity focus: columns, types (at a high level), foreign keys, and compliance-critical evidence fields.

**Generated:** 2026-05-27 22:27:33Z

---

## 0) What this means (Executive Summary)

- ✅ **Database is healthy**: tables exist, columns present, FK constraints exist, Alembic `current == head`.
- ⚠️ **ORM is under-declared**: `Task` model is missing explicit `ForeignKey()` declarations for most FK columns (Python introspection shows only `users.id`).
- ⚠️ **Column mismatches exist**: DB contains some columns that are not currently declared in the `Task` model (e.g., assignment/execution/visit linkage fields observed in DB output). `Visit` has potential naming alignment issues for supervisory flag (DB appears as `supervisory`, model exposes `is_supervisory`).

**Conclusion:** Continue development **without establishing a new baseline**. Fixes are **model-only** unless a DB column is genuinely missing; then add a **new forward-only Alembic migration**.

---

## 1) Guardrails (Non‑Negotiable)

1. **Tool separation**: SQL runs in pgAdmin/psql only; Python runs in a Python shell/venv only. Do not paste Python into SQL editors.
2. **Verify-first**: Always confirm Alembic and DB state before changes.
3. **Forward-only schema**: Never rewrite migration history; create repair migrations as needed.
4. **Compliance evidence**: Task completion must record `completed_at`, `completion_reference_type`, and `completion_reference_id`.
5. **Dev RLS rule**: RLS must remain OFF during active development; re-enable only in a separate security phase.

References: SNS EMR stability baseline and schema contracts emphasize forward-only migrations and runtime-vs-structural separation. citeturn21search2turn21search8turn21search7turn21search9

---

## 2) Environment & Evidence Captured

### 2.1 Alembic state
- `alembic current` == `alembic heads` == `533c2ae752e8 (head)` (confirmed in terminal)

### 2.2 DB checkpoint status
- A verified custom-format dump exists (stored under `db_checkpoints/`) with SHA256 integrity hash and TOC listing (confirmed earlier in terminal). The dump header indicates the server is PostgreSQL 13.23 while `pg_dump` is 16.13 (supported and acceptable).

### 2.3 DB validation (pgAdmin)
- `public.tasks` and `public.visits` exist.
- Column listings for both tables were retrieved via `information_schema.columns`.
- FK listing for both tables was retrieved via `information_schema.table_constraints` joins.

### 2.4 ORM introspection (Python)

**Task model columns (as printed):**
```text
['id', 'tenant_id', 'patient_id', 'benefit_period_id', 'task_type', 'origin', 'discipline',
 'regulatory_basis', 'status', 'due_date', 'completed_at', 'completion_reference_type',
 'completion_reference_id', 'alert_reason', 'created_at', 'updated_at', 'created_by']
```

**Visit model columns (as printed):**
```text
['tenant_id', 'patient_id', 'provider_id', 'visit_type', 'visit_discipline', 'visit_datetime', 'status',
 'acuity_state_at_visit', 'is_supervisory', 'finalized_at', 'finalized_by',
 'finalized_role_id', 'finalized_interface_id', 'id', 'created_at', 'updated_at', 'created_by']
```

**Task foreign keys (as printed):**
```text
{ForeignKey('users.id')}
```

**Visit foreign keys (as printed):**
```text
{ForeignKey('users.id'), ForeignKey('interfaces.id'), ForeignKey('tenants.id'),
 ForeignKey('roles.id'), ForeignKey('patients.id'), ...}
```

---

## 3) Discrepancy Matrix (DB ↔ Model)

> **Legend**
- ✅ = aligned
- ⚠️ = mismatch or uncertain (requires one more confirm query)
- ❌ = confirmed mismatch

### 3.1 `tasks` table/model discrepancies

#### A) Foreign key declarations (Confirmed)

| Item | DB | Model | Status | Impact |
|---|---|---|---|---|
| `tenant_id → tenants.id` | FK exists / expected | column exists but FK not detected | ❌ | tenant scoping/join integrity risk |
| `patient_id → patients.id` | FK exists | column exists but FK not detected | ❌ | patient joins, integrity risk |
| `benefit_period_id → benefit_periods.id` | FK exists | column exists but FK not detected | ❌ | benefit-period attribution risk |
| `visit_id → visits.id` | observed in DB checks | column missing in model | ❌ | visit→task evidence linkage risk |
| `assigned_user_id → users.id` | observed in DB checks | column missing in model | ❌ | task assignment features break |
| `executed_by → users.id` | observed in DB checks | column missing in model | ❌ | audit trail and completion actor missing |
| `created_by → users.id` | FK exists | column exists; FK detected (only one) | ⚠️ | confirm FK is bound to created_by |

#### B) Column presence mismatches (Observed)

| Column | DB observed | Model column list | Status | Notes |
|---|---:|---:|---|---|
| `name` | yes | no | ❌ | task display/labeling field |
| `assigned_user_id` | yes | no | ❌ | assignment workflow |
| `visit_id` | yes | no | ❌ | visit anchor |
| `executed_by` | yes | no | ❌ | audit execution actor |
| `executed_reason` | yes | no | ❌ | audit reason |
| `executed_source` | yes | no | ❌ | audit source |
| `completion_reference_type` | yes | yes | ✅ | compliance evidence |
| `completion_reference_id` | yes | yes | ✅ | compliance evidence |
| `completed_at` | yes | yes | ✅ | compliance evidence |

**Compliance note:** Task completion evidence fields are present in both DB and model (`completed_at`, `completion_reference_type`, `completion_reference_id`). This is required for audit-proof task completion. citeturn21search3turn21search9

---

### 3.2 `visits` table/model discrepancies

#### A) Supervisory flag naming (Likely)

| Item | DB | Model | Status | Impact |
|---|---|---|---|---|
| supervisory flag | `supervisory` (boolean) observed in DB | `is_supervisory` attribute | ⚠️ | supervisory RN visit anchors ROUTINE POC_UPDATE policy |

**Fix pattern:** map attribute to DB column explicitly:
```python
is_supervisory = Column('supervisory', Boolean, nullable=False, default=False)
```

#### B) Signing fields (Uncertain)

DB screenshots suggested possible `signed_at`/`signed_by` usage but at least one query indicated `signed_at` may not exist in the active DB. Resolve with a definitive `information_schema.columns` query before changing models.

#### C) Foreign keys (Partially aligned)

- Visit model FK set includes `patients.id`, `tenants.id`, `users.id`, `roles.id`, `interfaces.id`.
- Ensure FK bindings are attached to the correct columns (e.g., `created_by`, `finalized_by`, `patient_id`, `tenant_id`).

---

## 4) Root Cause Analysis (Why this happened)

- DB schema evolved via forward migrations and repair migrations.
- ORM models were updated for column names but **not consistently updated with explicit `ForeignKey()` definitions**.
- SQLAlchemy will not infer FKs unless declared (or unless reflection is used). Under-declared FKs lead to incomplete ORM metadata, which breaks joins and relationship definitions.

This is normal during rapid schema iteration and is fixable with a model-only alignment pass.

---

## 5) Remediation Plan (Forward‑Only, Minimal Risk)

### 5.1 Step 1 — Capture authoritative DB column lists (repeatable)

Run in **pgAdmin / psql** (SQL only):

**Tasks columns:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name='tasks'
ORDER BY ordinal_position;
```

**Visits columns:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name='visits'
ORDER BY ordinal_position;
```

**FK constraints:**
```sql
SELECT
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS referenced_table,
  ccu.column_name AS referenced_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('tasks','visits')
ORDER BY tc.table_name, kcu.column_name;
```

### 5.2 Step 2 — Align the SQLAlchemy models (model-only)

#### Task model (`app/models/task.py`)

- Add missing columns that exist in DB (`name`, `assigned_user_id`, `visit_id`, `executed_by`, `executed_reason`, `executed_source`) **only if confirmed by Step 5.1**.
- Add explicit FK declarations:
  - `tenant_id → tenants.id`
  - `patient_id → patients.id`
  - `benefit_period_id → benefit_periods.id`
  - `visit_id → visits.id` (if exists)
  - `assigned_user_id → users.id` (if exists)
  - `created_by → users.id`
  - `executed_by → users.id` (if exists)

#### Visit model (`app/models/visit.py`)

- Ensure FK declarations are explicit for:
  - `tenant_id → tenants.id`
  - `patient_id → patients.id`
  - `created_by → users.id`
  - `finalized_by → users.id`
  - `provider_id → users.id` (if that is intended)
- Resolve supervisory naming by mapping `is_supervisory` to DB column `supervisory` if DB uses that name.

### 5.3 Step 3 — Verify ORM metadata matches DB (Python)

Run in a **Python shell** (not pgAdmin):

```python
from app.models.task import Task
from app.models.visit import Visit

print([c.name for c in Task.__table__.columns])
print(Task.__table__.foreign_keys)

print([c.name for c in Visit.__table__.columns])
print(Visit.__table__.foreign_keys)
```

**Expected after fix:**
- `Task.__table__.foreign_keys` lists tenants/patients/benefit_periods/(visits)/users.

### 5.4 Step 4 — Verify key joins (Python or SQL)

**SQL spot-check (safe, read-only):**
```sql
SELECT t.id, t.status, t.completed_at, t.completion_reference_type, t.completion_reference_id,
       v.id AS visit_id
FROM tasks t
LEFT JOIN visits v ON v.id = t.visit_id
LIMIT 5;
```

### 5.5 Step 5 — Commit strategy (clean history)

- Commit **model alignment** separately from business logic.
- Do not modify old migrations.
- If DB changes are needed, create a **new** Alembic revision.

---

## 6) Work Items (Tonight/Tomorrow Checklist)

### Must-do
- [ ] Run Step 5.1 DB column + FK queries and save results.
- [ ] Update `Task` model with missing FK declarations.
- [ ] Add missing `Task` columns only if confirmed in DB.
- [ ] Map supervisory flag correctly in `Visit` model.
- [ ] Re-run Python verification for columns and FKs.

### Should-do
- [ ] Add/repair SQLAlchemy `relationship()` declarations for `Task.patient`, `Task.visit`, `Task.assigned_user`, etc., once FK metadata is correct.
- [ ] Add a unit test asserting FK presence in ORM metadata for `tasks` and `visits`.

### Nice-to-have (stability)
- [ ] Add `.gitattributes` to normalize line endings (reduce CRLF warnings).

---

## 7) Risk & Compliance Notes

- Missing FK declarations in ORM is a **latent integrity risk**: it can cause incorrect joins, broken relationship loading, and hard-to-debug compliance workflow failures.
- Task completion evidence fields are already present in both DB and model — keep them non-negotiable.
- Development RLS must remain OFF to avoid confusing functional issues with security policies. citeturn21search9

---

## Appendix A — Reference Architecture Contracts

- **Stability baseline**: “All future work must be additive.” citeturn21search2
- **Schema-only map**: Alembic + models are authoritative for schema evolution; forward-only migrations. citeturn21search8
- **Runtime vs structural**: runtime folders require validation; docs are structural. citeturn21search7
- **Dev RLS rule**: RLS OFF during development; re-enable only as a dedicated security phase. citeturn21search9

---

## Appendix B — Compliance Evidence Model (Tasks)

A task is only audit-proof when completion includes:
- `status = COMPLETED`
- `completed_at` timestamp
- `completion_reference_type`
- `completion_reference_id`

This evidence linkage is also described in the ICA/evidence model planning docs. citeturn21search3turn21search9
