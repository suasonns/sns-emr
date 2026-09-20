# PATIENT_CHART_SOURCE_MAPPING.md

## Status

DOCUMENT_REVIEWED / REPOSITORY_VALIDATION_REQUIRED

Companion source-citation register for `PATIENT_CHART_WORKFLOW_AUTHORITY.md`,
`PATIENT_CHART_CORRECTION_LIST.md`,
`PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`,
`PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md`, and
`PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md`. None of those five documents
is reopened by this document.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

## Purpose

Provide a single, structured register of every external regulatory or
guidance source cited across the Patient Chart documentation family,
with an explicit validation status per row.

## Column Definitions

- **Source File** — the cited source document.
- **Authority Type** — the regulatory or guidance category of the
  source.
- **Section or Topic** — the specific section or subject matter cited.
- **Explicit Source Content** — the supplied summary of what the source
  states.
- **Patient Chart Mapping** — how the Patient Chart authority package
  applies that content.
- **Affected Documents** — which Patient Chart documents reference this
  citation.
- **Requirement Label** — one of `CALIFORNIA_REQUIRED`,
  `FEDERAL_CMS_REQUIRED`, `LCD_DOCUMENTATION_GUIDANCE`,
  `ACCREDITATION_REQUIREMENT`, `SNS_INTERNAL_WORKFLOW`,
  `REPOSITORY_CURRENT_STATE`, or `FUTURE_PRODUCT_DECISION`.
- **Validation Status** — one of `DOCUMENT_REVIEWED`,
  `REPOSITORY_VALIDATION_REQUIRED`, or `DEEP_REVIEW_REQUIRED`.
- **Review Notes** — required caveats, scope limits, or follow-up
  actions.

## Source Mapping Register

