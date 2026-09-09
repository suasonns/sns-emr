# Revenue Leakage Detector — Design Spec

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

**Design only — nothing in this document has been implemented.**
Restates and extends `revenue_leakage_review.md` in the specific
per-step format requested (stall / money-loss / silent-failure /
AI-alertability), now including the eligibility-side steps that document
covered less thoroughly, and folding in this pass's benefit-period
correction.

| Step | Can the workflow stall? | Can money be lost? | Can the error go unnoticed? | Can AI alert the user (if built)? |
|---|---|---|---|---|
| Election | N/A as a distinct step (no separate entity — see `benefit_period_engine_review.md`) | No direct money risk here | N/A | N/A |
| Certification | YES — if never finalized, billing-readiness blocks correctly (confirmed working gate) | No — the gate prevents billing, it doesn't lose money, it correctly withholds it | **NO** — surfaced today via `BillingOverviewPage.tsx`'s explicit blocker reason | Yes — this is Priority 3 (Billing Readiness Engine), already mostly real |
| Benefit Period (current) | NO — resolver is robust, integrity-checked | No | No | N/A — already solid |
| Benefit Period (next/rollover) | **YES, operationally** — the engine is correct, but nothing calls it automatically or from any UI (confirmed this pass); a patient's next period may simply never get created because no one clicked a button that doesn't exist | **YES, indirectly** — if the next period is never created, nothing downstream (recert, claim) has a period to attach to, which can silently halt billing for that patient indefinitely | **YES — this is the most dangerous kind of gap**: there is no error, exception, or alert when a rollover simply never happens; it is an absence of action, not a failure that raises anything | Yes — this is now the corrected Priority #1 (Benefit Period Monitor) |
| Recertification | YES — if recert doesn't happen before benefit-period end, billing-readiness should catch it via the certification-finalized check on the new period, but "recert due soon" is not itself a distinct proactive alert (see `certification_monitor_spec.md`) | Indirect, same mechanism as Certification | Partially — the 14-day display is passive (must be viewed), not a push alert | Yes — Priority 2 (Certification Monitor) |
| Billing Readiness | NO — the check itself is robust and correctly enforced | No — it withholds billing correctly when blocked | No — explicit reasons shown | Already substantially real (Priority 3) |
| NOE | YES — "due/overdue" as a forward-looking list is not confirmed to exist (see `hospice_billing_architecture_review.md` Phase 4); only submitted/not-submitted state is confirmed | Yes, indirectly — a late/missed NOE can affect reimbursement per CMS rules (the `filed_within > 5` check exists as a readiness blocker, so this is at least partially caught) | Partially — caught at readiness-check time, but no dedicated forward-looking "NOEs due this week" list confirmed | Not yet designed — would extend Certification Monitor's pattern |
| Claim Status | YES — confirmed backward-transition defect (`export_patient_claim_edi`) | **YES, directly** — a claim silently reverted from PAID to SENT could be mistaken for unpaid and inappropriately re-worked, re-billed, or reported as outstanding when it was already settled | **YES — no audit event on this specific writer**, so the corruption leaves no trace pointing to its cause | Not yet designed; governance fix (`claim_state_machine.md`) should precede any AI layer here |
| Transmission | N/A — no data model exists to detect stalls in a step that isn't represented at all | Unknown — cannot detect leakage in a step with no representation | **YES by definition** — an unmodeled failure mode is inherently invisible | Cannot be designed until the data model exists |
| Remittance | YES — 835 upload has no UI, so remittances may simply never be posted in day-to-day operation | **YES, directly** — a real payment that arrives (paper EOB, portal download) but is never uploaded as an 835 never gets posted at all | **YES** — nothing flags "we expected a remittance and got none" | Yes — natural extension of Priority 4 (Revenue Leakage Monitor) |
| Payment matching | NO — unmatched payments are explicitly preserved (`match_status="UNMATCHED"`), not dropped | No — money is recorded even when unmatched | **YES for practical purposes** — recorded but not surfaced to any biller screen | Yes — straightforward: surface the existing `UNMATCHED` records |

## Updated ranking (supersedes `revenue_leakage_review.md`'s ranking, given this pass's benefit-period correction)

1. **CRITICAL (new #1)** — Benefit period rollover is correct but has no
   trigger; a patient's next period may never be created, and nothing
   raises an error when it isn't. This is the most dangerous class of
   gap in this whole review: silence, not failure.
2. **CRITICAL** — Claim status can move backward with no audit trail
   (`export_patient_claim_edi`).
3. **CRITICAL** — No transmission-confirmation data model exists at all.
4. **HIGH** — 835 remittances cannot be uploaded through any UI.
5. **MEDIUM** — Unmatched payments are safely retained but invisible to
   billers.
6. **MEDIUM** — NOE due/overdue forward-looking list not confirmed to
   exist.
7. **LOW** — Certification/recert alerts are passive, not push-based.

## Not built. Awaiting go-ahead per explicit instruction.
