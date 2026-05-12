# SNS EMR Field Pilot Runbook (Multi‑Tenant)

**Generated:** 2026-05-08T02:32:26Z

## Pilot Scope
- Pilot may run one agency at a time.
- Each pilot agency has a unique X‑System‑Key.

## Mandatory Checks
### Tenant Isolation
✅ Verify all endpoints scope by agency_id.
✅ Attempt cross‑agency access → MUST FAIL (401/403).

### Task Engine
✅ Create/seed IDG tasks per tenant.
✅ Overdue job runs without crashing app.

### Diagnosis Governance
✅ Attempt to save Primary Dx starting with F/R/V/W/X/Y/Z → MUST FAIL (422).

### Announcements
✅ Platform announcements visible to all tenants.
✅ Tenant announcements visible only to tenant staff.
✅ Announcements do not create tasks or alerts.

## Exit Criteria
✅ No agency can see another agency’s patients.
✅ Tasks and reports are tenant‑isolated.
✅ Governance controls enforced.
