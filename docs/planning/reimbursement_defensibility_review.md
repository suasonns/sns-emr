# Reimbursement Defensibility Review (Phase 27, 29, 31, 32)

Status: verification + research comparison. No production code changed. No billing feature or AI built.

Reframing acknowledged: the operative question is no longer "can SNS bill an ineligible patient"
(answered: it cannot reach actual reimbursement today, because billing-readiness and claim-path
validation both independently re-check certification). The operative question is now: **"if Medicare
audited this chart tomorrow, can SNS explain exactly why payment was appropriate, end to end, with
evidence?"**

---

## Phase 27 — Per-checkpoint defensibility (Required Evidence / Current Evidence / Gap / Risk)

| Checkpoint | Required Evidence (regulation) | Current Evidence in SNS | Gap | Risk |
|---|---|---|---|---|
| Election | Signed election statement; as of 10/1/2026, an automatically-furnished addendum within 5 days | `patients.election_signed_at` (real, persisted column, confirmed via `billing_readiness_service.py` docstring); `ElectionAddendumRequest` table tracks addendum requests/delivery **but only when a request is logged** | No automatic-furnish path; addendum compliance is invisible unless someone manually creates the request record | High, time-critical (see Phase 28) |
| Certification | Signed, FINALIZED cert by an authorized physician role, timed correctly relative to the benefit period | `Certification` model + `CertificationStatusEvent` audit trail (real, append-only, includes `changed_by_user_id`, `changed_by_role`, `changed_at`, `reason`) | None at the certification-record level itself — this checkpoint is strong | Low, for the record itself |
| Recertification | Same as certification, for cert_type=RECERT, tied to F2F for BP3+ | Same table/model as certification; `f2f_encounters` exists and is checked (`_has_attested_f2f`) | "Recert Overdue" has no dedicated derived signal (only a 15-day "expiring" window); F2F 30-day *window* validation was not independently re-verified this pass (attestation existence was) | Medium |
| Benefit Period | Correct period sequencing/lengths; **should** be gated by a valid certification | `rollover_benefit_period` — correct CMS 90/90/60 lengths, atomic, tested (4/4 guardrail tests) | **No certification gate at creation time; no audit trail (`created_by` unpopulated, no status-event table); no update/correct/delete endpoints exist at all** | High |
| NOE | Filed and *accepted* by MAC within 5 calendar days of election | `benefit_periods.noe_submitted_date` / `noe_exception_reason` checked in billing-readiness | Not verified whether SNS distinguishes *submission* from MAC *acceptance* — the legal clock runs to acceptance | Medium-High (unconfirmed either way) |
| Claim | Submitted only for a benefit period with valid, finalized certification on file | Billing-readiness independently re-verifies certification before allowing claim generation | Documented pre-existing gap: `Claim.status` has 3 writers, 2 unenforced/unaudited (Phase 5/6, unchanged) | High (pre-existing) |
| Remittance | Real 835/ERA data reflecting actual MAC adjudication | Dashboard 835 widget renders **fabricated** data (confirmed Phase 5/6, unchanged) | Same, unchanged | Medium-High (pre-existing) |
| Payment | Traceable to an accepted claim and posted remittance | Not re-verified this pass beyond the remittance widget finding above | Whether a real payment-posting ledger exists independent of the fabricated dashboard widget was not re-confirmed this session | Unknown — flagged, not assumed |

**Overall Phase 27 conclusion**: the *clinical/regulatory* checkpoints (Election, Certification,
Recertification) are individually strong — each has a real signed record and, for Certification, a
real audit trail. The *operational sequencing and audit* checkpoint (Benefit Period) is the weak link:
it is the one place in the entire chain where creation is not gated by the record it should depend on,
and it is also the one place with no audit trail of its own. This is a narrower, more precise framing
than "eligibility can be bypassed" — the eligibility *records* are fine; the *linkage and audit trail
between* Benefit Period and Certification is what is missing.

---

## Phase 29 — Certification-to-claim traceability chain

| Transition | Audit event? | Timestamp? | User? | Evidence retained? |
|---|---|---|---|---|
| Certification Draft created | Yes — `CertificationStatusEvent(to_status='DRAFT')` | Yes (`changed_at`) | Yes (`changed_by_user_id`, `changed_by_role`) | Yes |
| Certification Finalized | Yes — `CertificationStatusEvent(to_status='FINALIZED')` | Yes | Yes | Yes |
| → Benefit Period Creation | **No** — no query, no event linking a specific certification to the `rollover_benefit_period` call that (should have) required it | N/A | N/A | **No** — the FK exists in the *opposite* direction (`certifications.benefit_period_id`), so one can look up which certifications reference a given benefit period, but not reconstruct which certification (if any) *authorized* its creation, because none is required to exist first |
| Benefit Period Rollover (next period) | **No** | Generic `created_at`/`updated_at` only, not action-specific | **No** (`created_by` unpopulated) | **No** |
| → Billing Readiness check | **No** — `check_patient_billing_readiness` computes a live verdict but does not appear to persist its own result to any table (confirmed by re-reading the function; no `db.add`/`db.commit`/insert statement exists in it — it is a pure read/compute/return function) | N/A | N/A | **No** — the readiness verdict at any past point in time is not reconstructable; only today's live re-computation is available |
| → Claim Validation | Partially — 1 of 3 `Claim.status` writers is enforced/audited (Phase 5/6 finding, unchanged) | Partial | Partial | Partial |

### Can an auditor reconstruct "who made the patient billable, when, why," using SNS data only?

**NO.**

