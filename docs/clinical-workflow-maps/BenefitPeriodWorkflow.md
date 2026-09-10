# Benefit Period Workflow

**Status:** Business-rule specification. This document describes the *intended*
workflow as clarified directly by the agency (Love & Faith Hospice) using real
HospiceMD transfer and new-admission examples. As of this writing, SNS EMR does
not yet implement the SOC hard gate or the staff-entry UI described below — see
"Current implementation state" at the end of this document.

## Purpose

This is the permanent source of truth for how benefit period, starting cert,
and transfer status are determined in the hospice admission workflow, and — just
as importantly — how they are **not** determined. It exists so this business
rule is never re-litigated or re-derived from scratch in a future session.

## The workflow map

```
Referral
   |
   v
Intake
   |
   v
Document Upload            (HNP, insurance cards, transfer packets, eligibility PDFs)
   |
   v
OCR Harvest                 (automated: extracts candidate FACTS only)
   |
   v
Eligibility Verification    (270/271-style check, or manual verification upload)
   |
   v
Payer Determination         (staff confirms payer identity/contracted status)
   |
   v
Staff Determination         (staff enters Starting Cert, Benefit Period, Transfer Status)
   |
   v
SOC Entry                   (user attempts to set Start of Care)
   |
   v
Hard Gate Validation        (system checks staff determination is COMPLETE — does not compute it)
   |
   v
Admission Activation        (episode becomes billable)
   |
   v
Readiness Processing        (consumes only reviewed/staff-entered data, never raw OCR)
```

## What is automated vs. manual

| Stage | Automated? | Manual? |
|---|---|---|
| OCR Harvest | YES — text extraction + AI "key findings" classification runs automatically on upload (background job) | — |
| Fact extraction (Medicare #, MBI, Policy #, Subscriber #, Payer name) | YES — may be suggested/candidate-populated with a confidence score | Staff confirms/corrects |
| Benefit Period determination | **NEVER** automated | ALWAYS staff-entered |
| Starting Cert determination | **NEVER** automated | ALWAYS staff-entered |
| Certification Sequence | **NEVER** automated | ALWAYS staff-entered |
| Transfer Status determination | **NEVER** automated | ALWAYS staff-entered |
| Admission Approval / Readiness Status | **NEVER** automated as a *determination* | Staff-reviewed; system only reports/enforces afterward |
| Authorization Status (HMO/PPO/managed care) | **NEVER** automated | Staff answers Contracted? / Authorization Required? and uploads evidence |
| Future recertification schedule / reminders / tasks | YES — but only *after* staff have entered Starting Cert + Benefit Period + Transfer Status + SOC | — |
| SOC hard-gate check (is the determination complete?) | YES — a completeness/presence check | — (the check is automated; the answer it checks is not) |

## What creates blockers vs. what does not

**Does NOT block** (a patient may exist in all of these states indefinitely,
with zero benefit-period determination made):
- Referral
- Patient creation
- Document upload (HNP, insurance cards, transfer packets, any eligibility PDF)
- Insurance/payer identification (fact harvesting)
- Facesheet completion
- Eligibility review queue entry
- Transfer intake

**DOES block** (hard gate) — only when a user attempts one of:
1. SOC entry
2. Admission activation
3. Certification period setup
4. Episode activation for the billing workflow

At that moment, the system checks whether staff have already documented:
- Benefit Period (answered: First 90 / Second 90 / Third Benefit Period /
  Subsequent Benefit Period / Unknown / Transfer Patient)
- Starting Cert
- Supporting eligibility evidence uploaded

If any of these are missing, **BLOCK SAVE** with the message:

> "Benefit Period Documentation Required Before SOC Activation"

Never: "Medicare Detected" / "MBI Detected" — those are fact-harvest events, not
benefit-period-determination events, and must never be presented to the user as
if they satisfy the gate.

## Why benefit period is never inferred, even from "authoritative-looking" sources

Real-world hospice operations frequently have incomplete, delayed, or
misleading information available at the moment of referral or transfer. Example
scenario that must remain possible without producing a wrong answer:

1. Patient is admitted to Hospice Agency A.
2. Family becomes unhappy and calls Hospice Agency B.
3. Transfer begins.
4. Agency A has not yet billed; claims have not yet processed.
5. Medicare's systems may not yet reflect the true certification history.
6. Any eligibility response fetched at this moment can look incomplete or stale.

Any automatic benefit-period inference in this window can be **wrong**, with
real billing consequences. Benefit Period is therefore treated as an
**operational determination performed by staff using available evidence**, not
a derivable fact — unlike Medicare Number, MBI, Policy Number, Subscriber
Number, and Payer Name, which genuinely are facts and may be harvested.

## System role, precisely

```
System harvests  ->  Staff decides  ->  System records  ->  System enforces
```

- **Harvests**: OCR/AI suggests fact-type fields only, with confidence scores.
- **Decides**: staff enters Starting Cert, Benefit Period, Transfer Status, and
  uploads the supporting documentation (NOE history, transfer packet, Medicare
  eligibility verification, prior hospice discharge information, benefit period
  history, or other supporting eligibility evidence).
- **Records**: the system stores exactly what staff entered. It never invents,
  derives, defaults, or "helpfully" pre-fills these fields — including never
  defaulting Starting Cert to `1` or Benefit Period to "First 90" for a transfer
  patient just because those are common values.
- **Enforces**: the SOC hard gate is a *completeness check* over staff-entered
  fields, never a calculation engine. Once staff have established the anchor
  (Starting Cert + Benefit Period + Transfer Status + SOC), the system MAY
  calculate forward-looking dates: next recertification date, future
  certification periods, reminder tasks, readiness checks, missing-
  documentation reminders. It may never calculate/infer the *initial* benefit
  period itself — that is the one line that must never be crossed.

> "System-derived dates may only be calculated after staff establish the
> benefit-period source record. The system must never derive the initial
> benefit period, certification sequence, or transfer status."

## New Admission workflow

```
Patient referred
  -> Patient created
  -> Documents uploaded
  -> Insurance discovered (fact harvest)
  -> Eligibility uploaded
  -> Patient reviewed
  -> SOC entered
  -> NOW: system requires benefit-period determination
     (because the agency is creating an active, billable hospice episode)
```

Real-world reference example (HospiceMD, patient Shields, Loren): `ADMIT TYPE =
"New Admission"`, `STARTING CERT# = 1` with an explicit adjacent UI label **"no
prior hospice"**, SOC locked once entered (padlock icon), Eligibility/Submission
Documents populated with a `CoverageDetail_*.pdf` and an `Eligibility Print
View.pdf`, both dated the day *before* SOC.

## Transfer workflow

```
Patient referred
  -> Transfer packet uploaded
  -> Medicare identified (fact harvest)
  -> Patient created
  -> Documents uploaded
  -> Transfer information reviewed
  -> Starting Cert reviewed
  -> Prior benefit period reviewed
  -> SOC entered
  -> NOW: system requires benefit-period determination before episode activation
```

Required before SOC activation for a transfer patient, all staff-entered, none
defaulted: Transfer Source, Starting Cert, Benefit Period, Eligibility
Documentation, Certification Evidence.

Real-world reference example (HospiceMD, patient Saavedra, Jackie): `ADMIT TYPE
= "Transfer From Another Hospice"`, `XFER FROM = "Green Valley Hospice &
Palliative"`, `STARTING CERT# = 16` (continuing the inherited sequence, not
restarting at 1), `CERT VALID TO` field explicitly labeled **"(for transfer
patients only)"** carrying the inherited cert-period end date from the sending
hospice, `SOC` = the transfer date itself, `REF DATE` populated the day before
SOC.

