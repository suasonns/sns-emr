# Priority 3 — Facility Collection Alert Platform: Discovery & Architecture Spec (v1)

Status: DRAFT — pending CEO/Product Owner sign-off on Section 7.
**No implementation code in this branch. Discovery + spec only.**

Priority 3 is reframed per CEO directive from "Build Alerts" to
**"Complete and formalize the existing Alert platform."** A backend alert
system already exists from Priority 2 groundwork. This document inventories
it exactly, identifies the real gaps, and locks the target architecture
before any code is written.

---

## Section 1 — Complete list of existing alert types

`ALERT_TYPES` (`facility_payment_service.py`) declares **14** valid values,
but only **9** are ever actually triggered by
`evaluate_alerts_for_expectation()`. The other **5 are declared-but-dead**
(valid for validation/threshold config, never produced by any code path).

### 1a. Live (triggered) alert types

| Alert type | Trigger condition | Default severity | Threshold-configurable? |
|---|---|---|---|
| `FUNDING_SOURCE_NOT_VERIFIED` | `expectation.expected_funding_source == "NOT_VERIFIED"` | HIGH | No |
| `PARTIALLY_PAID` | `expectation.reconciliation_status == "PARTIALLY_PAID"` | MEDIUM | No |
| `UNMATCHED_PAYMENT_REQUIRES_RECONCILIATION` | `expectation.reconciliation_status == "UNMATCHED_PAYMENT"` | HIGH | No |
| `AMOUNT_MISMATCH` | `expectation.reconciliation_status == "OVERPAID"` | HIGH | No |
| `PAYMENT_NOT_RECEIVED_BY_DUE_DATE` | outstanding > 0 AND `due_date` has passed | HIGH | No |
| `SHARE_OF_COST_OUTSTANDING` | outstanding > 0 AND `responsibility_category == "SHARE_OF_COST"` | MEDIUM | No |
| `OVERDUE_30` | outstanding > 0 AND `days_outstanding >= 30` (default) | MEDIUM | Yes — `threshold_days`, default 30, enabled by default |
| `OVERDUE_60` | outstanding > 0 AND `days_outstanding >= 60` (default) | HIGH | Yes — `threshold_days`, default 60, enabled by default |
| `OVERDUE_90` | outstanding > 0 AND `days_outstanding >= 90` (default) | CRITICAL | Yes — `threshold_days`, default 90, enabled by default |
| `BALANCE_EXCEEDS_THRESHOLD` | outstanding >= `threshold_amount` (default `$0.01`) | MEDIUM | Yes — `threshold_amount`, default `$0.01`, enabled by default |

All 9 are generated only for expectations whose status is NOT in
`{DRAFT, CANCELLED, SUPERSEDED, CLOSED}` — alerts only ever exist against
effective, actionable records (consistent with the Financial Reporting
Dataset rule).

### 1b. Declared but dead (no trigger exists anywhere in the codebase)

| Alert type | Where declared | Trigger status |
|---|---|---|
| `EXPECTATION_MISSING` | `ALERT_TYPES` set only | **No trigger code anywhere.** |
| `NOT_BILLED` | `ALERT_TYPES` set + `facility_payment_expectation.py` status list | **No trigger code anywhere.** |
| `SECONDARY_PAYER_PAYMENT_MISSING` | `ALERT_TYPES` set only | **No trigger code anywhere.** |
| `COLLECTION_FOLLOWUP_REQUIRED` | `ALERT_TYPES` set only | **No trigger code anywhere.** |

These 5 (4 dead + already counted) are valid inputs to
`_upsert_open_alert`'s validation and `update_threshold`, meaning an admin
*could* configure a threshold for e.g. `NOT_BILLED` today and it would simply
never fire. This is a real gap: either wire up trigger logic for these four,
or remove them from `ALERT_TYPES` to stop presenting configuration options
that do nothing. **Recommend: defer new trigger logic to a follow-up story
(these represent net-new alert types, not "completion" of existing ones) and
file a tracked issue; do not silently leave them as dead configuration.**

---

## Section 2 — Existing alert lifecycle states

Current model (`FacilityCollectionAlertThreshold`/`FacilityCollectionAlert`):

```
status ∈ {OPEN, ACKNOWLEDGED, RESOLVED}
```

- `OPEN`: set on creation by `_upsert_open_alert`. Re-evaluation of the same
  condition updates the existing OPEN row in place (amounts/aging refresh)
  rather than creating a duplicate.
