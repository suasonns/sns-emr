# Certification-Gated Eligibility Review

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

## MOST IMPORTANT QUESTION — answered first, no hedging

**"Can SNS currently create a billable benefit period for a patient who
lacks a finalized certification?"**

# YES.

Evidence follows below. This is a real, confirmed gap, not a
theoretical one.

---

## Question 1 — Can BenefitPeriod creation occur without Initial Certification?

# YES.

Evidence: `rollover_benefit_period` (`app/services/benefit_period_service.py`)
takes exactly five business inputs — `tenant_id`, `patient_id`,
`election_date`, `start_date`, `benefit_type`. Its full logic (locking
existing rows, idempotency check, chronology validation, period-number
computation, CMS period-length computation, closing the old period,
creating the new one) contains **zero references** to any certification
table, certification model, or certification-status check. The function
was read in full this pass (again, for this specific question) — no
certification lookup exists anywhere in it.

## Question 2 — Can BenefitPeriod advancement occur without Recertification?

# YES.

Evidence: `benefit_type` is accepted as a bare string, validated only
against the literal set `{"INITIAL", "RECERT"}` (a type-format check,
not a business check). Nothing verifies that an actual recertification
record/event exists before accepting `benefit_type="RECERT"`. A caller
can pass the string `"RECERT"` with no underlying recertification having
occurred.

## Question 3 — Can `rollover_benefit_period` execute when Certification Expired?

# YES.

Evidence: same as Question 1 — the function has no certification-status
read of any kind, so an expired certification (or no certification, or a
never-existing certification) is indistinguishable to this function; all
are simply "not checked."

## Question 4 — Can `rollover_benefit_period` execute when no finalized certification exists?

# YES.

Same evidence as Questions 1 and 3. This confirms the earlier pass's
finding, re-verified specifically for this question, not merely
cross-referenced.

## Question 5 — Can administrators manually create benefit periods bypassing certification?

# YES.

Evidence: `POST /benefits/` (`rollover_benefit_period_endpoint`,
`app/api/benefits.py`) is role-gated to `RN`/`Administrator`
(`require_roles(["RN", "Administrator"])`) — that is the **only** guard
present. The endpoint validates date formats and UUID formats, then
calls `rollover_benefit_period` directly with no additional
certification check of its own. An Administrator (or RN) account can
call this endpoint for any patient, any dates, either `benefit_type`,
with no certification on file at all.

## Question 6 — Can API callers create benefit periods bypassing certification?

# YES.

Same endpoint, same evidence as Question 5 — "administrator" and "API
caller" are the same code path here; there is no separate, stricter
internal-only path. Any authenticated caller holding an `RN` or
`Administrator` role token can call `POST /benefits/` directly (e.g. via
`curl`/Postman/a future automated script) exactly as a UI would, with
identical lack of certification enforcement.

## Question 7 — What protects Benefit Period → Recertification → Benefit Period from invalid sequences?

Documented, exhaustively, because the honest answer is "less than the
question implies":

| Protection | Exists? | What it actually protects against |
|---|---|---|
| Row locking (`with_for_update`) | YES | Concurrent double-rollover race conditions — a technical integrity protection, not a business-rule protection |
| Idempotency check (same start_date/benefit_type/tenant/patient) | YES | Accidental duplicate calls with identical parameters — prevents duplicate rows, not invalid business sequences |
| Chronology validation (`start_date` not before current BP's `start_date`) | YES | Backward-dated periods — a date-ordering protection only |
| Certification-finalized check | **NO** | — |
| Certification-not-expired check | **NO** | — |
| Recertification-actually-occurred check | **NO** | — |
| Benefit-type/certification-consistency check (e.g., can't roll to "RECERT" without a recert record) | **NO** | — |

**Conclusion: the only protections in place are technical/structural
(concurrency, duplication, date ordering) — there is no business-rule
protection tying benefit-period advancement to certification or
recertification state at all.** The two systems (certification and
benefit period) are architecturally independent; nothing enforces their
intended dependency.

## Question 8 — Audit trail for Benefit Period Created / Rolled / Corrected / Closed

| Action | Endpoint | Writer | Audit event? | Timestamp? | User attribution? |
|---|---|---|---|---|---|
| Created (first period) | `POST /benefits/` | `rollover_benefit_period` | **NO** — no `append_audit_event`/`build_audit_event` call anywhere in the function | Implicit only (row's own `created_at`, if the `BaseModel` base class provides one — not independently confirmed this pass) | **NO** — `BenefitPeriod.created_by` column exists on the model but is **never populated** by `rollover_benefit_period` (confirmed by reading the full `BenefitPeriod(...)` constructor call — no `created_by=` argument is passed) |
| Rolled (subsequent period) | `POST /benefits/` | same | **NO** | Same | Same — no attribution captured despite the endpoint requiring an authenticated user (`user=Depends(require_roles(...))`) whose identity is available but simply not written to the row |
| Corrected | — | **No correction workflow exists at all** (consistent with the claim-status findings — there is no "correct a benefit period" action anywhere in the codebase) | N/A | N/A | N/A |
| Closed | (side effect of the next rollover call, not an independent action) | `rollover_benefit_period` (closes the *previous* current period as part of creating the next) | **NO** | Only if `end_date` counts as a timestamp of closure (it does, functionally) | **NO** |

**Conclusion: zero audit events exist for any benefit-period lifecycle
action.** This is the same pattern already found for two of the three
`Claim.status` writers — a real, recurring architectural gap, not
specific to billing alone.

---

## Full eligibility chain trace

Election → Certification → Benefit Period → Recertification → Benefit
Period → Billing Readiness

| Transition | Required? | Optional? | Enforced? | Documented? | Audited? |
|---|---|---|---|---|---|
| Election → Certification | Should be required (CMS rule: election triggers the certification requirement) | — | **NOT enforced in code** — no check that a `BenefitPeriod.election_date` value is backed by a real certification before/after | Documented here and in `benefit_period_engine_review.md` | No |
| Certification → Benefit Period | Should be required | — | **NOT enforced** — confirmed Q1/Q3/Q4 above | Documented here | No |
| Benefit Period → Recertification | Should be required before rolling to the next period | — | **NOT enforced** — confirmed Q2 above | Documented here | No |
| Recertification → Benefit Period (next) | Should be required | — | **NOT enforced** — same mechanism, `benefit_type="RECERT"` is just a string | Documented here | No |
| Benefit Period → Billing Readiness | **YES — this one IS enforced** | — | **YES** — `check_patient_billing_readiness` independently re-checks certification/F2F/POC/NOE/payer-sequence at readiness-check time, regardless of what was or wasn't checked when the benefit period was created | Documented in `billing_readiness_spec.md` | Not confirmed whether the *readiness check's result itself* is logged historically (open item from `billing_readiness_spec.md`) |

**The one enforced link in the whole chain is the last one.** Everything
upstream of "does this patient currently pass a billing-readiness check"
is unenforced at the point of creation — the system only catches an
invalid patient at the *billing* gate, not at the *eligibility-advancement*
gate. A patient can have an entirely unfounded sequence of benefit
periods created, and the only thing preventing them from actually being
billed is the separate, independent readiness check running later in
the pipeline.

**This is architecturally sound as a safety net (readiness is genuinely
robust and would catch most bad states before money moves) but is not
what "certification-gated eligibility" means** — the directive's framing
is correct: eligibility *advancement* itself should be gated, not just
final billing.
