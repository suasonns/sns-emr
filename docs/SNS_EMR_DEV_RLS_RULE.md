# SNS Hospice EMR — Development RLS Toggle Rule (LOCKED)

**Status:** FINAL • DO NOT REVISIT DURING DEVELOPMENT

This document is the authoritative rule for Row Level Security (RLS) usage in the SNS Hospice EMR.
It exists to prevent loss of development time and to ensure functional correctness before security enforcement.

---

## 1. Non‑Negotiable Development Rule

During active development:

- ❌ Row Level Security (RLS) MUST be OFF
- ❌ Tenant isolation policies MUST be disabled
- ❌ No `set_config(app.tenant_id, ...)` workarounds
- ✅ Focus exclusively on functional correctness, workflow logic, evidence, and compliance behavior

RLS is a **SECURITY PHASE** concern — not a **DEVELOPMENT PHASE** concern.

---

## 2. One‑Time Development Database Setup

Run **once per development database**.

### 2.1 Disable RLS on tenant‑scoped tables

```sql
ALTER TABLE visits   DISABLE ROW LEVEL SECURITY;
ALTER TABLE tasks    DISABLE ROW LEVEL SECURITY;
ALTER TABLE patients DISABLE ROW LEVEL SECURITY;
```

(Extend later if needed: notes, assessments, idg tables, etc.)

---

### 2.2 Drop tenant isolation policies (DEV ONLY)

```sql
DROP POLICY IF EXISTS tenant_isolation_visits   ON visits;
DROP POLICY IF EXISTS tenant_isolation_tasks    ON tasks;
DROP POLICY IF EXISTS tenant_isolation_patients ON patients;
```

This prevents accidental re‑activation or confusion.

---

### 2.3 Disable row security at the session level (belt + suspenders)

```sql
SET row_security = OFF;
```

---

## 3. Verification (REQUIRED)

Confirm RLS is fully disabled:

```sql
SELECT relname, relrowsecurity
FROM pg_class
WHERE relname IN ('visits', 'tasks', 'patients');
```

**Expected result:**

```
visits   | false
tasks    | false
patients | false
```

If any value is `true` → STOP and fix before coding.

---

## 4. Application Code Expectations (DEV MODE)

### 4.1 Tenant Context

In development, tenant context is ORM‑only:

```python
def _set_tenant_context(db_session, user):
    db_session.info["tenant_id"] = user.tenant_id
    db_session.info["user_id"] = user.id
```

❌ No database GUCs
❌ No LOCAL/NON‑LOCAL flags
❌ No RLS‑dependent visibility assumptions

---

## 5. Definition of Development Success

All of the following must be true:

- ✅ Tests pass without tenant context hacks
- ✅ Data persists across commits
- ✅ Tasks do not "disappear" after finalize
- ✅ POC_UPDATE creation works for CRISIS and ROUTINE paths
- ✅ Evidence references are present and auditable

---

## 6. When RLS Comes Back (NOT NOW)

RLS may only be re‑enabled when **ALL** are true:

- ICA, Bereavement, Skin, Safety/Fall, Pain logic complete
- Task engine rules frozen
- Evidence model stable
- IDG discrepancy gating implemented
- QA checklists pass without edge cases

### RLS Re‑enablement Rules

- Separate migration
- Separate test suite
- Separate security validation
- No mixing with feature development

Purpose of RLS when re‑enabled:

- ✅ Tenant data isolation
- ✅ No cross‑tenant leakage
- ✅ No functional data loss

---

## 7. Team Rule (MANDATORY)

> If data appears missing during development:
> 
> - DO NOT touch RLS
> - Verify RLS is OFF
> - Fix the functional logic instead

---

## 8. Status

- ✅ RLS OFF in development
- ✅ Functional correctness validated
- ✅ Security deferred intentionally

SNS EMR STATE:
- RLS OFF (dev mode locked)
- assessments schema implemented
- RN is baseline (not absolute truth)
- truth = IDG interdisciplinary consensus
- discrepancies are expected and tracked (not errors)
- next: ORM models aligned to interdisciplinary model

**This document is LOCKED.**
