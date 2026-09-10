# Readiness Reconciliation

**Status:** Business-rule / architecture reconciliation document, part of
the permanent `docs/workflows/` documentation set. Required before Priority
5/6 UI work proceeds, per directive: "Readiness cannot become another
source of truth. Readiness only CONSUMES; it owns none of the fields."

This document is written first, deliberately, so severity (READY / AT_RISK /
NOT_READY / BLOCKED) is **decided here**, not invented ad hoc while coding.

---

## Section 1 — Current Readiness Checks (as actually implemented today)

Source: `backend/app/billing/services/billing_readiness_service.py`
(`check_patient_billing_readiness`), which calls
`app.billing.services.eligibility_workflow_service.evaluate_admission_gate`
and `app.billing.services.msp_validation_service.resolve_payer_sequence`.
Severity today is a flat two-bucket model (`blockers` vs `warnings`),
rolled up by `readiness_workflow_service.derive_readiness_status` /
`compute_operational_bucket` into the 4-state
READY / AT_RISK / NOT_READY / BLOCKED shown on the dashboard.

| # | Check | Data source | Result today |
|---|---|---|---|
| 1 | Patient status must be `ACTIVE` | `patients.status` | Blocker (→ NOT_READY) |
| 2 | A billable benefit period must exist covering the service date | `benefit_periods` | Blocker (→ NOT_READY) |
| 3 | Election statement signed (INITIAL benefit period only) | `patients.election_signed_at` | Blocker (→ NOT_READY) |
| 4 | NOE (Notice of Election) filed within window (INITIAL period only) | `benefit_periods.noe_submitted_date` / `noe_exception_reason` | Missing entirely → Blocker; filed late with no exception → Warning (→ AT_RISK) |
| 5 | Certification of Terminal Illness / Recertification signed + finalized for the benefit period | `certifications` | Blocker (→ NOT_READY) |
| 6 | Face-to-face encounter attested (3rd+ benefit period) | `f2f_encounters` | Blocker (→ NOT_READY) |
| 7 | Active Plan of Care with physician-approved signature | `plan_of_care` / `poc_physician_approvals` | Blocker (→ NOT_READY) |
| 8 | Payer/MSP sequence is resolvable and unambiguous | `patient_payers` via `msp_validation_service.resolve_payer_sequence` | Blocker (→ NOT_READY) if ambiguous |
| 9 | Admission gate: an existing `EligibilityVerification` or `BenefitPeriodDetermination` row must not be in an unresolved review status | `eligibility_verifications` / `benefit_period_determinations` | Blocker (→ NOT_READY) only if a row exists and is unresolved; **absent rows are CLEAR by design** (non-regression rule for pre-existing/legacy patients) |
| 10 | Operational "Blocked" bucket | `readiness_follow_ups.status == 'BLOCKED'` (open) | Reclassifies an existing NOT_READY patient to the dashboard's BLOCKED bucket; never reclassifies READY/AT_RISK |

Separately, at **SOC entry time** (not billing readiness time),
`evaluate_soc_gate` (also in `eligibility_workflow_service.py`) hard-blocks
SOC activation itself when:

- No `BenefitPeriodDetermination` row exists yet, or
- `admit_type == TRANSFER_FROM_ANOTHER_HOSPICE` and no
  `transfer_evidence_document_id` is on file.

This means Transfer Evidence is already enforced — but as a **pre-SOC
admission gate**, not as a billing-readiness input. A patient who reached
SOC therefore already has Transfer Evidence on file if applicable; readiness
does not need to (and today does not) re-check it.

## Section 2 — Missing Readiness Inputs

Comparing Section 1 against `BenefitPeriodWorkflow.md`,
`AuthorizationWorkflow.md`, `PayerDeterminationWorkflow.md`,
`AdmissionTypesWorkflow.md`, and `SourceOfTruthMatrix.md`, the following
staff-reviewed fields exist and are storable today but are **not consumed
anywhere in `check_patient_billing_readiness`**:

