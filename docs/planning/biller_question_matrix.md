# Biller Question Matrix (Eligibility-First Reframing)

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Distinct from `biller_persona_matrix.md` (Phase 6, claims-oriented
questions). This matrix uses the specific eligibility-first question set
from the latest directive. Where a question overlaps one already
answered in `biller_persona_matrix.md` or
`hospice_billing_architecture_review.md`, the answer is restated briefly
with a cross-reference rather than re-investigated from scratch.

| Question | Can SNS answer? | Where | How | Using what data |
|---|---|---|---|---|
| Why is this patient billable? | **YES** | `BillingOverviewPage.tsx` | `check_patient_billing_readiness` | Certification, F2F, POC approval, NOE timing, payer sequence (`billing_readiness_service.py`) |
| Why is this patient NOT billable? | **YES** | Same screen | Same function returns explicit blocker reason strings, categorized via `categorize_blocker` | Same |
| When is recertification due? | **YES** | `PocCertificationPage.tsx` | `daysUntil(benefit_period.end_date)`, 14-day window | `BenefitPeriod.end_date` |
| What benefit period is active? | **YES** | (surfaced via readiness/cert screens, not a dedicated standalone screen) | `get_active_benefit_period` | `BenefitPeriod.is_current` |
| Has NOE been submitted? | **YES** | `NoeTrackingPage.tsx` | `GET /billing/noe-tracking` | `BenefitPeriod.noe_submitted_date` / `noe_exception_reason` |
| Has this claim been transmitted? | **NO** | — | No `ClaimTransmission` model/endpoint exists | See `claim_status_architecture.md` §2 — this is a data-model gap, not a missing report |
| Has payment been received? | **YES, with a caveat** | `BillingDashboard.tsx` claim list, filter `status=PAID` | `GET /billing/claims?status=PAID` | `Claim.status` — **can be wrong** if the confirmed "Export to Excel" bug already fired against that claim (see `claim_status_architecture.md`) |
| What claims are unpaid? | **YES** | Same claim list, filter `status` to `READY/SENT/ACCEPTED` | Same endpoint | `Claim.status` |
| What claims are partially paid? | **NO / UNKNOWN** | — | `Payment.paid_amount` vs. `Claim` billed amount is not confirmed to be compared or surfaced anywhere as a "partial payment" concept this pass | Data exists in `Payment`/`Claim` rows; no confirmed screen computes or displays the delta |
| What claims have no remittance? | **NO** | — | `Payment.match_status="UNMATCHED"` exists in the data model but is not surfaced on any screen or report found | See `payment_posting_architecture.md` step 6, `biller_persona_matrix.md` |

## What's new versus the earlier biller_persona_matrix.md

Two questions in this set were not asked in the earlier matrix and
surfaced a new, previously-undocumented gap:

- **"What benefit period is active?"** — answerable, but only indirectly
  (via the resolver function/readiness-adjacent screens); there is no
  confirmed single screen whose job is specifically "show me the active
  benefit period for this patient" as a standalone view.
- **"What claims are partially paid?"** — genuinely not confirmed either
  way this pass. Unlike "no remittance" (where the `UNMATCHED` field
  proves the concept exists in data but isn't surfaced), partial-payment
  tracking wasn't found to exist as a computed concept at all — flagged
  as **UNKNOWN**, not assumed missing, since it wasn't specifically
  searched for beyond this pass's grep.

## Summary count

Of the 10 questions in this eligibility-first set: **6 have a real,
wired, live-data answer** (why billable, why not billable, recert due,
active benefit period, NOE submitted, unpaid claims); **1 has a real
answer that can be silently wrong** (has payment been received); **3
have no confirmed answer** (transmitted, partially paid, no remittance).
This is a stronger ratio than the pure claims-side questions in
`biller_persona_matrix.md` (4/7 clean), reinforcing the directive's
thesis that the eligibility side of the system is more mature than the
claims/transmission side.
