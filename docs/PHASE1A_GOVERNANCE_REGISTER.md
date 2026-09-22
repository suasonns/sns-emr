# Phase 1A — Governance Register

Status: Planning/reconciliation only. Converts prior Phase 1A observations into
explicit, ID-tracked governance decisions. No code, schema, or migration changes.

---

### GOV-001 — Repository Recovery Status
- **Statement:** Staff Management, RBAC, Password Setup, and Audit Logs recovery
  work is merged into `main` (PR #91, commit `6f456ab`, plus dependency-closure
  hotfix `4182f0f`). Status: READY WITH CONDITIONS.
- **Owner:** Human (user) — final ratification pending open items below
- **Source Documents:** `OWNER_PLATFORM_FINAL_READINESS.md`, `PHASE1_MERGE_BLOCKERS.md`,
  `PHASE1_RELEASE_CANDIDATE.md`, `OWNER_PLATFORM_MERGE_REVIEW.md`; confirmed via
  `git merge-base --is-ancestor review/staff-management-rbac-auditlogs HEAD` (true)
  and `git merge-base --is-ancestor hotfix/owner-platform-pr91-dependency-closure HEAD` (true)
- **Date Established:** Merge occurred 2026-09-15 (`6f456ab`); reconciled/confirmed
  in this repository 2026-09-21
- **Status:** ESTABLISHED — CONDITIONAL (see GOV-007 dependency)
- **Impact:** Removes "recovery branch unmerged" as an open blocker for any future
  phase; the code artifact question is closed
- **Dependencies:** None blocking; informs GOV-002
- **Required Ratification:** Human confirmation that no further recovery-branch
  disposition action is needed (i.e., accept the merge as final)

---

### GOV-002 — Owner Platform Status
- **Statement:** Owner Platform is partially authoritative. 5 of 9 nav sections
  COMPLETE (Dashboard, Agency Management, System Health, Staff Management, Audit
  Logs). 4 sections remain PARTIAL/NOT STARTED (Analytics, Billing & Licensing,
  Settings, AI Command Center), each gated on Figma redesign approval (or, for AI
  Command Center, net-new backend architecture) per standing user directive.
- **Owner:** Human (user)
- **Source Documents:** `OWNER_PLATFORM_ROADMAP_STATUS.md`, `OWNER_PLATFORM_REMAINING_WORK.md`
- **Date Established:** 2026-09-15 (documents), reconciled 2026-09-21
- **Status:** ESTABLISHED
- **Impact:** Defines what "Owner Platform Complete" requires before ADR-004's
  gate can be evaluated as satisfied
- **Dependencies:** Depends on GOV-001 (recovery scope now closed); gates GOV-003
- **Required Ratification:** Confirm the 4-section remaining scope and Figma-first
  sequencing is still the standing directive (not superseded elsewhere)

---

### GOV-003 — Tenant Platform Status
- **Statement:** Tenant Platform remains DEFERRED. ADR-004's three gate
  conditions (Owner stabilization complete / roadmap complete / backlog reviewed)
  are not all satisfied while Owner Platform is only partially complete (GOV-002).
- **Owner:** N/A — governed by existing ADR-004, no new decision required unless
  overridden
- **Source Documents:** `docs/architecture/adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md`
- **Date Established:** ADR-004 accepted prior to this session; re-confirmed
  unmodified 2026-09-21
- **Status:** ESTABLISHED
- **Impact:** Blocks RNICA, AI Command Center backend, and other Tenant Platform
  intelligence work from beginning
- **Dependencies:** Depends entirely on GOV-002 reaching "Owner Platform COMPLETE"
- **Required Ratification:** None needed — ADR-004 is already accepted and in
  force; only a future ADR could supersede it

---

### GOV-004 — RNICA Authorization Status
- **Statement:** RNICA is DESIGN ONLY. `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`,
  `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`, and `RNICA_NARRATIVE_FIELDS_ANALYSIS.md`
  are target-state design/analysis artifacts; none contains language authorizing
  implementation to begin now. RNICA is additionally gated by GOV-003 (Tenant
  Platform deferral).
- **Owner:** Human (user) — any future implementation authorization must be
  explicit and separate from this reconciliation
- **Source Documents:** the three RNICA documents above; ADR-004
- **Date Established:** Reconciled 2026-09-21 (documents predate this session)
- **Status:** ESTABLISHED
- **Impact:** No RNICA implementation work may begin under current authorization
- **Dependencies:** GOV-003
- **Required Ratification:** None required to remain in current state; would
  require explicit new authorization to change

---

### GOV-005 — AI Authorization Status
- **Statement:** AI Command Center (and any Tenant Platform AI/intelligence work)
  is FOUNDATION ONLY. No backend exists anywhere in the codebase today (static UI
  shell, `readOnly` input, zero API wiring). Gated by GOV-003.
- **Owner:** Human (user)
- **Source Documents:** `OWNER_PLATFORM_REMAINING_WORK.md`; ADR-004
- **Date Established:** Reconciled 2026-09-21
- **Status:** ESTABLISHED
- **Impact:** No AI backend implementation work may begin under current
  authorization
- **Dependencies:** GOV-003
- **Required Ratification:** None required to remain in current state

---

### GOV-006 — Authority Model Status
- **Statement:** Exactly one authority model exists and is live: RBAC hierarchy =
  `ROLE_AUTHORITY_RANK` (data-driven); authority/permission check = `role_can()` +
  `PLATFORM_PERMISSION_MATRIX` (rank-comparison, deny-by-default, documented OWNER
  exception). No hardcoded delegation-exception bypass remains (`grep` confirmed
  zero matches in `backend/app/core/roles.py`).
- **Owner:** N/A — already implemented and merged; formalization only
- **Source Documents:** `OWNER_PLATFORM_FINAL_READINESS.md`, `RBAC_HIERARCHY_DECISION.md`,
  live `backend/app/core/roles.py`
- **Date Established:** Merged 2026-09-15 (`6f456ab`); formalized in
  `PHASE1A_AUTHORITY_MODEL.md` 2026-09-21
- **Status:** ESTABLISHED
- **Impact:** No further RBAC/authority design decision is required before any
  future implementation phase
- **Dependencies:** None
- **Required Ratification:** Second-reviewer sign-off on `roles.py` — **open**,
  see PHASE1A_DECISION_REGISTER.md item 1 (non-blocking governance item, not a
  code defect)

---

### GOV-007 — Implementation Sequence Approval
- **Statement:** Proposed sequence: (1) close open governance items (GOV-006's
  sign-off, GOV-002's tier ratification) → (2) complete remaining 4 Owner
  Platform sections in Figma-first order → (3) only then evaluate whether
  ADR-004's gate (GOV-003) is satisfied → (4) separately authorize Tenant
  Platform/RNICA/AI work at that time.
- **Owner:** Human (user) — this sequence is a restatement of existing approved
  ordering (`OWNER_PLATFORM_ROADMAP_STATUS.md` §6), not a new plan; requires
  explicit ratification to become binding
- **Source Documents:** `OWNER_PLATFORM_ROADMAP_STATUS.md`
- **Date Established:** Proposed 2026-09-21 (not yet ratified)
- **Status:** **PROPOSED — NOT YET RATIFIED**
- **Impact:** Until ratified, no phase after Phase 1A may claim an approved
  implementation order
- **Dependencies:** GOV-001 through GOV-006
- **Required Ratification:** Explicit human approval required — this is the one
  GOV item this register does not treat as already decided
