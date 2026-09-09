# Reimbursement Compliance Hardening (Phase 35, 39, 40)

Status: verification + design. No production code changed. No billing feature or AI built.

Goal: determine whether SNS can survive CMS/MAC review, payer audit, CDPH survey, or medical-record
review **without manual data reconstruction** — i.e., whether the evidence a reviewer would ask for is
already assembled and queryable, versus requiring staff to manually piece together disparate records.

This document consolidates conclusions already established with full evidence in
`reimbursement_defensibility_review.md`, `eligibility_integrity_review.md`, and
`certification_gated_eligibility_review.md` — it does not re-derive them, per the standing rule against
repeating already-completed investigation. It adds two things not previously covered: Phase 39
(Recertification Monitor design validation) and Phase 40 (documentation defensibility against actual
CMS/CDPH requirements, not internal assumption).

## Can SNS survive review without manual reconstruction? — by reviewer type

| Reviewer | Can SNS answer without manual reconstruction? | Basis |
|---|---|---|
| CMS/MAC claim review | Mostly yes for an individual claim (billing-readiness re-derives certification/F2F/POC/NOE/payer-sequence live), but the *historical* state at the time billing occurred is not preserved — only today's live re-computation is queryable (confirmed: `check_patient_billing_readiness` has no persistence, Phase 29) | Partial |
| Payer audit (post-payment) | Same limitation — no historical readiness-verdict record | Partial |
| CDPH survey | Strong for clinical-note corrections (`Amendment`/`RnicaAssessment` amendment models, confirmed compliant), strong for certification lifecycle (`CertificationStatusEvent`), weak for benefit-period lifecycle (no audit trail) | Mixed — do not average into one number, the categories differ too much |
| Medical-record review (chart-level) | Strong — Certification, Admission (`AdmissionStatusHistory`, confirmed this pass to have the same `changed_by`/`changed_at`/`previous_status`/`new_status`/`reason` audit pattern as Certification), and clinical-note amendments are all real and reconstructable | Strong |

## Phase 39 — Recertification Monitor design validation

Cross-checked against the real data model (`Certification`, `BenefitPeriod`) before any build:

| Signal | Data source | Calculation | Alert strategy (design) | Auditability |
|---|---|---|---|---|
| Recert Due | `Certification.expires_at` within a lead window | Same pattern as existing `cti_expiring` dashboard query (15-day window, proven) | Dashboard widget, no new schema | Query is reconstructable; the alert firing itself is not logged (a "was this alert ever shown/acted on" event does not exist — flagged as a gap for design, not yet a build decision) |
| Recert Approaching | Same field, wider window (e.g. 30 days) than "Due" | Same query shape, different threshold | Same | Same |
| Recert Overdue | `expires_at < now()` AND no successor `Certification` row (any status) referencing the next expected benefit period | **New query, not built yet** (identified in Phase 14 addendum) | Should be a hard flag, distinct from "expiring," surfaced both on dashboard and as a billing-readiness blocker | Same limitation — would need its own event log to be historically auditable, not just live-queryable |
| Expired Certification | `status='FINALIZED' AND expires_at < now()` | Existing pattern, reusable as-is | N/A — descriptive, not actionable alone | Same |
| Missing Signature | `signed_at IS NULL` | Direct column check | Should block Finalization itself (likely already enforced by the `FINALIZED` transition logic in `certification_service.py` — not independently re-verified this pass) | `CertificationStatusEvent` covers this if the transition is real |
| Missing Medical Director | No `Certification` row with `signed_by_role='MEDICAL_DIRECTOR'` for the required benefit period (CMS requires medical-director-or-designee involvement for certain certifications) | Not yet a built query — `signed_by_role` supports it directly, no schema change needed | New alert, design-only | Same |
| Missing Physician | Same pattern, any authorized physician role (`ATTENDING_PHYSICIAN`/`HOSPICE_PHYSICIAN`/`MEDICAL_DIRECTOR`) absent | Same — supported by existing column, not yet queried this way | New alert, design-only | Same |
| Missing Benefit Period Association | `Certification.benefit_period_id` is `nullable=False` (confirmed, `certification.py:34`) — **this specific gap cannot occur by construction**; the FK constraint prevents an orphaned certification from being saved at all | N/A — already prevented at the schema level | N/A | N/A |

**Conclusion**: the Recertification Monitor's hardest signal (Recert Overdue) requires one new query, not
new storage. "Missing Benefit Period Association" is not a real risk — it is already prevented by the
existing FK constraint, and should be removed from any future gap list as a non-issue, the same way MA
hospice carve-in was removed in the prior phase.

## Phase 40 — Documentation defensibility against actual requirements

| Question | Can SNS answer it today? | Required by | Evidence |
|---|---|---|---|
| Why hospice eligible? | Yes, per-benefit-period, live | 42 CFR 418.22 (certification narrative fields: `physician_narrative`, `clinical_decline_indicators`, `supporting_evidence` on `Certification`, confirmed to exist in prior segments) | Real, structured fields, not free text only |
| Why terminal? | Yes, same fields as above | Same regulation | Same |
| Why recertified? | Yes, same certification model, `cert_type='RECERT'` | Same regulation, recurring | Same |
| Why billable? | Yes, live, via billing-readiness blockers/passes | Composite of all upstream CMS requirements | Real, working, already-audited-elsewhere function |
| Why billable **as of a past date** (retrospective)? | **No** | Implicit expectation of any post-payment audit — the reviewer usually asks about a claim already paid, not one about to be submitted | This is the single most consequential documentation-defensibility gap: SNS can explain "why billable now" but not "why was this billable then," because no historical snapshot of the readiness verdict is retained |

No production code has changed. No billing feature or AI has been built.
