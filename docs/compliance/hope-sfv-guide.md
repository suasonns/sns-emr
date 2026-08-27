# HOPE / SFV Item Mapping Guide

Canonical CMS HOPE (Hospice Outcomes & Patient Evaluation) item-to-SNS-field mapping
reference. Source: `hope-sfv-guide.docx` (user-provided reference document, uploaded
2026-08-23), preserved alongside this markdown transcription for diff-friendly review.

Column legend:

| Column | Purpose |
| --- | --- |
| CMS Item Code | Official HOPE item code |
| CMS Item Name | Official HOPE item label |
| SNS Assessment Section | Where the RN documents naturally |
| SNS Source Field | Actual field in the RN ICA/HUV/Update UI |
| Mapping Type | HOPE, SFV, or HOPE + SFV |
| UI Color | Green or Orange |
| AI Pre-fill Source | H&P, hospital record, labs, MD note, medication list, or manual |
| RN Action | Validate, modify, or complete |
| Trigger Logic | When the item is required or activated |
| HOPE Output | Value sent into HOPE record |
| SFV Output | Whether SFV item is required |
| Export Status | Mapped, missing, pending validation, SFV required |

> Note: the "SNS Source Field" column explicitly lists **"RN ICA/HUV/Update UI"** for
> most items — i.e. this reference treats the Admission RNICA, HUV1/HUV2, and Update
> Assessment forms as sharing the same underlying documentation UI. This confirms the
> architecture decision (see `hope-huv1-assessment` / `hope-huv2-assessment` todos):
> HUV1/HUV2 = an "Update Assessment" reusing RNICA minus the HOPE/SFV-only sections,
> not a separate bespoke form.

## Section A — Administrative Information

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0050 | Type of Record | HOPE Record Admin | Record type | HOPE | Green | System-generated | Validate if correction/modification | Admission, modification, inactivation | HOPE record type | None | Mapped |
| A0100 | Facility Provider Numbers | Agency Settings | NPI, CCN, Facility ID | HOPE | Green | Agency profile | Validate agency setup | Always required for HOPE record | Provider identifiers | None | Mapped |
| A0215 | Site of Service at Admission | General Assessment | Site of Service | HOPE | Green | Admission record / AI if present | Validate | Admission only | Site of service code | None | Mapped |
| A0220 | Admission Date | General Assessment | Admission date | HOPE | Green | Admission record | Validate | Admission only | Admission date | None | Mapped |
| A0250 | Reason for Record | HOPE Record Admin | Reason for record | HOPE | Green | System-generated | Validate | Admission, HUV, Discharge logic | Reason code | None | Mapped |
| A0270 | Discharge Date | Discharge Workflow | Discharge date | HOPE | Green | Discharge record | Validate | Discharge only | Discharge date | None | Mapped |
| A0500 | Legal Name of Patient | Patient Overview | Legal first, middle, last name | HOPE | Green | Demographics / admission packet | Validate | Always required | Patient legal name | None | Mapped |
| A0550 | Patient ZIP Code | Patient Overview | ZIP code | HOPE | Green | Demographics | Validate | Always required | ZIP code | None | Mapped |
| A0600 | Social Security and Medicare Numbers | Patient Overview | Social Security number; Medicare Beneficiary Identifier | HOPE | Green | Demographics / eligibility | Validate when available | Complete at applicable HOPE timepoints; either value may be blank only when unavailable or not applicable | SSN and Medicare/MBI identifiers | None | Mapped |
| A0700 | Medicaid Number | Patient Overview | Medicaid number | HOPE | Green | Eligibility / payer record | Validate | If Medicaid applicable | Medicaid value or not applicable value | None | Mapped |
| A0810 | Sex | Patient Overview | Sex | HOPE | Green | Demographics | Validate | Required at applicable HOPE timepoints | Sex code: 1 Male; 2 Female | None | Mapped |
| A0900 | Birth Date | Patient Overview | Date of birth | HOPE | Green | Demographics | Validate | Always required | DOB | None | Mapped |
| A1005 | Ethnicity | Patient Demographics | Ethnicity | HOPE | Green | Demographics / patient interview | Validate | Admission demographic collection | Ethnicity response | None | Mapped |
| A1010 | Race | Patient Demographics | Race | HOPE | Green | Demographics / patient interview | Validate | Admission demographic collection | Race response(s) | None | Mapped |
| A1110 | Language | General Assessment | Preferred language, interpreter need | HOPE | Green | Intake / patient interview | Validate | Admission demographic collection | Language fields | None | Mapped |
| A1400 | Payer Information | Patient Overview / Billing | Payer source | HOPE | Green | Billing / insurance | Validate | Always required | Payer code | None | Mapped |
| A1805 | Admitted From | General Assessment | Admitted-from location | HOPE | Green | Referral / H&P / admission intake | Validate | Admission only | Admitted-from code | None | Mapped |
| A1905 | Living Arrangements | General Assessment | Living arrangement | HOPE | Green | Intake / social history | Validate | Admission only | Living arrangement code | None | Mapped |
| A1910 | Availability of Assistance | General Assessment | Caregiver availability | HOPE | Green | Intake / caregiver interview | Validate | Admission only | Assistance code | None | Mapped |
| A2115 | Reason for Discharge | Discharge Workflow | Discharge reason | HOPE | Green | Discharge note | Validate | Discharge record only | Discharge reason code | None | Mapped |

