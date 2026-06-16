
# SNS Hospice EMR — Tenant Hardening Execution Plan

## Objective
Guarantee that each tenant operates in an isolated, survey-defensible data boundary.

## Checklist

### Database
- All core tables contain tenant_id NOT NULL
- No rows with tenant_id IS NULL

### API
- All queries scoped by tenant_id
- Cross-tenant access returns 403/404

### Verification Queries
```sql
SELECT COUNT(*) FROM patients WHERE tenant_id IS NULL;
SELECT COUNT(*) FROM users WHERE tenant_id IS NULL;
```

## Post-Hardening
- Patient creation allowed
- Patient deletion allowed
- Parallel testing safe

## Rule
Tenant hardening must be completed before compliance or clinical enforcement.
