# Hospice Billing Architecture Review (Eligibility-First Reframing)

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

This document reframes the billing review around the real hospice
reimbursement lifecycle, per explicit directive: eligibility is upstream
of claims, not an afterthought to them. Nothing here contradicts the
Phase 4–6 claim/payment findings already documented in
`billing_inventory_and_gap_analysis.md`, `claim_status_architecture.md`,
`payment_posting_architecture.md`, `billing_action_map.md`,
`billing_user_capability_matrix.md`, `biller_persona_matrix.md`, and
`revenue_leakage_review.md` — those remain valid and are referenced,
not repeated, where they already answer a question asked here.

## 0. Hospice Billing Lifecycle Map

```
Referral → Admission → Election of Hospice Benefit → Certification of
Terminal Illness → Benefit Period Assignment → Plan of Care →
Eligibility Maintenance → Recertification → Level of Care Tracking →
Claim Creation → NOE Tracking → Claim Submission → Remittance →
Payment Posting → Revenue Reporting
```

| Stage | SNS status this pass |
|---|---|
| Referral → Admission | Not re-verified this pass (`referral.py`/`Admission` models exist; automatic-linkage confidence carried forward as **UNKNOWN** from Phase 5, not newly investigated) |
| Election of Hospice Benefit | **NO separate `Election` model exists.** `election_date` is a column directly on `BenefitPeriod` (`app/models/benefit_period.py:49`) — election is not tracked as its own entity/lifecycle, it is one field on the benefit-period row. This resolves a previously-open "Election SSOT" question: the SSOT *is* `BenefitPeriod`, by construction, because there is nothing else. |
| Certification of Terminal Illness | Real, enforced (`_has_finalized_certification` gate in `billing_readiness_service.py`) |
| Benefit Period Assignment | Real (`BenefitPeriod` table: `benefit_type`, `period_number`, `start_date`, `end_date`, `is_current`) |
| Plan of Care | Real, enforced (`_has_physician_approved_plan_of_care` gate) |
| Eligibility Maintenance | Real, computed on demand (`check_patient_billing_readiness`), not a standing/background job (see Phase 1 below) |
| Recertification | Real (same `BenefitPeriod.end_date` drives the recert-due display in `PocCertificationPage.tsx`) |
| Level of Care Tracking | Real, with an enforced overlap guard (`level_of_care_overlap_guard.py`) — see Phase 6 |
| Claim Creation → Payment Posting | Already fully documented — see `claim_status_architecture.md` and `payment_posting_architecture.md`; summarized in Phase 5 below, not re-litigated |

**The framing correction this document makes**: the earlier claims-first
audit treated "Election," "Certification," and "Benefit Period" as three
peer line-items in an inventory table. They are not peers — Election is
not even a distinct data concept in this codebase, it is a field owned
by Benefit Period, which is itself gated by Certification. The real
dependency chain is narrower and more load-bearing than a flat inventory
table implied.

---

## PHASE 1 — Hospice Eligibility Foundation

