# Schema Design Review — Review Checklist Result

Applied against: `/docs/biller-platform/BILLING_SCHEMA_DESIGN_REVIEW.md`

## A. Phase Validation

- [x] Current phase is Schema Design Review.
- [x] Discovery phase outputs referenced.
- [x] No implementation work performed.
- [x] No schema changes created.
- [x] No migrations created.
- [x] No APIs created.
- [x] No UI created.
- [x] No backfills executed.
- [x] No data modified.
- [x] No entities retired.

**RESULT: PASS**

## B. Discovery Traceability

- [x] System-of-Record Matrix referenced.
- [x] Legacy Billing Inventory referenced.
- [x] PatientInsurance Analysis referenced.
- [x] Ownership Boundaries referenced.
- [x] Repository Grounding referenced (added explicit citation of
  `REPOSITORY_GROUNDING_CORRECTION_REPORT.md` during this review).
- [x] Every major design decision traces back to repository evidence.
- [x] No design decision based solely on architecture preference.

**RESULT: PASS**

## C. System of Record Review

- [x] Authority identified for every concept.
- [x] Consumers identified for every concept.
- [x] Ownership documented for every concept.
- [x] Scope documented for every concept.
- [x] Relationships documented for every concept.
- [x] Duplicate structures documented for every concept.
- [x] Repository evidence cited for every concept.

Required concepts, all present in Section 1: Payer, PatientInsurance,
PatientPayer, PatientFaceSheet, Claim, Payment, ERA, Remittance,
Denial, Appeal, Credit Balance, NOE, CAP, Room & Board,
BillingProviderOrganization, BillingProviderAgencyAssignment,
BillingProviderAgencyServiceScope, Audit, Export.

Note: ERA and Remittance are documented as one combined entry because
they are the same underlying table (`remittance_advices`) in this
repository — a clarifying note was added during this review so this is
not mistaken for an omission.

**RESULT: PASS**

## D. Patient Coverage Authority

- [x] PatientInsurance reviewed.
- [x] PatientPayer reviewed.
- [x] PatientFaceSheet reviewed.
- [x] Ownership differences documented.
- [x] Data ownership documented.
- [x] Consumer ownership documented.
- [x] Historical preservation documented.
- [x] Data overlap documented.
- [x] Repository evidence provided.
- [x] No third PatientCoverage model proposed.
- [x] Authority explicitly unresolved, with documented blockers (three
  overlapping structures, no reconciliation rule, LINK vs. CONSOLIDATE
  undecided).

**RESULT: PASS** (acceptable outcome: explicitly unresolved with
documented blockers)

## E. Eligibility Authority

- [x] PayerEligibilityCheck reviewed.
- [x] EligibilityVerification reviewed.
- [x] Data overlap documented.
- [x] Consumers documented.
- [x] Ownership documented.
- [x] Repository evidence provided.
- [x] Future direction documented (non-binding).
- [x] No forced consolidation.
- [x] Authority explicitly unresolved, with documented blockers.

**RESULT: PASS**

## F. BillingProvider Review

- [x] BillingProviderOrganization reviewed.
- [x] BillingProviderOrganizationMembership reviewed.
- [x] BillingProviderAgencyAssignment reviewed.
- [x] BillingProviderAgencyServiceScope reviewed.
- [x] Existing consumers documented.
- [x] Ownership documented.
- [x] Future extension strategy documented (EXTEND is sufficient; no
  new structure recommended).
- [x] Team architecture impact documented.
- [x] Coverage-assignment impact documented.
- [x] Permission impact documented.

**RESULT: PASS**

## G. Dual-Write Review

- [x] All known multi-writer structures identified — a targeted
  repository-wide sweep for model-instantiation call sites across
  `Claim`, `Payment`, `Denial`, `Appeal`, `CreditBalanceCase`,
  `HospiceCapRecord`, `NoeEdiSubmission`, and `RemittanceAdvice` was
  performed during this review and found exactly one writer file per
  model; no additional dual-writer structure was found beyond
  `BillingProviderAgencyAssignment`. This was a targeted call-site
  search, not an exhaustive data-flow trace, and is reported as such.
