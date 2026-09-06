# FACILITY ALERTS V1 — FINAL ARCHITECTURE SPECIFICATION

Status: **PENDING SIGN-OFF.** This document consolidates the discovery
(`ARCHITECTURE.md`, sections 1–7 in this same directory) into a single
authoritative spec. No implementation code exists in this branch. Coding is
not authorized until this document is approved.

Reframing (approved): Priority 3 is not "Build Facility Alerts." It is
**"Complete and Operationalize the Existing Alert Platform"** — extend what
Priority 2 groundwork already built; do not replicate or parallel it.

---

## 1. Alert Type Inventory

| Alert Type | Current Status | Generated? | Threshold-Driven? | Severity | Auto-Resolve? | User-Resolve? | Notification Required? |
|---|---|---|---|---|---|---|---|
| `FUNDING_SOURCE_NOT_VERIFIED` | Live | Yes | No | HIGH | Yes (v1) | Yes | Yes |
| `PARTIALLY_PAID` | Live | Yes | No | MEDIUM | Yes (v1) | Yes | Yes |
| `UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION` | Live | Yes | No | HIGH | Yes (v1) | Yes | Yes |
| `AMOUNT_MISMATCH` | Live | Yes | No | HIGH | Yes (v1) | Yes | Yes |
| `PAYMENT_NOT_RECEIVED_BY_DUE_DATE` | Live | Yes | No | HIGH | Yes (v1) | Yes | Yes |
| `SHARE_OF_COST_OUTSTANDING` | Live | Yes | No | MEDIUM | Yes (v1) | Yes | No (in-app only) |
| `OVERDUE_30` | Live | Yes | Yes (days, default 30) | MEDIUM | Yes (v1) | Yes | No (in-app only) |
| `OVERDUE_60` | Live | Yes | Yes (days, default 60) | HIGH | Yes (v1) | Yes | Yes |
| `OVERDUE_90` | Live | Yes | Yes (days, default 90) | CRITICAL | Yes (v1) | Yes | Yes |
| `BALANCE_EXCEEDS_THRESHOLD` | Live | Yes | Yes (amount, default $0.01) | MEDIUM | Yes (v1) | Yes | No (in-app only) |
| `EXPECTATION_MISSING` | Declared, dead | No | No | — | — | — | — |
| `NOT_BILLED` | Declared, dead | No | No | — | — | — | — |
| `SECONDARY_PAYER_PAYMENT_MISSING` | Declared, dead | No | No | — | — | — | — |
| `COLLECTION_FOLLOWUP_REQUIRED` | Declared, dead | No | No | — | — | — | — |

"Auto-Resolve? Yes (v1)" means the new condition-cleared and
expectation-superseded auto-resolve hooks (Section 6) apply uniformly to all
9 live types — no per-type opt-out in v1.

"Notification Required?" marks which live types trigger the in-app
notification/badge (Section 5) at launch: `HIGH`/`CRITICAL` severity types,
plus `PARTIALLY_PAID` (money-impacting even at MEDIUM) and
`FUNDING_SOURCE_NOT_VERIFIED` (blocks billing entirely). `MEDIUM`-severity,
non-blocking types (`SHARE_OF_COST_OUTSTANDING`, `OVERDUE_30`,
`BALANCE_EXCEEDS_THRESHOLD`) surface in the Inbox but do not push a
notification badge, to avoid alert fatigue on the lowest-urgency tier.

---

## 2. Lifecycle State Diagram

