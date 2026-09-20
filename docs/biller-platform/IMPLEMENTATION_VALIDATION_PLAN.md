# Implementation Validation Plan

## Status

**PLANNING ONLY.** For every implementation sequence defined in
`IMPLEMENTATION_PLAN.md`, documents functional, data, security,
authorization, audit, reporting, export, and roll-forward validation
requirements. **No schema. No migrations. No code. No API. No UI.**

---

## 1. Functional Validation

- Milestone 1 (Foundation): permission checks and organization/
  assignment/scope CRUD behave per existing documented business
  rules with no schema change.
- Milestone 2 (Coverage): `PatientInsurance`/`PatientPayer` link
  (once implemented in a future authorized phase) does not alter
  either model's existing read/write behavior for its own consumers.
- Milestone 3 (Revenue Cycle Core): claims continue to source the
  837I payer/subscriber block from `PatientPayer`; payments and
  remittances continue to post/reconcile as today.
- Milestone 4 (Exceptions): denials/appeals/NOE/CAP creation paths
  unaffected by upstream changes.
- Milestone 5 (Facility Financials): full Room & Board chain
  functions end-to-end unchanged.
- Milestone 6 (Visibility): audit/reporting/settings reflect existing
  data accurately, with the approved "Medicare Part A Hospice" label.

## 2. Data Validation

- Verified record counts (from `LEGACY_BILLING_SCHEMA_INVENTORY.md`)
  serve as the baseline snapshot for every milestone; any future
  implementation phase must re-verify these counts are unchanged
  except through normal application writes, never through migration
  or backfill activity not separately authorized.
- No orphaned foreign key is introduced by the future
  `PatientInsurance`↔`PatientPayer` link or the optional
  `PayerEligibilityCheck`↔`EligibilityVerification` cross-reference.

## 3. Security Validation

- `PLATFORM_BILLING` vs. `BILLING` role distinction remains intact and
  is not weakened by any epic's implementation.
- `BillingProviderAgencyServiceScope.permission_level` (`VIEW`/`EDIT`)
  continues to gate access correctly after the Agency Assignment
  delegation change (Epic 3).

## 4. Authorization Validation

- After the future `owner_admin.py` delegation change (Epic 3, Story
  3.1), `BillingProviderAgencyAssignment` has exactly one write path;
  Owner Platform's administrative action still succeeds functionally
  but no longer writes the table directly.
- No epic grants Owner Platform new operational billing-write
  authority beyond the approved delegation model.

## 5. Audit Validation

- `AuditLog` and `facility_payment_audit_log` remain append-only
  across every epic; no update/delete path is introduced.
- Every new write path introduced by future implementation (e.g., the
  delegation change in Epic 3) is confirmed to still produce the same
  audit trail entries as before, or an equivalent entry, not a gap.

## 6. Reporting Validation

- Reporting surfaces (Epic 15) read existing tables only; no reporting
  epic introduces a write path or a new authoritative table.
- The open "duplicate export authority — NOT FULLY VERIFIED" item
  (Schema Design Review Section 7) is resolved (verified, not assumed)
  before Epic 15's reporting stories are finalized.

## 7. Export Validation

- Claim export (`claim_export_service.py`) 837I payer/subscriber block
  generation is validated unchanged after any Patient Coverage
  Authority implementation work.
- No new export-authority model is introduced without a separate,
  dedicated future review (Schema Design Review Section 6).

## 8. Roll-Forward Validation

- Every future migration (once separately authorized) must be
  forward-only, per the platform's established migration philosophy;
  this plan requires a documented rollback path (column drop, not data
  rewrite) be validated before any milestone is marked accepted.
- Any deviation from a locked architecture rule discovered during
  implementation triggers a roll-forward repair, never a destructive
  rollback of unrelated already-shipped data (see
  `IMPLEMENTATION_PLAN.md` Section 1.5).

---

## Status Summary

Validation requirements defined for all 8 required categories across
every implementation sequence/milestone. **No validation activity has
been executed by this document** — it defines what must be validated
during a future, separately authorized implementation phase.

**IMPLEMENTATION REMAINS BLOCKED.**
