# Admission Types Workflow

> **Status**: Target-state specification, now being implemented (Priority 5 of the
> Benefit Period / Document Harvest implementation plan). See
> `docs/workflows/BenefitPeriodWorkflow.md` for the full referral-to-readiness
> pipeline this document plugs into.

## Most important rule

**Admit Type is the driver.** It is a mutually-exclusive workflow-path selector,
not a patient attribute, not a status, and not a flag. Everything downstream
(which fields are visible, what the SOC hard gate requires, what readiness
checks) branches on `admit_type`.

**A discharged patient who returns later is a READMISSION, never a TRANSFER.**
Transfer means "admitted directly from another hospice provider" and nothing
else. Do not conflate the two.

```
admit_type ∈ { NEW_ADMISSION, READMISSION, TRANSFER_FROM_ANOTHER_HOSPICE }
```

This mirrors the real HospiceMD `ADMIT TYPE` dropdown
(`New Admission` / `Re-Admit` / `Transfer From Another Hospice`).

---

## NEW_ADMISSION

Patient is entering hospice for the first time (no prior hospice history).

- **Required fields**: Starting Cert, Benefit Period.
- **SOC requirement**: Benefit Period documented, Starting Cert documented.
- **Readiness behavior**: standard readiness checks only (payer, eligibility,
  authorization if applicable, benefit period, starting cert).
- **Benefit Period requirement**: staff-entered determination required before
  SOC; typically Starting Cert = 1 ("no prior hospice") but this is a staff
  entry, never a system default.
- **Transfer requirement**: none. Transfer fields are not shown, not
  validated, not required.
- **Authorization requirement**: only if payer is HMO/PPO/Commercial and
  `Authorization Required? = YES` (see `AuthorizationWorkflow.md`).
- **Required evidence**: eligibility verification documentation supporting
  the staff Benefit Period determination.

## READMISSION

Patient was previously discharged from **this same agency** (or hospice care
generally) and is now returning. Examples: hospitalized and discharged from
hospice, revoked, discharged alive, no longer eligible, any interruption
followed by a later return.

- **Required fields**: Starting Cert, Benefit Period.
- **SOC requirement**: Benefit Period documented, Starting Cert documented.
  **Identical to NEW_ADMISSION** -- readmission does not add transfer
  requirements.
- **Readiness behavior**: identical to NEW_ADMISSION. No transfer-specific
  blockers apply.
- **Benefit Period requirement**: staff-entered determination required
  before SOC; Starting Cert is very likely > 1 since there is prior hospice
  history, but this remains a staff determination, never system-derived.
- **Transfer requirement**: none. **Transfer fields must remain hidden and
  unvalidated for READMISSION.** This is the single most important
  distinction in this document -- a readmission is not a transfer, and must
  never trigger transfer-only UI, validation, or evidence requirements.
- **Authorization requirement**: same as NEW_ADMISSION.
- **Required evidence**: eligibility verification documentation; prior
  discharge/episode history if available (informational, not a hard block).

## TRANSFER_FROM_ANOTHER_HOSPICE

Patient is being admitted directly from a **different** hospice agency's
active or recently active care (family-initiated transfer, agency-initiated
transfer, etc.).

- **Required fields**: Starting Cert, Benefit Period, Transfer Source,
  Transfer Evidence.
- **SOC requirement**: Benefit Period documented, Starting Cert documented,
  Transfer Source documented, Transfer Evidence uploaded.
- **Readiness behavior**: standard checks **plus** a transfer-evidence
  blocker -- readiness cannot reach READY if Transfer Source or Transfer
  Evidence is missing while `admit_type = TRANSFER_FROM_ANOTHER_HOSPICE`.
- **Benefit Period requirement**: staff-entered determination required
  before SOC. Never default Starting Cert to `1` or Benefit Period to
  "First 90" for a transfer -- the whole point of the transfer path is that
  the patient already has hospice history elsewhere.
- **Transfer requirement**: this is the *only* admit type where the
  following fields are shown, editable, and required:
  - `transfer_source` -- name/identifier of the prior hospice agency.
  - `transfer_evidence_document_id` -- uploaded proof (transfer packet,
    prior cert history, prior benefit-period documentation).
  - Supporting notes / certification-support references as staff attach
    them.
- **Authorization requirement**: same as NEW_ADMISSION/READMISSION, evaluated
  independently of transfer status.
- **Required evidence**: transfer packet and/or prior certification history
  sufficient for staff to make the Benefit Period/Starting Cert
  determination, plus standard eligibility verification documentation.

---

## UI requirement

Transfer-specific fields (`transfer_source`, `transfer_evidence`, transfer
notes, transfer certification support) are **hidden by default** and only
rendered when the user sets `admit_type = TRANSFER_FROM_ANOTHER_HOSPICE`.
Switching `admit_type` back to `NEW_ADMISSION` or `READMISSION` hides the
transfer section again (the values may be retained in the database for audit
purposes, but are not required or displayed as active fields for those admit
types).

## SOC gate summary table

| Admit Type | Benefit Period | Starting Cert | Transfer Source | Transfer Evidence |
|---|---|---|---|---|
| NEW_ADMISSION | Required | Required | -- | -- |
| READMISSION | Required | Required | -- | -- |
| TRANSFER_FROM_ANOTHER_HOSPICE | Required | Required | Required | Required |

## What never changes across admit types

- The system never determines Benefit Period, Starting Cert, or Admit Type
  itself -- these are always staff-entered.
- The SOC hard gate is always a *completeness check*, never a determination
  engine, regardless of admit type.
- Once staff establish the anchor (Admit Type + Starting Cert + Benefit
  Period + SOC, and Transfer Source/Evidence when applicable), the system
  may calculate forward-looking dates (recert schedule, reminders) -- it may
  never derive the initial values themselves.