- [x] BillingProviderAgencyAssignment reviewed.
- [x] Current writers documented.
- [x] Current purpose documented.
- [x] Risks documented.
- [x] Ownership options documented.
- [x] No fixes implemented.
- [x] No write path chosen prematurely.

**RESULT: PASS**

## H. Entity Review

No entity in `BILLING_SCHEMA_DESIGN_REVIEW.md` carries an active
TENTATIVE CREATE recommendation. Section 6 explicitly declines to
advance the one candidate discussed (a possible future "Export Event"
model) to a CREATE recommendation, for lack of the very analysis this
section requires. This section's requirements are therefore vacuously
satisfied — there is no unjustified CREATE recommendation to fail on.

**RESULT: PASS** (no TENTATIVE CREATE entities present)

## I. Anti-Duplication Review

- [x] One payer authority strategy.
- [x] One plan authority strategy.
- [ ] One coverage authority strategy — **not literally satisfied**;
  three overlapping structures exist with no single strategy. This is
  the same item carried from Section D and is accepted here under the
  same "intentionally unresolved with documented blockers" exception
  stated in the Schema Design Approval Criteria.
- [x] One claim authority strategy.
- [x] One payment authority strategy.
- [x] One ERA authority strategy.
- [x] One remittance authority strategy (same table as ERA).
- [x] One denial authority strategy.
- [x] One appeal authority strategy.
- [x] One Room & Board authority strategy.
- [x] One permissions authority strategy.
- [ ] One settings authority strategy — **not verified**; no dedicated
  billing-settings search was performed in this or the design-review
  pass. Documented as an open item in Section 7, not silently passed.
- [x] One audit authority strategy.
- [ ] One export authority strategy — **not fully verified**; no
  dedicated "Export Event" model exists, and whether export activity is
  otherwise safely audited was flagged, not confirmed. Documented as an
  open item in Section 7, not silently passed.
- [x] No duplicate writable systems remain undocumented — the three
  items above are documented as open/unresolved rather than falsely
  certified as clear.

**RESULT: PASS WITH NOTED OPEN ITEMS** (coverage authority
intentionally unresolved per the approval criteria's explicit
exception; settings authority and export authority flagged
not-fully-verified rather than assumed clear)

## J. Migration Impact Review

- [x] Migration exposure documented for all three forward-looking
  candidates (Patient Coverage LINK/CONSOLIDATE, Eligibility
  consolidation, dual-write resolution).
- [x] Backfill exposure documented.
- [x] Historical preservation risk documented.
- [x] Data-loss risk documented.
- [x] Foreign-key impact documented.
- [x] Consumer impact documented.
- [x] Operational impact documented — added during this review (the
  original draft had left this "Not assessed" for all three
  candidates; corrected before this checklist was applied).
- [x] Verification approach documented — added during this review for
  the same reason.
- [x] No migration design approved — all three remain candidates only.

**RESULT: PASS** (corrected during this review — see Required
Corrections below)

## K. Database Safety Review