- `ACKNOWLEDGED`: **declared in the allowed-values set only — no service
  function, no endpoint, no code path ever sets this value.** Fully dead.
- `RESOLVED`: set only by `resolve_alert()` — requires non-empty
  `resolution_evidence`, stamps `resolved_by`/`resolved_at`, writes to the
  shared audit log.

**There is no automatic transition of any kind.** Once OPEN, an alert stays
OPEN forever unless a human calls `resolve_alert()` — even if the underlying
condition (e.g. the payment that made it `PARTIALLY_PAID`) is later fully
resolved by subsequent payment activity, or even if the expectation itself is
later superseded/cancelled. This is the single most consequential lifecycle
gap identified in this discovery.

---

## Section 3 — Current backend capabilities

| Capability | Exists? | Detail |
|---|---|---|
| Alert generation | ✅ | `evaluate_alerts_for_expectation()` — 9 live trigger conditions |
| Idempotent re-evaluation | ✅ | Upsert keyed on `(tenant_id, expectation_id, alert_type, status="OPEN")` |
| Per-tenant threshold config | ✅ | `FacilityCollectionAlertThreshold`, enable/disable + amount/day overrides, 4 configurable types |
| Alert resolution | ✅ | `resolve_alert()`, evidence required |
| Acknowledge | ❌ | Status value exists, no code sets it |
| Dismiss (distinct from resolve) | ❌ | Not implemented |
| Snooze | ❌ | Not implemented |
| Auto-resolve on condition-clear | ❌ | Not implemented — confirmed gap |
| Auto-close on expectation superseded/cancelled | ❌ | Not implemented — confirmed gap |
| Reassignment | ❌ | `assigned_to` column exists on the model; no endpoint/service function ever sets or changes it |
| Queue / unassigned bucket | ❌ | No concept exists; `assigned_to` is nullable but nothing gives "unassigned" any special meaning |
| Audit trail | ✅ | Every create/update/resolve writes to the shared generic `_write_audit()` ledger (`entity_type="ALERT"`) — same mechanism used for expectation corrections |
| Multi-tenant isolation | ✅ | Alerts are queried/filtered by `tenant_id`; no bespoke isolation logic |
| Notification delivery (email/push/in-app badge) | ❌ | Not implemented anywhere |

---

## Section 4 — Current API endpoints

All under `backend/app/billing/api/facility_payment_router.py`, all reusing
`_resolve_single_tenant_id(..., requested_scope="FINANCIAL_MONITORING")` —
**the exact same tenant-authorization helper as every other Facility
Collections endpoint. No alert-specific resolver, security layer, or
authorization path exists or is proposed.**

| Method | Path | Permission | Behavior |
|---|---|---|---|
| GET | `/billing/facility-payments/alerts` | VIEW (Financial Monitoring) | Tenant-scoped list; optional `status` filter |
| POST | `/billing/facility-payments/alerts/{alert_id}/resolve` | EDIT (Financial Monitoring) | Resolve with required `resolution_evidence` |
| GET | `/billing/facility-payments/alert-thresholds` | VIEW (Financial Monitoring) | Tenant-scoped threshold list, defaults merged in |
| PUT | `/billing/facility-payments/alert-thresholds/{alert_type}` | EDIT (Financial Monitoring) | Update enable/disable + amount/day threshold |

No endpoints exist for: acknowledge, dismiss, snooze, reassign, or any
bulk/queue operation.

---

## Section 5 — Current frontend capabilities

**None.** Full-text search of `sns-emr-frontend/src` for
`FacilityCollectionAlert` and the `/alerts` / `/alert-thresholds` endpoints
returns zero matches. There is no:

- Alert inbox/list page
- Alert badge/count anywhere in Billing nav
- Threshold configuration screen
- Resolve/acknowledge/dismiss UI
- Any linkage from the Facility Collections workspace to alerts

This confirms the CEO's conclusion: **almost the entire remaining Priority 3
surface area is frontend, plus the specific backend lifecycle gaps in
Sections 2–3.**

---

## Section 6 — Gap analysis (what exists vs. what is missing)

