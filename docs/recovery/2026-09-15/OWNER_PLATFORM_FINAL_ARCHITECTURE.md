# Owner Platform — Final Architecture Review

Read-only. No code changed, no merge, no commit. Synthesized from the recovered
`roles.py`/`role_guards.py`/`owner_admin.py` and prior recovery reports
(`conflict-analysis.md`, `rbac-validation.md`, `feature-recovery-summary.md`).

## Role scopes as implemented in the recovered code

Source of truth: `PLATFORM_PERMISSION_MATRIX` and `ACCESS_LEVEL_FOR_ROLE` in
`backend/app/core/roles.py`. Capability names are namespaced `staff.*` and only ever govern the
SNS Staff & Access surface — they do not touch clinical, financial, or tenant data models.

| Role | Access level tier | Granted `staff.*` capabilities |
|---|---|---|
| **Platform Owner** (`OWNER`) | LEVEL_1_OWNER | All (unconditional bypass — see `RBAC_SECURITY_REVIEW.md`/`OWNER_PLATFORM_SECURITY_REVIEW.md`) |
| **Platform Administrator** (`PLATFORM_ADMIN`) | LEVEL_2_ADMINISTRATOR | view, create, invite, edit_profile, assign_role, activate, suspend, disable, revoke_access, remove, reset_password, view_audit — everything except `assign_owner_role` and acting on OWNER/another PLATFORM_ADMIN target |
| **Security** (`PLATFORM_SECURITY`) | LEVEL_3_SPECIALIZED_ADMINISTRATOR | view, suspend, revoke_access, view_audit |
| **Compliance** (`PLATFORM_COMPLIANCE`) | LEVEL_3_SPECIALIZED_ADMINISTRATOR | view, view_audit (read-only + audit by design; escalations go through explicit delegated grants, not a default bundle) |
| **Billing Administration** (`PLATFORM_BILLING`) | LEVEL_3_SPECIALIZED_ADMINISTRATOR | view only |
| **AI Management** (`PLATFORM_AI_MANAGEMENT`) | LEVEL_3_SPECIALIZED_ADMINISTRATOR | view only |
| **Operations** (`PLATFORM_OPERATIONS`) | LEVEL_4_OPERATIONAL_STAFF | view only |
| **Developer** (`PLATFORM_DEVELOPER`) | LEVEL_4_OPERATIONAL_STAFF | view only |
| **DevOps** (`PLATFORM_DEVOPS`) | LEVEL_4_OPERATIONAL_STAFF | view only |
| **Implementation** (`PLATFORM_IMPLEMENTATION`) | LEVEL_4_OPERATIONAL_STAFF | view only |
| **QA** (`PLATFORM_QA`) | LEVEL_4_OPERATIONAL_STAFF | view only |
| **Support** (`PLATFORM_SUPPORT`) | LEVEL_5_LIMITED_SUPPORT | view, reset_password |
| **Customer Service** (`PLATFORM_CUSTOMER_SERVICE`) | LEVEL_5_LIMITED_SUPPORT | none (empty set — view-only via the LEVEL_5 UI tier, no `staff.*` capability granted at all) |
| **Auditor** (`PLATFORM_AUDITOR`) | LEVEL_6_READ_ONLY | view, view_audit |

Notes:
- Every non-OWNER role additionally sits behind a **target-hierarchy ceiling** in `role_can()`:
  no non-OWNER actor may ever mutate an OWNER target or assign the OWNER role; only OWNER may act
  on/assign PLATFORM_ADMIN.
- `direct_grants` (via `StaffPermissionGrant`) let `PLATFORM_ADMIN` (and only `PLATFORM_ADMIN`,
  per `DELEGATION_AUTHORITY_ROLES`) delegate a capability it already holds to another eligible
  identity for a specific, revocable window — this is the "responsibility-ownership" escalation
  path referenced in code comments (e.g. giving one `PLATFORM_SUPPORT` account a temporary
  `staff.suspend` grant for an active escalation).
- `staff.assign_owner_role` is in `NON_DELEGABLE_CAPABILITIES` — it can never be handed out via
  delegation, and `role_can()` denies it to every actor except OWNER unconditionally.

## Tenant isolation boundaries

Unchanged by this recovery. `tenant_id`-scoped row filtering throughout the application, and
`is_platform_role()`'s hard gate in `role_can()` (a non-platform actor role fails the very first
check and never reaches the capability matrix), keep the new `staff.*` surface fully outside
tenant-accessible territory. No recovered file modifies tenant row-level scoping logic.

## Biller boundaries

Biller/financial roles (`FINANCIAL_ADMIN_ROLES`: `CFO`, `CEO`, `FINANCIAL_ADMIN`, plus the
`BILLING_DEPARTMENT_ROLES` set) are explicitly excluded from `PLATFORM_ROLES` and therefore from
every `staff.*` capability — verified directly by the recovered test
`test_tenant_and_biller_roles_never_get_staff_capabilities`. Biller isolation from clinical
documentation (a separate, pre-existing concern in `CLINICAL_ADMIN_ROLES`/`FINANCIAL_ROLES`) is
untouched by this recovery.

## Training/Test agency and Production agency boundaries

Unchanged. `app/models/tenant.py`'s check constraint
(`tenant_type IN ('PRODUCTION','TRAINING','DEV','PLATFORM','BILLING')`) and its enforcement predate
and are not touched by any of the 46 recovered files. The recovered `staff.*` capability system
operates entirely within the `PLATFORM` tenant scope (`PLATFORM_TENANT_ID` constant, additive in
`protected_tenants.py`) — it has no interaction with PRODUCTION/TRAINING/DEV agency data.

## Architectural gaps for final sign-off (not defects, but open decisions)

1. **Hierarchy ordering** — the tier ordering above (Owner > Admin > Security/Compliance/Billing/
   AI > Operations/Developer/DevOps/Implementation/QA > Support/Customer Service > Auditor) needs
   explicit approval; see `RBAC_HIERARCHY_DECISION.md`.
2. **OWNER's unconditional bypass** is architecturally a code constant, not a database-driven
   grant like every other role now has (see `OWNER_PLATFORM_SECURITY_REVIEW.md` Finding 2).
3. **`authorization.ts` route-level broadening** (any platform-scope role, not just OWNER, can
   reach `/owner`) needs every existing (non-recovered) owner page audited for equivalent
   per-action server-side gating before this is considered architecturally closed
   (`OWNER_PLATFORM_SECURITY_REVIEW.md` Finding 1).
