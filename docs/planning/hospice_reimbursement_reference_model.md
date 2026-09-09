# Hospice Reimbursement Reference Model (Phase 18-22)

Status: research + comparison. No production code changed. No billing feature or AI built.

This document describes how hospice reimbursement actually works, independent of SNS, then compares
SNS against it. Sources: 42 CFR Part 418 (Subparts B, C), CMS Medicare Benefit Policy Manual Ch. 9,
CMS NOE timely-filing guidance, CMS VBID hospice-carve-in wind-down guidance, California Title 22
(CCR §§74800-74908, CDPH hospice-specific regulations), and this repo's own code (cited only where
comparing, never as the source of the regulatory requirement itself).

---

## A. Medicare Hospice Reference Model

### Lifecycle, required/optional, by payer type

| Step | Required? | Medicare (traditional) | Medicare Advantage (HMO) | Commercial PPO | California-specific |
|---|---|---|---|---|---|
| Referral | Optional (not a CMS-defined event) | No regulatory form | Same | Same | No CA-specific rule |
| Admission | Required | Must occur before election is effective | Same underlying rule | Payer-specific intake rules may apply | Title 22 admission documentation requirements apply |
| Election | **Required** | Signed election statement (42 CFR 418.24); as of 10/1/2026, a **written addendum listing non-covered items/services/drugs must be automatically furnished within 5 days of election**, not just on request | Same Medicare rules (hospice reverted fully to traditional Medicare Jan 1, 2025 — the VBID hospice carve-in ended 12/31/2024) | Payer determines election-equivalent process; no CMS form applies | Title 22 requires the record be complete and available for audit |
| Certification (initial) | **Required** | Physician (attending or hospice medical director/IDG physician) certifies terminal prognosis ≤6 months; written before billing, oral within 2 days permitted with written to follow, no more than 15 days before period start | Same clinical standard, billed to MAC not the MA plan | Payer-specific — often mirrors Medicare's clinical standard but is a private contract term, not a CMS regulation | New Title 22 hospice-specific sections require structured, timestamped, non-editable documentation of the certification event |
| Benefit Period 1 | **Required** | 90 days | Same | Payer-defined equivalent | N/A |
| Benefit Period 2 | **Required** if care continues | 90 days | Same | Payer-defined | N/A |
| Recertification | **Required** before each subsequent period | Face-to-face encounter by hospice physician/NP required within 30 days prior to recert starting at the 3rd benefit period (first 60-day period) and every 60-day period after | Same | Payer-defined, may differ | Same documentation-integrity rules apply |
| Benefit Period 3+ | **Required** if care continues | 60 days each, unlimited count | Same | Payer-defined | N/A |
| NOE (Notice of Election) | **Required**, Medicare only | Must be filed and *accepted* by the MAC within 5 calendar days of election effective date, or all days from election to acceptance become non-covered, provider-liable (coded OSC 77); not billable to the patient | Not applicable while under carve-in (ended); now applies again since MA reverted to traditional Medicare billing in 2025 | Not applicable — no NOE concept for commercial payers | N/A |
| Claim | **Required** | Submitted to MAC | Submitted to MAC (post-2025) | Submitted per payer contract/portal | N/A |
| Remittance/Payment | **Required** for revenue recognition | 835/ERA from MAC | Same, post-2025 | Payer-specific remittance format | N/A |
| Adjustments | Optional (as needed) | Standard claim adjustment/appeal process | Same | Payer-specific appeal process | N/A |
| Revocation | Optional (patient right) | Signed, dated, non-retroactive statement (42 CFR 418.28); patient returns to standard Medicare, may re-elect later | Same | Payer-defined equivalent | Documentation of revocation must be retained |
| Transfer | Optional | Only one active election at a time; per current CMS guidance the *receiving* hospice does not need to file a new NOE, only a transfer notice/record update | Same | Payer-defined | N/A |
| Discharge | Required when applicable | Must be documented with reason (no longer terminally ill / cause / relocation), care-planning and notification efforts (Medicare Benefit Policy Manual Ch. 9 §§20.2.2-20.2.3) | Same | Payer-defined | Title 22 requires documented discharge planning |
| Audit | Required (ongoing obligation) | Full clinical + billing record must be reconstructable for MAC/ZPIC/UPIC review | Same | Payer audit rights per contract | **New (2026)**: Title 22 hospice-specific sections require structured addenda (no silent edits), physician-notification tracking with date/time/method/response, addenda completed within a defined window (~48 hrs) with late entries flagged, and records "readily available for Department review" |
| Revenue recognition | Required | Tied to accepted NOE + valid certification + valid benefit period + accepted claim + posted remittance | Same, post-2025 | Payer-specific | N/A |