```
                 ┌───────────────┐
                 │     OPEN      │  condition detected by evaluate_alerts_for_expectation
                 └───────┬───────┘
                         │ acknowledge (no evidence)
                         ▼
                 ┌───────────────┐
                 │ ACKNOWLEDGED  │  user accepted ownership; still unresolved
                 └───────┬───────┘
                         │ start work (optional, no evidence)
                         ▼
                 ┌───────────────┐
                 │  IN_PROGRESS  │  work underway (optional sub-state)
                 └───────┬───────┘
                         │
        ┌────────────────┼─────────────────────┬───────────────────────┐
        │ snooze(until)  │ resolve(evidence)    │ dismiss(reason)       │
        ▼                ▼                      ▼                      │
 ┌─────────────┐  ┌─────────────┐        ┌─────────────┐               │
 │   SNOOZED   │  │  RESOLVED   │        │  DISMISSED  │               │
 └──────┬──────┘  └─────────────┘        └─────────────┘               │
        │ auto-return at/after snoozed_until (back to OPEN)             │
        └─────────────────────────────────────────────────────────────►│
                                                                        │
  System-driven, from ANY non-terminal state (OPEN/ACKNOWLEDGED/        │
  IN_PROGRESS/SNOOZED):                                                │
        │ condition no longer true                                    │
        ▼                                                              │
 ┌───────────────┐                                                     │
 │ AUTO_RESOLVED │  system note, mandatory audit entry                 │
 └───────────────┘                                                     │
        │ OR expectation superseded/cancelled/closed                   │
        └─────────────────────────────────────────────────────────────►│

  Tenant-driven, from ANY non-terminal state:
        │ threshold disabled for this alert_type
        ▼
 ┌───────────────┐
 │  SUPPRESSED   │  policy-disabled, not deleted, audit preserved
 └───────────────┘

 EXPIRED — vocabulary reserved for a future hard-time-boundary case; no v1
 alert type produces it; no trigger code in this release.

 Terminal states: RESOLVED, DISMISSED, AUTO_RESOLVED, SUPPRESSED, EXPIRED.
 Re-evaluation of the same expectation/alert_type after a terminal state
 creates a brand-new OPEN alert if the condition recurs (existing upsert
 behavior, unchanged).
```

---

## 3. Ownership Model

- **Single assignee per alert.** `assigned_to` (nullable, existing column) →
  one user, within the tenant that owns the alert.
- Alert ownership is **tenant-scoped only** — no cross-agency, no
  billing-provider-level, no owner-user assignment. Identical to every other
  Facility Collections authorization boundary.
- Any user with `FINANCIAL_MONITORING` `EDIT` access to the tenant may
  reassign an alert to any other user who also has that access — no separate
  "assignment" permission tier.
- Reassignment **requires an audit note** (who, why) — written through the
  existing `_write_audit(entity_type="ALERT", field_name="assigned_to", ...)`
  ledger. No new audit mechanism.
- External billing-organization users are treated identically to in-tenant
  billers: if their account already has `FINANCIAL_MONITORING` access to the
  tenant (existing Billing Provider access model), they can be assigned and
  can self-assign like anyone else.
- Owner users are **excluded** from the assignee pool entirely (Section 9).

---

## 4. Queue Model

- **No new table, no routing engine, no work-distribution logic.**
- Convention: `assigned_to IS NULL` **is** the queue. Any alert without an
  assignee is implicitly "in the tenant's queue" and visible/actionable by
  every user with `FINANCIAL_MONITORING` access to that tenant.
- The Alert Inbox UI (Section 9) provides a default "Queue (Unassigned)"
  filter view plus a "My Alerts" (`assigned_to = current_user`) view — both
  are just query filters over the existing table, not separate models.
- Self-assign ("Claim") is simply a reassignment where the new assignee is
  the acting user; same audit path as any other reassignment.

---

## 5. Notification Model

Approved scope for v1:

| Channel | Status | Notes |
|---|---|---|
| In-app Alert Inbox | **Required, v1** | Primary surface; all live alert types listed here. |
| In-app nav badge (unresolved count) | **Required, v1** | Count of OPEN/ACKNOWLEDGED/IN_PROGRESS alerts in the tenant's queue + assigned-to-me, split by severity for the notification-required subset (Section 1). |
| Email | Optional, not built in v1 | Explicitly deferred; no delivery infra exists to reuse, would be new cross-cutting work. |
| Escalation notification | Future | Deferred; depends on reassignment/SLA policy not yet defined. |
| SMS | Not required | Out of scope entirely. |
| Teams/Slack-style integration | Future | Deferred. |

No notification-preferences model, no delivery queue, no external
integration is built in this phase. This keeps Priority 3 inside its
scope boundary (per the one-business-objective-per-branch rule) instead of
absorbing a notification-infrastructure project.

---

## 6. Auto-Resolution Rules

Two system-triggered paths, both evaluated inside the existing
`evaluate_alerts_for_expectation()` call (no new scheduler/cron/background
job — it already runs whenever an expectation is recomputed):

1. **Condition-cleared auto-resolve**: for each of the 9 live alert types,
   if an alert currently in `OPEN`/`ACKNOWLEDGED`/`IN_PROGRESS`/`SNOOZED`
   has a trigger condition that is no longer true on re-evaluation, it
   transitions to `AUTO_RESOLVED` with a system-authored
   `resolution_evidence` string identifying exactly what changed (e.g.
   `"Auto-resolved: reconciliation status changed to PAID."`,
   `"Auto-resolved: outstanding balance reached $0.00."`).
