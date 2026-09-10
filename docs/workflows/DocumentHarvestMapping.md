# Document Harvest Mapping

**Status:** Reference mapping, confirmed against the actual codebase (file/line
references included). This is the permanent source of truth for "what gets
harvested from a document, where it goes, and who owns the final value." Update
this file whenever a harvesting/mapping code path changes — do not let this
drift out of sync with the code again.

## How to read this table

- **SOURCE** — where the raw value originates (an uploaded document, OCR/AI
  extraction, or a staff-entered field).
- **TARGET** — the database column/model the value ends up in, if any.
- **RULE** — `AUTOMATED` (system may write this without staff review),
  `STAFF REVIEWED` (system may suggest/candidate-populate, staff must confirm
  before it is treated as final), or `NOT AUTOMATED — STAFF ENTERED ONLY`
  (system must never write or suggest a value; the field is entered from
  scratch by staff).
- **OWNER** — which role/system is the source of truth once the value exists.
- **CONSUMERS** — what downstream feature reads this value today.

## Fact fields (safe to harvest, suggest, and auto-populate)

| SOURCE | TARGET | AUTOMATED? | MANUAL? | OWNER | CONSUMERS |
|---|---|---|---|---|---|
| Uploaded HNP/insurance PDF → OCR → AI extraction | `patient_facesheet.mbi_number` | Auto-populate candidate value | Review required (staff confirms) | Staff (Facesheet) | Facesheet chart, HOPE-A1400 reporting |
| Uploaded HNP/insurance PDF → OCR → AI extraction | `patient_facesheet.primary_payer` / `primary_payer_type` | Auto-populate candidate value | Review required | Staff (Facesheet) | Facesheet chart only |
| Uploaded HNP/insurance PDF → OCR → AI extraction | `patient_facesheet.primary_policy_number` | Auto-populate candidate value | Review required | Staff (Facesheet) | Facesheet chart only |
| Uploaded HNP/insurance PDF → OCR → AI extraction | `patient_facesheet.secondary_*` (mirrors primary_* for secondary payer) | Auto-populate candidate value | Review required | Staff (Facesheet) | Facesheet chart only |
| Referral raw-text paste → `/patients/from-hnp` → `hnp_parser_service.py` → `build_hnp_summary()` | `Patient` (demographics), `PatientFaceSheet` (demographics + diagnosis fields only), `PatientDiagnosis`, `Admission` | Automated for demographics/diagnosis only | Reviewable after import | System (import) | Patient chart, diagnosis list, admission record |

## Fields the AI document harvester (`document_harvest_job.py`) actually extracts today

The background harvester (`run_document_intelligence()` in
`backend/app/services/evidence/document_harvest_job.py`, triggered via FastAPI
`BackgroundTasks` immediately after `POST /documents/` commits) runs:

1. `extract_text_from_file()` — OCR/text extraction → `document_records.document_text`
2. `classify_and_extract_document()` — AI classification →
   `document_records.extracted_values` (JSON: `ai_summary`, `ai_confidence`,
   `ai_document_type_guess`, `ai_needs_manual_review`, `ai_key_findings[]`)
3. `harvest_from_source()` (`harvest_service.py`) — writes each finding to the
   **clinical Evidence Registry** (`evidence_record`), an RN-reviewable queue.

The AI's `category` enum (from the prompt in `document_intelligence_service.py`,
~line 380) is: `lab_result, diagnosis, functional_status, decline_indicator,
medication, vital_sign, imaging_finding, administrative`.

**There is no `insurance`/`payer`/`benefit_period` category in this taxonomy.**
Anything payer-adjacent that the AI notices (e.g. a finding labeled "Coverage")
falls under the generic `administrative` catch-all as free-text label+value —
it is never structured, never typed as insurance data, and is never mapped
anywhere outside the clinical Evidence Registry. It does **not** reach
`PatientFaceSheet`, `PatientInsurance`, or the Eligibility Workspace.

| SOURCE | TARGET | AUTOMATED? | MANUAL? | OWNER | CONSUMERS |
|---|---|---|---|---|---|
| `document_records.extracted_values.ai_key_findings[]` (category=`diagnosis`, `functional_status`, `decline_indicator`, `imaging_finding`, `medication`, `vital_sign`) | `evidence_record` (clinical Evidence Registry) | Auto-populated finding | Review required (`review_harvested_signal()` / `review_harvested_signals_batch()` in `harvest_service.py`) | RN (clinical review) | RNICA / clinical evidence UI, decline/root-cause narrative |
| `document_records.extracted_values.ai_key_findings[]` (category=`administrative`, e.g. label "Coverage", "Record type") | **NO MAPPING** — stays inside the JSON blob only | Not automated (no structured target exists) | N/A — nothing to review, nothing to consume | Nobody — architectural gap, not a bug | None today |