| Concept | Screen | API | Service | Table | Source of Truth | Audit Trail | User Workflow | Status |
|---|---|---|---|---|---|---|---|---|
| Election | (none dedicated — no screen shows "election" as its own concept) | (none dedicated) | n/a | `BenefitPeriod.election_date` | `BenefitPeriod` | Same audit posture as Benefit Period (row-level only, no dedicated event log) | Implicit, created alongside benefit period | **PARTIAL** — real data exists, but there is no election-specific screen, API, or audit event; a biller cannot ask "when did this patient elect" without going through the benefit-period view |
| Certification | `PocCertificationPage.tsx` | `GET /billing/poc-certification-status` | `billing_readiness_service.py` (`_has_finalized_certification`) | (certification table, gated not owned by billing_readiness_service) | Certification finalization flag | Enforced as a readiness blocker | Real, wired screen | **PRODUCTION READY** (confirmed Phase 6) |
| Recertification | Same screen (recert = approaching benefit-period end) | Same endpoint | Same | `BenefitPeriod.end_date` | `BenefitPeriod` | Same as Benefit Period | Real, wired screen, 14-day window | **PRODUCTION READY** (confirmed Phase 6) |
| Benefit Period | (claim/certification screens reference it; no dedicated benefit-period screen with full history found this pass) | `get_active_benefit_period` (`benefit_period_resolver.py`) resolves the *active* period only | `benefit_period_resolver.py` | `BenefitPeriod` | `BenefitPeriod` | Row-level only | Read via readiness checks and cert-status screen | **PARTIAL** — the active period is resolvable; there is no confirmed screen/API for *full benefit-period history* as its own view (carried forward as open item, not re-verified this pass) |
| Terminal Prognosis Support | Not re-investigated this pass — this is RNICA/clinical-documentation territory, explicitly frozen per the "RNICA is now frozen" instruction from the prior priority shift; treated as **out of scope for re-audit**, referenced only as an upstream input to certification | — | — | — | — | — | — | **OUT OF SCOPE (frozen)** |
| Plan of Care | Gated the same way as Certification | Same readiness endpoint | `_has_physician_approved_plan_of_care` | (POC table) | POC approval flag | Enforced as a readiness blocker | Enforced, not separately screened this pass | **BACKEND CONFIRMED / frontend screen not re-verified this pass** |

### Direct answers

**"Can SNS answer: why is this patient eligible for hospice today?"**
**Partially.** SNS can answer *why a patient passes the billing-readiness
check* (certification, F2F, POC, NOE timing, payer sequence — see
`check_patient_billing_readiness`), which is a close proxy for hospice
eligibility but is explicitly a *billing* readiness check, not a
clinical eligibility determination. Six-month-prognosis / terminal-status
clinical support itself is RNICA territory and was not re-audited this
pass (frozen per prior instruction). So: **YES for the billing-relevant
subset of eligibility, UNKNOWN/OUT-OF-SCOPE for the underlying clinical
prognosis determination itself.**

**"Can SNS answer: why is this patient eligible for billing today?"**
**YES.** This is exactly what `check_patient_billing_readiness` computes
and exposes via `BillingOverviewPage.tsx`, with specific, real blocker
reasons (missing cert, missing F2F, missing POC approval, ambiguous
payer sequence, late NOE without exception reason). This is the
strongest, most production-ready capability found across this entire
review.

---

## PHASE 2 — Certification Lifecycle

| Item | Classification |
|---|---|
| Initial Certification | **IMPLEMENTED**, enforced as a readiness gate |
| Recertification | **IMPLEMENTED**, driven by `BenefitPeriod.end_date`, surfaced in `PocCertificationPage.tsx` |
| Certification Expiration | **IMPLEMENTED** — 14-day window, sorted soonest-first, overdue shown distinctly |
| Physician Association | Not re-verified this pass — carried forward as unconfirmed, not assumed either way |
| Medical Director Association | Not re-verified this pass — same |
| Certification Tracking | **IMPLEMENTED** (same screen/endpoint) |
| Certification Reporting | **IMPLEMENTED** (the tracking screen doubles as the report — there is no separate "certification report" artifact found, which is fine operationally but worth naming precisely) |
| Certification Alerts | **PARTIAL** — the screen visually distinguishes overdue (red) vs. approaching (amber), but this is an on-screen visual cue, not a push/proactive alert (e.g. no email/notification found this pass) |

### Direct answer

**"If a biller asks: which patients require recertification in the next
14 days? Can SNS answer? Show evidence."**

**YES.** Evidence: `PocCertificationPage.tsx` computes
`daysUntil(r.benefit_period.end_date)`, filters to `days <= 14`, sorts
ascending, and renders both the "POC Expiring Soon" count and a list
with each patient's remaining/overdue day count — backed by the real
`GET /billing/poc-certification-status` endpoint (`fetchPocCertificationStatus`
in `api/dashboard.ts`), not mock data. This was confirmed by direct
source read (`sns-emr-frontend/src/pages/billing/PocCertificationPage.tsx`
lines 23, 75–93, 150–190), not inferred from the page existing.

