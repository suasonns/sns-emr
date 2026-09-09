# Certification-Gated Eligibility Model (Phase 11)

Status: **DESIGN ONLY. NOT IMPLEMENTED.** No code changed. This document specifies a target state
model; it does not describe current behavior (see `eligibility_integrity_review.md` for current
behavior).

Base states reuse the real, already-existing `Certification.status` values (`DRAFT`,
`PENDING_SIGNATURE`, `FINALIZED`, `SUPERSEDED` — `app/models/certification.py:44-47`) plus derived
states computed from `expires_at` and elapsed time, which do not currently exist as stored statuses.

---

## State definitions

### 1. Draft Certification (`status=DRAFT`) — *exists today*
- **Allowed**: continue editing physician narrative/supporting evidence; move to Pending Signature.
- **Blocked**: cannot be referenced as satisfying any benefit-period gate; cannot support a claim.
- **Benefit Period impact**: none — should not authorize creation or advancement of any period.
- **Billing impact**: none — cannot be counted by `_has_finalized_certification`.
- **Claim impact**: none.

### 2. Pending Signature (`status=PENDING_SIGNATURE`) — *exists today*
- **Allowed**: physician signature action (transitions to Finalized).
- **Blocked**: same as Draft — not a gating certification.
- **Benefit Period impact**: none.
- **Billing impact**: none.
- **Claim impact**: none.

### 3. Finalized Certification (`status=FINALIZED`, `signed_at IS NOT NULL`) — *exists today*
- **Allowed**: gates the benefit period it references (target state); satisfies billing-readiness
  check (already true today).
- **Blocked**: cannot be re-edited (narrative fields should be immutable once finalized — not verified
  in this pass, flagged as an open question).
- **Benefit Period impact (target)**: an `INITIAL` cert should permit creation of BP1; a `RECERT` cert
  should permit advancement to the next period.
- **Billing impact**: satisfies `_has_finalized_certification` (already true today).
- **Claim impact**: satisfies the certification blocker in `check_patient_billing_readiness`.

### 4. Expired Certification (`status=FINALIZED`, `expires_at < now()`) — *derived, not stored*
- **Allowed**: remains a valid historical/legal record (per the model's own docstring: "a signed CTI
  remains a valid legal record after its benefit period ends").
- **Blocked (target)**: should **not** authorize creation/advancement of a *new* benefit period — an
  expired cert only proves the period it originally covered was authorized, not that the next one is.
- **Benefit Period impact (target)**: does not satisfy the gate for the *next* rollover; a fresh
  Recertification is required.
- **Billing impact**: today, `_has_finalized_certification` checks `status='FINALIZED'` and
  `signed_at IS NOT NULL` for the *specific* `benefit_period_id` being billed — it does not check
  `expires_at`. Because the cert is scoped to the period it was signed for, this is likely correct
  as-is for billing the *original* period, but the "expired" derived state is what should block
  *forward* rollover.
- **Claim impact**: none directly (claims target the period the cert was signed for, not future periods).

### 5. Recert Due (derived: `expires_at` within N days, e.g. the existing 15-day `cti_expiring`
   dashboard window — `dashboard_service.py:1135-1144`) — *partially exists today (dashboard signal only)*
- **Allowed**: normal patient care continues; RN/physician workflow should surface a task/reminder
  (an `IDG_REVIEW` task is already seeded on rollover, but nothing is currently seeded specifically for
  recert-due).
- **Blocked**: none yet — this is a warning state, not a hard stop.
- **Benefit Period impact**: none yet (current period continues).
- **Billing impact**: none yet — current period's claims are unaffected.
- **Claim impact**: none yet.

### 6. Recert Overdue (derived: `expires_at < now()` with no successor `Certification` in
   `DRAFT`/`PENDING_SIGNATURE`/`FINALIZED` for the next period) — *does not exist today*
- **Allowed (target)**: continued clinical care; should generate a hard compliance flag.
- **Blocked (target)**: should block rollover to the next benefit period (this is the direct target
  fix for the Q1/Q2 gap in `eligibility_integrity_review.md`) and should independently surface in
  billing-readiness as a distinct blocker from generic "missing certification" (helps billers/auditors
  distinguish "never certified" from "certification lapsed").
- **Benefit Period impact (target)**: rollover attempts should raise, not silently create the next period.
- **Billing impact**: existing `_has_finalized_certification` already indirectly catches this for the
  *next* period (no FINALIZED cert exists for it yet), but does not catch it for `is_current` periods
  that were created without ever having a valid cert — because the period already exists.
- **Claim impact**: any claim against a period created without gating should still be blocked today by
  the existing billing-readiness check — confirmed working (Q7 above).

### 7. Certification Replaced (`status=SUPERSEDED`, `superseded_by_id` set) — *exists today*
- **Allowed**: remains a queryable historical record via `superseded_by_id`/`superseded_at`
  (`certification.py:70-72`).
- **Blocked**: cannot itself satisfy any current gate (superseded by definition).
- **Benefit Period impact**: none (historical only).
- **Billing impact**: should not satisfy `_has_finalized_certification` for a period that requires the
  superseding cert instead — not verified whether the query at `billing_readiness_service.py:129-152`
  excludes `SUPERSEDED` explicitly; it filters `status = 'FINALIZED'`, and `SUPERSEDED` is a distinct
  literal, so this is already correctly excluded by construction.
- **Claim impact**: none.

---

## Summary table

| State | Gates BP creation? (target) | Satisfies billing-readiness? (today) | Audited transition? (today) |
|---|---|---|---|
| Draft | No | No | Yes (`CertificationStatusEvent`) |
| Pending Signature | No | No | Yes |
| Finalized | **Yes (not implemented)** | Yes | Yes |
| Expired | No (for forward rollover) | Yes, for its own period | N/A (derived) |
| Recert Due | No (warning only) | Yes, for its own period | N/A (derived) |
| Recert Overdue | **Should block (not implemented)** | N/A | N/A (derived) |
| Superseded | No | No (correctly excluded) | Yes |

This model requires **no new database columns** for the stored states (`DRAFT`/`PENDING_SIGNATURE`/
`FINALIZED`/`SUPERSEDED` already exist and are already audited). The derived states (Expired, Recert
Due, Recert Overdue) can be computed at query time from `expires_at`, mirroring the existing
`cti_expiring` dashboard query pattern — no new storage is strictly required for those either, though
a "Recert Overdue" specific dashboard/blocker label does not exist yet and would need to be added as
new (labeling-only) logic when this is built.
