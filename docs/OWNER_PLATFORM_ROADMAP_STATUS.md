# OWNER PLATFORM ROADMAP STATUS

**Date:** 2026-09-15
**Merge status of recovery branch:** `RECOVERY IMPLEMENTATION READY FOR
MERGE REVIEW` — **NOT** "Owner Platform Complete." No commit, no merge, no
PR has been made. `recovery/copilot-session-2026-09-14` remains isolated
and intact.

> This report inventories the whole Owner Platform (9 nav sections). It
> does not re-litigate Staff Management/RBAC/Audit Logs/Password Setup —
> those are covered by `OWNER_PLATFORM_FINAL_READINESS.md` and are
> classified merge-candidate-ready, not "complete" until merged/deployed.

---

## 1. Completed Owner Platform Sections

| Section | Status | Notes |
|---|---|---|
| Dashboard | **COMPLETE** | Live on `main`, backend-wired (`fetchOwnerDashboard`). Unchanged by recovery. |
| Agency Management (Tenant Management) | **COMPLETE** | Live on `main` (`TenantManagement.jsx`, 520 lines) — onboarding, financials toggle, admin creation, fully backend-wired. Unchanged by recovery. |
| System Health | **COMPLETE** | Live on `main` (`SystemHealth.jsx` + backend `system_health()`). Unchanged by recovery. |

## 2. Remaining Owner Platform Sections

| Section | Status | Merge-candidate-ready? |
|---|---|---|
| Staff Management (incl. RBAC) | Merge-candidate ready, **not merged** | Yes — see `OWNER_PLATFORM_FINAL_READINESS.md` |
| Audit Logs | Merge-candidate ready, **not merged** | Yes — see `OWNER_PLATFORM_FINAL_READINESS.md` |
| Analytics | **PARTIAL** (live, minimal scope — 82 lines, single data source) | No — needs Figma redesign first, per your directive |
| Billing & Licensing | **PARTIAL** (live, largest of the four — 751 lines; some metrics may still show "not available yet" fallback rather than live data) | No — needs Figma redesign first, per your directive |
| Settings | **PARTIAL** (live, minimal — 122 lines, fetches tenant list only, no dedicated backend) | No — needs Figma redesign first, per your directive |
| AI Command Center | **NOT STARTED** functionally (static UI shell, `readOnly` input, zero backend/API wiring) | No — needs Figma redesign first, per your directive |

---

## 3. Which Sections Have Approved Design

| Section | Approved design exists? |
|---|---|
| Staff Management (incl. RBAC) | **Yes** — approved design already exists; recovered implementation follows it, no redesign performed. |
| Audit Logs | **Yes** — approved design already exists; recovered implementation follows it, no redesign performed. |
| Dashboard, Agency Management, System Health | Implicitly approved (already shipped, live, complete). |
| Analytics | **No** — flagged by you for Figma redesign before further implementation. |
| Billing & Licensing | **No** — flagged by you for Figma redesign before further implementation. |
| Settings | **No** — flagged by you for Figma redesign before further implementation. |
| AI Command Center | **No** — flagged by you for Figma redesign before further implementation. |

## 4. Which Sections Require Figma Redesign

Per your standing directive, these four sections must go through Figma
redesign **before** any new production UI is built:

1. **Analytics**
2. **Billing & Licensing**
3. **Settings**
4. **AI Command Center**

No implementation, no placeholder UI, and no production code should be
written for these sections until an approved Figma design exists for each.
This report does not begin that redesign work — it only records the
requirement and sequencing.

---

## 5. Dependencies For Each Remaining Section

| Section | Depends on | Blocking relationship |
|---|---|---|
| Staff Management / RBAC | Merge decision on `recovery/copilot-session-2026-09-14` | Blocks nothing else in this list — independent of the four Figma-pending sections. |
| Audit Logs | Same recovery-branch merge decision as Staff Management (same batch) | Same as above. |
| Analytics | (a) Figma redesign approval, (b) decision on whether existing `fetchOwnerAdoptionHealth()` backend is reused or replaced | Cannot start production implementation until (a) is complete. |
| Billing & Licensing | (a) Figma redesign approval, (b) confirmation of which displayed metrics are already live vs. still "not available yet" fallback in the current implementation | Cannot start redesign-driven implementation until (a); (b) should inform what the redesign needs to cover. |
| Settings | (a) Figma redesign approval, (b) product definition of Settings' actual scope (today it only fetches a tenant list — no defined scope beyond that) | (b) is arguably needed before (a) can be meaningfully drafted — Figma needs a scope to design against. |
| AI Command Center | (a) Figma redesign approval, (b) net-new backend design (zero existing backend today — this is the only section requiring backend architecture from scratch, not just UI) | (b) is the largest lift of the four; Figma design should account for what a from-scratch backend can realistically support first. |