### What makes billing invalid / what causes denial (Medicare)
- No election statement, or election statement missing required elements (choice of hospice/attending
  physician, waiver-of-standard-Medicare acknowledgment, coverage/cost-sharing explanation).
- **As of 10/1/2026**: election statement addendum not automatically furnished within 5 days — this is
  a new denial/citation risk, not merely a "furnish on request" courtesy anymore.
- No certification, or certification not signed by an authorized physician role, or certification
  signed/dated outside the ±15-day window relative to the benefit period it covers.
- No face-to-face encounter (or one outside the 30-day pre-recert window) for benefit period 3+.
- NOE not filed/accepted within 5 calendar days — resulting days become provider-liable, not billable
  to Medicare or the patient (this is a hard financial loss, not a resubmittable denial).
- Claim submitted for a benefit period with no valid certification on file for that period.
- Revocation on file with no subsequent valid re-election for a later claim.

### Can SNS explain why Medicare would pay / deny?

**Why Medicare would deny — partially, via the existing `check_patient_billing_readiness` blockers**
(certification missing/not finalized, NOE timeliness/exception, payer-sequence ambiguity, F2F
attestation, POC approval — all confirmed real and working, see `billing_readiness_spec.md`). **Why
Medicare would pay** is not explicitly modeled as an affirmative statement anywhere — SNS today only
answers "not blocked" (absence of blockers), not "here is the complete set of satisfied requirements
that together constitute an affirmative payment case." This is a real gap: an absence of a documented
blocker is not the same statement as a documented, itemized satisfaction of every requirement, and an
auditor/surveyor will expect the latter.

---

## B. Medicare Advantage (HMO) Hospice Differences

- **Current reality (post-1/1/2025): there is no more "carve-in."** The VBID Hospice Benefit Component
  ended 12/31/2024. All MA beneficiaries electing hospice now revert to traditional Medicare hospice
  billing rules — claims go to the MAC, not the MA plan, and standard NOE/certification/benefit-period
  rules apply exactly as under traditional Medicare.
- **What this means for SNS**: any HMO-specific hospice billing pathway does not need special-case
  logic beyond what traditional Medicare already requires — this significantly *simplifies* the
  original Phase 20 research question. There is currently no live MA hospice carve-in demonstration for
  SNS to accommodate. This should be documented explicitly so future engineering does not build unused
  MA-specific hospice billing logic.
- **What could still differ operationally**: while a patient is *not yet* electing hospice (i.e., still
  receiving concurrent MA-covered care before an election), authorization/referral rules are pure MA
  plan territory and outside the hospice billing scope entirely — this is a separate workflow (medical,
  not hospice-billing) and out of scope for this review.
- **SNS comparison**: no HMO-specific code branch was found in the billing pipeline in any prior
  segment's review, which is now understood to be *correct*, not a gap — there is currently nothing
  Medicare-Advantage-specific for hospice billing to branch on.

## C. PPO / Commercial Hospice Differences

- Commercial (non-Medicare) hospice coverage is governed entirely by the individual payer contract —
  there is no CMS-equivalent regulatory floor. Benefit limits, authorization requirements, and
  documentation standards vary payer-to-payer and are not standardized the way Medicare's 90/90/60-day
  structure is.
- Operationally, commercial payers commonly still expect: a signed election-equivalent document,
  physician certification of terminal prognosis, and periodic recertification — but timing windows,
  face-to-face requirements, and NOE-equivalent notices are payer-specific, not CMS-mandated.
