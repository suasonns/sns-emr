# Priority 3 — Facility Collection Alerts: Architecture Specification (v1)

Status: DRAFT — pending CEO/Product Owner approval. No implementation in this
branch until this document is signed off.

## 0. Critical scoping finding: this is NOT greenfield

Before answering the architecture questions, a codebase audit found that a
substantial part of the "Priority 3 Alert System" backend **already exists**,
built and tested during Priority 2 groundwork. This section documents exactly
what exists today so we do not redesign or reimplement it.

### Already implemented (backend)

- **Model**: `FacilityCollectionAlert` (`backend/app/billing/models/facility_collection_alert.py`)
  - Fields: `tenant_id`, `patient_id`, `facility_payment_expectation_id`,
    `alert_type`, `severity`, `expected_amount`, `received_amount`,
    `outstanding_amount`, `due_date`, `days_outstanding`, `status`,
    `assigned_to`, `resolution_evidence`, `resolved_by`, `resolved_at`,
    `created_at`, `updated_at`.
  - `status` ∈ `{OPEN, ACKNOWLEDGED, RESOLVED}` (`ACKNOWLEDGED` is declared in
    the enum but **no code path currently sets it** — see Open Question 2).
  - `severity` ∈ `{LOW, MEDIUM, HIGH, CRITICAL}`.
- **Model**: `FacilityCollectionAlertThreshold` — per-tenant, per-alert-type
  `enabled` / `threshold_amount` / `threshold_days`, unique on
  `(tenant_id, alert_type)`. Falls back to `DEFAULT_ALERT_THRESHOLDS` when no
  tenant override row exists.
- **Alert types already generated** by
  `evaluate_alerts_for_expectation()` (`facility_payment_service.py:1361`):
  `FUNDING_SOURCE_NOT_VERIFIED`, `PARTIALLY_PAID`,
  `UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION`, `AMOUNT_MISMATCH`,
  `PAYMENT_NOT_RECEIVED_BY_DUE_DATE`, `SHARE_OF_COST_OUTSTANDING`,
  `OVERDUE_30` / `OVERDUE_60` / `OVERDUE_90` (threshold-driven),
  `BALANCE_EXCEEDS_THRESHOLD` (threshold-driven).
- **Idempotent upsert**: `_upsert_open_alert()` keys on
  `(tenant_id, expectation_id, alert_type, status="OPEN")` — re-evaluating an
  expectation updates the existing OPEN alert's amounts/aging in place rather
  than spawning duplicates.
- **Exclusion from non-effective expectations**: `evaluate_alerts_for_expectation`
  returns `[]` immediately for `DRAFT`/`CANCELLED`/`SUPERSEDED`/`CLOSED`
  expectations — alerts only ever exist against effective, actionable records.
  This is consistent with the Priority 2 Financial Reporting Dataset rule.
- **Resolution**: `resolve_alert()` — requires non-empty
  `resolution_evidence`, sets `status="RESOLVED"`, `resolved_by`, `resolved_at`,
  writes an audit log entry via the shared `_write_audit()` mechanism (same
  audit infrastructure used for expectation corrections/activations).
- **API** (`facility_payment_router.py`):
  - `GET /billing/facility-payments/alerts?tenant_id=&status=` — tenant-scoped
    list, optional status filter.
  - `POST /billing/facility-payments/alerts/{alert_id}/resolve` — requires
    `EDIT` permission level under `requested_scope="FINANCIAL_MONITORING"`.
  - `GET /billing/facility-payments/alert-thresholds` / `PUT
    /billing/facility-payments/alert-thresholds/{alert_type}` — tenant-scoped
    threshold configuration, `VIEW`/`EDIT` permission levels respectively.
  - **Tenant isolation reuses the exact same `_resolve_single_tenant_id(...,
    requested_scope=...)` authorization helper as every other Facility
    Collections endpoint** — no new resolver, no special alert authorization
    path. This already satisfies the CEO's multi-tenant-reuse mandate.
- **Tests**: `test_overdue_90_alert_default_and_custom_thresholds`,
  `test_alert_resolution_requires_evidence` (in
  `test_facility_payment_visibility.py`, part of the 34/34 passing suite).

### NOT implemented (the real Priority 3 scope)

- **Any frontend UI.** There is no alert inbox/queue page, no alert badge/count
  anywhere in the biller nav, no threshold-configuration screen. Confirmed via
  full-text search of `sns-emr-frontend/src` — zero references to
  `FacilityCollectionAlert` or the `/alerts` endpoints on the frontend today.
- **Acknowledge workflow.** The `ACKNOWLEDGED` status value exists in the
  model's allowed set but no service function or endpoint ever sets it.
- **Auto-resolution when the underlying condition clears.**
  `evaluate_alerts_for_expectation` only ever creates/refreshes alerts for
  conditions that are *currently* true. If a `PARTIALLY_PAID` alert is OPEN
  and the expectation is later fully paid, nothing today automatically
  resolves that alert — it stays OPEN until a human manually resolves it with
  evidence, even though the condition is gone. **This needs an explicit
  decision (Open Question 1).**
