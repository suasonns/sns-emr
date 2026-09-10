# Authorization Workflow

**Status:** Business-rule specification, part of the permanent
`docs/workflows/` documentation set. Companion to `PayerDeterminationWorkflow.md`,
`BenefitPeriodWorkflow.md`, and `ReadinessConsumptionMap.md`.

## Scope

This document covers the HMO / PPO / Commercial / managed-care branch of the
Payer Determination Workflow — i.e. any payer that is not billed under the
Medicare hospice benefit-period rules described in `BenefitPeriodWorkflow.md`.

## The workflow map

```
Payer Confirmed (staff-reviewed, see PayerDeterminationWorkflow.md)
   |
   v
Contracted?               -- YES / NO / UNKNOWN (staff answer, saved)
   |
   v
Authorization Required?    -- YES / NO / UNKNOWN (staff answer, saved)
   |
   +-- YES --> Authorization Uploaded?
   |              |
   |              +-- YES --> Eligibility Review --> Readiness consumes reviewed result
   |              |
   |              +-- NO  --> Readiness BLOCKED (missing required authorization)
   |
   +-- NO  --> Non-Authorization Verification Uploaded?
                  |
                  +-- YES --> stored as NON_AUTH_VERIFICATION --> Eligibility Review --> Readiness consumes reviewed result
                  |
                  +-- NO  --> Readiness BLOCKED (missing required verification-of-no-auth evidence)
```

## Step-by-step rules

### 1. Contracted?

Staff answers **YES / NO / UNKNOWN** after confirming the payer. This answer is
saved and becomes part of the reviewed payer record that readiness later
consumes. It is never inferred from a payer name string alone (e.g. "Blue
Shield" does not by itself imply contracted status — different plans/products
under the same payer brand may have different contract status).

### 2. Authorization Required?

Staff answers **YES / NO / UNKNOWN**. Like Contracted?, this is a staff
determination, not an automatic inference from the payer name or from OCR.

### 3a. If Authorization Required = YES

Require an uploaded authorization document. Acceptable evidence types:
- Authorization approval
- Prior authorization
- Managed care approval
- Other payer authorization

**Readiness impact:** without this evidence uploaded and reviewed, readiness
becomes/remains **blocked**. This is analogous to the SOC hard gate in
`BenefitPeriodWorkflow.md`, but scoped to the authorization requirement rather
than the benefit period — it is a completeness check, not a decision the
system makes on its own.

### 3b. If Authorization Required = NO

Require an uploaded verification of the no-authorization determination.
Acceptable evidence types:
- Coverage verification
- Representative note (e.g. a payer rep confirmed no auth needed for this
  service/level of care)
- Eligibility confirmation

This evidence is stored as a distinct evidence type: **`NON_AUTH_VERIFICATION`**
(implemented — see "Current implementation state" below). This evidence type
exists specifically so "no authorization was required" is always a
documented, auditable claim rather than an assumed default — a patient must
never be treated as "no auth needed, therefore ready" without evidence on file.

## Documentation requirements summary

| Question | Answer | Required upload | Evidence type |
|---|---|---|---|
| Contracted? | YES/NO/UNKNOWN | — | (recorded, no upload required) |
| Authorization Required? | YES | Authorization approval / prior auth / managed care approval / other payer authorization | `AUTHORIZATION` |
| Authorization Required? | NO | Coverage verification / representative note / eligibility confirmation | `NON_AUTH_VERIFICATION` |
| Authorization Required? | UNKNOWN | — (readiness should treat this as incomplete, not as "no auth needed") | — |

## Readiness impact rule

Readiness must consume the **reviewed** Contracted/Authorization-Required
answer plus the corresponding uploaded evidence — never re-derive these from
the payer name or from OCR. See `ReadinessConsumptionMap.md`.

## Insurance verification boundary

SNS EMR does not perform eligibility/authorization verification itself — it
has no NGS Connex, CMS, Medicare, or payer-database lookup integration, and no
name+DOB+SSN insurance-discovery capability. Insurance verification is
performed outside SNS EMR. SNS stores and audits reviewed results and
supporting evidence.

## Current implementation state (as of this document's update)

Confirmed via repository trace:

- `PatientFaceSheet.contracted_status` and
  `PatientFaceSheet.authorization_required_status` (tri-state:
  `YES`/`NO`/`UNKNOWN`) are implemented, staff-writable via
  `POST /patients/{patient_id}/facesheet`, and server-validated to reject any
  other value.
- `PatientFaceSheet.non_auth_verification_document_id` (FK to
  `eligibility_source_documents`) and the `NON_AUTH_VERIFICATION` /
  `TRANSFER_EVIDENCE` evidence-type classifications exist on
  `ELIGIBILITY_DOCUMENT_TYPES`.
- Payer verification audit fields
  (`payer_verified_date`/`payer_verified_by`/`payer_verification_notes`/
  `verification_document_reference`) are implemented and staff-writable via
  the same endpoint; `payer_verified_by` is always server-stamped from the
  acting user, never client-supplied.
- **Not yet implemented:** `billing_readiness_service.check_patient_billing_readiness`
  does not yet consume Contracted?/Authorization Required? or the associated
  evidence when computing readiness/blocked status. The staff answers and
  evidence can be recorded today, but the readiness-blocking rule described
  above (block when Authorization Required = YES with no authorization
  uploaded, or = NO with no `NON_AUTH_VERIFICATION` uploaded) is not yet
  wired into the readiness engine. This is tracked as Priority 7/8 (Readiness
  Integration).
- The Facesheet's existing "Authorization Documents" and
  "Eligibility/Submission Documents" upload widgets (`PatientFacesheet.jsx`)
  are generic document uploads today — the frontend does not yet present a
  structured Contracted/Authorization-Required question UI backed by the new
  fields.
