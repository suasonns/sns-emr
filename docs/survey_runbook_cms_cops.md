# SNS Hospice EMR — CMS CoPs Survey Runbook (Evidence Pack)

**Purpose:** Provide survey-defensible evidence for multi-tenant isolation, authorization, clinical record integrity, and auditability.

**Default Tenant ID (dev):** `0dac0f4a-9ce2-470d-8c1d-1c4e210b560d`

---

## A. Multi‑Tenant Isolation (HIPAA / CMS expectation)

### Control
- All PHI tables include `tenant_id` (NOT NULL)
- API queries scope by `tenant_id`
- Cross-tenant requests return **404** (no existence leak)

### Evidence (SQL)
```sql
SELECT table_name
FROM information_schema.columns
WHERE column_name = 'tenant_id'
  AND table_schema = 'public'
ORDER BY table_name