---

## PHASE 3 — Benefit Period Lifecycle

| Item | Status | Evidence |
|---|---|---|
| Creation | Real (`BenefitPeriod` rows exist with `period_number`, `benefit_type`) | `app/models/benefit_period.py` |
| Tracking | Real | Same |
| Status (`is_current`) | Real, explicit boolean column | Same |
| Calculation (active period resolution) | Real | `get_active_benefit_period` (`benefit_period_resolver.py`) |
| Change logic (rollover to next period) | **Not confirmed this pass** — no function found named/behaving like "roll to next period" or "create period N+1"; only *resolving the current* period was found, not *advancing* it. Carried forward as an open item, explicitly flagged rather than guessed at. | grep for benefit-period creation/rollover logic beyond the resolver found nothing further this pass |
| Recertification Dependency | Real — recert due date **is** `BenefitPeriod.end_date`, directly | `PocCertificationPage.tsx` |
| Reporting | Partial — surfaced only via the cert-status screen, no dedicated "benefit period report/history" screen confirmed | — |
| Audit Trail | Row-level only (no dedicated benefit-period audit event log found this pass) | — |

### Direct answers

- **Current Benefit Period?** YES — `get_active_benefit_period` resolves it directly.
- **Next Benefit Period?** **UNKNOWN / likely gap** — no rollover/advancement logic was found this pass; whether a "next" period is pre-created, computed on demand, or must be manually created was not confirmed. Flagged, not assumed.
- **Recert Due Date?** YES — `BenefitPeriod.end_date`, surfaced on `PocCertificationPage.tsx`.
- **Benefit Period History?** **PARTIAL/UNKNOWN** — the table clearly supports it (`period_number`, `is_current` imply a full row-per-period history exists in the data), but no confirmed screen/report surfaces that full history to a user this pass.

**Gap to document**: "next benefit period" and "full benefit-period
history as its own view" are both real, plausible, and *not yet
confirmed* — this is a good, concrete Phase-1-after-Thursday candidate,
distinct from (and smaller than) the claim-status/835 issues already
documented.

---

## PHASE 4 — NOE Review

Already substantially covered in `biller_persona_matrix.md` and
`payment_posting_architecture.md`; restated here in the NOE-specific
framing requested:

| Question | Answer | Evidence |
|---|---|---|
| Which NOEs are due? | **PARTIAL/UNKNOWN** — `NoeTrackingPage.tsx` shows submission status; whether it proactively computes "due" (i.e., approaching the 5-day filing deadline referenced in `billing_readiness_service.py:277`) versus only showing already-submitted/not-submitted state was not re-verified this pass | `billing_readiness_service.py:277` (`filed_within > 5`) is a *readiness blocker check*, not confirmed as a *forward-looking due-date list* |
| Which NOEs are overdue? | Same caveat — the readiness blocker fires per-patient at readiness-check time; a dedicated "overdue NOE list" report was not confirmed this pass | — |
| Which NOEs were submitted? | **YES** | `NoeTrackingPage.tsx` / `GET /billing/noe-tracking` |
| Which NOEs failed? | **NO** — no concept of NOE submission failure (as distinct from "not yet submitted") was found | Consistent with the broader "no transmission-failure concept exists anywhere" finding in `claim_status_architecture.md`/`revenue_leakage_review.md` |

---

## PHASE 5 — Claim Architecture Review (in context, not repeated)

Full detail already exists and is not re-litigated: see
`claim_status_architecture.md` (writers, readers, statuses, transitions,
audit trail per writer) and `payment_posting_architecture.md` (835
pipeline). The one framing addition this pass: **claims are downstream
of a genuinely strong eligibility foundation.** The claim-status bug and
the fake 835 widget are real and serious, but they sit at the *end* of a
pipeline whose *beginning* (readiness, certification, recert, benefit
period) is the most production-ready part of the whole system. A
demo/roadmap conversation should lead with that strength, not bury it
under the claims-side defects.

