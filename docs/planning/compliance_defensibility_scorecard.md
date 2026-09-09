# Compliance Defensibility Scorecard (Phase 41)

Status: verification synthesis. No production code changed. No billing feature or AI built. Scores
reconfirm and extend `reimbursement_defensibility_review.md`'s Phase 32 scorecard with three new
categories (Medical Record, Plan of Care, Interdisciplinary Review) evaluated this phase.

| Category | Score | Evidence |
|---|---|---|
| Election | 4 (Strong) | Real `election_signed_at`; real addendum-request/delivery tracking for the current rule. Not 5: no confirmed user-attribution for the signing event itself (Phase 37), and the 10/1/2026 mandatory-furnish gap (Phase 36). |
| Certification | 5 (Fully Defensible) | Real lifecycle, real physician-role attribution, real append-only `CertificationStatusEvent` audit trail, structured narrative fields satisfying 42 CFR 418.22's evidentiary requirement. Unchanged from Phase 32. |
| Recertification | 3 (Adequate) | Shares Certification's strong model; lacks a distinct Recert Overdue signal (one new query away, per Phase 39); F2F 30-day window validation not independently reconfirmed. |
| Benefit Period | 2 (Weak) | Correct calculations, atomic technical guarantees, proven by test execution — but zero certification gate at creation and zero audit trail. Unchanged, most consequential finding across this entire engagement. |
| NOE | 3 (Adequate) | Real fields, real timeliness blocker; acceptance-vs-submission distinction unconfirmed (real defensibility risk if the distinction doesn't exist, since the CMS clock legally runs to MAC acceptance). |
| Claim | 2 (Weak) | Pre-existing, unchanged: 2 of 3 `Claim.status` writers unenforced/unaudited. |
| Remittance | 2 (Weak) | Dashboard 835 widget confirmed fabricated; underlying real payment ledger not reconfirmed this pass — scored conservatively, not assumed. |
| Payment | 2 (Weak, provisional) | Same basis as Remittance — not independently re-verified this session. |
| Audit Trail (overall, cross-cutting) | 3 (Adequate, uneven) | Excellent for Certification, Admission, and clinical-note amendments; absent for Benefit Period; unconfirmed for Billing Readiness (no historical persistence at all, confirmed this pass — Phase 37). |
| Medical Record (overall documentation quality) | 4 (Strong) | Certification narrative fields, Admission status history, clinical-note `Amendment` model, and Referral's creation/review attribution are all real, structured records — not free-text-only documentation. |
| Plan of Care | 3 (Adequate, provisional) | A physician-approval check (`_has_physician_approved_plan_of_care`) exists and is real (confirmed in prior segment's billing-readiness review), but its own version history/audit trail was not independently verified in this or any prior phase — scored as adequate rather than strong pending that confirmation, not assumed either way. |
| Interdisciplinary Review (IDG) | 3 (Adequate, provisional) | An `IDG_REVIEW` task is real and auto-seeded on every benefit-period rollover (confirmed, `benefit_period_service.py`), giving a genuine trigger mechanism — but whether task *completion* is itself checked or audited anywhere downstream was not verified in this or any prior phase. |

## Overall read
The pattern is now consistent across every phase of this engagement, not a one-time observation: SNS's
**individual clinical/regulatory records are strong** (Certification, Admission, clinical-note
amendments, Election's core fields, Plan-of-Care/IDG triggers all real and non-fabricated). The
**consistently weak points are narrower and more specific than "billing is broken"**: (1) Benefit
Period's creation-gating and audit trail, (2) the complete absence of historical persistence for the
Billing Readiness verdict (meaning "why/who/when billable" can only ever be answered as of *today*, not
retrospectively), and (3) two pre-existing, unchanged, previously-documented issues (Claim status
writer gaps, fabricated remittance widget) that are real but were already known before this compliance-
focused reframing began.

No production code has changed. No billing feature or AI has been built.