| Missing input | Owner (SSOT) | Where it's stored today |
|---|---|---|
| Primary Payer (confirmed/staff-reviewed) | `PatientFaceSheet.primary_payer` | Stored, unread by readiness |
| Contracted Status (YES/NO/UNKNOWN) | `PatientFaceSheet.contracted_status` | Stored, unread by readiness |
| Authorization Required? (YES/NO/UNKNOWN) | `PatientFaceSheet.authorization_required_status` | Stored, unread by readiness |
| Authorization evidence (`AUTHORIZATION` document) | `EligibilitySourceDocument` | Stored, unread by readiness |
| Non-Authorization verification (`NON_AUTH_VERIFICATION`) | `PatientFaceSheet.non_auth_verification_document_id` / `EligibilitySourceDocument` | Stored, unread by readiness |
| Payer verification audit fields | `PatientFaceSheet.payer_verified_date/by/notes/verification_document_reference` | Stored (Priority 4, this session), unread by readiness |
| Admit Type | `Admission`/`BenefitPeriodDetermination.admit_type` | Stored, unread by readiness (only read by the SOC gate, pre-admission) |
| Transfer Evidence | `BenefitPeriodDetermination.transfer_evidence_document_id` | Enforced pre-SOC only (Section 1); not re-checked by readiness |
| Election/Consent documents (`ELECTION_STATEMENT`, `CONSENT_FORM`, etc.) | Not yet built — Priority 6 | N/A (document types do not exist yet) |

**Not missing** — already consumed correctly, no change needed:
Benefit Period existence/determination, Starting Cert (via benefit period),
election statement *signature* (`election_signed_at` — a distinct legacy
concept from the new Election/Consent *document* workflow), NOE, CTI/Recert,
F2F, Plan of Care, Payer/MSP sequence resolution.

## Section 3 — Readiness Severity (decision, documented before coding)

Per directive, severity is decided here, not invented while coding.

