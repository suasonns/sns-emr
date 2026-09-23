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
---
## 2026-05-28 — Architectural Decisions Update

- Single UI and codebase for all tenants
- Behavioral differences via subscription + tenant config
- Multi-tenant user support with per-tenant roles
- Sensitive HR data masked and tenant-configurable enforcement
- Owner-level platform dashboard confirmed
- Tenant hardening required before clinical workflows

---

## Documentation Index

This section links the current active decision/architecture/tracking documents. Historical and
superseded documents are listed separately below and are retained for traceability only — do not
treat them as current.

### Active

- [`ACCESS_CONTROL_MODEL.md`](./ACCESS_CONTROL_MODEL.md) — master, authoritative access-control design reference (OWNER = Model A: no automatic tenant/patient-data access)
- [`phase2/SUPERADMIN_OWNER_MODEL_DECISION.md`](./phase2/SUPERADMIN_OWNER_MODEL_DECISION.md) — current SUPERADMIN/OWNER product decision (ACTIVE PRODUCT DECISION)
- [`PHASE2_EXECUTION_PACKAGE.md`](./PHASE2_EXECUTION_PACKAGE.md) — current Phase 2 execution package
- [`PHASE2_TERMINOLOGY_DECISION.md`](./PHASE2_TERMINOLOGY_DECISION.md) — ratified terminology decision (`ACP` = Advance Care Planning; not "Access Control Policy")
- [`FIELD_TESTING_BLOCKER_REGISTER.md`](./FIELD_TESTING_BLOCKER_REGISTER.md) — current field-testing blocker register
- [`architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`](./architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md) — platform/tenant hierarchy (OWNER does not operate hospice agencies)
- [`tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md`](./tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md) — active RNICA redesign source-of-truth (design input only; code/schema/migrations blocked under this doc)
- [`tenant-platform/SNS_CONSTITUTION.md`](./tenant-platform/SNS_CONSTITUTION.md) — standing engineering authority document governing RNICA/HOPE/SFV/Finalization/Compliance work
- [`tenant-platform/RNICA_PHASE3_REMEDIATION_REGISTER.md`](./tenant-platform/RNICA_PHASE3_REMEDIATION_REGISTER.md) — master defect register for RNICA Phase 3 remediation (AUDIT BASELINE / REMEDIATION REQUIRED — defects open, not compliant)
- [`tenant-platform/RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md`](./tenant-platform/RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md), [`tenant-platform/HOPE_FIELD_TRACE_MATRIX.md`](./tenant-platform/HOPE_FIELD_TRACE_MATRIX.md), [`tenant-platform/SFV_LIFECYCLE_TRACE_MATRIX.md`](./tenant-platform/SFV_LIFECYCLE_TRACE_MATRIX.md), [`tenant-platform/ITEM_CODE_CONFLICT_MATRIX.md`](./tenant-platform/ITEM_CODE_CONFLICT_MATRIX.md), [`tenant-platform/DEAD_EXPORT_PATH_ANALYSIS.md`](./tenant-platform/DEAD_EXPORT_PATH_ANALYSIS.md), [`tenant-platform/LOCK_GATE_DEPENDENCY_TRACE.md`](./tenant-platform/LOCK_GATE_DEPENDENCY_TRACE.md), [`tenant-platform/MISSING_FIELD_RECONCILIATION.md`](./tenant-platform/MISSING_FIELD_RECONCILIATION.md), [`tenant-platform/DUPLICATE_AUTHORITY_MATRIX.md`](./tenant-platform/DUPLICATE_AUTHORITY_MATRIX.md), [`tenant-platform/HISTORICAL_COMPATIBILITY_RESULTS.md`](./tenant-platform/HISTORICAL_COMPATIBILITY_RESULTS.md), [`tenant-platform/RNICA_ACCEPTANCE_TEST_MATRIX.md`](./tenant-platform/RNICA_ACCEPTANCE_TEST_MATRIX.md), [`tenant-platform/AUTHORITY_APPLICABILITY_REGISTER.md`](./tenant-platform/AUTHORITY_APPLICABILITY_REGISTER.md), [`tenant-platform/STAFF_SUPPORT_IMPACT_REGISTER.md`](./tenant-platform/STAFF_SUPPORT_IMPACT_REGISTER.md), [`tenant-platform/CLINICAL_NARRATIVE_OWNERSHIP_AUDIT.md`](./tenant-platform/CLINICAL_NARRATIVE_OWNERSHIP_AUDIT.md) — RNICA Phase 2 audit baseline (AUDIT BASELINE / REMEDIATION REQUIRED — see remediation register above)
- [`phase2/ACCESS_CONTROL_DEFECT_REMEDIATION.md`](./phase2/ACCESS_CONTROL_DEFECT_REMEDIATION.md) — AC-001/002/003 remediation record (COMPLETE)
- [`phase2/ACCESS_CONTROL_DEFECT_VALIDATION.md`](./phase2/ACCESS_CONTROL_DEFECT_VALIDATION.md) — AC-001/002/003 validation evidence (COMPLETE)
- [`phase2/SUPERADMIN_OWNER_ACCOUNT_VALIDATION.md`](./phase2/SUPERADMIN_OWNER_ACCOUNT_VALIDATION.md) — SUPERADMIN/OWNER account validation (VALIDATED / CLOSED)

### Historical / Superseded (retained for traceability only)

- [`phase2/SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md`](./phase2/SUPERADMIN_DEVELOPER_LOGIN_VALIDATION.md) — SUPERSEDED by `SUPERADMIN_OWNER_MODEL_DECISION.md`
- [`phase2/SUPERADMIN_PLAN_TRACEABILITY.md`](./phase2/SUPERADMIN_PLAN_TRACEABILITY.md) — REFERENCE ONLY
- [`phase2/ACCESS_CONTROL_CURRENT_STATE.md`](./phase2/ACCESS_CONTROL_CURRENT_STATE.md), [`phase2/ACCESS_CONTROL_DECISION.md`](./phase2/ACCESS_CONTROL_DECISION.md), [`phase2/ACCESS_CONTROL_DEFECT_REACHABILITY.md`](./phase2/ACCESS_CONTROL_DEFECT_REACHABILITY.md), [`phase2/ACCESS_CONTROL_EVIDENCE.md`](./phase2/ACCESS_CONTROL_EVIDENCE.md) — REFERENCE ONLY (point-in-time evidence-gathering, superseded as decision records by the ACTIVE documents above)
- `OWNER_PLATFORM_*.md` (top-level `docs/`) and `recovery/2026-09-15/OWNER_PLATFORM_*.md` — SUPERSEDED (2026-09-15 pre-merge recovery-branch reports)