| Source File | Authority Type | Section or Topic | Explicit Source Content | Patient Chart Mapping | Affected Documents | Requirement Label | Validation Status | Review Notes |
|---|---|---|---|---|---|---|---|---|
| DPH-18-002E-HospiceAgencies_Text.pdf | California hospice requirement | Section 74860: Admission and certification | Admission requires the applicable physician order and an initial certification record with required dates, signatures, and supporting clinical documentation. | Map admission-order ownership, certification-record ownership, certifying practitioner, practitioner role, certification date, authentication, signature, narrative, episode, payer, and program context. Do not infer certification from diagnosis or LCD evidence. | PATIENT_CHART_WORKFLOW_AUTHORITY.md; PATIENT_CHART_CORRECTION_LIST.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | California licensing certification must remain separately identified from Medicare benefit certification. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California hospice requirement | Section 74864: Assessments | The source describes an initial RN assessment, a comprehensive assessment, written documentation, filing in the medical record, and periodic assessment updates. | Preserve RNICA and authorized discipline-assessment ownership. Map assessment author, dates, filing, update history, patient condition changes, outcome progress, response to care, and assessment-to-POC relationships. | PATIENT_CHART_WORKFLOW_AUTHORITY.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | Exact repository implementation and timer enforcement must be discovered rather than assumed. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California hospice requirement | Section 74868: Individualized Plan of Care | The interdisciplinary team develops the written individualized Plan of Care based on the comprehensive assessment and in collaboration with the applicable physician authority. | Separate assessment evidence, IDT development, physician collaboration, approval, signature, activation, implementation, and version history. | PATIENT_CHART_WORKFLOW_AUTHORITY.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | A proposed POC element must not be represented as active without the required recorded approval. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California hospice requirement | Section 74872: Plan of Care review | The Plan of Care is reviewed and updated as required by the patient's condition and at least every 15 days. Reviews include recent assessment information, progress toward outcomes, response to care, physician collaboration, and preservation of all POC versions. | Map POC review due dates, prior versions, current version, proposed modifications, physician collaboration, approval, signature, activation, supersession, and amendment. | PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | Repository discovery must verify whether current status values distinguish proposed, approved, signed, active, superseded, and amended. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California medical-record requirement | Section 74888: Medical Record Service | Patient records must be complete, accurate, accessible to authorized users, systematically organized, and supported by retrieval, reconciliation, deficiency analysis, correction, and amendment processes. | Map record retrieval, authorized access, discharge reconciliation, deficiency analysis, correction requests, amendment requests, decisions, denial justification, and source-record preservation. | PATIENT_CHART_WORKFLOW_AUTHORITY.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | Do not mark administrative discharge complete until applicable reconciliation conditions are satisfied. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California medical-record requirement | Authentication, corrections, and addenda | Authorized entries use unique identity and authentication. Corrections require a written explanation, discovery date, correction date, and authentication. Addenda must be distinct and traceable. | Preserve original entries. Separate review, approval, authentication, signature, correction, amendment, and addendum events. Record actor, role, date, time, reason, and source record. | PATIENT_CHART_CORRECTION_LIST.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | Silent overwrite and reattribution of authorship are prohibited by the authority package. |
| DPH-18-002E-HospiceAgencies_Text.pdf | California electronic-record requirement | Electronic access, authentication, backup, and recovery | The source addresses access controls, unique authentication, regular backups, disaster recovery, manual documentation during system outages, and linkage of electronic patient information from multiple providers. | Inventory role-based access, unique identifiers, shared-credential prevention, backup behavior, downtime documentation, restoration, reconciliation, and multi-provider record linkage. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | CALIFORNIA_REQUIRED | REPOSITORY_VALIDATION_REQUIRED | The documentation PR does not authorize system changes. |
| cms guidelines.pdf | CMS LCD documentation guidance | LCD L34538: Hospice Determining Terminal Status | Medicare hospice coverage depends on physician certification of a prognosis of six months or less if the terminal illness follows its normal course. Documentation must support terminal status. | Patient Chart may display source-linked supporting evidence and authenticated certification status. Patient Chart must not generate eligibility, terminal prognosis, or physician certification. | PATIENT_CHART_WORKFLOW_AUTHORITY.md; PATIENT_CHART_CORRECTION_LIST.md; PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Use evidence-support language rather than automatic eligibility language. |
| cms guidelines.pdf | CMS LCD documentation guidance | Individualized documentation and contradictory findings | The LCD recognizes that listed guidelines are not the only possible support and that patient-specific documentation should explain relevant clinical findings, including findings inconsistent with a six-month prognosis. | Do not implement checklist-only pass or fail. Map contradictory evidence, stability, improvement, decline, individualized factors, and clinician documentation. | PATIENT_CHART_CORRECTION_LIST.md; PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | The LCD-support interface must not replace individualized physician judgment. |
| hospice_terminal_prog_non-disease_specific.pdf | LCD-aligned working guide | Non-disease-specific decline and baseline guidance | The guide describes medical-record support for the six-month prognosis, baseline and follow-up evidence where appropriate, functional status, ADL dependence, symptoms, complications, utilization, nutrition, and comorbidities. | Map dated PPS, KPS, ADL, nutrition, symptom, complication, hospitalization, utilization, and comorbidity evidence to authoritative records. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Diagnosis alone must not be represented as sufficient documentation support. |
| ALS.pdf | Disease-specific LCD working guide | ALS documentation support | The guide uses multiple patient-specific factors, including breathing capacity, swallowing, progression, nutritional status, treatment choices, and complications. | Preserve dated, source-linked ALS findings. Do not convert individual findings into an automatic prognosis or eligibility verdict. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Use together with current controlling LCD guidance. |
| hospice_terminal_prog_pulmonary_disease.pdf | Disease-specific LCD working guide | Pulmonary-disease documentation support | The guide references severe chronic lung disease, documented progression, hypoxemia or hypercapnia, and supporting factors such as weight loss and tachycardia. | Map objective measurements, source dates, hospital records, progression evidence, symptoms, and supporting findings without requiring evidence described as optional. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Applicability and source dates must remain explicit. |
| hospice_terminal_prog_renal_failure.pdf | Disease-specific LCD working guide | Renal-disease documentation support | The guide references dialysis or transplant decisions, renal measurements, symptoms, treatment status, and comorbid conditions. | Map treatment decisions, renal measurements, symptoms, dates, and comorbidities to authoritative records. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Treatment choice and clinical measurements require separate source provenance. |
| hospice_terminal_prog_stroke_coma.pdf | Disease-specific LCD working guide | Stroke and coma documentation support | The guide references functional status, nutrition and hydration, aspiration, imaging, neurologic responses, and complications. | Preserve measurement, source, date, clinical context, and diagnosis applicability for stroke or coma evidence. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Do not apply stroke/coma criteria to unrelated diagnoses. |
| hospice_terminal_prog_liver_disease.pdf | Disease-specific LCD working guide | Liver-disease documentation support | The guide references coagulation findings, albumin, end-stage liver complications, nutrition, muscle wasting, and supporting clinical factors. | Map dated laboratory results, complications, nutritional evidence, and source records while preserving physician judgment. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Laboratory results alone must not become an automatic verdict. |
| heart disease.pdf | Disease-specific LCD working guide | Heart-disease documentation support | The guide references treatment status, NYHA Class IV, symptoms at rest, and additional supporting factors. | Map treatment status, procedure decisions, NYHA class, symptoms, measurements, and supporting findings to authoritative sources. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | NYHA applicability and source documentation must be verified. |
| dementia.pdf | Disease-specific LCD working guide | Dementia due to Alzheimer's disease | The guide references FAST stage, ADL dependence, continence, communication, complications, and nutrition, and limits the disease-specific section to Alzheimer's disease and related disorders. | Apply disease-specific logic only in the documented applicable diagnosis context. Preserve dated FAST, ADL, communication, complication, and nutrition evidence. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md | LCD_DOCUMENTATION_GUIDANCE | DOCUMENT_REVIEWED | Do not generalize the Alzheimer-related guidance to every dementia diagnosis. |
| 1.pdf | CMS LCD reference | LCD L33393 | The retrieved enterprise result identifies the file as LCD L33393, but the retrieved result did not expose sufficient section-level content for this review. | Open and map applicable L33393 sections during repository discovery before assigning requirements to this source. | PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md; PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md | LCD_DOCUMENTATION_GUIDANCE | DEEP_REVIEW_REQUIRED | Do not claim a section-level L33393 requirement until the exact section is retrieved and documented. |

## Source-Conflict Precedence

Apply, in descending order:
1. Newest California CDPH hospice requirements
2. Current California statutes and directives
3. Current federal CMS hospice requirements
4. Current applicable CMS LCD guidance
5. Accreditation standards
6. Internal and legacy interpretations

Conflicts between rows above (for example, the California 12-month
initial-certification reference versus the Medicare six-month benefit
standard) must be documented per `PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md`
item 1, not silently resolved.

## Provenance note

All citations in this register are recorded as supplied source input.
They have not been independently re-verified against the underlying
regulatory or guidance PDFs by this repository session. `1.pdf` (LCD
L33393) is explicitly marked `DEEP_REVIEW_REQUIRED` because the supplied
source content was insufficient to extract section-level requirements.
No row in this register may be treated as implementation-ready until
its `Validation Status` reads `DOCUMENT_REVIEWED` and repository
discovery under `PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md` has confirmed
the corresponding repository behavior.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