## Benefit-period-family fields — never automated, regardless of source

These fields must never be written, suggested, defaulted, or inferred by any
part of the system — not by OCR, not by the HNP import, not by an eligibility
verification/coverage response, not by a prior-certification lookup. Full
justification lives in `BenefitPeriodWorkflow.md`.

| SOURCE | TARGET | AUTOMATED? | MANUAL? | OWNER | CONSUMERS |
|---|---|---|---|---|---|
| — (must be staff-entered from scratch) | Benefit Period (First 90 / Second 90 / Third / Subsequent / Unknown / Transfer Patient) | **NO MAPPING** | Staff Entered Only | Staff | Readiness engine (once reviewed), recert scheduling |
| — (must be staff-entered from scratch) | Starting Cert # | **NO MAPPING** — must never default to `1` | Staff Entered Only | Staff | Cert-period display, recert scheduling |
| — (must be staff-entered from scratch) | Certification Sequence | **NO MAPPING** | Staff Entered Only | Staff | Recert scheduling |
| — (must be staff-entered from scratch) | Transfer Status (Yes/No + Transfer Source) | **NO MAPPING** | Staff Entered Only | Staff | Benefit Period Review, readiness engine |
| — (must be staff-entered from scratch) | Admission Approval / Readiness Status (as a *determination*) | Not automated as a determination | Staff Entered Only; system reports/enforces afterward | Staff, then system enforces | Billing Readiness Workspace |
| — (must be staff-entered from scratch) | Authorization Status (Contracted? / Authorization Required?) | **NO MAPPING** | Staff Entered Only | Staff | Readiness engine, claims submission gate |
| Staff-entered Benefit Period + Starting Cert + Transfer Status + SOC (the "anchor") | Future recertification schedule, reminders, tasks | Automated — but only after the anchor exists | N/A once anchor exists | System (scheduling only) | Recert reminders/tasks, IDG scheduling |

## Other structured models involved (confirmed distinct, do not conflate)

| Model | Table | Confirmed scope | Rows today |
|---|---|---|---|
| `PatientFaceSheet` | `patient_facesheet` | Free-text HOPE-A1400-reporting fields, edited via Facesheet chart "Insurance" card. `save_facesheet()` writes only this model — no side effects, no audit event. | in use |
| `PatientPayer` | `patient_payers` | Structured claims/MSP-domain model (`msp_validation_service.py`, `facility_payment_service.py`, `credit_balance_service.py`). Full CRUD via `POST/PUT /patients/{id}/payers`. **Not read by the eligibility roster or readiness engine.** | 5 rows system-wide |
| `PatientInsurance` | `patient_insurances` | The canonical model backing `list_eligibility_roster()` (`GET /billing/eligibility-roster`). No application-code creator exists anywhere — only a test fixture constructs one. Introduced in commit `64e036c`. | **0 rows, every tenant** |

## Evidence-type taxonomy for authorization/eligibility uploads (target state)

| Evidence type | Required when | Notes |
|---|---|---|
| Authorization approval / prior authorization / managed care approval | Authorization Required = YES | Blocks readiness if missing |
| `NON_AUTH_VERIFICATION` (coverage verification / representative note / eligibility confirmation) | Authorization Required = NO | New evidence-type name, not yet implemented in code |
| Benefit Period supporting evidence (NOE history, transfer packet, Medicare eligibility verification, prior hospice discharge information, benefit period history) | SOC entry for Medicare, especially Transfer Patient | Required to clear the SOC hard gate (not yet implemented) |

## Summary for future developers

1. **What OCR does**: extracts text + a fixed set of clinical "key findings"
   (diagnosis/functional status/decline indicators/imaging/medication/vitals)
   plus generic administrative notes. It also candidate-populates a narrow set
   of insurance *facts* (Medicare #, MBI, policy #, payer name, subscriber #)
   for the Facesheet — but has **no dedicated payer/benefit-period extraction
   target** in its schema today.
2. **What staff does**: confirms/corrects harvested facts; manually enters
   Benefit Period, Starting Cert, Certification Sequence, Transfer Status,
   Contracted/Authorization answers; uploads supporting evidence for each.
3. **What the system calculates**: forward-looking dates (recertification
   schedule, reminders, tasks) — but only after staff have established the
   benefit-period anchor.
4. **What the system must never calculate**: the initial Benefit Period,
   Starting Cert, Certification Sequence, or Transfer Status — from any source,
   including OCR, Medicare, eligibility verification results, coverage
   responses, prior certifications, or transfer packets.

See `BenefitPeriodWorkflow.md` for the full workflow narrative and the
real-world justification for this rule.