> **Superseded by `docs/workflows/ReadinessDecisionMatrix.md`.** That
> document is now the authoritative, finalized severity table (approved
> after this document's first draft) and also documents the governing
> Admission Gate vs. Billing Readiness distinction. The table below is
> kept for historical trace of how the decision was reached; if the two
> ever disagree, `ReadinessDecisionMatrix.md` wins.

| Condition | Severity | Rationale |
|---|---|---|
| Unknown/unconfirmed Payer | **AT_RISK** (warning) | A billing-relevant gap, but claims can often still be prepared pending confirmation; matches the existing pattern of NOE-late-with-no-exception being a warning, not a blocker. |
| Contracted Status = UNKNOWN | **AT_RISK** | Same reasoning — incomplete staff review, not proof of a problem. |
| Authorization Required = YES, no Authorization evidence uploaded | **BLOCKED** (NOT_READY-tier blocker) | Matches the existing CTI/F2F/POC pattern: a CMS/payer-required document that is provably missing is always a hard blocker, never a soft warning. |
| Authorization Required = NO, no `NON_AUTH_VERIFICATION` evidence uploaded | **AT_RISK** (recommended; see rationale below) | The "no auth needed" claim itself is unverified, which is a real gap — but it is staff's own determination already on file (Contracted/Auth-Required answers), not a missing externally-required CMS document like CTI/F2F. Treating it as a hard blocker would block claims solely for missing corroborating evidence of an already-recorded staff decision. Recommend AT_RISK with a task/follow-up, escalate to BLOCKED only if the agency's own policy requires it (configurable later, not by default). |
| Transfer Admission, no Transfer Evidence | **BLOCKED** | Already enforced earlier (pre-SOC hard gate) — cannot occur post-admission by construction. Readiness does not need its own rule; documented here only so the invariant is explicit and testable. |
| Election/Consent documents missing (post-admission) | **AT_RISK**, never a blocker | Per directive: "Consent Missing → AT_RISK or FOLLOW-UP REQUIRED → Open task → Track deficiency. Not admission blocker." Explicitly must never gate SOC or readiness READY/NOT_READY the way CTI/F2F/POC do. |

Restated as the exact BLOCKED/AT_RISK examples from the directive, confirmed
consistent with the table above:

```
Unknown Payer                          -> AT_RISK      (not BLOCKED)
Authorization Required, no evidence    -> BLOCKED
Transfer Admission, no Transfer Evid.  -> BLOCKED       (pre-SOC, already enforced)
Election Documents Missing             -> AT_RISK       (not BLOCKED)
```

## Section 4 — Readmission vs. Transfer vs. New Admission Differences

| Admit Type | Additional readiness inputs required | Rationale |
|---|---|---|
| `NEW_ADMISSION` | None beyond the standard Section 1 checks. | Baseline case. |
| `READMISSION` | None beyond the standard Section 1 checks. Explicitly **no** transfer-specific evidence requirement. | Per `AdmissionTypesWorkflow.md`: a readmission (hospitalized → discharged → returns) is not a transfer and must never require Transfer Source/Transfer Evidence. |
| `TRANSFER_FROM_ANOTHER_HOSPICE` | Transfer Evidence document — already enforced at the pre-SOC hard gate (Section 1); no additional readiness-time check needed. | Transfer admissions carry genuinely higher documentation risk (prior hospice's benefit-period/cert history) — but the gate already exists earlier in the workflow, so readiness should not duplicate it (duplicating it would create a second owner of the same "is transfer evidence present" answer — an SSOT violation). |

## Section 5 — Consent / Election Readiness

Explicit design decision, per directive:

- Missing election/consent documentation is **never** a readiness blocker
  and **never** blocks SOC or admission.
- It produces: **AT_RISK** status (or a dedicated follow-up/task type once
  Priority 6 exists), a compliance task visible to Admissions, and an
  auditable deficiency record.
- This mirrors the existing precedent already in the codebase: NOE-filed-
  late is a warning, not a blocker, even though it has real financial
  consequences — proving that "financially consequential but not a hard
  CMS billing block" already has a working pattern to reuse (`warnings`
  list → AT_RISK), rather than inventing a new severity tier.

## Section 6 — Authorization Readiness (recommendation)

- **Authorization Required = YES, no Authorization evidence** → **BLOCKED**.
  Recommendation: treat identically to the existing CTI/F2F/POC blockers —
  add `"Authorization Required but no authorization evidence is on file."`
  to `blockers` when `authorization_required_status == "YES"` and no
  reviewed `AUTHORIZATION`-classified `EligibilitySourceDocument` exists for
  the patient.
- **Authorization Required = NO, no `NON_AUTH_VERIFICATION` evidence** →
  **AT_RISK** (recommended, not BLOCKED). Rationale: unlike CTI/F2F/POC
  (externally required CMS documents that must exist), this is missing
  *corroboration* of a staff-entered determination that is already on
  file and already audited (`contracted_status`/
  `authorization_required_status`). Blocking claims on this alone would
  make readiness stricter than the staff's own recorded review, which
  contradicts "readiness only consumes, never re-decides." Recommend
  `warnings.append("Authorization Required = NO but no non-authorization "
  "verification evidence is on file.")`
- **Authorization Required = UNKNOWN** → **AT_RISK**. An unanswered
  question is an incomplete review, not a proven problem — same logic as
  Contracted Status = UNKNOWN.

## Section 7 — Benefit Period Readiness

**No change.** Benefit Period missing before SOC remains a hard BLOCKED
condition, exactly as already implemented (`evaluate_soc_gate`,
`SOC_GATE_BLOCKER_MESSAGE`) and already covered in Section 1 check #2/#9.
This document does not alter that rule.

## Most Important Rule — Readiness Owns Nothing

Readiness (`billing_readiness_service` / `readiness_workflow_service`) may
only **read** already-staff-reviewed values from their existing SSOT
locations:

- Admit Type, Benefit Period, Starting Cert, Transfer Evidence →
  `BenefitPeriodDetermination` / `Admission` (owned there — see
  `AdmissionTypesWorkflow.md`, `BenefitPeriodWorkflow.md`).
- Payer, Contracted Status, Authorization Required?, payer verification
  fields → `PatientFaceSheet` (owned there — see
  `PayerDeterminationWorkflow.md`, `AuthorizationWorkflow.md`,
  `SourceOfTruthMatrix.md`).
- Election/Consent documents → Document Registry, once Priority 6 exists.

Readiness must never introduce a new column/table that duplicates any of
these answers, and must never write back to any of them. It only produces
a derived, read-only verdict (`BillingReadinessVerdict`) plus
blocker/warning labels.

## Desired State Summary

| Input | Current | Desired |
|---|---|---|
| Payer confirmed | Not consumed | Consumed; AT_RISK if unconfirmed/UNKNOWN |
| Contracted Status | Not consumed | Consumed; AT_RISK if UNKNOWN |
| Authorization Required + evidence | Not consumed | Consumed; BLOCKED if YES+no evidence, AT_RISK if NO+no non-auth evidence, AT_RISK if UNKNOWN |
| Transfer Evidence | Enforced pre-SOC only | No change — do not duplicate at readiness time |
| Election/Consent documents | Do not exist yet (Priority 6) | AT_RISK / follow-up task when missing; never a blocker |

## Next Steps (unblocked by this document)

1. Priority 5 — wire Contracted/Authorization Required consumption into
   `check_patient_billing_readiness` exactly as recommended in Section 6
   (read-only; no new tables).
2. Priority 6 — build the Election/Consent Document Workflow (8 document
   types, post-admission compliance task, AT_RISK-only severity per
   Section 5).
3. Priority 7 — wire Payer/Contracted/Authorization consumption into
   readiness (Section 2/6), plus Election/Consent AT_RISK consumption once
   Priority 6 exists.
4. Priority 8 — end-to-end Billing Readiness validation matrix per the
   final deliverables list.