| Area | Exists | Missing |
|---|---|---|
| Alert generation | 9 live trigger types, idempotent | 4 dead declared types with no trigger (tracked separately, not built now) |
| Lifecycle | OPEN → RESOLVED (evidence) | ACKNOWLEDGED, DISMISSED, SNOOZED, AUTO_RESOLVED, SUPPRESSED, EXPIRED — none implemented; no auto-transitions of any kind |
| Ownership | `assigned_to` column present, unused | Reassignment endpoint, "queue" concept, audit-on-reassign |
| Thresholds | Full per-tenant CRUD for 4 types | Nothing missing here — complete |
| Auth/tenant isolation | Fully reused from Priority 2 | Nothing missing — do not touch |
| Audit | Generic ledger reused | Nothing missing structurally; new transitions must call it |
| API | 4 endpoints (list, resolve, get/put thresholds) | acknowledge, dismiss, snooze, reassign endpoints |
| Frontend | Nothing | Alert inbox, nav badge, threshold config screen, resolve/dismiss/acknowledge/snooze UI, reassignment UI |
| Notifications | Nothing | In-app only for v1 (see Section 7); email/push explicitly deferred |
| Owner Dashboard | N/A | Summary-metrics-only read rollup (no operational queue) |

**Conclusion: Priority 3 is backend-completion (lifecycle + reassignment +
a handful of endpoints) plus new frontend, not a new platform.**

---

## Section 7 — Final Alert Architecture Spec (locked pending sign-off)

### 7.1 Lifecycle states — LOCKED per CEO's proposed model

```
OPEN
  │
  ├─ acknowledge ──────────────> ACKNOWLEDGED
  │                                  │
  │                                  ├─ start work ──> IN_PROGRESS
  │                                  │                     │
  ├───────────────── resolve(evidence) ───────────────────┤
  ├───────────────── dismiss(reason)   ───────────────────┤
  ├───────────────── snooze(until)     ──> SNOOZED ────────┤ (auto-returns to OPEN at/after `snoozed_until`)
  │
  ├─ system: condition cleared ───────> AUTO_RESOLVED (evidence = system note, audited)
  ├─ system: expectation superseded/cancelled ─> AUTO_RESOLVED (evidence = system note, audited)
  └─ tenant disables alert_type via threshold ─> (no new OPEN alerts created; existing OPEN rows for that type transition to SUPPRESSED)

RESOLVED / DISMISSED / AUTO_RESOLVED / SUPPRESSED / EXPIRED = terminal.
```

Definitions (locking the CEO's semantics precisely):

- **OPEN** — new condition detected by `evaluate_alerts_for_expectation`.
- **ACKNOWLEDGED** — a biller has seen it and is nominally responsible; no
  evidence required; purely informational triage state.
- **IN_PROGRESS** — optional, explicit "work started" sub-state after
  acknowledgement; no evidence required; purely informational.
- **SNOOZED** — temporarily hidden from the default inbox view with a
  `snoozed_until` timestamp; a scheduled/lazy check (evaluated at next
  `evaluate_alerts_for_expectation` run or inbox load, whichever is simpler
  to implement reliably) returns it to `OPEN` once `snoozed_until` passes. No
  new backend job/scheduler is introduced — reuses the same evaluation path
  that already runs whenever an expectation is touched.
- **DISMISSED** — user determined the alert is not actionable; **requires a
  reason**, stored in `resolution_evidence`, audited; distinct terminal
  status from `RESOLVED` so reporting never conflates "we fixed it" with "we
  chose to ignore it."
- **RESOLVED** — underlying condition was corrected by user action; evidence
  required (unchanged from today).
- **AUTO_RESOLVED** — system detected the underlying condition (or the
  expectation itself) no longer applies; evidence is a system-authored note;
  **audit entry required** (reuses the existing `_write_audit` ledger, no new
  table).
- **SUPPRESSED** — the tenant disabled that `alert_type` via
  `alert-thresholds`; existing OPEN alerts of that type are transitioned to
  SUPPRESSED (not silently left OPEN/orphaned, and not deleted — preserves
  audit history).
- **EXPIRED** — reserved for a future case where an alert's relevance has a
  hard time boundary unrelated to the expectation's own status (none of the
  9 live alert types currently need this; defined now so the vocabulary
  exists, but no code path produces it in v1).

### 7.2 Ownership model — LOCKED per CEO's recommendation

**Single Assignee + Queue.**

- Every alert has exactly one optional `assigned_to` (single user, within the
  owning tenant) — no multi-assignee.
- `assigned_to IS NULL` is the **queue**: visible to every biller with
  `FINANCIAL_MONITORING` `VIEW` access to that tenant, and any of them with
  `EDIT` access may claim it (self-assign) or act on it directly without
  claiming it first.