---

## PHASE 6 — Level of Care Review

| Item | Status | Evidence |
|---|---|---|
| Storage | Real — LOC is stored per service-level model (`_model_for_service_level` dispatches by LOC type in `level_of_care_overlap_guard.py`), referenced from `visits.py`/`patients.py` | `app/services/level_of_care_overlap_guard.py:29` |
| Workflow | An enforced **overlap guard** exists: `ensure_no_level_of_care_overlap` raises `LevelOfCareOverlapError` when a new LOC period would overlap an existing active one | `level_of_care_overlap_guard.py:21,74` |
| Billing usage | Not re-confirmed this pass whether/how LOC feeds claim-line pricing directly (the rate-schedule/pricing gap was already documented separately as a placeholder in the master doc's Section 11) | Carried forward, not re-verified |
| Reporting | Not confirmed this pass — no dedicated LOC report/screen found | — |
| Source of Truth | The per-service-level table(s) dispatched by `_model_for_service_level` | — |
| Audit Trail | The overlap guard itself is a preventive control, not an audit log — whether LOC *changes* are logged after the fact was not confirmed this pass | — |

### Direct answers

- **Can LOC changes be audited?** **UNKNOWN** — a preventive guard exists (can't create an overlapping period), but no confirmed after-the-fact change log was found.
- **Can LOC history be reconstructed?** **LIKELY, PARTIALLY** — since overlaps are prevented, the underlying rows should form a valid non-overlapping timeline by construction, but no dedicated "LOC history" view was confirmed.
- **Can billing explain why a claim used a specific LOC?** **UNKNOWN** — not traced this pass; flagged as an open item rather than assumed either way.

---

## Top 10 Billing Risks (eligibility-first ranking — replaces the earlier claims-first Top 10)

Ranked by how early in the lifecycle the risk sits and how much it could
silently invalidate everything downstream of it:

1. **CRITICAL — No confirmed benefit-period rollover/advancement logic.** If "next benefit period" isn't reliably created, every downstream step (recert, claim, NOE) for period N+1 has nothing to attach to. (Phase 3, new finding this pass.)
2. **CRITICAL — No transmission-confirmation data model.** A claim can be marked "sent" with zero proof of actual transmission. (Restated from `claim_status_architecture.md`.)
3. **CRITICAL — "Export to Excel" can silently revert a PAID claim, with no audit event.** (Restated from `billing_action_map.md`.)
4. **HIGH — Election has no dedicated audit trail or screen.** It is a single column on `BenefitPeriod`; a biller cannot answer "when/how was this election recorded" independently of the benefit-period row. (Phase 1, new finding this pass.)
5. **HIGH — No confirmed "NOE due/overdue" forward-looking list**, only submitted/not-submitted state and a readiness-time blocker check. (Phase 4.)
6. **HIGH — 835 ingestion has no upload UI**, so real remittances may never enter the system in practice regardless of backend correctness. (Restated from `payment_posting_architecture.md`.)
7. **MEDIUM — No confirmed benefit-period history view.** The data likely supports it; no screen was confirmed to expose it. (Phase 3.)
8. **MEDIUM — The 835 Remittance dashboard widget shows fabricated data.** (Restated.)
9. **MEDIUM — Unmatched remittances are retained but not surfaced to billers.** (Restated from `biller_persona_matrix.md`.)
10. **LOW/UNKNOWN — LOC change audit trail and LOC-to-claim traceability not confirmed.** Preventive overlap guard exists (a real strength), but after-the-fact auditability is unverified. (Phase 6, new finding this pass.)

**Framing note**: prior to this pass, the highest-ranked risks were all
claims/EDI-side. This pass surfaces that the *highest-leverage* new risk
(#1, benefit-period rollover) sits far upstream of claims — consistent
with the directive's thesis that eligibility problems should be found
before claims problems, because an eligibility problem invalidates
everything after it.
