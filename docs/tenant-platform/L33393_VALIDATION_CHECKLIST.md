# L33393_VALIDATION_CHECKLIST.md

## Document

`1.pdf`
LCD: `L33393`
Status: `DEEP_REVIEW_REQUIRED`

Companion working checklist for condition **PC-COND-1** in
`PATIENT_CHART_REVIEWER_SIGN_OFF.md` and the `DEEP_REVIEW_REQUIRED` row
for `1.pdf` in `PATIENT_CHART_SOURCE_MAPPING.md`. This checklist is
more detailed than `PATIENT_CHART_LCD_L33393_VALIDATION_CHECKLIST.md`
and supersedes it as the working document for PC-COND-1; the earlier
file is left in place for history and should be treated as superseded
rather than an independent authority.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

## Validation Rule

Do not assign a section-level requirement to LCD L33393 until the
complete source section, revision/effective-date context, and
applicability have been retrieved and recorded.

## Source Identity

- [ ] Confirm LCD number and title.
- [ ] Record contractor and jurisdiction.
- [ ] Record current status.
- [ ] Record revision number.
- [ ] Record revision effective date.
- [ ] Record source retrieval date.
- [ ] Record the exact source location used for each mapped
      requirement.

## Coverage and Certification

- [ ] Identify the physician-certification requirement.
- [ ] Verify the six-month prognosis standard.
- [ ] Identify initial-certification guidance.
- [ ] Identify recertification guidance.
- [ ] Identify patient-specific documentation expectations.
- [ ] Identify guidance for patients who do not neatly meet listed
      criteria.
- [ ] Identify guidance for stability or improvement.
- [ ] Identify discharge considerations tied to prognosis.

## General Documentation

- [ ] Map observations and measurements expected in the record.
- [ ] Map baseline and follow-up evidence.
- [ ] Map PPS/KPS guidance.
- [ ] Map ADL-dependence guidance.
- [ ] Map nutritional-decline guidance.
- [ ] Map symptom and complication guidance.
- [ ] Map utilization or hospitalization guidance.
- [ ] Map comorbidity guidance.
- [ ] Map objective-finding guidance.
- [ ] Map contradictory or stabilizing evidence.
- [ ] Verify whether diagnosis alone is insufficient.

## Disease-Specific Sections

- [ ] Cancer.
- [ ] Dementia and Alzheimer-related disorders.
- [ ] ALS.
- [ ] Heart disease.
- [ ] Pulmonary disease.
- [ ] Renal disease.
- [ ] Liver disease.
- [ ] Stroke and coma.
- [ ] HIV disease.
- [ ] Any additional disease category present in L33393.

For each applicable section:

- [ ] Record exact section/page.
- [ ] Record applicability conditions.
- [ ] Record required versus supporting findings.
- [ ] Record optional evidence explicitly as optional.
- [ ] Record source date and measurement requirements.
- [ ] Record conflicts with L34538 or newer CMS guidance.
- [ ] Apply the newest controlling CMS source when a conflict exists.

## Diagnosis and Coding

- [ ] Compare the proposed principal diagnosis with attached
      restriction lists.
- [ ] Separate principal terminal diagnosis from related conditions.
- [ ] Separate coexisting conditions from symptoms.
- [ ] Identify diagnoses that cannot appropriately serve as principal
      hospice diagnosis.
- [ ] Document any conflict between a code list, disease guide, and
      current CMS source.

## Patient Chart Mapping

- [ ] Identify the Patient Chart workflow phase affected.
- [ ] Identify the source authority.
- [ ] Identify the repository entity.
- [ ] Identify the service and API.
- [ ] Identify the status model.
- [ ] Identify validation behavior.
- [ ] Identify audit behavior.
- [ ] Identify historical-record impact.
- [ ] Identify test impact.

## Safety and Authority Boundaries

- [ ] No automatic eligibility verdict is introduced.
- [ ] No automatic prognosis is introduced.
- [ ] No physician-certification logic is inferred from documentation
      criteria.
- [ ] Supporting evidence remains separate from certification.
- [ ] Physician judgment remains authoritative.
- [ ] Contradictory evidence remains visible.

## Cross-Reference Updates

- [ ] Update `PATIENT_CHART_SOURCE_MAPPING.md`.
- [ ] Update `PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md`.
- [ ] Update `PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md` if new
      discovery fields are required.
- [ ] Update the PR body only when the source mapping is verified.
- [ ] Record unresolved gaps as blockers or discovery items.

## Final Result

- [ ] VALIDATED
- [ ] VALIDATED_WITH_GAPS
- [ ] NOT_VALIDATED

Reviewer:

Role or credentials:

Date:

Notes:

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