- Snooze, dismiss (as distinct from resolve), reassignment, recurrence,
  notification/inbox delivery, and any task-linkage — none of this exists yet.

Given the above, Priority 3 implementation work is almost entirely
**frontend + a small, targeted set of backend additions** for the genuine
gaps below — not a backend rebuild.

## 1. Alert ownership model

**Decision: Agency-level ownership, not individual-user ownership, as the
default.**

- An alert belongs to the tenant (agency) that owns the underlying
  `FacilityPaymentExpectation`, identically to every other Facility
  Collections record. This matches the existing `tenant_id`-scoped model and
  requires no new authorization concept.
- `assigned_to` (already a column on the model, currently unused by any
  endpoint) becomes an **optional** pointer to a specific biller *within* that
  tenant, for workload distribution — not a replacement for tenant ownership.
  Any biller with `FINANCIAL_MONITORING` `VIEW`/`EDIT` access to the tenant can
  see and act on an alert whether or not it is assigned to them; assignment is
  a triage/organization aid, not an access-control gate.
- There is no "specific queue" concept in this system (no ticketing-style
  queues elsewhere in the app) — the existing Facility Collections report +
  new Alert Inbox, filtered by status/severity/assignee, plays that role.

## 2. Alert lifecycle

**Decision: extend, don't replace, the existing 3-state model.**

Current: `OPEN → RESOLVED` (evidence required).

Proposed v1 lifecycle:

```
OPEN ──acknowledge──> ACKNOWLEDGED ──resolve(evidence)──> RESOLVED
  │                        │
  └──────resolve(evidence)─┘
  │
  └──system auto-resolve (condition cleared)──> RESOLVED (evidence = system-generated note)
```

- `ACKNOWLEDGED` becomes real: a lightweight "seen, working on it" transition
  requiring no evidence (unlike resolve). Purely informational triage state;
  does not block resolving directly from `OPEN`.
