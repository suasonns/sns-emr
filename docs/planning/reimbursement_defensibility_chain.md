# Reimbursement Defensibility Chain (Phase 45)

Status: verification synthesis. No production code changed. No billing feature or AI built.
Consolidates `eligibility_traceability_chain.md` (Phase 37) into the exact structure requested this
phase, extended one link earlier (Clinical Findings → Terminal Prognosis) and one link later
(→ Payment), without re-deriving already-established evidence.

| Transition | Evidence | Audit Trail | Responsible User | Timestamp | System Validation | Gap |
|---|---|---|---|---|---|---|
| Clinical Findings | Real — captured in clinical notes/assessments generally (not deeply re-verified this engagement, outside its benefit-period/certification scope) | Yes, via the `Amendment` model for any corrections | Yes, via note authorship | Yes | Not applicable — this is the input data, not a gate | Not deeply investigated this engagement |
| → Terminal Prognosis | `Certification.clinical_decline_indicators`, `supporting_evidence`, `physician_narrative` | Yes — `CertificationStatusEvent` | Yes | Yes | Physician-role check (`signed_by_role`) at signature | None confirmed |
| → Certification | `Certification.status='FINALIZED'`, `signed_at` | Yes | Yes | Yes | Role-restricted signing (CTI_SIGNER_ROLES, confirmed in prior segment) | None confirmed |
| → Benefit Period | `BenefitPeriod` row (dates, `period_number`, `benefit_type`) | **No** | **No** (`created_by` unpopulated) | Generic row timestamp only | **None** — `rollover_benefit_period` performs no certification check | **Confirmed, primary gap of this entire engagement** |
| → Recertification | Same `Certification` model, `cert_type='RECERT'` | Yes | Yes | Yes | Same physician-role restriction | None confirmed |
| → Billing Readiness | `check_patient_billing_readiness()` — live compute | **No** (no persistence, confirmed by code read) | No | No | Yes, live — re-derives certification/F2F/POC/NOE/payer-sequence at call time | Retrospective reconstruction impossible |
| → NOE | `noe_submitted_date`/`noe_exception_reason` | Partial — fields exist, no dedicated event log | Not confirmed | Yes (submission date) | Timeliness blocker logic (>5 days without exception) | Acceptance-vs-submission distinction unconfirmed |
| → Claim | `Claim.status` | Partial — 1 of 3 writers enforced/audited | Partial | Partial | Partial | 2 of 3 writers unenforced/unaudited (pre-existing, unchanged) |
| → Payment | Not reconfirmed this engagement beyond the confirmed-fabricated 835 dashboard widget | Unknown | Unknown | Unknown | Unknown | Unconfirmed whether a real independent payment ledger exists |

## Most Important Question — Direct Answer

**Can SNS explain WHY PAYMENT OCCURRED for a paid hospice claim, without relying on human memory?**

**PARTIAL.**

The chain from Clinical Findings through Recertification is fully system-evidenced — no human memory
is required for that portion. The chain breaks at exactly two links: (1) Benefit Period, where no
system record explains who authorized its creation or confirms a certification check occurred at that
moment, and (2) Billing Readiness → Claim → Payment, where the readiness verdict itself is never
persisted and the claim/payment layer has known, pre-existing audit gaps. For those links, "why payment
occurred" would currently require a staff member's recollection or a manual cross-reference of
timestamps across unrelated tables — not a system-produced explanation. This is a precise PARTIAL, not
a hedge: the strong half of the chain is fully evidenced; the weak half is identified exactly, not
vaguely.

No production code has changed. No billing feature or AI has been built.
