# Implementation Authorization Package

## Status

**PLANNING ONLY — SELF-CERTIFICATION FOR REVIEW.** This document
compiles the Implementation Planning checklist result and states
whether the program is ready for a future Implementation Authorization
Review. **It does not itself authorize implementation.** No schema.
No migrations. No code. No API. No UI.

---

## Pre-Authorization Checklist

- ✅ **Authority decisions remain unchanged.** Patient Coverage
  (Option C), Eligibility (Option C), and `BillingProviderAgencyAssignment`
  (Option B) as approved in `FINAL_SCHEMA_AUTHORIZATION_REVIEW.md` are
  unmodified by any Implementation Planning document.
- ✅ **`PatientCoverage` not introduced.** No epic, story, domain entry,
  or preservation item in `IMPLEMENTATION_EPICS.md`,
  `IMPLEMENTATION_STORIES.md`, `DOMAIN_IMPLEMENTATION_ORDER.md`, or
  `DATA_PRESERVATION_PLAN.md` proposes a `PatientCoverage` model.
- ✅ **No duplicate authorities introduced.** All 13 locked categories
  (Payer, Plan, Claim, Payment, ERA, Remittance, Denial, Appeal, Room
  & Board, Audit, Export, Permissions, Settings) were checked against
  every epic in `IMPLEMENTATION_EPICS.md`; no epic proposes a
  duplicate.
- ✅ **No ownership drift.** `DOMAIN_IMPLEMENTATION_ORDER.md` restates
  each structure's approved authority exactly as locked in
  `FINAL_SCHEMA_AUTHORIZATION_REVIEW.md`; no domain entry reassigns
  authority.
- ✅ **No unreviewed CREATE entities.** Every domain entry's strategy
  is REUSE or EXTEND only; no TENTATIVE CREATE item was advanced past
  what was already found insufficient-evidence in
  `BILLING_SCHEMA_DESIGN_REVIEW.md` Section 6.
- ⚠ **Validation strategy — drafted, pending approval.**
  `IMPLEMENTATION_VALIDATION_PLAN.md` defines all 8 required
  categories; awaiting explicit user approval.
- ⚠ **Test strategy — drafted, pending approval.**
  `IMPLEMENTATION_TEST_STRATEGY.md` defines all 10 required
  categories; awaiting explicit user approval.
- ⚠ **Data preservation — drafted, pending approval.**
  `DATA_PRESERVATION_PLAN.md` covers all three locked authorities plus
  cross-cutting audit/legacy-artifact requirements; awaiting explicit
  user approval.
- ⚠ **Implementation roadmap — drafted, pending approval.**
  `IMPLEMENTATION_PLAN.md` defines sequence, dependencies, milestones,
  releases, validation checkpoints, rollback/repair checkpoints, and
  acceptance gates; awaiting explicit user approval.

## Open Items Requiring Resolution Before Implementation Authorization

1. The field-reconciliation pass extending
   `PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md` to include
   `PatientFaceSheet` (Implementation Stories Epic 5, Story 5.2) has
   not yet been performed.
2. The "duplicate export authority — NOT FULLY VERIFIED" item (Schema
   Design Review Section 7 / Implementation Stories Epic 15, Story
   15.1) has not yet been resolved.
3. The `SourceOfTruthMatrix.md` / `PatientFaceSheet` SSOT-claim
   documentation conflict remains uncorrected (non-schema follow-on
   action, still open).
4. The `owner_admin.py` delegation code change (Epic 3, Story 3.1) and
   the resulting service-scope remediation (Epic 4, Story 4.1) are
   both designed but not implemented — as expected at this phase.

None of the above items block Implementation *Planning* completion;
all four are correctly scoped as pending items to be resolved before
or during a future, separately authorized Implementation phase.

## Implementation Authorization Blocker — Tenant Platform Redesign

**STATUS: BLOCKING.** Per instruction, Implementation Authorization for
the Billing/Biller Platform work documented in this package **cannot
be approved** until the following, separate Tenant Platform Redesign
initiative is completed and Figma-approved:

- ☐ Tenant navigation redesigned
- ☐ Tenant dashboard redesigned
- ☐ Patient workspace redesigned
- ☐ Clinical workflow redesigned
- ☐ Intake workflow redesigned
- ☐ AI workflow redesigned
- ☐ SNS-specific UX established
- ☐ HospiceMD look-and-feel removed
- ☐ Tenant platform reviewed against competitive products
- ☐ Figma approved

This blocker is orthogonal to the Billing/Biller Platform's own
readiness: the seven Implementation Planning deliverables above remain
independently reviewable and approvable on their own merits, but
**Implementation Authorization Review for this program will not be
granted while this checklist has unchecked items**, per this
instruction. No item on this checklist has been started, verified, or
completed by this document — this is a recorded blocking condition
only, not a redesign plan. A separate Tenant Platform Redesign
discovery/planning effort (not part of this Billing/Biller Platform
governance track) would be required to address it.

## Deliverables Produced This Phase

| Phase | Deliverable | Status |
|---|---|---|
| 1 | `IMPLEMENTATION_PLAN.md` | Drafted |
| 2 | `IMPLEMENTATION_EPICS.md` | Drafted |
| 3 | `IMPLEMENTATION_STORIES.md` | Drafted |
| 4 | `DOMAIN_IMPLEMENTATION_ORDER.md` | Drafted |
| 5 | `DATA_PRESERVATION_PLAN.md` | Drafted |
| 6 | `IMPLEMENTATION_VALIDATION_PLAN.md` | Drafted |
| 7 | `IMPLEMENTATION_TEST_STRATEGY.md` | Drafted |
| 8 | `IMPLEMENTATION_AUTHORIZATION_PACKAGE.md` (this document) | Drafted |

## Final Output

**READY FOR IMPLEMENTATION AUTHORIZATION REVIEW: PENDING USER
APPROVAL OF THE SEVEN DELIVERABLES ABOVE — AND BLOCKED BY THE TENANT
PLATFORM REDESIGN CHECKLIST ABOVE.**

**NOT READY FOR IMPLEMENTATION.**

Once the user reviews and approves
`IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_EPICS.md`,
`IMPLEMENTATION_STORIES.md`, `DOMAIN_IMPLEMENTATION_ORDER.md`,
`DATA_PRESERVATION_PLAN.md`, `IMPLEMENTATION_VALIDATION_PLAN.md`, and
`IMPLEMENTATION_TEST_STRATEGY.md`, this package may be resubmitted as
**READY FOR IMPLEMENTATION AUTHORIZATION REVIEW.** A separate,
explicit Implementation Authorization Review is required after that
before any schema, migration, code, API, or UI work may begin.

**IMPLEMENTATION REMAINS BLOCKED.**