An auditor *can* fully reconstruct the certification lifecycle (who signed what, when, in what role,
why — via `CertificationStatusEvent`). An auditor *cannot* reconstruct: (a) who created or rolled the
benefit period the certification is attached to, or when, (b) whether a billing-readiness check ever
passed for this patient at the time billing occurred, versus only reflecting today's live state, or
(c) a single continuous narrative connecting "certification signed" → "benefit period created" →
"claim submitted" as one auditable sequence — each piece is independently evidenced, but the *chain
itself* is not. This is the precise, narrow gap the reframed question exposes: not "is any single
record fake or missing" (they mostly aren't), but "is the sequence and its authorization
reconstructable" (it is not).

---

## Phase 31 — CDPH gap review

| Requirement | SNS status | Evidence |
|---|---|---|
| Structured addendum workflow for clinical notes (no silent edits; separate, signed, timestamped, classified addenda) | **Fully compliant** (newly confirmed this pass — was flagged "not investigated" in the prior phase) | `app/models/amendment.py`: `Amendment` model with `clinical_note_id`, `author_id`, `created_by`, `reason` (required, non-nullable), `content`, `created_at`, `original_finalized_at` — this is exactly the CDPH-required pattern, already implemented for general clinical notes. `rnica_amendment.py` provides an equivalent for RNICA assessments specifically. |
| Physician notification for significant changes, tracked with date/time/method/response | **Unknown** — not located in this pass; distinct from the amendment model above (that model tracks note corrections, not physician-notification events specifically) | Needs dedicated follow-up |
| Addenda completed within a defined window (~48 hrs), late entries flagged | **Partial** — `Amendment.created_at` and `original_finalized_at` allow computing elapsed time after the fact, but no evidence was found of an enforced deadline or a "late" flag/label at write time | Needs follow-up to confirm whether lateness is only computable or actually surfaced |
| Records include audit trails, e-signatures for care-plan reviews | **Partial** — Certification has both; Benefit Period has neither; Plan-of-Care's own audit trail was not independently verified this pass (only that a boolean-equivalent approval check exists in billing-readiness) | Mixed — do not treat as uniformly compliant or non-compliant |
| Admission documentation | **Real model exists** (`app/models/admission.py`, `admission_status_history.py`, `admission_action_request.py` — a full admission model with its own status-history table, following the same audit pattern as `CertificationStatusEvent`) | Not deeply inspected this pass beyond confirming existence and the parallel audit-trail pattern; treat as likely-strong based on the pattern match, not fully confirmed |
| Election storage | **Real** — `patients.election_signed_at`, `election_date` on `BenefitPeriod` | Confirmed |
| Transfer / discharge records | **Not investigated this engagement** | Unknown |
| Record retention (7-year Title 22 floor) | **Not investigated this engagement** | Unknown — a storage/retention-policy question, out of scope for this session's code-evidence method |

**Revision to the prior phase's CDPH conclusion**: the prior phase (Phase 18-26) flagged the clinical-
note addendum/correction workflow as entirely unscoped and unknown. This pass located and confirmed it
— it exists, is well-modeled, and appears to satisfy CDPH's structured-addendum requirement. This is an
explicit correction of an "unknown" to a "confirmed compliant" finding, made transparently rather than
silently carried forward as still-unknown.

---

## Phase 32 — Eligibility Defensibility Scorecard

| Area | Score | Justification |
|---|---|---|
| Election | 4 (Strong) | Real signed-date field; real addendum-request/delivery tracking. Not 5 because the addendum tracking is on-request only, and the automatic-furnish requirement is imminent (see Phase 28). |
| Certification | 5 (Fully Defensible) | Real lifecycle model, real physician-role attribution, real append-only audit trail (`CertificationStatusEvent`), each transition timestamped and user-attributed. |
| Benefit Period | 2 (Weak) | Correct calculations and atomic technical guarantees, but zero certification gate at creation and zero audit trail — the two things an auditor would ask for first. |
| Recertification | 3 (Adequate) | Shares Certification's strong record/audit model, but lacks a distinct "Recert Overdue" signal and the F2F 30-day window's own validation was not reconfirmed this pass. |
| NOE | 3 (Adequate) | Real fields, real timeliness blocker logic in billing-readiness; unconfirmed whether acceptance-vs-submission distinction is tracked, which is a defensibility risk if wrong. |
| Claim | 2 (Weak) | Pre-existing, unchanged: 2 of 3 status writers are unenforced/unaudited. |
| Payment | 2 (Weak, provisional) | Remittance dashboard widget is confirmed fabricated; underlying payment-posting ledger not reconfirmed this pass — scored conservatively pending that confirmation, not assumed worse or better than evidence supports. |
| Audit Trail (overall) | 3 (Adequate, uneven) | Excellent for Certification and clinical-note amendments; absent for Benefit Period; unknown for Plan of Care and admission's deeper detail. |
| Documentation (overall) | 4 (Strong) | Admission, election, certification, and clinical-note-amendment models are all real, structured, and follow a consistent, defensible pattern across the codebase — the weakest link is specifically Benefit Period, not documentation generally. |

**Overall defensibility read**: SNS's documentation and clinical-record architecture is materially
stronger than the earlier "billing architecture" framing suggested — most individual records are real,
signed, and attributable. The system's single most consequential weak point, confirmed and reconfirmed
across every phase of this engagement, remains the same one: **Benefit Period creation is neither gated
by Certification nor independently audited.** Everything else in this scorecard is either strong or a
genuinely open question flagged as such, not a second confirmed high-risk item of the same magnitude.

No production code has changed. No billing feature or AI has been built.