- [x] No alembic stamp proposed.
- [x] No migration rewrite proposed.
- [x] Forward-only migration approach maintained.
- [x] Forward-only repair approach maintained (citing this
  repository's own prior repair-migration pattern).
- [x] Schema drift risks documented (as an open item — no
  model-vs-database column-level drift check was performed; only the
  read-only table-existence/record-count check from the Legacy
  Inventory).
- [x] Historical records protected.
- [x] Active production structures protected.

**RESULT: PASS** (added as a new Section 10 during this review — the
original draft had no dedicated Database Safety Review section)

## L. Fail Conditions

- [ ] Third PatientCoverage model proposed — not triggered.
- [ ] Duplicate payer authority created — not triggered.
- [ ] Duplicate plan authority created — not triggered.
- [ ] Duplicate claim authority created — not triggered.
- [ ] Duplicate payment authority created — not triggered.
- [ ] Duplicate eligibility authority created — not triggered.
- [ ] Existing billing structures ignored — not triggered.
- [ ] Legacy structures buried — not triggered.
- [ ] Ownership assumptions replace repository evidence — not
  triggered.
- [ ] CREATE recommendations lack justification — not triggered (none
  exist).
- [ ] Migration implementation work started — not triggered.

**RESULT: PASS** (no fail condition triggered)

---

## Final Decision

**APPROVED WITH CORRECTIONS**

Corrections were identified and applied to
`BILLING_SCHEMA_DESIGN_REVIEW.md` during this checklist review, rather
than deferred:
1. Added a dedicated Section 10 (Database Safety Review) — previously
   absent entirely.
2. Added Operational Impact and Verification Approach detail to all
   three Section 8 migration-impact candidates — previously marked
   "Not assessed."
3. Performed and documented a broader dual-writer sweep across all
   remaining billing models (Section 5) — previously the document only
   addressed the one already-known conflict without checking for
   others.
4. Added an explicit citation of `REPOSITORY_GROUNDING_CORRECTION_REPORT.md`
   and a clarifying note on the combined ERA/Remittance entry.

No correction changed any REUSE/EXTEND/LINK/CONSOLIDATE/DO NOT
CREATE/TENTATIVE CREATE decision, and none authorizes schema,
migration, API, or UI work.

## Schema Design Authorization Gate

- [x] Discovery outputs approved.
- [x] System-of-record review approved.
- [x] Patient Coverage review approved (intentionally unresolved, with
  documented blockers).
- [x] Eligibility review approved (intentionally unresolved, with
  documented blockers).
- [x] BillingProvider review approved.
- [x] Dual-write review approved (documented, not fixed).
- [x] Anti-duplication review approved (with two open items honestly
  flagged: settings authority, export authority).
- [x] Migration-risk review approved.
- [x] Database safety review approved.
- [x] Every CREATE recommendation justified (none exist to justify).

All boxes checked. Per the gate's own rule, this means:

**SCHEMA DESIGN = APPROVED FOR NEXT PHASE (with the above corrections
applied)**
**MIGRATION DESIGN = still requires its own separate review and
authorization — not opened by this checklist result.**
**IMPLEMENTATION = BLOCKED.**

## Review Summary

**Strengths:**
- Every one of the 19 required billing concepts is documented with
  authority, consumers, ownership, scope, and repository-cited
  evidence, with no concept ignored or silently buried.
- Patient Coverage Authority and Eligibility Authority are both
  honestly left unresolved with documented blockers rather than forced
  to a premature decision, and no third `PatientCoverage` model is
  proposed anywhere.
- The `BillingProviderAgencyAssignment` dual-write conflict is
  documented with real code citations (exact file/line writers on both
  sides) rather than described abstractly.

**Unresolved Risks:**
- Coverage authority: three structures (`PatientInsurance`,
  `PatientPayer`, `PatientFaceSheet`) still store overlapping
  payer/subscriber identity data with no reconciliation rule.
- `BillingProviderAgencyAssignment` remains writable from both Owner
  Platform and Biller Platform code paths, with a further verified
  asymmetry (Owner-created assignments lack service scopes).
- Settings authority and export-event authority were not fully
  verified in this pass and remain open items.

**Required Corrections (applied during this review):**
- Database Safety Review section added (previously missing).
- Operational Impact / Verification Approach added to all three
  migration-impact candidates (previously "Not assessed").
- Broader dual-writer sweep performed and documented across all
  remaining billing models.

**Recommendation:**
Proceed to a dedicated Migration Design Review only for the specific,
narrow items already flagged as open (Patient Coverage LINK/CONSOLIDATE
option, Eligibility Authority direction, dual-write resolution option),
using the option analyses already on record in
`TENANT_BILLER_OWNERSHIP_BOUNDARIES.md` and this document as the
starting point. Implementation remains blocked until that separate
review is completed and approved.
