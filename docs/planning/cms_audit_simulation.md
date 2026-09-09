# CMS Audit Simulation (Phase 43)

Status: verification synthesis, scenario-based. No production code changed. No billing feature or AI
built. This document reorganizes previously-established evidence (see `reimbursement_defensibility_review.md`,
`eligibility_traceability_chain.md`, `eligibility_integrity_review.md`) around a realistic audit
scenario rather than by module/service, per this phase's explicit instruction. No new code claims are
made that were not already evidenced in prior phases; this document's contribution is the narrative
framing, not new investigation.

## Scenario

A MAC post-payment reviewer selects a paid hospice claim for Patient "J.M.," benefit period 2 (a
recertification period), and requests: "Show me why this patient was billable, and why this specific
payment was proper."

## Walkthrough

**Election.** The reviewer asks for the signed election statement and proof the required addendum
(non-covered items/services) was furnished on time. SNS has `patients.election_signed_at` — a real,
persisted date. If a staff member logged an addendum request, `ElectionAddendumRequest` shows the
request/delivery dates and computed compliance. If no request was ever logged (the common case under
today's on-request rule), SNS has **no record at all** of whether an addendum was owed or furnished —
the reviewer would have to be told "we don't have a record because none was requested," which is a
correct answer only under the current rule, not the rule effective 10/1/2026.
**Evidence: exists (signed date), weak/absent for addendum unless a request happened to be logged.**

**Certification.** The reviewer asks who certified terminal prognosis, what evidence supported it, and
when. SNS produces: `Certification.physician_narrative`, `clinical_decline_indicators`,
`supporting_evidence`, `signed_by_role`, `signed_by_user_id`, `signed_at`, plus the full
`CertificationStatusEvent` history (DRAFT → PENDING_SIGNATURE → FINALIZED, each with `changed_by_user_id`,
`changed_at`, `reason`). This is a complete, strong answer.
**Evidence: exists, strong.**

**Benefit Period.** The reviewer asks: who created benefit period 2, when, and what confirmed the
recertification was valid at the moment it was created? SNS can show the `BenefitPeriod` row itself
(dates, `period_number`, `benefit_type`) but **cannot show who created it** (`created_by` is never
populated) **and cannot show that a certification check occurred at creation time** (`rollover_benefit_period`
performs no such check — confirmed by direct code read in `eligibility_integrity_review.md`). The
reviewer would have to accept "the certification exists elsewhere in the record, and we trust the
sequence was followed" — an inference, not a documented fact.
**Evidence: must be inferred.**

**Recertification.** Same underlying `Certification`/`CertificationStatusEvent` model as initial
certification — same strength. The reviewer can confirm a `RECERT`-type certification was signed by an
authorized physician role, with narrative evidence, timestamped.
**Evidence: exists, strong.**

**Plan of Care.** The reviewer asks whether the plan of care was physician-approved for this period.
`_has_physician_approved_plan_of_care` is a real, working check used by billing-readiness. Its own
version history/audit trail was not independently confirmed in any phase of this engagement.
**Evidence: exists (a pass/fail signal), audit depth unconfirmed.**

**NOE.** The reviewer asks whether the Notice of Election was filed within 5 days and *accepted* by the
MAC. SNS tracks `noe_submitted_date`/`noe_exception_reason` and a billing-readiness blocker for late
filing. Whether SNS distinguishes submission from MAC acceptance was not confirmed in any phase.
**Evidence: exists for submission; acceptance-tracking unconfirmed.**

**Claim.** The reviewer asks who changed the claim to its current status and when. Confirmed (Phase
5/6, unchanged): 1 of 3 `Claim.status` writers is enforced/audited; 2 are not.
**Evidence: partial, weak for 2 of 3 code paths.**

**Payment.** The reviewer asks for the remittance backing this payment. The dashboard's 835 widget is
confirmed fabricated (Phase 5/6). Whether a real, separate payment-posting ledger exists independent of
that widget was not reconfirmed in this engagement.
**Evidence: weak to unknown.**

## Direct Answer

**Can SNS currently survive a documentation review for a paid hospice claim? — PARTIAL.**

The clinical eligibility substance (certification, recertification) would fully satisfy a reviewer —
this is genuinely strong, evidenced, and not fabricated. The procedural chain (who/when created the
benefit period, whether it was gated by the certification, NOE acceptance vs. submission, and the
claim/remittance layer) contains real gaps that would require the reviewer to accept inference or
staff testimony in place of system-recorded evidence. This is not a fail — nothing here is fraudulent or
contradicted by the record — but it is not a full pass either, because "we're confident the sequence
was followed" is not the same evidentiary standard as "the system recorded that the sequence was
followed."

No production code has changed. No billing feature or AI has been built.
