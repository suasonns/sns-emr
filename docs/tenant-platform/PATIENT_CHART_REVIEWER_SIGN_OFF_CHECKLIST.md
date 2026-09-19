# PATIENT_CHART_REVIEWER_SIGN_OFF_CHECKLIST.md

## Status

REVIEWER CHECKLIST — TEMPLATE (unsigned)

Per-area reviewer checklist companion to `PATIENT_CHART_REVIEWER_SIGN_OFF.md`
(which records the overall PR-level approval decision and the
PC-COND-1..4 conditional-approval tracking table). This checklist
provides the itemized confirmations each named review area must check
before recording its own decision in `PATIENT_CHART_REVIEWER_SIGN_OFF.md`.
It does not reopen that document, or any other Patient Chart authority
document.

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

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

Reviewer:

Role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

## Clinical Authority

- [ ] Clinical findings remain linked to authoritative source records.
- [ ] Supporting evidence does not replace physician judgment.
- [ ] Assessment findings do not silently activate Plan-of-Care
      changes.
- [ ] Review, approval, authentication, and signature remain separate
      events.
- [ ] Finalization remains the sole active RNICA Final Clinical
      Narrative authority.

Reviewer:

Credentials or role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

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

Reviewer:

Role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

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

Reviewer:

Role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

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

Reviewer:

Role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

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

Reviewer:

Role:

Decision: [ ] APPROVED [ ] APPROVED_WITH_CONDITIONS [ ] CHANGES_REQUIRED [ ] BLOCKED

Date:

Conditions:

## Conditional Approval Register

| Condition ID | Review Area | Required Action | Owner | Blocking | Resolution Evidence | Status |
|---|---|---|---|---|---|---|
| | | | | YES / NO | | OPEN / RESOLVED |

This register is a per-area working table. The authoritative,
currently-populated conditional-approval record for PR #92 is the
Conditional-Approval Tracking table in
`PATIENT_CHART_REVIEWER_SIGN_OFF.md` (PC-COND-1 through PC-COND-4).

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

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE
