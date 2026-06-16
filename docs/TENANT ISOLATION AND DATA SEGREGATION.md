SNS HOSPICE EMR
TENANT ISOLATION AND DATA SEGREGATION
CMS CoPs + ACHC (Deemed) Evidence Checklist

Document ID: SNS-EMR-CMS-ACHC-TENANT-ISOLATION
Version: 1.0
Scope: Multi-tenant isolation evidence for PHI-bearing tables and tenant-scoped access behavior.
Environment: Development (Row Level Security intentionally OFF per development rule); tenant isolation enforced at application/query layer.

1. PURPOSE
   Provide survey-defensible evidence that each tenant operates in an isolated boundary and that PHI records are safeguarded from unauthorized access or commingling.

2. REGULATORY / ACCREDITATION REFERENCES
   2.1 CMS Hospice CoPs (42 CFR Part 418)
       - 42 CFR 418.104: Condition of participation: Clinical records
         Key standards used for this evidence:
         (a) Content; (b) Authentication; (c) Protection of information; (d) Retention
       - Surveyor guidance reference: CMS State Operations Manual (SOM) Appendix M (Hospice Interpretive Guidelines)

   2.2 ACHC (Deemed Status Context)
       - ACHC is a CMS-approved accrediting organization for hospices (deemed status).
       - ACHC standards must meet or exceed Medicare CoPs; survey evidence therefore maps primarily to the CoPs above.
       - NOTE: ACHC detailed standard text is proprietary; do not reproduce the standards verbatim in public documents.
         Instead, cite the current ACHC Hospice Accreditation Standards manual section used by your organization (e.g., "Information Management / Record Security").

3. CONTROL SET A: STRUCTURAL TENANT OWNERSHIP (DATABASE SCHEMA EVIDENCE)

   CONTROL A1: Tenant identifier column exists on tenant-scoped tables
   Evidence type: information_schema inspection (read-only)
   SQL (pgAdmin/psql):
     SELECT
       table_name,
       column_name,
       is_nullable,
       data_type
     FROM information_schema.columns
     WHERE table_schema = 'public'
       AND column_name = 'tenant_id'
     ORDER BY table_name;

   Acceptance criteria:
     - All PHI-bearing core tables include tenant_id.
     - For core clinical tables, tenant_id is NOT NULL (is_nullable = 'NO') where enforced by design.

   Evidence capture:
     - Screenshot: A1_tenant_id_columns.png
     - Export: Query result (CSV or screenshot)

   CONTROL A2: No rows exist with tenant_id IS NULL (backfill complete)
   Evidence type: null-check counts (read-only)
   SQL (pgAdmin/psql):
     SELECT COUNT(*) AS null_tenant_patients FROM patients WHERE tenant_id IS NULL;
     SELECT COUNT(*) AS null_tenant_visits   FROM visits   WHERE tenant_id IS NULL;
     SELECT COUNT(*) AS null_tenant_tasks    FROM tasks    WHERE tenant_id IS NULL;

   Acceptance criteria:
     - All three counts must equal 0.

   Evidence capture:
     - Screenshots: A2_patients_null_tenant.png, A2_visits_null_tenant.png, A2_tasks_null_tenant.png

   CONTROL A3: tenant_id referential integrity enforced via foreign keys
   Evidence type: constraint inspection (read-only)
   SQL (pgAdmin/psql):
     SELECT
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
       AND kcu.column_name = 'tenant_id'
     ORDER BY tc.table_name;

   Acceptance criteria:
     - For tenant-scoped transactional tables, tenant_id references tenants.id.

   Evidence capture:
     - Screenshot: A3_tenant_fk_constraints.png

4. CONTROL SET B: LOGICAL ISOLATION (NO CROSS-TENANT COMMINGLING)

   CONTROL B1: Each table has a single authoritative primary key and is tenant-scoped
   Evidence type: schema review + design statement
   Method:
     - Confirm patient primary key is patients.id (UUID) and the table includes tenant_id.
     - Confirm visit primary key is visits.id (UUID) and visit rows reference patients.id via FK.
   Acceptance criteria:
     - Records are uniquely keyed; cross-tenant reuse of the same row is structurally prevented.

   Evidence capture:
     - Screenshot or export: table definition / constraints (optional)
     - Narrative statement (1 paragraph) in binder describing uniqueness and FK enforcement

5. CONTROL SET C: DEVELOPMENT SECURITY POSTURE (RLS OFF BY DESIGN)

   CONTROL C1: Row Level Security disabled during active development
   Evidence type: pg_class inspection (read-only)
   SQL (pgAdmin/psql):
     SELECT relname, relrowsecurity
     FROM pg_class
     WHERE relname IN ('patients', 'visits', 'tasks');

   Acceptance criteria:
     - relrowsecurity = false for all listed tables in development environments.

   Evidence capture:
     - Screenshot: C1_rls_disabled.png

6. API / APPLICATION BEHAVIOR (SURVEY NARRATIVE EVIDENCE)
   NOTE: This evidence is typically demonstrated via API tests and logs, not only SQL.

   CONTROL D1: Tenant-scoped queries (no cross-tenant access)
   Evidence type: automated tests and/or controlled API calls
   Expected behavior:
     - All record queries are scoped by tenant_id at query time.
     - Cross-tenant access attempts return 404 (no existence leak) or 403 per policy.
   Evidence capture:
     - Test output excerpts + CI logs demonstrating 404/403 behavior
     - API screenshots (optional)

7. PASS/FAIL SUMMARY (FOR SURVEYOR)
   - A1 PASS if tenant_id exists on core PHI tables and nullability matches design.
   - A2 PASS if all null-tenant counts are 0.
   - A3 PASS if tenant_id FKs exist for tenant-scoped transactional tables.
   - B1 PASS if PK + FK structure prevents commingling.
   - C1 PASS if RLS is OFF in development (per SDLC rule).
   - D1 PASS if automated tests show no cross-tenant access (404/403).

8. ATTACHMENTS LIST
   - A1_tenant_id_columns.png
   - A2_patients_null_tenant.png
   - A2_visits_null_tenant.png
   - A2_tasks_null_tenant.png
   - A3_tenant_fk_constraints.png
   - C1_rls_disabled.png
   - (Optional) CI logs: tenant_scope_tests.txt
   - (Optional) API capture: cross_tenant_access_negative_tests.pdf