# CDPH Survey Simulation (Phase 44)

Status: verification synthesis, scenario-based. No production code changed. No billing feature or AI
built. Reorganizes prior evidence (`reimbursement_defensibility_review.md` Phase 31,
`reimbursement_compliance_hardening.md`) around a realistic CDPH survey walkthrough rather than by
module.

## Scenario

A CDPH surveyor selects Patient "J.M." for an on-site chart review under the new Title 22 hospice-
specific sections (CCR §§74800-74908) and asks the agency to produce evidence, section by section.

| Section | Can SNS produce sufficient evidence? | Can SNS reconstruct chronology? | Can SNS demonstrate compliance? | Result |
|---|---|---|---|---|
| Admission | Yes — `Admission` + `AdmissionStatusHistory` (`previous_status`, `new_status`, `changed_by`, `changed_at`, `reason`, confirmed real this pass) | Yes — full status-transition history | Yes | **PASS** |
| Assessment | Not independently investigated in this engagement (outside the benefit-period/certification/billing scope this engagement was scoped to) | Unknown | Unknown | **UNKNOWN** |
| Plan of Care | Physician-approval check exists and is real (`_has_physician_approved_plan_of_care`) | Not confirmed — its own version/audit history was not verified in any phase | Partial — a pass/fail signal exists, not a full documented history | **PARTIAL** |
| Clinical Documentation / Addenda | `Amendment` model (structured, signed, timestamped, `reason` required non-null) + `rnica_amendment.py` for RNICA-specific assessments — confirmed this pass to match CDPH's structured-addendum requirement | Yes | Yes | **PASS** |
| Interdisciplinary Review (IDG) | `IDG_REVIEW` task auto-seeded on every benefit-period rollover — a real trigger mechanism | Whether *completion* of the task is tracked/audited downstream was not verified in any phase | Partial — trigger exists, completion-tracking unconfirmed | **PARTIAL** |
| Benefit Period | `BenefitPeriod` rows exist, correct CMS calculations, tested | **No** — no audit trail, `created_by` unpopulated, no status-event table (confirmed, unchanged across every phase of this engagement) | No | **FAIL** |
| Certification | `Certification` + `CertificationStatusEvent` — full lifecycle, physician-role attribution, narrative evidence fields | Yes | Yes | **PASS** |
| Medical Record (overall) | Referral (creation/review attribution), Admission (full history), Certification (full history), clinical-note amendments (full history) are all real and structured | Yes, for the pieces listed; not yet evaluated for retention/export capability (out of scope this engagement) | Yes, for the pieces listed | **PASS**, with retention/export explicitly unevaluated |
| Discharge | Not investigated in this engagement | Unknown | Unknown | **UNKNOWN** |
| Transfer | Not investigated in this engagement | Unknown | Unknown | **UNKNOWN** |

## Summary

CDPH's newest, most novel requirement — structured, non-silent, timestamped clinical-note addenda —
is the one SNS demonstrably **passes**, confirmed directly in code (`Amendment`,
`rnica_amendment.py`). This is worth stating plainly: the single most recently-changed regulatory
requirement in this entire engagement is also one of the best-covered areas of the codebase. The
**one confirmed FAIL is Benefit Period**, for the same reason it has appeared in every phase of this
engagement: no audit trail. Everything else is either a clear PASS (Admission, Certification, Medical
Record core) or an honestly-labeled UNKNOWN/PARTIAL that this engagement's scope did not reach
(Assessment, Discharge, Transfer, IDG-completion tracking, Plan-of-Care versioning) — these are not
assumed compliant or non-compliant, they are explicitly flagged as needing a dedicated follow-up review
before CDPH survey readiness can be claimed for those sections specifically.

No production code has changed. No billing feature or AI has been built.