- Reassignment is a first-class action, **requires an audit note** (reuses
  `_write_audit`, `entity_type="ALERT"`, `field_name="assigned_to"`).
- Alert ownership is tenant-scoped only — no cross-agency assignment, no
  billing-provider-level assignment, no owner-user assignment. This matches
  the existing Facility Collections authorization model exactly.
- External billing organizations: same as any other biller — if their user
  account has `FINANCIAL_MONITORING` access to the tenant (already how
  Billing Provider access works today), they see and can be assigned alerts
  like any in-tenant biller. No new concept required.
- Owner users: **do not** receive individual alerts or appear in the
  assignee list — consistent with Owner Dashboard boundary (7.5).

### 7.3 Auto-resolution — LOCKED

Two system-triggered `AUTO_RESOLVED` paths, both firing inside
`evaluate_alerts_for_expectation` (the same function already called whenever
an expectation is recomputed — no new scheduler):

1. **Condition-cleared auto-resolve**: for each of the 9 live alert types, if
   an existing OPEN/ACKNOWLEDGED/IN_PROGRESS/SNOOZED alert's trigger
   condition is no longer true when the expectation is re-evaluated, that
   alert transitions to AUTO_RESOLVED with a system-authored evidence string
   (e.g. `"Auto-resolved: reconciliation status changed to PAID."`).
2. **Expectation-superseded/cancelled auto-resolve**: any still-open alert
   referencing an expectation that has itself transitioned to
   `SUPERSEDED`/`CANCELLED`/`CLOSED` is auto-resolved with
   `"Auto-resolved: expectation superseded/cancelled."` — closing the gap
   where `evaluate_alerts_for_expectation` currently returns `[]` for those
   statuses but leaves prior alerts dangling OPEN.

Both are audited exactly like a manual resolve.

### 7.4 Evidence & audit requirements

| Transition | Evidence required? | Audited? |
|---|---|---|
| OPEN → ACKNOWLEDGED | No | Yes (status change) |
| ACKNOWLEDGED → IN_PROGRESS | No | Yes |
| any → SNOOZED | No (optional note) | Yes, includes `snoozed_until` |
| any → DISMISSED | **Yes** (reason) | Yes |
| any → RESOLVED | **Yes** (evidence) | Yes (unchanged from today) |
| any → AUTO_RESOLVED | System note (no user input) | **Yes, mandatory** |
| any → SUPPRESSED | No (system-driven by threshold change) | Yes |
| reassignment | **Yes** (audit note) | Yes |

No new audit table — all of the above write through the existing generic
`_write_audit(entity_type="ALERT", ...)` ledger.

### 7.5 Permissions — LOCKED (unchanged from prior draft)

Reuse `FINANCIAL_MONITORING` scope exactly as implemented today:
`VIEW` = list/see; `EDIT` = acknowledge/snooze/dismiss/resolve/reassign/edit
thresholds. **No new resolver, security layer, permission engine, or
authorization path** — per CEO's explicit instruction.

### 7.6 Notifications — LOCKED for v1

In-app only: Alert Inbox page + an OPEN/unassigned-queue count badge on the
Billing nav. Email/SMS/push explicitly deferred to a follow-up story.

### 7.7 Owner Dashboard boundary — LOCKED (approved as previously drafted)

Owner Portal may show only aggregate metrics (counts by severity/tenant,
aging summaries) via a read-only rollup query. It never surfaces the
operational queue, assignment, or resolution workflow. Alert execution stays
entirely inside the Billing Portal operational workspace.

### 7.8 Explicit non-goals for v1

- Building trigger logic for the 4 dead alert types (`EXPECTATION_MISSING`,
  `NOT_BILLED`, `SECONDARY_PAYER_PAYMENT_MISSING`,
  `COLLECTION_FOLLOWUP_REQUIRED`) — tracked as a separate follow-up, since
  these are net-new alert types, not completion of the existing platform.
- Task-system integration — no task/ticket system exists in this codebase to
  integrate with.
- Multi-assignee / queue-as-a-formal-entity (a real `Queue` model) — the
  `assigned_to IS NULL` convention covers the "queue" requirement without a
  new table.
- Email/push notification delivery and digest scheduling.
- `EXPIRED` alert generation — vocabulary defined, no trigger implemented.

---

## Implementation NOT authorized

Per CEO directive, this document is discovery + locked architecture only.
Implementation (backend lifecycle/reassignment endpoints, frontend Alert
Inbox, Owner Dashboard summary widget, and tests) begins only after explicit
sign-off on Section 7.
