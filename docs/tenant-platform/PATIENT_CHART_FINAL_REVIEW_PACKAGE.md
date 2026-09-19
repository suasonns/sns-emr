# PATIENT_CHART_FINAL_REVIEW_PACKAGE.md

## Status

FINAL REVIEW PACKAGE (bundled compilation)

This document bundles, for reviewer convenience, the final approval
comment and the three companion review/checklist documents added to
PR #92. Each section below is also maintained as its own standalone
file, which remains the authoritative version if this compilation ever
diverges from it:

- Approval comment: posted directly as a PR review comment on PR #92
  (see `PATIENT_CHART_FINAL_PR_APPROVAL_COMMENT.md`-sourced content
  below).
- `L33393_VALIDATION_CHECKLIST.md`
- `PATIENT_CHART_REVIEWER_SIGN_OFF_CHECKLIST.md`
- `PATIENT_CHART_CROSS_REFERENCE_REVIEW.md`

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

---

# PR #92 Final Approval Comment

## Decision

**APPROVED WITH CONDITIONS**

PR #92 establishes the documentation-only Patient Chart authority,
compliance-discovery, source-mapping, and reviewer-governance baseline.

The documentation package preserves source ownership across RNICA,
Visit Notes, Medications, Physician Orders, DME, Plan of Care, IDG,
Communication Log, Compliance and HOPE, and transition records.
Presentation and aggregation do not transfer source-record ownership.

## Approval Scope

This approval authorizes:

- Merge of the documentation pull request
- Documentation-only repository discovery
- Current-state mapping
- Gap analysis
- Implementation-discovery documentation

This approval does **not** authorize:

- Application implementation
- API or schema changes
- Database migrations
- Validation or permission changes
- Production-data changes
- Automated hospice-eligibility decisions
- Prognosis generation
- Physician-certification automation
- Automatic Plan-of-Care activation

## Compliance Review

The package correctly requires Patient Chart to display source-linked
clinical evidence without replacing physician certification or
individualized clinical judgment. CMS/LCD guidance must remain
documentation support rather than an automatic pass/fail mechanism.

The package also requires repository discovery of medical-record
authentication, correction, amendment, addendum, reconciliation,
deficiency-analysis, authorized-access, and Plan-of-Care versioning
behavior.

## Conditions

1. Complete section-level validation of LCD L33393 before assigning any
   L33393 requirement to implementation.
2. Validate certification ownership, source linkage, signer identity,
   dates, narrative location, and status lifecycle.
3. Validate Plan-of-Care proposal, review, approval, signature,
   activation, supersession, amendment, and version-history behavior.
4. Validate correction, amendment, addendum, authentication,
   countersignature, and audit-event behavior.
5. Keep California licensing requirements, federal CMS requirements,
   LCD guidance, SNS internal workflow, repository current state, and
   future product decisions separately classified.
6. Do not replace unresolved authority questions with implementation
   assumptions.

## Final Authorization

- **Documentation Pull Request:** APPROVED WITH CONDITIONS
- **Repository Discovery:** AUTHORIZED
- **Application Implementation:** NOT AUTHORIZED
- **Merge Status:** READY AFTER REQUIRED REVIEWER SIGN-OFFS

---

# LCD L33393 Validation Checklist

See standalone file `L33393_VALIDATION_CHECKLIST.md` for the
canonical, checkbox-tracked version of this checklist. Content is
reproduced here for bundled review convenience only.

## Document

`1.pdf`
LCD: `L33393`
Status: `DEEP_REVIEW_REQUIRED`

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

---

# Patient Chart Final Reviewer Sign-Off Checklist

See standalone file `PATIENT_CHART_REVIEWER_SIGN_OFF_CHECKLIST.md` for
the canonical, checkbox-tracked version of this checklist. Content is
reproduced here for bundled review convenience only.

## Scope

This checklist approves the documentation baseline and
repository-discovery scope only.

It does not authorize application implementation, deployment, API or
schema changes, migrations, production-data changes, automated
eligibility decisions, prognosis generation, physician-certification
automation, or automatic Plan-of-Care activation.

## Product and Workflow Authority

- [ ] The ten workflow phases use consistent names.
- [ ] Presentation does not transfer source-record ownership.
- [ ] Patient Story and Know the Patient remain presentation layers.
- [ ] RNICA remains assessment authority.
- [ ] Visit Notes remains visit-documentation authority.
- [ ] Medication, Physician Orders, DME, Plan of Care, IDG,
      Communication Log, Compliance and HOPE, and transition ownership
      remain separate.
- [ ] Future product direction is separated from current repository
      behavior.

Reviewer: | Role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## Clinical Authority

- [ ] Clinical findings remain linked to authoritative source records.
- [ ] Supporting evidence does not replace physician judgment.
- [ ] Assessment findings do not silently activate Plan-of-Care
      changes.
- [ ] Review, approval, authentication, and signature remain separate
      events.
- [ ] Finalization remains the sole active RNICA Final Clinical
      Narrative authority.

Reviewer: | Credentials or role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## California Compliance

- [ ] Admission and certification discovery is included.
- [ ] Initial and comprehensive assessment discovery is included.
- [ ] Plan-of-Care development, review, approval, signature, and
      version history are included.
- [ ] Medical-record retrieval, reconciliation, and deficiency analysis
      are included.
- [ ] Corrections, amendments, denied-request justification, and
      addenda are included.
- [ ] Unique authentication, countersignatures, audit history, access
      control, backup, disaster recovery, and downtime documentation
      are included.
- [ ] California requirements remain separately classified from
      Medicare requirements.

Reviewer: | Role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## CMS and LCD Review

- [ ] Physician certification remains separate from LCD evidence.
- [ ] No automatic eligibility or prognosis engine is authorized.
- [ ] Baseline and follow-up evidence remain source-linked.
- [ ] Functional status, ADLs, nutrition, symptoms, complications,
      hospitalizations, comorbidities, and disease-specific findings
      remain source-linked.
- [ ] Contradictory or stabilizing findings are included in discovery.
- [ ] Recertification uses the same prognosis standard and
      individualized documentation.
- [ ] LCD L33393 remains `DEEP_REVIEW_REQUIRED` until section-level
      validation is complete.

Reviewer: | Role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## Privacy, Security, and Record Integrity

- [ ] Role-based access and unique authentication are included in
      discovery.
- [ ] Shared-credential prevention is included.
- [ ] Original entries are preserved.
- [ ] Correction, amendment, addendum, authentication, and audit
      history are included.
- [ ] Backup, disaster recovery, and downtime documentation are
      included.
- [ ] No patient-sensitive information is added to this documentation
      PR.

Reviewer: | Role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## Engineering Discovery

- [ ] Exact repository paths are required.
- [ ] Missing repository behavior will not be invented.
- [ ] Current state, target state, defects, and future direction remain
      separate.
- [ ] Historical-record impact is required.
- [ ] Test impact is required.
- [ ] Blocking status is required.
- [ ] No code, API, schema, migration, validation, permission, or
      production-data changes are included.

Reviewer: | Role: | Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED | Date: | Conditions:

## Conditional Approval Register

| Condition ID | Review Area | Required Action | Owner | Blocking | Resolution Evidence | Status |
|---|---|---|---|---|---|---|
| | | | | YES / NO | | OPEN / RESOLVED |

## Final Gate

- [ ] Every review area has a recorded decision.
- [ ] Every reviewer and role are identified.
- [ ] Every condition is recorded.
- [ ] Every blocking condition is resolved or explicitly carried as a
      discovery blocker.
- [ ] California, CMS, LCD, internal workflow, repository state, and
      future decisions remain separately classified.
- [ ] `PATIENT_CHART_SOURCE_MAPPING.md` has been reviewed.
- [ ] `L33393_VALIDATION_CHECKLIST.md` has been added or linked.
- [ ] Cross-references are consistent.
- [ ] Documentation-only boundary is confirmed.

## Final Authorization

Documentation Pull Request:

- [ ] APPROVED
- [ ] APPROVED_WITH_CONDITIONS
- [ ] CHANGES_REQUIRED
- [ ] BLOCKED

Repository Discovery:

- [ ] AUTHORIZED
- [ ] NOT_AUTHORIZED

Application Implementation:

- [x] NOT_AUTHORIZED

Final approver:

Role:

Date:

Decision notes:

---

# Patient Chart Cross-Reference Consistency Review

See standalone file `PATIENT_CHART_CROSS_REFERENCE_REVIEW.md` for the
canonical, checkbox-tracked version of this review. Content is
reproduced here for bundled review convenience only.

## Status

`PASS_WITH_VERIFICATION_ITEMS`

## Canonical Workflow Names

Use exactly:

1. Patient Story
2. Know the Patient
3. Assess
4. Document Visit
5. Manage Treatment
6. Plan Care
7. Coordinate Team
8. Ensure Compliance
9. Handle Transitions
10. Track & Report

## Canonical Requirement Labels

Use only:

- `CALIFORNIA_REQUIRED`
- `FEDERAL_CMS_REQUIRED`
- `LCD_DOCUMENTATION_GUIDANCE`
- `ACCREDITATION_REQUIREMENT`
- `SNS_INTERNAL_WORKFLOW`
- `REPOSITORY_CURRENT_STATE`
- `FUTURE_PRODUCT_DECISION`

## Canonical Capability Classifications

Use only:

- `REUSABLE`
- `REQUIRES_PRESENTATION_REWIRING`
- `REQUIRES_LOGIC_REWIRING`
- `REQUIRES_REDESIGN`
- `MISSING_PRESENTATION`
- `MISSING_API_OR_SERVICE`
- `MISSING_SCHEMA`
- `CONFIRMED_DEFECT`
- `BLOCKED_BY_AUTHORITY_DECISION`
- `FUTURE_PRODUCT_DIRECTION`
- `NOT_CURRENTLY_CONNECTED`

## Canonical Plan-of-Care States

Use these authority concepts consistently:

- Draft
- Proposed
- Under Review
- Approved
- Signed
- Active
- Superseded
- Amended

Repository discovery may record different existing enum names, but
current repository values must not silently replace the approved
authority concepts.

## Canonical Certification and LCD Terms

Preferred:

- Physician Certification
- Physician Certification Status
- Supporting Evidence Identified
- LCD Supporting Evidence Present
- Clinical Documentation
- Documentation Review Complete
- Recertification

Avoid unsupported conclusions:

- Eligible
- Eligibility Confirmed
- LCD Passed
- Automatically Qualified
- Automatically Eligible
- Prognosis Generated
- Certification Verified

## Required Cross-References

- [ ] `PATIENT_CHART_WORKFLOW_AUTHORITY.md` links to the correction
      list, screen matrix, discovery prompt, compliance review, source
      mapping, and reviewer sign-off.
- [ ] `PATIENT_CHART_CORRECTION_LIST.md` references the workflow
      authority and source mapping.
- [ ] `PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md` references the
      workflow authority and correction list.
- [ ] `PATIENT_CHART_GITHUB_DISCOVERY_PROMPT.md` references all
      authority documents and the source mapping.
- [ ] `PATIENT_CHART_COMPLIANCE_GAP_REVIEW.md` references the source
      mapping and L33393 deep-review requirement.
- [ ] `PATIENT_CHART_SOURCE_MAPPING.md` marks L33393 as
      `DEEP_REVIEW_REQUIRED` until validated.
- [ ] `PATIENT_CHART_REVIEWER_SIGN_OFF.md` links to the source mapping,
      compliance review, and L33393 checklist.
- [ ] PR description links all included governance artifacts.
- [ ] Acceptance criteria reference the reviewer sign-off and source
      mapping.

## Verification Result

- Workflow naming: [ ] PASS [ ] FAIL
- Requirement labels: [ ] PASS [ ] FAIL
- Capability classifications: [ ] PASS [ ] FAIL
- Plan-of-Care terminology: [ ] PASS [ ] FAIL
- Certification terminology: [ ] PASS [ ] FAIL
- File links: [ ] PASS [ ] FAIL
- Documentation-only boundary: [ ] PASS [ ] FAIL

Reviewer:

Date:

Notes:

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
