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
(not yet implemented in code — see "Current implementation state" below). This
evidence type exists specifically so "no authorization was required" is always
a documented, auditable claim rather than an assumed default — a patient must
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

## Current implementation state (as of this document's creation)

Confirmed via repository trace: the `NON_AUTH_VERIFICATION` evidence type, the
Contracted?/Authorization Required? staff-answer fields, and the corresponding
readiness-blocking logic described above are **not yet implemented** anywhere
in the codebase. The Facesheet's existing "Authorization Documents" and
"Eligibility/Submission Documents" upload widgets (`PatientFacesheet.jsx`) are
generic document uploads today — they do not yet carry a structured
Contracted/Authorization-Required answer, and are not yet wired into the
readiness engine. This document describes the target state to build toward.