- **SNS comparison**: `payer` and `payer_sequence` concepts already exist in the billing-readiness
  check (confirmed in the Phase 5/6 and Phase 9 reviews), which is payer-agnostic infrastructure — this
  is the correct foundation for commercial-payer variability, but no payer-specific rule configuration
  (e.g., "Payer X requires recert every 90 days regardless of BP number") was found to exist. This is a
  legitimate, currently-undocumented gap, not urgent relative to the Medicare/certification-gating
  findings, but real.

## D. California Hospice Compliance Mapping

CDPH adopted comprehensive, hospice-specific Title 22 regulations (CCR §§74800-74908). Key new
requirements directly relevant to SNS's EMR architecture:

| Requirement | SNS coverage |
|---|---|
| Structured addendum workflow — no silent edits to clinical notes; addenda must be separate, signed, timestamped, and classified | **Not verified this pass** — flagged for a targeted follow-up read of the clinical-notes/addendum code path (outside this review's benefit-period/certification scope); this is a new, hospice-specific requirement, not a general EMR nice-to-have. |
| Physician notification for significant changes tracked with date/time/method/response; failure to document is citable | **Not verified this pass** — same follow-up flag as above. |
| Addenda/corrections completed within a defined window (~48 hrs), late entries flagged | **Not verified this pass.** |
| Records must include audit trails, physician e-signatures for care-plan reviews | **Partially confirmed**: `Certification` has a real e-signature-equivalent (`signed_by_role`, `signed_by_user_id`, `signed_at`) and a real audit trail (`CertificationStatusEvent`). `BenefitPeriod` does not (confirmed this session, Phase 12/13 addendum). Plan-of-care e-signature/audit was not re-verified this pass (prior segments referenced `check_patient_billing_readiness`'s `_has_physician_approved_plan_of_care` check exists, implying at least a stored approval state, but its own audit trail was not inspected). |
| Records readily available for CDPH review; retention (traditional Title 22 floor: 7 years for adults) | Not evaluated in this review — a data-retention/export capability question, not a workflow-gating question; out of scope for the benefit-period/certification focus of this engagement. |

**Bottom line for California**: the new CDPH hospice-specific rules raise the bar specifically on
*auditability of every edit and notification*, which is exactly the same category of gap already found
in `BenefitPeriod` (no audit trail) — this is not a new, unrelated finding, it is additional regulatory
weight behind a gap already identified. It also surfaces a **new, not-previously-investigated
question** (addendum/correction workflow for clinical notes generally) that should be scoped as its own
follow-up review before being assumed either present or absent.

---

## Direct research-grounded conclusions carried into the gap matrix and re-prioritization

1. The certification-gating gap (found via code review, prior sessions) is independently confirmed by
   regulation as the correct #1 concern: CMS explicitly conditions each benefit period's validity on a
   timely, correctly-signed certification/recertification — SNS's code gap and the regulatory
   requirement are the same requirement, viewed from two different evidence sources, and they agree.
2. **A new, time-sensitive, previously-undiscovered gap**: SNS's `election_addendum_service.py`
   implements the **on-request** addendum rule (5 days if requested within the election window, 3 days
   if requested later) — the rule that applies **today**. CMS's mandatory-for-all-elections version of
   this same addendum takes effect **10/1/2026**. This is real, evidence-based (direct code read,
   confirmed the function requires a `requested_date` and raises if none is provided), and is
   time-critical: it was not on any prior gap list because no one had researched the upcoming
   regulatory change until this phase.
3. Medicare Advantage hospice carve-in is a non-issue for current engineering — it ended 1/1/2025.
   Any backlog item framed as "MA hospice differences" should be retired or re-scoped, not built.
4. California's new Title 22 hospice rules reinforce (not duplicate) the BenefitPeriod audit-trail gap,
   and separately raise a new, unscoped question about clinical-note addendum/correction workflow that
   should be a distinct future review, not assumed covered by this engagement's findings.
