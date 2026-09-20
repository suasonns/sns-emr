# RNICA Document Freeze, Source-Change Control, and Evidence-Only Action Plan

**STATUS:** DISCOVERY / GOVERNANCE CONTROL ONLY. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED
**SCHEMA:** BLOCKED
**MIGRATIONS:** BLOCKED
**AUTOMATIC VISIT CLASSIFICATION:** BLOCKED

## Decision

The RNICA authority, SFV, HOPE, California, traceability, validation, and acceptance documents are now:

`FROZEN_FOR_EVIDENCE_COLLECTION`

The current structure must not be rewritten merely to improve wording, formatting, organization, labels, dashboards, tables, or acceptance language.

The project now moves from:

`DOCUMENT REVISION`

to:

`EVIDENCE COLLECTION AND CONTROL CLOSURE`

Current tracker status:

- Completed controls: `22/77`
- Remaining controls: `55/77`
- Implementation authorization: `NOT_AUTHORIZED`

---

# 1. Document-Freeze Policy

## Frozen Artifacts

Freeze the current approved versions of:

- RNICA authority matrix
- RNICA assessment and visit-classification rules
- RNICA visit-classification decision table
- RNICA assessment state model
- RNICA classification test scenarios
- RNICA HOPE source-validation gaps
- RNICA SFV/LVN escalation authority
- SFV traceability matrix
- SFV validation dashboard
- SFV acceptance checklist
- Issue #121 structure and completion-count model

## Freeze Rule

Do not revise a frozen artifact unless at least one approved revision trigger is satisfied.

The following are not valid revision triggers:

- Rewording for style
- Reformatting tables
- Rearranging headings
- Renaming a section without changing meaning
- Adding another summary of existing requirements
- Repeating an already documented citation
- Recalculating unchanged dashboard counts
- Rewriting an existing checklist in another format
- Creating another version of the same authority matrix
- Reopening a settled interpretation without new controlling evidence

## Allowed Without Unfreezing

The following evidence-only actions do not require reopening the frozen documents:

- Attach a source
- Add an exact citation
- Record a source version
- Record an effective date
- Add a repository path
- Add a model, table, field, API, or workflow reference
- Attach a validation report
- Attach a test result
- Add approval evidence
- Change a control status
- Update completion counts
- Close a validated control
- Link an issue or pull request
- Record a reviewer's decision

These updates must add evidence without changing the previously approved rule.

---

# 2. Approved Revision Triggers

A frozen document may be revised only when one or more of these triggers applies.

## Regulatory Trigger

- A new California CDPH regulation becomes effective.
- A California statute or directive changes the existing rule.
- A federal CMS Condition of Participation changes.
- A controlling CMS final rule changes an existing requirement.
- A new controlling LCD revision changes the applicable documentation rule.

## HOPE or iQIES Trigger

- CMS publishes a new HOPE Guidance Manual version.
- CMS publishes a revised HOPE item set.
- CMS publishes a new final HOPE data-specification version.
- CMS publishes applicable errata.
- CMS changes an iQIES fatal or warning edit relevant to RNICA.
- CMS changes a timepoint, trigger, item definition, submission sequence, or correction rule.
- CMS publishes controlling clarification that resolves or contradicts an existing interpretation.

CMS currently maintains HOPE specifications and errata through the Hospice Outcomes and Patient Evaluation (HOPE) Technical Information page. The source lists final data specifications, errata, iQIES submission, and the Validation Utility Tool.

## Conflict Trigger

- A newer controlling source conflicts with a frozen rule.
- Two controlling sources produce different requirements.
- The current authority label is proven incorrect.
- An internal SNS rule was incorrectly presented as a regulatory requirement.
- A regulatory requirement was incorrectly presented as an internal preference.

## Repository Trigger

- Repository discovery proves that the documented source of truth is incorrect.
- A current workflow cannot support the documented rule.
- A model, field, table, API, or status has a different meaning than documented.
- An implementation constraint changes the approved architecture.
- A validated defect shows that the frozen rule would cause unsafe or noncompliant behavior.

## Clinical-Authority Trigger

- The Medical Director approves a different clinical escalation rule.
- The Director of Patient Care Services approves a different nursing workflow.
- Compliance rejects or changes an internal policy.
- An agency policy is formally approved, replaced, or withdrawn.

## Safety Trigger

- The frozen rule could misclassify a visit.
- The frozen rule could hide a required notification.
- The frozen rule could alter or lose medical-record evidence.
- The frozen rule could activate an unapproved Plan-of-Care change.
- The frozen rule could incorrectly generate, complete, correct, or submit a HOPE record.

California requires written approval before implementing a proposed Plan-of-Care modification, notification when a significant change may require modification, preservation of Plan-of-Care versions, authenticated record entries, traceable corrections, and distinct addenda. DPH-18-002E-HospiceAgencies_Text.pdf supports treating safety, record-integrity, and approval conflicts as valid revision triggers.

---

# 3. Revision Approval Gate

