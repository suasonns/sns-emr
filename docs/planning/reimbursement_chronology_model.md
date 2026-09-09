# Reimbursement Chronology Model (Phase 51)

Status: verification synthesis + design. No production code changed. No billing feature or AI built.
This document reframes the eligibility/traceability findings from Phases 1-50 under the corrected
framing: the problem is not that any single record is wrong or missing — it is that the full chain
cannot always be reconstructed as one continuous, causally-linked, evidenced chronology.

For every event in the chain, this model requires: **WHO, WHEN, WHY, WHAT EVIDENCE.** Each row below
states what SNS can answer today, using only already-confirmed evidence from prior phases.

| Event | WHO | WHEN | WHY | WHAT EVIDENCE | Chronology-reconstructable? |
|---|---|---|---|---|---|
| Clinical Findings | Note author (via note authorship) | Note timestamp | Clinical judgment, narrative | Note content + `Amendment` trail if corrected | Yes, for the finding itself |
| → Terminal Prognosis | Certifying physician (`signed_by_user_id`, `signed_by_role`) | `Certification.signed_at` | `physician_narrative`, `clinical_decline_indicators`, `supporting_evidence` | Structured fields, not free text only | **Yes** |
| → Certification | Same physician | `signed_at`; full lifecycle via `CertificationStatusEvent.changed_at` | Recorded in `CertificationStatusEvent.reason` | Append-only event stream | **Yes** |
| → Benefit Period | **Unknown** — `created_by` never populated | Generic row timestamp only, not action-specific | **Unknown** — no reason/justification field exists on `BenefitPeriod` or any related event | **None** — no event, no linkage record to the certification that should have gated it | **No — the single break point in this entire chain** |
| → Recertification | Same physician-attribution strength as initial Certification | Same | Same | Same | **Yes** |
| → Billing Readiness | N/A — no actor, it's a computation | N/A — not persisted, only computed live | The blockers/passes *are* the "why," but only for the current moment | None retained after the HTTP response returns | **No — cannot answer for any past moment, only right now** |
| → NOE | Not confirmed (submission recorded; who submitted not confirmed this engagement) | `noe_submitted_date` | Timeliness blocker logic implies "why" only in the negative (why blocked), not an affirmative record | `noe_submitted_date`/`noe_exception_reason` | Partial |
| → Claim | Partial — 1 of 3 status writers | Partial | Partial | Partial | Partial |
| → Payment | Not reconfirmed this engagement; dashboard widget confirmed fabricated | Unknown | Unknown | Unknown | Unknown |

## The single most important structural fact this model makes explicit

Every event **before** Benefit Period is fully reconstructable (WHO/WHEN/WHY/EVIDENCE all answerable).
Every event **at and after** Benefit Period has at least one dimension missing. This is not eight
separate small gaps — it is **one structural break point** (Benefit Period creation/rollover having no
actor, reason, or linkage record) that then cascades: because Benefit Period itself isn't
attributable, nothing built on top of it (Billing Readiness, Claim, Payment) can cite it as a
justified, attributed cause either, even where those later stages have their own partial
record-keeping.

No production code has changed. This is a verification and design document only.
