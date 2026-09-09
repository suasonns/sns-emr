# Billing Readiness Engine — Design Spec

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

**Design only — nothing in this document has been implemented.** This
is intended to become the first AI-assisted billing feature, per
explicit instruction: it must answer **"Why can I bill this patient?" /
"Why can't I bill this patient?"** — never "generate a claim."

## What already exists (the foundation this engine would wrap, not replace)

`check_patient_billing_readiness` (`app/billing/services/billing_readiness_service.py`)
already computes exactly this today, in code, and is already wired to
`BillingOverviewPage.tsx`. It is the single strongest capability found
across the entire billing review (confirmed across three prior
documents). The "Billing Readiness Engine" as a development priority is
**not a greenfield build** — it is: (a) confirming the existing engine's
coverage is complete, (b) adding the missing states below, and (c)
possibly adding an explanatory/AI presentation layer over it.

## Desired output (already partially real)

| State | Exists today? |
|---|---|
| READY | YES — implicit (no blockers returned) |
| BLOCKED | YES — explicit blocker list returned by `check_patient_billing_readiness` |
| AT RISK | **NO** — today's engine is binary (blocked or not); there is no "at risk but not yet blocked" intermediate state (e.g., "cert expires in 3 days, still valid today, but will block tomorrow") |

## Example (from the directive) mapped to real code

> BLOCKED — Reason: Certification expired

Maps to: `_has_finalized_certification` returning false →
`categorize_blocker` → blocker string returned to caller. **Already
real.**

> BLOCKED — Reason: Recert due

**Not yet a distinct blocker** — "recert due" (a forward-looking date)
is different from "certification expired" (already past). Today's
engine only detects the *already-expired* case as a blocker; "recert due
soon" would need to be added as a new, distinct check (borrowing the
`daysUntil` logic from `PocCertificationPage.tsx`).

> BLOCKED — Reason: Benefit period invalid

**Not yet a distinct, named blocker.** `get_active_benefit_period` can
return `None` or raise `ValueError` (overlapping periods) — whether
`check_patient_billing_readiness` currently surfaces *that specific
failure* as a labeled blocker (as opposed to erroring some other way) was
not confirmed this pass.

> BLOCKED — Reason: Election missing

Since there is no separate Election entity (confirmed in the prior
pass), this maps to "no `BenefitPeriod` row / no `election_date`" —
whether this is already a distinct, named blocker in the current engine
was not confirmed this pass.

## Inputs (already real, confirmed)

Certification finalization, F2F attestation, Plan of Care physician
approval, NOE filing timeliness (`filed_within > 5` without an exception
reason), payer sequence resolvability.

## Inputs (would need to be added)

Recert-due-soon (forward-looking), explicit benefit-period-invalid
labeling, explicit election-missing labeling, an AT RISK intermediate
tier with its own threshold logic.

## Rules

Every existing rule already returns a short, specific reason string
(`categorize_blocker`) — this is exactly the "must explain, not just
score" principle already required by the project, and the existing code
already follows it. Any new AI layer added on top must preserve this
property: every recommendation must carry Reason + Evidence + Source
Data + Dependency + Missing Requirement, per the explicit design
principle — not a bare READY/BLOCKED label with no explanation.

## Dependencies

`billing_readiness_service.py`, `BenefitPeriod` (via the resolver),
certification/F2F/POC tables, NOE fields on `BenefitPeriod`, payer
sequence logic (location not re-confirmed this pass).

## Evidence

Every blocker the engine returns today is traceable to a specific
boolean check against a specific table/column — this traceability is
already a strength to preserve, not something to add.

## User Experience

Today: `BillingOverviewPage.tsx` shows blocker reasons in prose form.
Any future engine should keep this per-reason clarity; an "AI" framing
should not collapse the existing specific reasons into a vaguer summary.

## Auditability

**Not yet confirmed** whether a readiness check's *result* (as opposed
to the underlying data it read) is itself logged anywhere — i.e., can
SNS show "on this date, this patient was BLOCKED for this reason,"
historically, or does it only compute readiness fresh, on demand, with
no history of past computed results? Not investigated this pass; flagged
as an open question the engine's design would need to resolve before
build.

## Not built. Awaiting go-ahead per explicit instruction.

---

## Phase 3 spec-review addendum (2026-09-08)

Directive requirement: "the readiness engine must answer why can/can't
I bill this patient... inputs should include Election, Certification,
Benefit Period, Recertification, NOE, Claim State... do not allow
readiness scoring to ignore upstream eligibility failures."

**Re-checked against the original spec's own inputs list**: Certification
(YES, already an input), F2F (YES), Plan of Care (YES), NOE filing
timeliness (YES), payer sequence (YES). **Missing from the original
spec's input list, now added per this review**: an explicit **Benefit
Period validity** input (does an active, correctly-sequenced benefit
period exist at all for this patient — as opposed to just checking
certification/F2F/POC in isolation) and an explicit **Claim State**
input (is there already a claim in a state that makes "is this patient
billable" a different question, e.g. a claim already `PAID` for the
current period).

**Critical finding from this review**: because
`certification_gated_eligibility_review.md` confirms benefit periods can
be created without certification, the readiness engine's Benefit-Period
input, if added naively, would only be able to say "a benefit period
exists" — not "a *validly-gated* benefit period exists." **The readiness
engine must not treat "a BenefitPeriod row exists" as equivalent to "this
patient's eligibility chain is valid."** Until eligibility-chain gating
is fixed (or until the readiness engine independently re-verifies
certification/recert validity itself, which `check_patient_billing_
readiness` already does today for certification specifically), the
engine's BLOCKED/READY answer already correctly does **not** rely on the
unverified benefit-period creation step — it re-derives certification
validity itself rather than trusting that a benefit period's mere
existence implies a valid certification. **This is confirmed to already
be true of the existing code** (`_has_finalized_certification` is
checked independently in `billing_readiness_service.py`, not inferred
from `BenefitPeriod` existing) — so the spec's core safety property
(does not ignore upstream eligibility failures) already holds for
certification specifically. It does **not yet** account for benefit
period *sequencing* validity itself (e.g., an out-of-order or
duplicate-purpose period) as its own distinct check — flagged as a gap
to close before implementation, not assumed already covered.