2. **Expectation-superseded/cancelled auto-resolve**: any non-terminal alert
   whose parent expectation has itself moved to
   `SUPERSEDED`/`CANCELLED`/`CLOSED` is auto-resolved with
   `"Auto-resolved: expectation superseded/cancelled."` This directly closes
   the "zombie alert" gap identified in discovery, where
   `evaluate_alerts_for_expectation` already skips generating new alerts for
   those statuses but previously left old ones dangling OPEN.

This is the "Digital Dust Rule": no alert is allowed to remain open once its
underlying condition is gone. Both paths are mandatorily audited exactly
like a manual resolve (Section 7).

---

## 7. Evidence Requirements

| Transition | Evidence required? |
|---|---|
| OPEN → ACKNOWLEDGED | No |
| ACKNOWLEDGED → IN_PROGRESS | No |
| any non-terminal → SNOOZED | No (optional note); `snoozed_until` required |
| any non-terminal → DISMISSED | **Yes** — reason required |
| any non-terminal → RESOLVED | **Yes** — evidence required (unchanged from today) |
| any non-terminal → AUTO_RESOLVED | System-authored note (no human input possible) |
| any non-terminal → SUPPRESSED | No (system-driven by threshold change) |
| reassignment (including self-claim) | **Yes** — audit note required |

---

## 8. Audit Requirements

- **No new audit table.** Every transition above writes through the
  existing generic `_write_audit(entity_type="ALERT", entity_id=..., ...)`
  ledger — the same mechanism already used for expectation corrections,
  activations, and today's `resolve_alert()`.
- Every audit row records: previous status, new status, acting user (or
  `system` for auto-resolve), role, and the evidence/reason/note text.
- Audit history is permanent and immutable, consistent with the "historical
  versions are audit artifacts, not obligations" principle already locked
  for Facility Collections.

---

## 9. UI Screens (wireframe-level, before implementation)

| Screen | Purpose | Key elements |
|---|---|---|
| **Alert Inbox** | Primary work surface | Filters: status, severity, category (Section 4 of discovery doc), assignee (Me / Queue / a specific user), tenant. Default view = non-terminal, sorted by severity then age. Row actions: Acknowledge, Claim, Resolve, Dismiss, Snooze. Unresolved-count badge feeds from here. |
| **Alert Detail** | Full context on one alert | All alert fields, linked expectation summary, full audit/status history, "Jump to Expectation" (opens the existing Facility Collections workspace — no new detail view for the expectation itself). |
| **Alert Assignment** | Reassign / claim | Modal/inline from Inbox or Detail; assignee picker scoped to tenant users with `FINANCIAL_MONITORING` access; requires audit note (Section 3/7). |
| **Alert History** | Audit trail view | Read-only list of every status transition for an alert (part of Alert Detail, not necessarily a separate route). |
| **Resolve Alert** | Terminal resolution | Evidence text field (required), submit → `RESOLVED`. |
| **Dismiss Alert** | Terminal non-fix | Reason text field (required), submit → `DISMISSED`. |
| **Threshold Configuration** | Existing capability, needs UI | Per-tenant enable/disable + amount/day thresholds for the 4 configurable types — the API already exists (Section 4 of discovery doc); this is purely new UI. |
| **Alert Settings** | Tenant-level preferences | Which severities trigger the nav badge (Section 5 defaults, tenant-overridable later — not required for v1 if defaults are acceptable). |
| **Alert Metrics** | Owner Dashboard summary widget only | Counts by severity/tenant, aging distribution, resolution rate — read-only rollup, lives in Owner Portal per Section 10, not a biller-facing screen. |

No new design system components are anticipated — these reuse the existing
table/filter/modal patterns already established in the Facility Collections
report and workspace pages.

---

## 10. Permission Matrix

