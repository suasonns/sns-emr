# Readiness Consumption Map

**Status:** Reference mapping, confirmed against the actual codebase where
noted, plus target-state rows for the not-yet-built Benefit Period / SOC hard
gate / Authorization workflows described in `BenefitPeriodWorkflow.md` and
`AuthorizationWorkflow.md`. Companion to `PayerDeterminationWorkflow.md` and
`DocumentHarvestMapping.md`.

## Purpose

Prove, field by field, that the readiness engine consumes only reviewed data —
never raw OCR, never an un-reviewed eligibility response, never a
system-inferred benefit period. This is the enforcement mechanism for the rule
stated in every other document in this folder: **the system harvests, staff
decides, the system records, the system enforces.**

## How to read this table

- **SOURCE DATA** — the specific field/record readiness reads.
- **OWNER** — who/what is the source of truth for that field.
- **AUTOMATIC?** — does the system populate/compute this without staff review?
- **MANUAL?** — does a staff action populate/confirm this?
- **BLOCKING?** — does a missing/unreviewed value block readiness?
- **WHY?** — the reasoning tying back to the business rule.

## Confirmed (implemented today)

| SOURCE DATA | OWNER | AUTOMATIC? | MANUAL? | BLOCKING? | WHY? |
|---|---|---|---|---|---|
| `Admission.status == 'ADMITTED'` (checked in `_apply_billing_impact()` / `_patient_is_admitted()`, `eligibility_action_router.py`) | Staff (admission workflow) | No | Yes — set via the admission process | Yes — this is the one confirmed real gate in code today; without it, a live billing-readiness re-evaluation is never triggered | Only an actually-admitted episode should trigger a real billing-readiness re-evaluation |
| Eligibility verification result (`record_eligibility_verification()`) | Staff (biller/RN action via `eligibility_action_router.py`) | No | Yes — explicit action endpoint | Contributes to readiness verdict | Readiness must consume a reviewed verification action, not a raw eligibility check |
| Benefit period determination (`record_benefit_period_determination` action) | Staff (biller/RN action) | No | Yes — explicit action endpoint | Contributes to readiness verdict | Confirms readiness already reads a *recorded determination*, never computes one itself, for the current (post-admission) benefit-period tracking that exists today |
| RN review outcome | RN (explicit action endpoint) | No | Yes | Contributes to readiness verdict | Clinical sign-off is a human action |
| `PatientInsurance` rows | Nobody — 0 rows exist system-wide, no application-code creator | No | N/A — not currently populated by anyone | **Not consumed at all** by the readiness/eligibility chain (confirmed via zero references in `readiness_workflow_service.py`, `admission_readiness_gate.py`, `eligibility_workflow_service.py`, `billing_readiness_service.py`, `eligibility_action_router.py`) | Readiness does not depend on this model today — see `DocumentHarvestMapping.md` model table |
| Raw OCR output (`document_records.extracted_values`, `document_text`) | System (harvester) | Yes — extraction is automatic | N/A | **Never consumes directly** — confirmed zero references to `document_records`/`extracted_values` in any readiness/eligibility service | Raw OCR is never treated as ground truth by readiness; it must pass through a review action first |

## Target state (documented in `BenefitPeriodWorkflow.md` / `AuthorizationWorkflow.md`, not yet implemented)

| SOURCE DATA | OWNER | AUTOMATIC? | MANUAL? | BLOCKING? | WHY? |
|---|---|---|---|---|---|
| Initial Benefit Period (First 90/Second 90/Third/Subsequent/Unknown/Transfer Patient) | Staff | No — must never be automated | Yes — required staff answer at SOC entry | Yes — SOC hard gate | Benefit period is an operational determination, not a derivable fact; incomplete/stale payer data at referral/transfer time makes automatic inference unsafe |
| Starting Cert # | Staff | No — must never default to `1` | Yes | Yes — SOC hard gate | Same as above; defaulting silently misrepresents transfer patients as first-time admissions |
| Transfer Status + Transfer Source | Staff | No | Yes | Yes — SOC hard gate (transfer patients only) | Transfer patients are the exact case that proves benefit period cannot be auto-derived |
| Benefit Period supporting evidence upload (NOE history, transfer packet, Medicare eligibility verification, prior hospice discharge info, benefit period history) | Staff (uploads) | No | Yes | Yes — required alongside the determination itself | A determination without evidence is not reviewable/auditable |
| Contracted? answer | Staff | No | Yes | Contributes to readiness | Not inferable from payer name alone — see `PayerDeterminationWorkflow.md` |
| Authorization Required? answer | Staff | No | Yes | Contributes to readiness | Same reasoning as Contracted? |
| Authorization evidence (when Authorization Required = YES) | Staff (uploads) | No | Yes | Yes — readiness blocked if missing | Explicit requirement in `AuthorizationWorkflow.md` |
| `NON_AUTH_VERIFICATION` evidence (when Authorization Required = NO) | Staff (uploads) | No | Yes | Yes — readiness blocked if missing | "No auth needed" must always be an evidenced claim, never an assumed default |
| Future recertification schedule / reminders / tasks | System (calculation) | **Yes** — but only once the anchor (Benefit Period + Starting Cert + Transfer Status + SOC) already exists | N/A | Not itself blocking (it is a downstream convenience calculation) | This is the one place automation is explicitly allowed — calculating forward from an already-established, staff-confirmed anchor is different from determining the anchor itself |

## The one sentence this entire document exists to prove

**Readiness consumes reviewed data. Readiness never consumes raw OCR.** Every
row above that is BLOCKING traces back to an explicit staff action or upload,
never to an automatic extraction or inference step.
