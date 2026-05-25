## ✅ SNS EMR Stability Baseline v1

This system has been verified stable with:

- FastAPI started via `uvicorn app.main:api`
- Alembic: current == heads
- Dev-login uses deterministic UUID + tenant-scoped email
- Tenant rule toggles enforced correctly
  - Tenant A: DX + CHF + COPD → WARN_ONLY
  - Tenant B: DX + CHF → WARN_ONLY
- No cross-tenant leakage
- No enforcement side effects

This is a locked baseline.
All future work must be additive.