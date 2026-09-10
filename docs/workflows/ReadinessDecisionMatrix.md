# Readiness Decision Matrix

**Status:** Business-rule specification, part of the permanent
`docs/workflows/` documentation set. This is the authoritative,
finalized severity table for every readiness/admission condition in the
Payer / Contracted / Authorization / Transfer / Consent workflows. Written
and approved **before** any Priority 5 UI or readiness-consumption code,
per directive: "I want all readiness severity decisions finalized. If we
build UI first, we will end up rewriting readiness later."

Supersedes/finalizes the severity table drafted in
`ReadinessReconciliation.md` Section 3 — this document is the one to read
for "what happens when." `ReadinessReconciliation.md` remains the current
vs. desired *implementation* trace (what's wired today vs. not).

## Governing distinction: Admission Gate vs. Billing Readiness

These are two different concerns and must never be merged:

| | Admission Gate | Billing Readiness |
|---|---|---|
| Question it answers | Can this patient be admitted? Can SOC be established? Can the episode begin? | Can this episode be safely billed? Can a claim be submitted? Is reimbursement expected? |
| Enforcement point | Pre-SOC / pre-episode-start (`evaluate_soc_gate`, `AdmissionGuardrailService`, `SOCValidationService`) | Post-admission, at claim-preparation time (`check_patient_billing_readiness`) |
| What it owns/enforces hard | Benefit Period existence, Starting Cert, Transfer Evidence (Transfer admit type only) | Nothing — it is read-only; it only produces a derived verdict |
| Failure mode | Blocks the action outright (SOC cannot be entered, admission cannot proceed) | Produces a `blockers`/`warnings` verdict; does not by itself prevent any admission/clinical action |

**Rule:** Benefit Period, Starting Cert, and Transfer Evidence stay owned
and hard-enforced by the Admission Gate. They are never moved into, or
re-enforced a second time by, Billing Readiness. (Billing Readiness can
still *read* Benefit Period existence as an input — see row below — but
it does not duplicate the Admission Gate's enforcement; a patient who
reached ADMITTED status already satisfied it.)

## Full Condition Matrix

| Condition | READY | AT_RISK | NOT_READY | BLOCKED | Owner | Reason |
|---|:-:|:-:|:-:|:-:|---|---|
| Benefit Period missing before SOC | | | | ✅ | Admission Gate | Cannot establish a compliant episode; SOC entry is refused outright (`evaluate_soc_gate`, pre-existing, unchanged) |
| Benefit Period present, covers service date | ✅ | | | | Admission Gate → read by Billing Readiness | Already-satisfied precondition; readiness reads existence, does not re-enforce |
| Starting Cert missing | | | | ✅ | Admission Gate | Same hard pre-SOC enforcement as Benefit Period; unchanged |
| Transfer Admission, Transfer Evidence missing | | | | ✅ | Admission Gate | Admission should not proceed; enforced at pre-SOC gate, not duplicated in Billing Readiness |
| Readmission, Transfer Evidence missing | ✅ | | | | N/A (no effect) | Transfer rules do not apply to Readmission — explicitly no requirement, no check, no severity |
| Payer Unknown / not yet confirmed | | ✅ | | | Billing Readiness (reads Payer Determination Workflow) | Admission allowed to proceed; billing needs follow-up, not a hard block |
| Verified Payer confirmed | ✅ | | | | Billing Readiness | Precondition satisfied |
| Contracted Status = UNKNOWN | | ✅ | | | Billing Readiness (reads Contracted Status Workflow) | Incomplete staff review, not a proven problem |
| Contracted Status = YES (contracted) | ✅ | | | | Billing Readiness | Precondition satisfied |
| Contracted Status = NO (not contracted) | | ✅ | | | Billing Readiness | **For now**: treated as AT_RISK, not BLOCKED — see rationale below. Revisit once agency operational policy on non-contracted billing is confirmed. |
| Authorization Required = UNKNOWN | | ✅ | | | Billing Readiness (reads Authorization Workflow) | Incomplete staff review, not a proven problem |
| Authorization Required = YES, evidence uploaded | ✅ | | | | Billing Readiness | Precondition satisfied |
| Authorization Required = YES, no evidence uploaded | | | | ✅ | Billing Readiness | A CMS/payer-required document is provably missing — same treatment as CTI/F2F/POC, always a hard blocker |
| Authorization Required = NO, `NON_AUTH_VERIFICATION`-class evidence uploaded | ✅ | | | | Billing Readiness | Precondition satisfied |
| Authorization Required = NO, no non-auth verification evidence uploaded | | ✅ | | | Billing Readiness | Missing corroboration of an already-recorded staff decision, not a missing externally-required document. AT_RISK, not BLOCKED, unless agency policy later changes. |
| Election/Consent documents missing (post-admission) | | ✅ | | | Documentation Workflow (Priority 6, not yet built) | Never an admission or SOC blocker; produces a follow-up/compliance task |
| Election/Consent documents present | ✅ | | | | Documentation Workflow | Precondition satisfied |

`NOT_READY` (as distinct from `BLOCKED`) is the existing generic bucket
for any blocker without an open `ReadinessFollowUp.status == 'BLOCKED'`
record — see `readiness_workflow_service.compute_operational_bucket`. The
per-condition rows above use "BLOCKED" to mean "this condition, by
itself, is severe enough that it should always contribute a hard
`blockers[]` entry" (which the existing bucket logic then classifies as
NOT_READY, escalating to the dashboard's BLOCKED bucket only if an
associated follow-up is explicitly marked BLOCKED). This document does
not change that existing two-layer model — see
`ReadinessReconciliation.md` Section 1 for the mechanics.

## Rationale: Contracted = NO is AT_RISK, not BLOCKED (for now)

Billing a non-contracted payer is a real agency policy question (some
agencies still bill out-of-network with different reimbursement
expectations; some do not). Blocking it outright is a policy decision
this project has not been given authority to make. Recommendation:
AT_RISK now, with an explicit note that this may become BLOCKED later
once agency operational policy is confirmed. Do not hard-code BLOCKED
without that confirmation.

## Rationale: Authorization Required = NO, no evidence is AT_RISK, not BLOCKED

Same reasoning as documented in `ReadinessReconciliation.md` Section 6:
the "no auth needed" determination is itself a staff decision already on
file and audited (`authorization_required_status`); missing
*corroborating* evidence of that decision is a follow-up item, not proof
the claim is unbillable. Treating it as BLOCKED would make readiness
stricter than the staff's own recorded review.

## Ownership rule (restated, non-negotiable)

- **Authorization Workflow** owns `authorization_required_status` and
  authorization evidence. It is the only place that decision is entered,
  changed, or corrected.
- **Contracted Status Workflow** owns `contracted_status` and contracted
  review evidence. Same rule.
- **Billing Readiness** consumes both (read-only) to compute
  `blockers`/`warnings`. It never writes to, infers, or overrides either
  field, and the business rule for what each value *means* for severity
  lives in each workflow's own evaluation function (see
  `AuthorizationWorkflow.md`), not duplicated inline inside
  `billing_readiness_service.py`. `check_patient_billing_readiness` only
  calls each workflow's evaluation function and folds the returned
  blockers/warnings into its own list — exactly like it already does
  today for `evaluate_admission_gate` and `resolve_payer_sequence`.

## Display-label translation layer (no enum rename)

Per directive, the stored values (`YES`/`NO`/`UNKNOWN` for both
`contracted_status` and `authorization_required_status`) are NOT renamed.
A presentation-only label mapping is used instead, so the business
concept (Contracted / Not Contracted / Unknown, Authorization Required /
Authorization Not Required / Unknown) is what staff see, while the API
and database keep the existing values, avoiding a database / API /
frontend / readiness / audit migration:

| Field | Stored value | Displayed label |
|---|---|---|
| Contracted Status | `YES` | Contracted |
| Contracted Status | `NO` | Not Contracted |
| Contracted Status | `UNKNOWN` | Unknown |
| Authorization Required Status | `YES` | Authorization Required |
| Authorization Required Status | `NO` | Authorization Not Required |
| Authorization Required Status | `UNKNOWN` | Unknown |

If/when the agency-policy questions above (Contracted=NO severity, and
whether to rename the stored enum values) are resolved, update this
table and `ReadinessReconciliation.md` together — do not let them drift
independently.