## Section F — Preferences

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F2000 | CPR Preference | General Assessment / Advance Care Planning | CPR preference discussion | HOPE | Green | POLST, advance directive, H&P, admission packet | Validate | Admission HOPE | CPR discussion code/date | None | Mapped |
| F2100 | Other Life-Sustaining Treatment Preferences | General Assessment / Advance Care Planning | Life-sustaining treatment preference | HOPE | Green | POLST, advance directive, MD note | Validate | Admission HOPE | Treatment preference code/date | None | Mapped |
| F2200 | Hospitalization Preference | General Assessment / Goals of Care | Hospitalization preference | HOPE | Green | H&P, goals-of-care note, admission interview | Validate | Admission HOPE | Hospitalization preference code/date | None | Mapped |
| F3000 | Spiritual/Existential Concerns | Spiritual Screening | Spiritual/existential concern asked and response | HOPE | Green | Usually not reliable from AI unless documented in prior record | RN completes/validates | Admission HOPE | Spiritual concern code/date | None | Mapped |

## Section I — Active Diagnoses

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I0010 | Principal Diagnosis | Diagnosis Review | Principal hospice diagnosis | HOPE | Green | H&P, certification, hospital record, diagnosis list | Validate | Required at applicable HOPE timepoints | Principal diagnosis category | None | Mapped |
| I0600 | Heart Failure | Diagnosis Review | Heart failure comorbidity | HOPE | Green | H&P, hospital record, problem list | Validate | If active heart failure condition exists | Active diagnosis indicator | May activate NYHA display, not SFV by itself | Mapped |
| I6202 | Chronic Obstructive Pulmonary Disease (COPD) | Diagnosis Review | Active COPD diagnosis | HOPE | Green | H&P, hospital record, active problem list | Validate active status | Code only when COPD is active at the assessment timepoint | Active diagnosis indicator | None | Mapped |
| I8005 | Other Medical Condition | Diagnosis Review | Other active condition | HOPE | Green | H&P, problem list | Validate | If other condition is active and applicable | Other condition indicator | None | Mapped |

