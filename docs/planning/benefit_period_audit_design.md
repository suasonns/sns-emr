# Benefit Period Audit Trail Design (Phase 38)

Status: **DESIGN ONLY. NOT IMPLEMENTED.** No code changed. Modeled directly on `CertificationStatusEvent`
(`app/models/certification.py:77-104`) and `AdmissionStatusHistory` — both real, working, proven
patterns already in this codebase, reused here rather than inventing a new pattern.

## Proposed table: `BenefitPeriodStatusEvent`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | Standard |
| `tenant_id` | UUID, not null, indexed | Matches existing tenant-scoping convention |
| `benefit_period_id` | UUID FK → `benefit_periods.id`, not null, indexed | Cascades on delete, mirroring `CertificationStatusEvent.certification_id` |
| `patient_id` | UUID FK → `patients.id`, not null, indexed | Denormalized for query performance, matching the pattern in other event tables |
| `event_type` | String, not null | One of: `CREATED`, `UPDATED`, `ROLLED`, `CLOSED`, `CORRECTED`, `REOPENED` (see below — note two of these have no corresponding code path today and would need one built first) |
| `actor_user_id` | UUID FK → `users.id`, nullable | The user who performed the action; null only for a system/background actor, never for a real RN/Administrator-initiated call |
| `actor_role` | String, nullable | Authenticated role at the time of action (mirrors `Certification.signed_by_role`'s "never client-supplied" discipline) |
| `occurred_at` | DateTime (tz-aware), not null | When the action happened, distinct from `created_at` on the event row itself |
| `reason` | Text, nullable | Required for `CORRECTED`/`REOPENED` at the application layer even if nullable at the schema layer (matches `CertificationStatusEvent.reason` being nullable but conventionally always populated for non-automatic transitions) |
| `old_value` | JSON/Text, nullable | Snapshot of the changed fields before the event (e.g. `is_current`, `end_date`) |
| `new_value` | JSON/Text, nullable | Snapshot after |
| `automatic` | Boolean, not null, default false | Mirrors `CertificationStatusEvent.automatic` — distinguishes system-triggered rollovers from manual ones, if any automatic trigger is ever added |

## Required events

| Event | Actor | Timestamp | Reason | Old Value | New Value | Retention |
|---|---|---|---|---|---|---|
| BenefitPeriod Created | RN/Administrator via `POST /benefits/` (role already gated, confirmed) | Yes | Optional — creation is usually self-explanatory (e.g. "initial election") | N/A (no prior row) | Full new-row snapshot | Same retention policy as `CertificationStatusEvent` — never deleted, append-only |
| BenefitPeriod Updated | **No code path exists today** — flagged as a prerequisite: this event type cannot be implemented until an update endpoint exists at all (confirmed in `benefit_period_engine_review.md` Phase 12/13 addendum: only `POST`/`GET` exist) | N/A until built | N/A until built | N/A | N/A | N/A |
| BenefitPeriod Rolled | RN/Administrator via `POST /benefits/` with `benefit_type=RECERT` | Yes | Optional, but should record which certification (if the gating fix from Phase 9 is implemented) authorized the rollover | Prior current BP's `is_current`/`end_date` | New BP's full snapshot | Same as above |
| BenefitPeriod Closed | Implicit side effect of the *next* rollover (setting `is_current=False`) — should become its own explicit event even though it remains a side effect of the same call, not a separate endpoint | Yes | Optional | `is_current=True`, `end_date=NULL` (if previously open-ended) | `is_current=False`, `end_date=<computed>` | Same as above |
| BenefitPeriod Corrected | **No code path exists today** — same prerequisite gap as "Updated"; this is the event type CDPH's structured-addendum expectations would apply to most directly if/when a correction capability is built (should require `reason`, non-null, at the application layer, matching the `Amendment` model's already-proven `reason` non-nullable convention) | N/A until built | Required once built | N/A | N/A | N/A |
| BenefitPeriod Reopened | **No code path exists today** — would only be needed if a Corrected/Closed reversal capability is ever built; not currently a real operation | N/A until built | N/A until built | N/A | N/A | N/A |

## Design notes
- Two of the six requested event types (`Updated`, `Corrected`) and the reversal type (`Reopened`)
  cannot be designed as "audit events for an existing action" because **no such action exists in the
  codebase today** — designing their audit shape ahead of the action itself is reasonable groundwork,
  but building the audit table alone does not close any real gap until the corresponding
  create/rollover-adjacent endpoints are also built. This mirrors the same discipline used for
  Certification, where the audit table exists because the actions (DRAFT→PENDING_SIGNATURE→FINALIZED)
  already exist.
- Minimum viable version: implement `CREATED`, `ROLLED`, and `CLOSED` only (matching real, existing
  code paths), by adding one `db.add(BenefitPeriodStatusEvent(...))` call inside the existing
  `rollover_benefit_period` transaction, populated with the authenticated user/role passed down from
  `app/api/benefits.py` (which already has `current_user` via its existing auth dependency — no new
  plumbing required, only using data already available at the call site).
- `created_by` population on `BenefitPeriod` itself (a simpler, complementary fix) requires no new
  table at all — just passing `created_by=` into the existing `BenefitPeriod(...)` constructor call,
  using the same `current_user` already available in `app/api/benefits.py`.

No production code has changed. This is a design document only.