**Cross-cutting dependency:** none of the four Figma-pending sections
depend on the Staff Management / RBAC / Audit Logs merge decision, and vice
versa — they can proceed on independent tracks. The recovery-branch merge
is not a blocker for starting Figma redesign work on the other four
sections, and Figma work is not a blocker for the recovery-branch merge
decision.

---

## 6. Estimated Implementation Order

1. **Resolve recovery-branch merge decision** (Staff Management + RBAC +
   Audit Logs) — closest to done, already merge-candidate-ready, no design
   work required.
2. **Define Settings' actual scope** — needed as an input to Figma, and is
   the smallest/lowest-risk of the four remaining sections to scope.
3. **Figma redesign: Settings** — smallest surface area once scoped.
4. **Figma redesign: Analytics** — existing backend already provides a
   data source; redesign can build on what's live today.
5. **Figma redesign: Billing & Licensing** — largest existing surface
   area of the four; redesign should explicitly address which metrics
   remain in "not available yet" fallback.
6. **Figma redesign: AI Command Center** — largest lift; needs backend
   architecture defined alongside (or before) the visual design, since no
   backend exists today.
7. **Implementation, in the same order (2→6 mirrored)**, once each
   section's Figma design is approved.
8. **Final Owner Platform freeze** — only after all 9 sections are
   COMPLETE and validated.

This ordering is a recommendation based on current scope/readiness
signals (smallest/most-defined first, largest/least-defined last); it is
not a commitment and should be confirmed or reprioritized by you.

---

## 7. Exact Path From Today To "OWNER PLATFORM COMPLETE"

1. Decide on the recovery-branch merge (Staff Management, RBAC, Audit
   Logs, Password Setup) — currently `RECOVERY IMPLEMENTATION READY FOR
   MERGE REVIEW`. On approval: commit → PR → merge → re-validate on
   `main` → freeze this portion of the Owner Platform baseline.
2. Confirm/ratify the `PLATFORM_AI_MANAGEMENT` / `PLATFORM_OPERATIONS`
   interim role-tier placement (open item from
   `OWNER_PLATFORM_FINAL_READINESS.md`) — non-blocking for the merge
   above, but should be closed before the AI Command Center /
   Operations-tooling work begins later.
3. Define Settings' scope (product decision, not engineering).
4. Produce approved Figma designs for Settings, Analytics, Billing &
   Licensing, and AI Command Center (in the order proposed in §6, or as
   you reprioritize).
5. Implement each of the four sections against its approved Figma design
   only — no redesign, no alternate layouts, no placeholder UI, per your
   standing rule.
6. Confirm Billing & Licensing's live-data coverage (close the "not
   available yet" fallback gaps identified in
   `OWNER_PLATFORM_REMAINING_WORK.md`) as part of its redesign/
   reimplementation.
7. Build the AI Command Center backend from scratch (currently zero
   backend) as part of its redesign/reimplementation.
8. Run full validation (backend tests, frontend build, lint) across the
   entire Owner Platform once all 9 sections are implemented.
9. Only once all 9 sections are COMPLETE and validated: freeze the Owner
   Platform architecture, record the final navigation, and mark
   **OWNER PLATFORM COMPLETE.**
10. Only after step 9: begin Tenant Platform (incorporating October CMS
    regulatory changes there, per your standing instruction, not before).

---

## Current Status Summary

| | |
|---|---|
| Recovery branch (Staff Mgmt / RBAC / Audit Logs / Password Setup) | **RECOVERY IMPLEMENTATION READY FOR MERGE REVIEW** |
| Owner Platform overall | **NOT COMPLETE** — 4 of 9 sections (Analytics, Billing & Licensing, Settings, AI Command Center) remain unfinished and pending Figma redesign |
| Action taken this pass | Documentation only. No code changed. No commit. No merge. No PR. |