## Section J — Health Conditions

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J0050 | Death is Imminent | Imminently Dying Assessment | Life expectancy of 3 days or less | HOPE | Green | Current clinical assessment, RN observation, MD note | Complete/validate | Complete at Admission and HUV timepoints | 0 No; 1 Yes | None | Mapped |
| J0900 | Pain Screening | Pain Assessment | Pain screening completed, screening date, pain present | HOPE | Green | Current pain assessment and patient/caregiver interview | Complete/validate | Complete at applicable HOPE timepoints | Pain screening response and date | None | Mapped |
| J0905 | Pain Active Problem | Pain Assessment | Pain active problem yes/no | HOPE | Green | Pain assessment / problem list | Validate | If pain screen indicates ongoing pain issue | Active pain problem code | May feed J2051A | Mapped |
| J0910 | Comprehensive Pain Assessment | Pain Assessment | Comprehensive pain assessment completed/components/date | HOPE | Green | Pain assessment | Validate/complete | If comprehensive pain assessment is applicable | Comprehensive pain assessment output | None directly | Mapped |
| J0915 | Neuropathic Pain | Pain Assessment | Neuropathic pain indicator | HOPE | Green | H&P, pain note, neuropathy documentation | Validate | If pain assessment captures neuropathic pain | Neuropathic pain code | None directly | Mapped |
| J2030 | Screening of Shortness of Breath | Respiratory Assessment | SOB screened, date, SOB present | HOPE | Green | H&P, hospital record, oxygen order, respiratory notes | Validate | SOB screening documented | SOB screening output | Feeds J2051B | Mapped |
| J2040 | Treatment for Shortness of Breath | Respiratory Assessment | SOB treatment initiated/continued, date | HOPE | Green | Oxygen order, medication order, treatment record | Validate | If SOB present/treatment documented | SOB treatment output | None directly | Mapped |
| J2050 | Symptom Impact Screening | Symptom Impact / HOPE Symptom Section | Screening completed and screening date | HOPE | Green | Current clinician assessment and patient/caregiver input | Complete/validate | If J2050A = 0, skip J2051–J2053 and proceed to M1190; if J2050A = 1, complete J2051 | J2050A response and J2050B date | Determines whether symptom-impact items are completed | Mapped |
| J2051A | Symptom Impact: Pain | Pain Assessment / Symptom Impact | Pain impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | Pain assessment | Validate | If pain impact is moderate or severe, SFV required | Pain impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051B | Symptom Impact: Shortness of Breath | Respiratory Assessment / Symptom Impact | SOB impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | Respiratory assessment | Validate | If SOB impact is moderate or severe, SFV required | SOB impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051C | Symptom Impact: Anxiety | Neuro/Mental/Psychosocial / Symptom Impact | Anxiety impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, psychosocial note, RN observation | Validate | If anxiety impact is moderate or severe, SFV required | Anxiety impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051D | Symptom Impact: Nausea | GI/Nutrition / Symptom Impact | Nausea impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, GI note, medication list | Validate | If nausea impact is moderate or severe, SFV required | Nausea impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051E | Symptom Impact: Vomiting | GI/Nutrition / Symptom Impact | Vomiting impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, GI note, medication list | Validate | If vomiting impact is moderate or severe, SFV required | Vomiting impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051F | Symptom Impact: Diarrhea | GI/Nutrition / Symptom Impact | Diarrhea impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, GI note, bowel documentation | Validate | If diarrhea impact is moderate or severe, SFV required | Diarrhea impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051G | Symptom Impact: Constipation | GI/Nutrition / Symptom Impact | Constipation impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, bowel documentation, medication list | Validate | If constipation impact is moderate or severe, SFV required | Constipation impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2051H | Symptom Impact: Agitation | Neuro/Mental/Sensory / Symptom Impact | Agitation impact severity | HOPE + SFV | Green + Orange if Moderate/Severe | H&P, hospital record, behavior notes | Validate | If agitation impact is moderate or severe, SFV required | Agitation impact code | Triggers SFV if threshold met | Mapped or SFV Required |
| J2052 | Symptom Follow-up Visit (SFV) | SFV Engine / SFV Review | In-person SFV completed; SFV date; reason not completed | HOPE + SFV | Orange | System trigger plus RN/LPN/LVN follow-up documentation | Complete after trigger | Complete only when any J2051 response is 2 Moderate or 3 Severe; in-person SFV should occur within 2 calendar days | J2052A completion status, J2052B date, or J2052C reason not completed | SFV completion record | Pending until resolved |
| J2053 | SFV Symptom Impact | SFV Engine / SFV Review | Follow-up impact for pain, shortness of breath, anxiety, nausea, vomiting, diarrhea, constipation, and agitation | HOPE + SFV | Orange | In-person SFV observations, clinical assessment, and patient/caregiver input | Complete after a completed SFV | Complete when J2052A = 1; may be completed by an RN or LPN/LVN | J2053A–H impact codes | Follow-up symptom-impact findings | Pending until completed |

