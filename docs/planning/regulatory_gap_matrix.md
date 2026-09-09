# Regulatory Gap Matrix (Phase 23)

Status: verification + research comparison. No production code changed. No billing feature or AI built.
Cross-references `hospice_reimbursement_reference_model.md` (the regulatory source of truth) and this
engagement's prior code-evidence documents (`eligibility_integrity_review.md`,
`certification_gated_eligibility_review.md`, `benefit_period_engine_review.md`, Phase 5/6 claim-status
and remittance reviews). Every "SNS Coverage" cell is either previously-confirmed-by-code-read or
newly-confirmed in this pass — none are inferred from an endpoint merely existing.

| Requirement | Source | SNS Coverage | Gap | Risk | Priority |
|---|---|---|---|---|---|
| Certification (initial) | 42 CFR 418.22 | Model + lifecycle + audit trail exist and are correct (`Certification`, `CertificationStatusEvent`) | Not enforced as a precondition for benefit-period creation | High — root cause of the eligibility-integrity finding | 1 |
| Recertification | 42 CFR 418.22 | Same table/model as certification (`cert_type=RECERT`); billing-readiness re-checks it at claim time | Same gap as above, plus no "Recert Overdue" derived signal exists yet (only a 15-day "expiring" dashboard widget) | High | 1 |
| Election | 42 CFR 418.24 | `election_date` exists as a column on `BenefitPeriod`; no dedicated `Election` model/screen/audit trail | Election has no independent lifecycle or audit trail — it inherits `BenefitPeriod`'s own audit gap | Medium | 3 |
| Election Statement Addendum (mandatory version) | 42 CFR 418.24, CMS FY2027 rule, **effective 10/1/2026** | `election_addendum_service.py` implements only the **pre-10/1/2026 on-request** rule (`requested_date` required, raises if absent) | **Confirmed this pass**: no automatic-furnish-within-5-days-of-every-election path exists; the mandatory version is not implemented | **High and time-critical** — effective date is ~3 weeks from this review | **0 (time-boxed ahead of #1)** |
| Benefit Period creation/rollover | 42 CFR 418.21 | `rollover_benefit_period` exists, tested, CMS-correct 90/90/60 period lengths, atomic | Zero certification/recert gate; idempotency gap (differing `start_date` not deduped); no update/correct/delete endpoints exist at all | High | 1 |
| Benefit Period audit trail | Implicit CMS/CDPH auditability expectation; explicit new CDPH Title 22 auditability rules | None — `created_by` unpopulated, no status-event table | Auditor cannot reconstruct benefit-period transition history for a patient | High (elevated further by new CDPH rules) | 2 |
| Face-to-Face encounter (BP3+) | 42 CFR 418.22(a)(4) | `_has_attested_f2f` check exists in billing-readiness; F2F screens exist per prior segment's review | Not re-verified this pass whether the 30-day-prior-to-recert *window* itself is validated, vs. only attestation existence | Medium — flagged, not confirmed either way | Needs follow-up read before ranking |
| NOE (Notice of Election) | 42 CFR 418.24, CMS timely-filing guidance (5-day rule, OSC 77) | `noe_submitted_date` / `noe_exception_reason` checked in billing-readiness; "filed_within > 5 and no exception reason" blocker exists | Not verified this pass whether SNS tracks *MAC acceptance* (vs. just submission) — the 5-day clock legally runs to acceptance, not submission | Medium-High — a submitted-but-not-yet-accepted NOE could be miscounted as compliant | Needs follow-up read |
| Claim submission/status | Standard MAC claim lifecycle | 3 writers to `Claim.status` (1 enforced/audited, 2 not) — confirmed in Phase 5/6 | Documented, unchanged this pass | High (pre-existing, unchanged) | 4 |
| Remittance/835 | Standard MAC ERA | Dashboard 835 widget renders fabricated data (confirmed Phase 5/6); no `ClaimTransmission` model | Documented, unchanged this pass | Medium-High (pre-existing, unchanged) | 5 |
| Revocation | 42 CFR 418.28 | **Not investigated in this engagement at all** | Unknown — no prior document in this engagement addresses revocation | Unknown until investigated | Needs a dedicated follow-up review before ranking |
| Discharge | Medicare Benefit Policy Manual Ch. 9 §§20.2.2-20.2.3 | **Not investigated in this engagement at all** | Unknown | Unknown | Needs a dedicated follow-up review |
| Transfer (between hospices) | Current CMS guidance (receiving hospice does not need a new NOE) | **Not investigated in this engagement at all** | Unknown | Unknown | Needs a dedicated follow-up review |
| Plan of Care (physician-approved) | Hospice CoPs (general requirement, not benefit-period-specific) | `_has_physician_approved_plan_of_care` check exists in billing-readiness | Its own audit trail/versioning was not re-verified this pass | Unknown until investigated | Needs follow-up read |
| Interdisciplinary Group (IDG) review | Hospice CoPs | `IDG_REVIEW` task auto-seeded on every `rollover_benefit_period` call (14-day due date) | Whether the *task being completed* is itself checked anywhere downstream was not verified this pass | Unknown | Needs follow-up read |
| Medicare Advantage hospice-specific rules | VBID hospice carve-in (ended 12/31/2024) | N/A — no special MA hospice logic exists in SNS | **Correctly a non-gap**: MA hospice fully reverted to traditional Medicare rules 1/1/2025; no engineering work should be scoped here | None | Remove from backlog |
| PPO / commercial payer-specific hospice rules | Individual payer contracts (no CMS floor) | `payer`/`payer_sequence` concepts exist as payer-agnostic infrastructure in billing-readiness | No payer-specific rule configuration (e.g., differing recert cadence per payer) found | Low-Medium — real but not urgent | 6 |
| California Title 22 hospice-specific documentation rules (structured addenda, physician-notification tracking, ~48hr correction window) | New CDPH regulations, CCR §§74800-74908 | **Not investigated in this engagement** — flagged as a distinct, previously-unscoped review need | Unknown scope until a dedicated clinical-notes/addendum-workflow review is performed | Unknown, but the *category* (auditability of edits) is already known to be a weak area given the BenefitPeriod finding | Needs a dedicated follow-up review; do not assume covered or uncovered |
| California medical record retention (7-year floor) | Title 22 (general, pre-2026 baseline) | Not evaluated — a data-retention/export capability question | Unknown | Unknown | Out of scope for benefit-period/certification focus; separate review |

## Notes on matrix discipline
- Every "Not investigated" / "Unknown" row is stated as such deliberately, per the standing rule to
  never infer coverage from an endpoint or table merely existing. These rows are gaps in *this
  engagement's knowledge*, not confirmed gaps in SNS itself, and must not be conflated with the rows
  that are confirmed gaps by direct evidence.
- The Election Statement Addendum row is the one genuinely new, time-critical finding from the
  regulatory-research phase that did not exist in any prior gap list — it was invisible to pure
  code/architecture review because the *current* on-request implementation is correct for *today's*
  rule; only comparing against the upcoming regulatory change surfaces it.