| Action | Required scope/level | Notes |
|---|---|---|
| View alert inbox / detail | `FINANCIAL_MONITORING` VIEW | Same as today's `GET /alerts` |
| Acknowledge / start progress / snooze | `FINANCIAL_MONITORING` EDIT | New endpoints, same scope as `resolve` |
| Resolve / Dismiss | `FINANCIAL_MONITORING` EDIT | Dismiss is a new endpoint, same scope as existing `resolve` |
| Reassign / claim | `FINANCIAL_MONITORING` EDIT | New endpoint, same scope |
| View / edit thresholds | `FINANCIAL_MONITORING` VIEW / EDIT | Unchanged, already implemented |
| Owner Dashboard alert metrics | Owner-role summary scope (existing) | Read-only aggregate query; no access to individual alerts or the Inbox |

**No new scope, resolver, or authorization path is introduced anywhere in
this table.** Every row reuses `_resolve_single_tenant_id(...,
requested_scope="FINANCIAL_MONITORING")` exactly as Priority 1/2 already
validated.

---

## 11. Dead Alert Disposition Plan

| Alert Type | Classification | Rationale | Disposition |
|---|---|---|---|
| `EXPECTATION_MISSING` | **Category A — Valid Future Alert** | Real potential value (flag a billable service period with no expectation record at all), but requires a fundamentally different query pattern (scanning for absence across service periods, not evaluating an existing expectation) — a materially larger design than the other 9 types. | Defer. File as its own follow-up story; do not build in Priority 3. |
| `NOT_BILLED` | **Category D — Required for Priority 3** | `NOT_BILLED` is already a valid, populated value in `FACILITY_RECONCILIATION_STATUSES` on the expectation model itself — the underlying condition already exists and is trivial to wire into `evaluate_alerts_for_expectation` (same pattern as the existing `PARTIALLY_PAID`/`UNMATCHED_PAYMENT`/`OVERPAID` checks). High business value (an un-billed expectation sitting idle is exactly what this platform should surface) at low implementation cost. | **Build in Priority 3** alongside the lifecycle/ownership work — one small additional trigger condition, not a new subsystem. |
| `SECONDARY_PAYER_PAYMENT_MISSING` | **Category A — Valid Future Alert** | Plausible value, but requires new correlation logic between secondary-payer expected vs. received amounts that does not currently exist in the rollup (`compute_rollup` operates on total expectation, not split by payer). Non-trivial new logic. | Defer. File as its own follow-up story. |
| `COLLECTION_FOLLOWUP_REQUIRED` | **Category B — Deprecated** | Its stated purpose (flagging that collection follow-up is needed) is already fully covered by the existing `OVERDUE_30`/`OVERDUE_60`/`OVERDUE_90` tiers. Keeping it would create two overlapping, ambiguous ways to say the same thing. | **Recommend removal** from `ALERT_TYPES` in Priority 3 to stop presenting a configuration option that does nothing and never will. |

No dead enumeration is left floating indefinitely: 1 is removed, 1 is built
now, 2 are explicitly deferred with a named reason and a follow-up-story
recommendation (not silence).

---

## 12. Open Questions

1. **`NOT_BILLED` severity/threshold**: should it be a fixed severity (e.g.
   MEDIUM, analogous to `PARTIALLY_PAID`) or threshold-driven by days since
   the service period ended? Recommend: fixed MEDIUM severity, no threshold,
   to match its simplicity — confirm before implementation.
2. **Snooze duration UI**: fixed presets (1 day / 3 days / 1 week) vs. an
   arbitrary date picker? Recommend presets for v1 to keep the control
   simple; open for decision.
3. **Nav badge severity cutoff** (Section 1/5): confirm the proposed
   HIGH/CRITICAL + `PARTIALLY_PAID` + `FUNDING_SOURCE_NOT_VERIFIED` badge
   set, or specify a different cutoff.
4. **Alert Settings screen**: is a tenant-configurable badge-severity
   override needed for v1, or are the Section 1 defaults acceptable
   platform-wide for now? Recommend deferring the override to a follow-up
   (ties into the same "notification preferences" scope already deferred in
   Section 5).
5. **`COLLECTION_FOLLOWUP_REQUIRED` removal**: confirm removal is acceptable
   (Section 11) rather than keeping it as an inert, unused enum value for
   backward compatibility.

---

## Sign-off

Implementation (backend: `NOT_BILLED` trigger, acknowledge/in-progress/
snooze/dismiss/reassign endpoints, auto-resolve hooks; frontend: Alert
Inbox/Detail/Assignment/Threshold-Config/Owner-metrics screens; tests for
every new transition and the tenant-isolation/permission reuse) begins only
after this document — including the Open Questions in Section 12 — is
approved.