## Section M — Skin Conditions

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1190 | Skin Conditions | Skin / Wounds Assessment | Skin condition present yes/no | HOPE | Green | H&P, wound notes, hospital record | Validate | Skin assessment documented | Skin condition code | None | Mapped |
| M1195 | Types of Skin Conditions | Skin / Wounds Assessment | Type(s) of skin condition | HOPE | Green | Wound documentation | Validate | If skin condition exists | Skin condition type codes | None | Mapped |
| M1200 | Skin and Ulcer/Injury Treatments | Skin / Wounds Assessment | Skin/wound treatment | HOPE | Green | Wound orders, treatment orders | Validate | If treatment documented/applicable | Treatment code(s) | None | Mapped |

## Section N — Medications & Finalization

| CMS Item Code | CMS Item Name | SNS Assessment Section | SNS Source Field | Mapping Type | UI Color | AI Pre-fill Source | RN Action | Trigger Logic | HOPE Output | SFV Output | Export Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N0500 | Scheduled Opioid | Medication Review | Scheduled opioid initiated/continued, date | HOPE | Green | Medication list, orders, MAR | Validate | If scheduled opioid exists | Scheduled opioid code/date | None | Mapped |
| N0510 | PRN Opioid | Medication Review | PRN opioid initiated/continued, date | HOPE | Green | Medication list, orders, MAR | Validate | If PRN opioid exists | PRN opioid code/date | None | Mapped |
| N0520 | Bowel Regimen | Medication Review / GI | Bowel regimen status, documented reason if not initiated/continued, and date when applicable | HOPE | Green | Medication list, bowel regimen order, clinical documentation | Complete/validate | Complete only if N0500A = 1 or N0510A = 1 | N0520A code 0, 1, or 2; N0520B date when code = 2 | None | Mapped |
| Z0350 | Date Assessment Completed | Finalization / Sign-off | Assessment completed date | HOPE | Green | System timestamp | Validate at sign-off | Assessment finalization | Completion date | None | Mapped |
| Z0400 | Signatures of Persons Completing Record | Finalization / Sign-off | Completing clinician(s) | HOPE | Green | Authenticated user/session | Sign | Finalization | Signature record | None | Mapped |
| Z0500 | Signature of Person Verifying Record Completion | Finalization / Sign-off | Verifying person/signature/date | HOPE | Green | Authenticated verifier | Sign/verify | Required before export | Verification signature | None | Mapped |

## Cross-check notes against current implementation (as of 2026-08-23)

Checked against `sns-emr-frontend/src/intake/hopeReportMapper.js` / `HopeReport.jsx`:

- **SFV trigger logic matches**: `getSfvStatus()` already implements "any J2051(A-H) =
  Moderate/Severe → SFV required within 2 calendar days", including the "may be
  documented by an RN or LPN/LVN" language for J2053, consistent with this guide.
- **Z0350/Z0400/Z0500** are present in the finalization/sign-off flow.
- **Not yet verified**: whether I0600/I6202/I8005 comorbidity codes are populated from
  real active-diagnosis data (Heart Failure/COPD/Other) for patients with those
  conditions (e.g. Loren Shields' CHF) — flagged for follow-up.
- **N0520 conditional trigger** ("only if N0500A=1 or N0510A=1") and **A0600** ("either
  value may be blank only when unavailable/not applicable") are validation nuances
  worth confirming against `hopeReportMapper.js`'s current validation, not yet checked.
- **A0250 variants** (HUV/Discharge reason codes) are a known gap — see
  `hope-report-cms-code-gaps` todo.
