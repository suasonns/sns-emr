# Eligibility Traceability Chain (Phase 37)

Status: verification only. No production code changed. No billing feature or AI built.

Single-patient trace, each transition evaluated for Trigger / Source Record / Audit Event / Timestamp /
Responsible User / Evidence. Evidence basis: direct model/service reads this session and prior sessions
(cited inline); no cell is inferred from an endpoint merely existing.

| Transition | Trigger | Source Record | Audit Event | Timestamp | Responsible User | Evidence retained? |
|---|---|---|---|---|---|---|
| Referral | Referral submitted | `Referral` (`created_by` **non-nullable** FK to `users.id`, `created_at`) | No — only current-state fields (`status`, `reviewed_by`/`reviewed_at`); no separate status-history/event table | Yes (`created_at`, `reviewed_at`) | Yes, for creation and review, but not for every intermediate status change | Partial — who created/reviewed is known; a full status-change history (e.g. every PENDING→...→CONVERTED transition) is not |
| Admission | Referral converted / admission created | `Admission` + `AdmissionStatusHistory` (`previous_status`, `new_status`, `changed_by`, `changed_at`, `reason` — confirmed this pass) | **Yes** | Yes | Yes | Yes — full transition history reconstructable |
| Election | Election signed | `patients.election_signed_at`; `ElectionAddendumRequest` for addendum obligations | No dedicated event table for the election signing act itself, only the timestamp column | Yes (`election_signed_at`) | Not confirmed — no `signed_by`/`created_by`-equivalent for the election signature was located this pass (flagged, not assumed) | Partial |
| Certification | Physician signs CTI | `Certification` + `CertificationStatusEvent` | **Yes** | Yes | Yes (`changed_by_user_id`, `changed_by_role`, `signed_by_role`) | Yes — full lifecycle reconstructable |
| Benefit Period (creation/rollover) | `rollover_benefit_period` call | `BenefitPeriod` | **No** | Only generic row timestamps, not action-specific | **No** (`created_by` unpopulated) | **No** — confirmed, unchanged from every prior phase of this engagement |
| Recertification | Physician signs RECERT | Same `Certification`/`CertificationStatusEvent` as above | Yes | Yes | Yes | Yes |
| Billing Readiness | Claim-prep attempt | `check_patient_billing_readiness()` — live compute, confirmed no persistence | **No** | No | No | **No** — only today's live re-computation is available; no historical verdict is retained |
| Claim | Claim generated/submitted | `Claim` | Partial — 1 of 3 `status` writers enforced/audited (Phase 5/6, unchanged) | Partial | Partial | Partial |
| Remittance | 835/ERA received | Dashboard widget confirmed fabricated (Phase 5/6, unchanged); underlying real ledger not reconfirmed this pass | Unknown | Unknown | Unknown | Unknown — flagged, not assumed |
| Payment | Payment posted | Not reconfirmed this pass | Unknown | Unknown | Unknown | Unknown |

## Answers

**Can an auditor reconstruct WHY this patient became billable? — PARTIAL.**
Yes for the clinical justification (Certification's narrative fields, `CertificationStatusEvent`
audit trail) at *today's* state. No for a *historical* point-in-time justification, since Billing
Readiness results are never persisted — "why billable" can only be answered as of right now, not as of
the date a specific past claim was submitted.

**Can an auditor reconstruct WHO made this patient billable? — NO, as a single answer.**
Individual pieces have clear attribution (who signed the certification, who created the admission
record), but no single record or event says "this action is what made the patient billable" — billing
readiness is a derived, unpersisted computation, not an attributable action taken by a person at a
point in time. There is no "who flipped the readiness flag" because there is no readiness flag to flip
— it is recomputed fresh every time.

**Can an auditor reconstruct WHEN this patient became billable? — NO.**
Same root cause: no historical readiness snapshot exists. The closest available timestamp is when the
last-required upstream record (e.g., the finalized certification) was completed, which is a reasonable
proxy but not the same as a system-recorded "became billable at this timestamp" event.

## Weakest links, precisely stated
1. Benefit Period creation/rollover has zero audit attribution (unchanged, most consequential, root
   cause of most downstream traceability gaps).
2. Billing Readiness is a pure live computation with no historical persistence — this is the reason
   "when/why/who" cannot be answered *retrospectively* even though they can be answered *currently*.
3. Election's own signing event has a timestamp but no confirmed user-attribution field, a smaller but
   real gap not previously called out this precisely.

No production code has changed. No billing feature or AI has been built.
