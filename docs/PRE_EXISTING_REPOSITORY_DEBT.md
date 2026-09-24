# PRE-EXISTING REPOSITORY DEBT

**Status:** Informational only. Does not affect Phase 1 (Owner Platform Foundation) readiness.
**Phase 1 classification remains: READY FOR PR REVIEW.**

---

## 1. Exact failing test name
`backend/tests/test_treatment_identity_migration.py::test_migration_remaps_treatment_references_and_preserves_survivor_metadata`

## 2. Exact migration involved
`backend/alembic/versions/p9r8q7s6t5u4_add_billing_scope_permission_levels.py`
(its `downgrade()` function, line 37)

## 3. Exact root cause
The test attempts `command.downgrade(cfg, PRE_MIGRATION_REVISION)` where
`PRE_MIGRATION_REVISION = "c3f7a1e9b0d2"`. That target revision sits earlier
in the migration chain than `p9r8q7s6t5u4_add_billing_scope_permission_levels.py`,
so Alembic must execute `p9r8q7s6t5u4`'s `downgrade()` as part of the plan.
That function unconditionally raises:
```
raise NotImplementedError("Forward-only migration")
```
This is an intentional, by-design irreversible migration (it is not a bug in
the migration itself) — but it makes any test or operational procedure that
needs to downgrade past this point in the chain permanently unable to do so.
Confirmed via direct execution to reproduce identically on unmodified `main`
(commit `b552fcb`), independent of any Owner Platform / Phase 1 changes.

## 4. Affected subsystem
Billing (the migration adds "billing scope permission levels"). The failing
test itself belongs to the treatment/ontology identity-migration test suite,
which is unrelated to Billing in purpose but shares the same linear Alembic
migration chain — so any downgrade-based test whose target revision precedes
`p9r8q7s6t5u4` is affected, regardless of which subsystem authored the test.

## 5. Impact by platform area
| Area | Impacted? |
|---|---|
| Owner Platform | No |
| Tenant Platform | No (not directly; shares the migration chain but no Tenant Platform code depends on downgrading past this point) |
| Billing | Yes — this is the migration's origin; any Billing rollback/downgrade tooling that needs to cross this revision boundary will hit the same `NotImplementedError` |
| Admissions | No |
| HOPE | No |
| Clinical Documentation | Indirectly — the failing test covers ontology/treatment-identity migration behavior (survivor metadata remapping), which is Clinical Documentation/ontology-adjacent; the test itself cannot currently validate downgrade behavior across this boundary |

## 6. Risk level
**LOW–MEDIUM.**
- Not a defect in Phase 1 or Owner Platform.
- Does not affect forward migrations, current schema state, or any runtime behavior — only a downgrade path is blocked.
- Medium risk only in the narrow scenario of needing to roll back the database schema to a point earlier than `p9r8q7s6t5u4` (e.g., a full historical rollback or a rebuild of an old environment) — this would fail today independent of Phase 1.
- No security, data-integrity, or authorization impact.

## 7. Recommended future remediation phase
Address as part of a dedicated **Billing & Licensing** work phase (already
identified as a future Owner Platform section, per the roadmap: Analytics,
Billing & Licensing, Settings, AI Command Center). Recommended remediation
options for that phase:
- Implement a real `downgrade()` for `p9r8q7s6t5u4_add_billing_scope_permission_levels.py` if reversibility is required, or
- Update `test_treatment_identity_migration.py`'s `PRE_MIGRATION_REVISION` target/approach so it no longer needs to cross this forward-only boundary, or
- Formally document the forward-only boundary as an intentional schema checkpoint and adjust any tooling/tests that assume full reversibility.

This should not be scheduled ahead of, or in place of, the already-planned Billing & Licensing Figma-first design phase; it can be folded into that phase's implementation work.

---

**This document does not reopen Owner Platform Phase 1 work, does not reclassify Phase 1 as incomplete, and does not add this debt to the Owner Platform Foundation scope.**
