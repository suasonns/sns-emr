# SUPERADMIN / Owner Account — Approved Model Decision (A vs B)

**Document Status:** ACTIVE PRODUCT DECISION — supersedes any prior statement that defined
SUPERADMIN merely as a developer login. SUPERADMIN = SNS Tech Solutions Platform Owner; OWNER is
the canonical implementation role. Model A (Platform Owner only, no automatic tenant/patient-data
access) is confirmed as both the current implementation and the approved design.

Scope: Determine whether the **approved product design** intends SUPERADMIN
(the `OWNER` role, the SNS Tech Solutions platform-owner account) to be:

- **Model A** — Platform Owner only (no tenant/patient-data access at all)
- **Model B** — Platform Owner with explicit, audited tenant-support access

This is a design-vs-implementation reconciliation only. No code, schema, or
migration was changed. No new "elevated access" mode was inferred or built.

## 1. Evidence Table

| Source | Statement | Supports A | Supports B |
|---|---|---|---|
| `docs/ACCESS_CONTROL_MODEL.md` (§ Level 0 — Platform, "Platform Owner" row) | "Owns SNS Hospice Solutions. Can create/suspend tenants (`/api/owner/tenants`), view platform-wide operational metrics. **Cannot access patient charts, clinical notes, orders, POC, IDG, or any clinical documentation.**" | ✅ | — |
| `docs/ACCESS_CONTROL_MODEL.md` (§ "Key security invariants (already enforced)") | "**Platform Owner ≠ Tenant Owner.** `OWNER` never gets `CLINICAL_ADMIN_ROLES` fallback — verified via `/api/dashboard/tenant`, `/api/dashboard/clinical-alerts`, `/idg/sessions`, `TenantDashboard.jsx` all blocking `OWNER`." | ✅ | — |
| `docs/ACCESS_CONTROL_MODEL.md` (§ Level 0, "Platform Support" row) | "`PLATFORM_SUPPORT` — New, additive. **Not yet wired to any endpoint** — reserved for future support-tooling access." | — | Weak/partial — describes a **separate, distinct, unimplemented role**, not an OWNER capability |
| `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` | "The Owner Platform does NOT operate hospice agencies." | ✅ | — |
| `docs/PHASE1A_AUTHORITY_MODEL.md` (§ 4, Exception Handling) | "Any future escalation mechanism (e.g., temporary elevated access, break-glass patterns) is **not currently implemented and is not authorized by this reconciliation** — it would require a separate, explicit decision." | ✅ (as current state) | — (explicitly defers a B-like mechanism to a future, separate decision) |
| `docs/phase2/ACCESS_CONTROL_CURRENT_STATE.md` (row: "Emergency access") | "No break-glass/emergency-access code, model, or documentation was found anywhere in the repository." | ✅ | — |
| `docs/recovery/2026-09-15/RBAC_SECURITY_REVIEW.md` (Finding 2) | Discusses OWNER's unconditional `staff.*` authority being a hardcoded "root" pattern, and notes that a compliance model requiring "all privilege, including Owner's, be revocable/auditable ... e.g. for a break-glass ... scenario" is **not currently met**, offering it as an open, undecided future option ("Either choice needs an explicit decision — this review does not recommend one over the other.") | Neutral/undecided | Neutral/undecided (about staff-authority revocability, not patient-data access — tangential) |
| `backend/app/core/roles.py` (`PLATFORM_ROLES`, `PLATFORM_PERMISSION_MATRIX`) | `PLATFORM_SUPPORT` capabilities today: `staff.view`, `staff.reset_password` only — no patient/tenant-data capability exists for any platform role, including `PLATFORM_SUPPORT` | ✅ | — |
| `backend/app/core/middleware/clinical_access_guard.py` (live-verified) | OWNER receives 403 on `/patients` and all clinical prefixes; no code path grants exception | ✅ | — |
| `backend/app/api/auth.py` (`switch-agency`/`linked-agencies`) | Only tenant-plurality feature in repo; requires the target account's own password, unrelated to OWNER support access | — | — (not evidence for either; addresses a different scenario) |

## 2. Decision Matrix

| Dimension | Model A — Platform Owner Only | Model B — Platform Owner + Explicit Audited Tenant Support Access |
|---|---|---|
| Tenant access | Manage tenant *records* only (create/suspend, financials toggle, metrics) | Same, plus an ability to enter a tenant's operational context |
| Patient-data access | **None** — no route, no capability, ever | Time-boxed / audited access to a specific tenant's patient data, entered deliberately |
| Support workflow | None exists; support requires the tenant's own staff or a distinct not-yet-built role | Requires an explicit "enter support mode" action, scoped grant, and exit path |
| Audit requirements | Only OWNER's own platform-admin mutations are audited (already implemented — 15 `log_event` sites in `owner_admin.py`) | Would additionally require audit events for support-session start/end and every in-session patient-data access (not implemented) |
| Tenant switching requirements | Not applicable — OWNER never "switches into" a tenant | Would require session state entry/exit, state-clearing on exit, and non-disclosing cross-tenant responses outside the granted session (not implemented) |
| Implementation status | **Fully implemented and verified** (this is the current, live behavior) | **Not implemented anywhere in the codebase** — no route, capability, model, or test exists for it |

## 3. Current Implementation vs. Approved Product Design

- **CURRENT IMPLEMENTATION:** Model A. Verified live and by tests
  (`test_owner_platform_rbac_matrix.py`, `test_auth_hardening.py`,
  `clinical_access_guard.py`, this session's own live HTTP checks). OWNER has
  zero patient-data access under any code path.
- **APPROVED PRODUCT DESIGN:** `docs/ACCESS_CONTROL_MODEL.md` is the
  authoritative, repository-committed design reference for this exact
  question, and it states the same thing in its own words: OWNER "Cannot
  access patient charts, clinical notes, orders, POC, IDG, or any clinical
  documentation." This is **Model A**, explicitly and unambiguously, for the
  `OWNER` role itself.
- The same document also names a **separate, not-yet-implemented** role,
  `PLATFORM_SUPPORT`, "reserved for future support-tooling access." This is
  evidence that the product's long-term intent may eventually include a
  *support* capability — but it is scoped to a **different role**, not to
  `OWNER`, and it remains entirely unbuilt (no endpoint, no capability
  beyond `staff.view`/`staff.reset_password`, no audit model, no UI). It
  does not describe "OWNER with support access" (Model B for the SUPERADMIN/
  OWNER account specifically) — it describes a distinct future role that,
  if built, would still leave `OWNER` itself under Model A.

**Conclusion: CURRENT IMPLEMENTATION and APPROVED PRODUCT DESIGN are
ALIGNED for the `OWNER`/SUPERADMIN account — both are Model A.**

The only open item is whether the platform will, in the future, build the
separate `PLATFORM_SUPPORT` role's "future support-tooling access" — that is
a distinct, not-yet-designed feature for a different role, not a gap between
OWNER's current implementation and OWNER's approved design.

## 4. Final Status

**VERIFIED COMPLETE** — for the `OWNER`/SUPERADMIN account: current
implementation (Model A, zero patient-data access) matches the approved
product design (`docs/ACCESS_CONTROL_MODEL.md`, same Model A statement,
verbatim).

Separately noted (not a defect, not part of this VERIFIED COMPLETE
determination): whether/when to design and build the distinct
`PLATFORM_SUPPORT` role's future support-tooling access remains a
**PRODUCT DECISION REQUIRED** for that separate role — it does not change
OWNER's own model, which is fully aligned and implemented today.

CONFIRMATION: ACP REMAINS ADVANCE CARE PLANNING.