## Medicare workflow

- OCR/AI may identify Medicare, MBI, and auto-populate candidate values with a
  confidence score.
- At SOC entry, require a Benefit Period Review with an explicit staff answer:
  First 90 / Second 90 / Third Benefit Period / Subsequent Benefit Period /
  Unknown / Transfer Patient.
- If "Transfer Patient" is selected, require uploaded evidence supporting the
  transfer benefit period (NOE history, transfer packet, Medicare eligibility
  verification, prior hospice discharge information, benefit period history, or
  other supporting eligibility evidence).
- Readiness consumes the reviewed result only — it never re-derives payer or
  benefit period at evaluation time, and never reads raw OCR output.

## HMO / PPO / Managed-care workflow

Separate from the Medicare benefit-period workflow above. After payer
identification (fact harvest):

1. **Is agency contracted?** → YES / NO / UNKNOWN (staff answer, saved)
2. **Authorization required?** → YES / NO / UNKNOWN (staff answer, saved)
   - If **YES**: require upload of authorization approval / prior authorization
     / managed care approval / other payer authorization. Without this evidence,
     readiness may become blocked.
   - If **NO**: require upload of verification of the no-auth requirement
     (coverage verification, representative note, or eligibility confirmation),
     stored as evidence type **`NON_AUTH_VERIFICATION`**.
3. Eligibility Review (staff-reviewed).
4. Readiness consumes the reviewed result — same rule as the Medicare workflow:
   never re-asks "what is the payer?", never re-derives authorization status.

## Current implementation state (as of this document's creation)

Confirmed via full repository trace in a prior investigation this session:

- The canonical readiness/eligibility chain (`readiness_workflow_service.py`,
  `admission_readiness_gate.py`, `eligibility_workflow_service.py`,
  `billing_readiness_service.py`, `eligibility_action_router.py`) has **zero**
  dependency on `PatientInsurance` today, and there is **no SOC hard gate
  implemented yet** anywhere in the codebase.
- `patient_insurances` (the `PatientInsurance` model) has **zero rows**
  system-wide, in every tenant, with no application-code creator — only a test
  fixture constructs one.
- The one real, currently-enforced gate found in code is
  `_apply_billing_impact()` in `eligibility_action_router.py`, which requires
  `Admission.status == 'ADMITTED'` before a live billing-readiness
  re-evaluation is triggered — unrelated to benefit period.
- The `/patients/from-hnp` import endpoint (`persist_patient_from_hnp_extraction`
  in `backend/app/api/patients.py`) creates/updates `Patient`,
  `PatientFaceSheet`, `PatientDiagnosis`, and `Admission`, but extracts **zero**
  payer/insurance/Medicare/MBI fields today.
- The document-upload background harvester (`document_harvest_job.py` →
  `document_intelligence_service.py` → `harvest_service.py`) runs OCR + AI
  classification successfully on upload, but its category taxonomy
  (`lab_result, diagnosis, functional_status, decline_indicator, medication,
  vital_sign, imaging_finding, administrative`) has **no dedicated
  insurance/payer/benefit-period category** — it is a clinical evidence
  harvester, not an insurance/benefit-period harvester. See
  `DocumentHarvestMapping.md` for the full field-by-field mapping.

This document describes the target state. Implementing the SOC hard gate,
staff-entry UI for Starting Cert/Benefit Period/Transfer Status, and the
`NON_AUTH_VERIFICATION` evidence type are future work, not yet built.