- **Resolved vs. Dismissed vs. Expired vs. Cancelled vs. Suppressed** — per
  the CEO's explicit question, these must mean distinct things, so v1 defines:
  - **RESOLVED**: the underlying financial condition was addressed (payment
    posted, funding source verified, reconciliation completed) — evidence
    required, exactly as today.
  - **DISMISSED** *(new)*: a biller determined the alert is not actionable /
    not applicable (e.g. a known, accepted delay) without the underlying
    condition changing. Requires a reason (same evidence-required pattern as
    resolve, reusing `resolution_evidence` field, but recorded as a distinct
    terminal status so reporting can separate "we fixed it" from "we chose to
    ignore it").
  - **AUTO-RESOLVED** *(new, system-generated)*: the underlying condition
    cleared on its own (e.g. payment posted) before a human acted. Recorded
    via the same `RESOLVED` status with a system-authored
    `resolution_evidence` (e.g. `"Auto-resolved: reconciliation status
    changed to PAID."`) rather than a 5th status value, to avoid fragmenting
    reporting between "resolved" states.
  - **EXPIRED / CANCELLED**: **not adopted in v1.** Alerts here are generated
    from a live rollup of an effective expectation; if the expectation itself
    is cancelled/superseded/closed, `evaluate_alerts_for_expectation` already
    returns no alerts for it — but existing OPEN alerts referencing that
    expectation are not currently auto-closed either (same gap as auto-resolve,
    same fix). We propose folding this into the same auto-resolve mechanism
    (`"Auto-resolved: expectation superseded/cancelled."`) rather than adding
    two more terminal statuses whose meaning would overlap heavily with
    resolve/dismiss.
  - **SUPPRESSED**: not a per-alert status — already covered at the
    configuration layer by `FacilityCollectionAlertThreshold.enabled=false`,
    which prevents an alert type from being generated for a tenant at all. No
    additional status value needed.
- **Recurrence**: alerts do not need an explicit "recurrence" concept — the
  existing upsert-on-OPEN behavior already means a new OPEN alert of the same
  type is naturally created the next time the condition is evaluated true
  again after a prior one was resolved/dismissed (since the upsert only
  matches existing rows with `status="OPEN"`). No separate recurrence engine
  needed.

## 3. Alert permissions

**Decision: reuse `FINANCIAL_MONITORING` scope exactly as already
implemented — no new permission scope, no new resolver.**

- `VIEW`: list alerts, view thresholds.
- `EDIT`: acknowledge / resolve / dismiss alerts, reassign within tenant,
  edit thresholds.
- No new role is introduced. This directly satisfies the CEO's multi-tenant
  rule ("reuse existing authorization infrastructure, no shortcuts, no new
  resolver, no special alert authorization path").

## 4. Alert categories

Categories = the existing `alert_type` enum (9 values, listed in §0), grouped
for UI purposes only (no schema change) into:

- **Documentation** — `FUNDING_SOURCE_NOT_VERIFIED`
- **Reconciliation** — `PARTIALLY_PAID`, `UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION`,
  `AMOUNT_MISMATCH`
- **Aging / Overdue** — `PAYMENT_NOT_RECEIVED_BY_DUE_DATE`, `OVERDUE_30`,
  `OVERDUE_60`, `OVERDUE_90`
- **Balance** — `SHARE_OF_COST_OUTSTANDING`, `BALANCE_EXCEEDS_THRESHOLD`

New categories/types can be added later without a lifecycle or permission
change, since both are orthogonal to `alert_type`.

## 5. Notification strategy

**Decision for v1: in-app only. No email/SMS/push in this phase.**

- An **Alert Inbox** page in the Billing Portal (see §8) is the v1
  notification surface: sortable/filterable by status, severity, category,
  assignee, tenant (for cross-agency billers).
- A small unread/OPEN count badge on the Billing nav "Facility Collections"
  (or a new "Alerts" nav entry — see §8) satisfies the "billers must not miss
  this" requirement without building an email/notification pipeline this
  phase. Email/digest notification is explicitly deferred to a follow-up
  story, not because it isn't valuable, but because it introduces a new
  cross-cutting concern (notification preferences, delivery infra) outside
  this PR's scope discipline.

## 6. Resolution workflow

1. Biller opens Alert Inbox, filters to `OPEN` (default view).
2. Biller may **Acknowledge** (no evidence) to signal "in progress," or go
   straight to **Resolve** / **Dismiss** (evidence required either way).
3. Resolving/dismissing writes to the existing `_write_audit()` ledger
   (entity_type="ALERT"), identical to today's `resolve_alert()`.
4. A "Jump to Expectation" action opens the Facility Collections Expectation
   Workspace for the linked `facility_payment_expectation_id`, reusing the
   existing selection/workspace behavior (including the just-fixed
   selection-eviction fix) rather than building a second detail view.

## 7. Audit model

**Decision: reuse the existing generic audit log — no new audit table.**

- All alert state transitions (create/update via upsert, acknowledge,
  resolve, dismiss, auto-resolve, reassign) are written through the same
  `_write_audit(entity_type="ALERT", ...)` helper already used for
  expectation corrections and activations. This keeps a single, queryable
  audit trail across Facility Collections rather than fragmenting it per
  feature.

## 8. Frontend & Owner Dashboard boundary

- New page: `FacilityCollectionAlertsPage.tsx` under
  `sns-emr-frontend/src/pages/billing/`, added to the Billing Portal nav
  (alongside Facility Collections), **not** the Owner Portal — consistent
  with the already-approved separation of Billing operational workflows from
  Owner Portal platform administration.
- Owner Dashboard receives **summary metrics only** (e.g. count of OPEN alerts
  by severity per tenant, aggregate aging), never the operational alert
  queue/resolve workflow itself — matching the CEO's explicit Owner Dashboard
  warning. This is a read-only rollup query against `FacilityCollectionAlert`,
  not a new dataset.

## 9. Alert ↔ task relationship

There is no existing task-tracking system in this codebase to integrate with
(no `Task`/`Ticket` model found in the repository). Alerts are therefore
**not** linked to a task entity in v1. "Jump to Expectation" (§6) plus the
Alert Inbox itself serves as the actionable work queue. If a task system is
introduced later, alert→task linkage should be added as its own follow-up
story rather than speculatively built now.

## 10. Explicit non-goals for v1 (deferred, tracked separately if approved)

- Email/SMS/push notifications and digest scheduling.
- Cross-tenant alert sharing/escalation.
- Task-system integration (no task system currently exists).
- `EXPIRED` / `CANCELLED` as distinct terminal statuses (folded into
  auto-resolve per §2).

## 11. Summary of decisions requiring explicit sign-off

| # | Question | Proposed decision |
|---|---|---|
| 1 | Auto-resolve alerts when condition clears? | Yes — new auto-resolve path in `evaluate_alerts_for_expectation`, recorded as `RESOLVED` with system-authored evidence. |
| 2 | Activate unused `ACKNOWLEDGED` status? | Yes — evidence-free triage transition. |
| 3 | Add `DISMISSED` as a 4th terminal status? | Yes — distinct from `RESOLVED` for reporting accuracy. |
| 4 | Add `EXPIRED`/`CANCELLED` statuses? | No — folded into auto-resolve. |
| 5 | Alert ownership: tenant vs. individual? | Tenant-owned; `assigned_to` optional/advisory only. |
| 6 | New permission scope for alerts? | No — reuse `FINANCIAL_MONITORING`. |
| 7 | Notification channel for v1? | In-app inbox + nav badge only; email/push deferred. |
| 8 | New audit table? | No — reuse existing generic audit log. |
| 9 | Owner Dashboard alert visibility? | Summary metrics only, never the operational queue. |
| 10 | Task-system linkage? | None — no task system exists to link to. |

Pending approval of §11, implementation will proceed as:
1. Backend: acknowledge/dismiss endpoints + auto-resolve hook + reassignment
   endpoint (small, additive changes to the existing service/router).
2. Frontend: Alert Inbox page + nav entry/badge + threshold config screen.
3. Owner Dashboard: read-only summary widget.
4. Tests for every new transition and the tenant-isolation/permission reuse.
