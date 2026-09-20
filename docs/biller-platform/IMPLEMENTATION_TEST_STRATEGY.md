# Implementation Test Strategy

## Status

**PLANNING ONLY.** Documents the test strategy required across all
implementation sequences. **No schema. No migrations. No code. No
API. No UI. No test execution is performed by this document.**

---

## 1. Unit Testing

- Each REUSE/EXTEND change (e.g., the future `owner_admin.py`
  delegation change in Epic 3) requires unit tests covering the
  changed function in isolation, consistent with the 13 existing test
  files already identified in `LEGACY_BILLING_SCHEMA_INVENTORY.md`.
- New unit tests must not require any schema change to pass; they
  validate behavior against the existing, approved schema.

## 2. Integration Testing

- Agency Assignment delegation (Epic 3) requires an integration test
  confirming `owner_admin.py::set_tenant_financials` produces the same
  externally-observable result (tenant financials enabled) while
  internally routing through Biller Platform's assignment logic.
- Patient Coverage link (Epic 5, once implemented) requires an
  integration test confirming `PatientInsurance` and `PatientPayer`
  reads/writes remain correct with the new link present.

## 3. Authorization Testing

- `PLATFORM_BILLING` vs. `BILLING` role checks must be tested across
  every epic that touches an existing authorization boundary,
  especially Epic 3 (Agency Assignment) and Epic 17 (Security/
  Permissions).
- Confirm no epic's implementation allows a role to bypass its
  existing permission_level (`VIEW`/`EDIT`) gate.

## 4. Audit Testing

- Confirm append-only behavior of `AuditLog` and
  `facility_payment_audit_log` is preserved: attempt an update/delete
  in a test environment only, and confirm it is rejected or otherwise
  never exercised by application code.
- Confirm every new/changed write path (e.g., Epic 3's delegation
  change) still produces an equivalent audit entry.

## 5. Billing Workflow Testing

- End-to-end test of Milestone 1→3 flow: organization → assignment →
  service scope → payer/patient-payer → eligibility → claim, using
  existing test fixtures (extending, not replacing, the 13 existing
  test files).

## 6. Claims Testing

- Regression test of claim creation and the 837I payer/subscriber
  block generation from `PatientPayer`, both before and after any
  Patient Coverage Authority link is implemented, to confirm no
  behavior change.

## 7. Payment Testing

- Regression test of payment posting and adjustment creation
  (`payment_service.py`), unaffected by upstream Coverage/Eligibility/
  Claims changes.

## 8. Eligibility Testing

- Regression test of both `PayerEligibilityCheck` and
  `EligibilityVerification` creation/read paths, confirming they
  remain separate concepts per the approved decision, and that any
  future optional cross-reference FK does not alter either model's
  existing status-field semantics.

## 9. Room & Board Testing

- Regression test of the full facility-payment chain (expectation →
  allocation → alert → audit log), confirming the cohesive,
  singularly-owned domain remains intact through all upstream Payment
  Posting changes.

## 10. Regression Testing

- Full regression pass across all 13 existing billing test files
  (`test_eligibility_workflow_service.py`,
  `test_eligibility_roster_endpoint.py`, and the other 11 identified
  in `LEGACY_BILLING_SCHEMA_INVENTORY.md`) must pass unchanged (or
  with only additive test cases) before any milestone is marked
  accepted.
- Regression coverage must include every locked architecture rule:
  no `PatientCoverage` model exists, no consolidation of either locked
  pair has occurred, no duplicate authority exists for any of the 13
  protected categories (Payer, Plan, Claim, Payment, ERA, Remittance,
  Denial, Appeal, Room & Board, Audit, Export, Permissions, Settings).

---

## Status Summary

Test strategy defined for all 10 required categories. **No test has
been executed and no test code has been written by this document** —
it defines what a future, separately authorized implementation phase
must test.

**IMPLEMENTATION REMAINS BLOCKED.**
