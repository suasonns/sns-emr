# Election / Consent Document Workflow (Priority 6)

> Companion to `docs/workflows/SourceOfTruthMatrix.md`,
> `docs/workflows/ReadinessDecisionMatrix.md`, and
> `docs/workflows/AuthorizationWorkflow.md`. This document is the
> authoritative design record for the Election/Consent documentation
> workflow -- read it before touching
> `app/billing/services/election_consent_workflow_service.py`.

## The concept, renamed

This workflow was originally going to be framed as an "Admission
Authorization" step gating `POST /admissions/{patient_id}/authorize`.
That framing was rejected. Real hospice operations do not gate
admission on signed paperwork -- agencies scan/fax/DocuSign consent
packages in on their own timeline, sometimes after SOC. The concept is
renamed to **Election / Consent Documentation**: it is a post-admission
compliance/document workflow, not an admission gate.

```
Referral
  |
Eligibility Review
  |
Benefit Period Review
  |
SOC
  |
Admission
  |
Election / Consent Documents Required   <-- this workflow
  |
Document Upload
  |
Compliance Tracking (Billing Readiness AT_RISK warning only)
```

NOT: `Referral -> Election Signed -> Admission`.

## Hard rules

1. **SOC and admission are never blocked** on election/consent document
   presence. There is no code path where a missing consent document
   prevents `SOCValidationService` or the admission gate from
   succeeding.
2. **No new "status" field.** There is no `consent_status`,
   `election_status`, or `admission_authorized` column anywhere. The
   question "has consent been documented?" has exactly one answer
   location: whether an `ACTIVE` `DocumentRecord` of a recognized
   election/consent type exists for the patient. A parallel status
   column would be a second answer to the same question -- exactly the
   SSOT violation this project has been removing everywhere else.
3. **Missing documentation is AT_RISK only.** Billing Readiness surfaces
   a warning, never a blocker. See `ReadinessDecisionMatrix.md`.
4. **Any one of the eight document types satisfies the requirement.**
   Agencies collect different subsets of the packet; the system does
   not require every type to be present, only at least one.

## Document types

All are ordinary `DocumentRecord.document_type` string values (that
column has no DB-level enum/allow-list, so no migration was required --
consistent with how other ad hoc document types, e.g. `AUTHORIZATION`,
are already used from the facesheet's document upload widget):

- `ELECTION_STATEMENT`
- `CONSENT_FORM`
- `PATIENT_RIGHTS`
- `HIPAA_ACKNOWLEDGEMENT`
- `NOTICE_OF_PRIVACY_PRACTICES`
- `ADVANCE_DIRECTIVE`
- `FINANCIAL_RESPONSIBILITY`
- `OTHER_ADMISSION_DOCUMENT`

The allow-list of these eight names lives in one place:
`ELECTION_CONSENT_DOCUMENT_TYPES` in
`app/billing/services/election_consent_workflow_service.py`.

## Ownership (SSOT)

| Concept | Owner | Consumer |
|---|---|---|
| Election / Consent Documents | Document Registry (`DocumentRecord`, `lifecycle_status = ACTIVE`) | Billing Readiness (read-only) |

`election_consent_workflow_service.py` is a **read-only consumer**. It
never writes to `DocumentRecord` and never introduces a cached/derived
status column. `has_election_consent_evidence()` is the single query
that answers "is documentation present?" -- exactly one implementation,
reused by both the pure evaluator and (if a UI badge is ever added) any
future display logic.

## Compliance follow-up (explicitly NOT built as new infrastructure)

The user's design brief described an automatic "Admission Completed ->
Consent Package Uploaded? -> NO -> Compliance Warning -> Open Task ->
Visible to Admissions" flow. This is satisfied entirely by **existing**
generic mechanisms, with no new task/status table:

- The AT_RISK warning from `evaluate_election_consent_readiness()` is
  already visible to Admissions/Billing wherever Billing Readiness
  results are surfaced (readiness dashboard, patient-level readiness
  check) -- this *is* the "visible to Admissions" requirement.
- If staff want an explicit, assignable, due-dated task tracked outside
  the passive readiness warning, the **existing** generic
  `ReadinessFollowUp` / `ReadinessAssignment` tables (Sprint 2, see
  `app/billing/services/readiness_workflow_service.py`) are the correct
  mechanism -- they already support `notes`, `due_date`, `status`
  (OPEN/IN_PROGRESS/BLOCKED/RESOLVED/CANCELLED), and are not
  insurance/consent-specific. No new "Consent Task" table was created;
  doing so would duplicate this existing generic system.
- Readiness evaluation itself remains a pure, read-only function -- it
  does not auto-create a `ReadinessFollowUp` row as a side effect.
  Follow-up creation is always an explicit staff action via the
  existing follow-up API, exactly as it already works for every other
  AT_RISK/NOT_READY finding today.

## Readiness consumption

`check_patient_billing_readiness()` calls
`evaluate_election_consent_readiness()` once, after the benefit period
has already resolved (i.e. only in the normal post-admission readiness
path, never as an admission gate). A missing document produces exactly
one warning string and zero blockers; a present document produces no
finding at all.

## Non-goals (explicitly out of scope)

- No `POST /admissions/{patient_id}/authorize` semantics change beyond
  what was already true: that endpoint does not write SOC and was
  already out of the SOC discussion (see `AdmissionTypesWorkflow.md`).
  It may be repurposed into document-compliance tracking or retired in
  a future, separately-scoped change; this workflow does not require
  that decision to be made now.
- No new UI screen/module. If a minimal UX affordance is added, it
  reuses the existing document upload widget already present on the
  facesheet, following the same "no new screen" pattern as Priority 5.