Before changing a frozen artifact, create one source-change decision-log entry and complete all fields.

A revision is authorized only when:

- [ ] A valid trigger is identified
- [ ] The new source is attached
- [ ] The source title and issuing authority are recorded
- [ ] Publication and effective dates are recorded
- [ ] The exact section, item, edit, or provision is cited
- [ ] The old rule is quoted
- [ ] The proposed replacement is quoted
- [ ] The conflict or impact is explained
- [ ] Affected documents are listed
- [ ] Affected controls and tests are listed
- [ ] Compliance approval is recorded
- [ ] Clinical approval is recorded when applicable
- [ ] Engineering impact is recorded when applicable
- [ ] The decision is linked to a pull request

If these conditions are not met:

`DO_NOT_REVISE`

---

# 4. Source-Change Decision Log

Use this table for every future source change.

| Change ID | Date Identified | Source Authority | Source Title and Version | Publication Date | Effective Date | Exact Section or Edit | Prior Rule | New Requirement | Conflict or Impact | Affected Artifacts | Affected Controls | Decision | Approvers | PR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SRC-001 |  |  |  |  |  |  |  |  |  |  |  | PENDING |  |  |

## Decision Values

Use only:

- `NO_CHANGE`
- `EVIDENCE_ADDED`
- `CLARIFICATION_ONLY`
- `REVISION_REQUIRED`
- `SUPERSEDES_PRIOR_RULE`
- `IMPLEMENTATION_IMPACT`
- `REJECTED_NOT_CONTROLLING`

## Source Priority

Apply sources in this order:

1. Newest California CDPH hospice requirements
2. Current California statutes and directives
3. Current federal CMS Hospice Conditions of Participation
4. Current official CMS HOPE and HQRP materials
5. Current CMS hospice LCD guidance
6. Accreditation requirements
7. Formally approved SNS policy
8. Repository current state
9. Legacy internal interpretation

## Supersession Rule

When a newer controlling source changes an existing rule:

- Preserve the prior rule in history.
- Mark the prior rule as superseded.
- Record the effective date of the replacement.
- Do not silently overwrite the old interpretation.
- Identify affected tests, workflows, fields, APIs, forms, and training.
- Update only the artifacts affected by the changed requirement.

Revision history for CMS guidance shows that some revisions are substantive while others are annual reviews or typographical corrections. Therefore, publication of a new revision by itself does not automatically justify rewriting RNICA. The impact must first be evaluated.

---

# 5. Evidence-Only Action Plan

## Operating Rule

The remaining 55 controls are evidence tasks.

Do not rewrite the authority documents while completing these controls.

For every control:

1. Retrieve the controlling source or repository evidence.
2. Record the exact location.
3. Record the finding.
4. Attach or link the evidence.
5. Record the applied decision.
6. Add or link the corresponding test scenario.
7. Obtain required review.
8. Change the control status.
9. Update the dashboard count.

## Evidence Package Required for Closure

Each control must include:

- Direct source URL or repository path
- Source title and version
- Publication date, if stated
- Effective date, if stated
- Exact section, item, edit, field, model, or table
- Relevant excerpt or technical result
- Validation date
- Accountable owner
- Reviewer
- Applied RNICA decision
- Test or repository proof
- Linked issue or pull request
- Final disposition

No control may close from:

- A new summary
- A reworded policy
- An uncited interpretation
- A screenshot without source context
- A meeting statement without recorded evidence
- Schedule completion alone

---

# 6. Remaining 55 Controls

## Workstream A: CMS SFV Edge Cases

**Target:** `15/15`
**Current:** `0/15`
**Deliverable:** Evidence and disposition only

- [ ] SFV-001: Patient death before expected SFV
- [ ] SFV-002: Discharge before expected SFV
- [ ] SFV-003: Revocation before expected SFV
- [ ] SFV-004: Transfer before expected SFV
- [ ] SFV-005: Patient refusal
- [ ] SFV-006: Patient unavailable
- [ ] SFV-007: Caregiver refusal
- [ ] SFV-008: Inability to complete because of clinical condition
- [ ] SFV-009: Same-day trigger and SFV
- [ ] SFV-010: SFV after the two-calendar-day window
- [ ] SFV-011: Overlapping trigger windows
- [ ] SFV-012: Multiple symptoms from one trigger
- [ ] SFV-013: Corrected trigger after SFV
- [ ] SFV-014: Inactivated trigger after SFV
- [ ] SFV-015: Death/discharge measure treatment

### Closure Evidence

For each item:

- CMS source
- Exact section
- Disposition
- Given/When/Then test
- Compliance review

Do not change the core SFV authority statements unless the evidence contradicts them.

---

## Workstream B: iQIES and Data Specifications

**Target:** `15/15`
**Current:** `0/15`
**Deliverable:** Technical evidence only

- [ ] IQIES-001: Current final HOPE specification version
- [ ] IQIES-002: Current errata version
- [ ] IQIES-003: SFV fatal edits
- [ ] IQIES-004: SFV warning edits
- [ ] IQIES-005: Missing-trigger edits
- [ ] IQIES-006: Date-sequence edits
- [ ] IQIES-007: Duplicate-record edits
- [ ] IQIES-008: Missing-J2052 edits
- [ ] IQIES-009: Missing-J2053 edits
- [ ] IQIES-010: Accepted submission
- [ ] IQIES-011: Accepted-with-warning submission
- [ ] IQIES-012: Rejected or fatal submission
- [ ] IQIES-013: Modification workflow
- [ ] IQIES-014: Inactivation workflow
- [ ] IQIES-015: Correction and resubmission

### Closure Evidence

For each item:

- Specification or errata version
- Effective date
- Edit number
- Edit condition
- Expected result
- Validation report or VUT evidence
- Test scenario
- Engineering and compliance review

The current CMS technical page identifies final HOPE Data Specifications V1.00.1 and Errata V1.00.3, with the cited errata effective February 18, 2026. This information should be logged as evidence, not used as a reason to rewrite unrelated documents.

---

## Workstream C: Repository Mapping

**Target:** `15/15`
**Current:** `0/15`
**Deliverable:** Repository evidence only

- [ ] REPO-001: Authoritative HOPE entity
- [ ] REPO-002: J2050/J2050B
- [ ] REPO-003: J2051
- [ ] REPO-004: J2052
- [ ] REPO-005: J2053
- [ ] REPO-006: HOPE Admission
- [ ] REPO-007: HUV1
- [ ] REPO-008: HUV2
- [ ] REPO-009: SFV
- [ ] REPO-010: Patient, episode, and benefit-period linkage
- [ ] REPO-011: Service, entry, and signature timestamps
- [ ] REPO-012: Clinician identity, credential, and discipline
- [ ] REPO-013: Version and correction history
- [ ] REPO-014: Modification and inactivation behavior
- [ ] REPO-015: iQIES submission and validation statuses

### Closure Evidence

For each item:

- Repository path
- Model and table
- Field names
- API or service
- Current behavior
- Source-of-truth owner
- Gap or conflict
- Test proof
- Engineering review

If repository evidence matches the frozen rule, close the control without modifying the authority documents.

If repository evidence conflicts with the frozen rule, create a source-change decision before revising anything.

---

## Workstream D: SNS Clinical-Policy Approval

**Target:** `10/10`
**Current:** `0/10`
**Deliverable:** Recorded decisions only

- [ ] SNS-001: LVN severe-symptom escalation
- [ ] SNS-002: Findings requiring RN review
- [ ] SNS-003: RN-review priority and response requirement
- [ ] SNS-004: Responsible RN and fallback ownership
- [ ] SNS-005: Incomplete-review escalation
- [ ] SNS-006: Physician/Medical Director notification triggers
- [ ] SNS-007: Plan-of-Care review triggers
- [ ] SNS-008: Required LVN evidence
- [ ] SNS-009: Late-SFV review ownership
- [ ] SNS-010: Correction and amendment authority

### Closure Evidence

For each item:

- Decision text
- Decision owner
- Approver
- Effective date
- Workflow impact
- Evidence requirements
- Test scenario
- GitHub approval record

California already requires written approval before implementing proposed Plan-of-Care modifications, significant-change notification as soon as possible within 24 hours when modification may be necessary, periodic Plan-of-Care review, preservation of all Plan-of-Care versions, authenticated entries, and traceable corrections and addenda. SNS decisions must operate within those boundaries.

---

# 7. Dashboard Update Rule

Update only the control status and counts.

Do not rewrite the issue body after each closure.

Use:

| Workstream | Complete | Total | Remaining |
|---|---:|---:|---:|
| Core CMS SFV rules | 17 | 17 | 0 |
| CMS SFV edge cases | 0 | 15 | 15 |
| iQIES/data specifications | 0 | 15 | 15 |
| Repository mappings | 0 | 15 | 15 |
| SNS policy approvals | 0 | 10 | 10 |
| California controls | 5 | 5 | 0 |
| **Overall** | **22** | **77** | **55** |

After closing a control:

1. Check the item.
2. Update its status.
3. Increase the completed total by one.
4. Reduce the remaining total by one.
5. Link the evidence.
6. Do not revise unrelated text.

---

# 8. Freeze Exit Rule

The document freeze ends only when:

- A valid revision trigger is approved, or
- All controls reach `77/77` and implementation planning is separately authorized.

## Final Status

- Authority documents: `FROZEN`
- Decision log: `ACTIVE`
- Evidence collection: `AUTHORIZED`
- Remaining controls: `55`
- Document rewriting: `NOT_AUTHORIZED_WITHOUT_TRIGGER`
- Application implementation: `NOT_AUTHORIZED`
- Database changes: `NOT_AUTHORIZED`
- Production deployment: `NOT_AUTHORIZED`

---

Related: `docs/rnica/RNICA_AUTHORITY_MATRIX.md`, `docs/rnica/RNICA_SFV_LVN_ESCALATION_AUTHORITY.md`, GitHub issue #121.
