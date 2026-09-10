# SSOT Audit Report

Code-level audit (not a design review) of single-write-path / single-owner
status for the entities that Billing Readiness and the Admission (SOC) Gate
consume. Performed at the end of Priority 6, prior to production
deployment, per direct instruction to verify implementation rather than
produce more design documentation.

## Method

For each entity: locate every write path (grep for the writing
service/column across `app/`), confirm there is exactly one, confirm
Billing Readiness and the Admission Gate only ever read it, and confirm no
UI/API path outside that one writer can independently set the same value.

## Results

| Entity | Single Writer | Single Storage | Readiness = Read-Only | Admission Gate = Read-Only | Status |
|---|---|---|---|---|---|
| Benefit Period | `record_benefit_period_determination()` (`eligibility_workflow_service.py`) → `benefit_periods` table | Yes (post-fix) | Yes | Yes (consumer) | **FIXED** -- see below |
| Starting Cert | Same determination flow as Benefit Period, `BenefitPeriodDetermination` | Yes | Yes | Yes | PASS |
| Admit Type | `eligibility_workflow_service.py` admission-type fields | Yes | Yes | Yes | PASS |
| Transfer Evidence | `record_eligibility_source_document()` / transfer-specific fields, `eligibility_workflow_service.py` | Yes | Yes | Yes | PASS |
| Verified Payer | `PatientFaceSheet` (payer fields) via facesheet save path only; Payer Review Workflow is storage/audit only, no independent write path | Yes | Yes | N/A | PASS |
| Contracted Status | `PatientFaceSheet.contracted_status`, staff-set via facesheet save only | Yes | Yes (`evaluate_contracted_status_readiness`, read-only) | N/A | PASS |
| Authorization Required Status | `PatientFaceSheet.authorization_required_status`, staff-set via facesheet save only | Yes | Yes (`evaluate_authorization_readiness`, read-only) | N/A | PASS |
| Consent Documents | `DocumentRecord` (general document registry), no separate "consent status" field | Yes | Yes (`evaluate_election_consent_readiness`, read-only) | N/A | PASS |

**7 of 8 entities were already clean (single writer, single storage,
readiness/gate consume read-only). One real duplicate-ownership violation
was found and fixed immediately, per instruction, rather than deferred to
another review cycle.**

## Violation Found and Fixed: Benefit Period

**Finding:** `PatientFaceSheet.benefit_period_number` / `benefit_period_start`
/ `benefit_period_end` were a second, independently staff-editable answer to
"what benefit period is this patient in," parallel to the actual SSOT (the
`benefit_periods` table, owned by `record_benefit_period_determination()`
in the Eligibility / Admission Review workflow). The facesheet UI
(`PatientFacesheet.jsx`) exposed three editable "(manual)" fields that wrote
directly to these columns via a generic `setattr` loop in
`save_facesheet()` (`app/api/patients.py`), independent of the Eligibility
workflow's determination.

**Fix (implemented same session, no review cycle):**
- `save_facesheet()` now strips `benefit_period_number` / `benefit_period_start`
  / `benefit_period_end` from incoming request data before the write loop --
  silently ignored, not rejected (the frontend always resubmits the full
  form, so a hard rejection would break unrelated saves).
- The facesheet GET response's `benefit_period` block is now sourced from a
  new read-only helper, `_fetch_ssot_benefit_period()`, which queries the
  `benefit_periods` table -- the same table
  `billing_readiness_service._fetch_billable_benefit_period()` already
  reads from. This mirrors the existing SSOT-read pattern rather than
  introducing a new one.
- `PatientFacesheet.jsx` no longer sends these three fields in its save
  payload and no longer renders them as editable fields; the benefit-period
  display is now labeled **"ELIGIBILITY / ADMISSION REVIEW (SSOT)"**
  unconditionally (previously it distinguished "system-calculated" vs.
  "manual").
- The `PatientFaceSheet.benefit_period_number/start/end` DB columns are
  left in place (no migration) -- they are now vestigial/unused. Dropping
  them is a follow-up cleanup, out of scope for this fix (no new
  workstreams).

**Distinct, not a violation:** `_compute_benefit_period_schedule()` (in
`app/api/patients.py`) derives a schedule projection from `election_date`
alone, exposed as a separate `auto_calculated` field, used only for
recert/F2F due-date reminders. It has no write path, is not consumed by
Billing Readiness or the Admission Gate, and is clearly labeled as advisory
-- not a second answer to "what benefit period is this," so it was left
unchanged.

## Readiness Write Behavior

Confirmed by direct code inspection of `billing_readiness_service.py`:
`check_patient_billing_readiness()` and `build_tenant_billing_readiness_report()`
only ever write to `BillingReadinessVerdict` (the audit/history table for
past verdicts). No write path exists from readiness evaluation to `Patient`,
`PatientFaceSheet`, `BenefitPeriod`, or `DocumentRecord`. **Readiness reads
data; it never owns or writes patient/clinical data.**

## Admission Gate Behavior

Confirmed via existing, passing tests (not new test infrastructure):

| Scenario | Expected | Test(s) |
|---|---|---|
| No Benefit Period Determination | SOC BLOCKED | `test_soc_gate_blocks_when_no_determination_exists`, `test_set_soc_datetime_blocked_when_no_benefit_period_determination` |
| Starting Cert missing | SOC BLOCKED | `test_soc_gate_blocks_when_starting_cert_missing` |
| Transfer admission, Transfer Evidence missing | SOC BLOCKED | `test_soc_gate_blocks_transfer_without_transfer_source_and_evidence`, `test_set_soc_datetime_blocked_for_transfer_without_transfer_evidence` |
| New Admission, Benefit Period + Starting Cert present | SOC clear | `test_soc_gate_clear_for_new_admission_with_benefit_period_and_starting_cert` |
| Readmission, no transfer fields required | SOC clear | `test_soc_gate_clear_for_readmission_without_transfer_fields` |
| Transfer, all transfer fields documented | SOC clear | `test_soc_gate_clear_for_transfer_with_all_transfer_fields_documented`, `test_set_soc_datetime_proceeds_for_transfer_with_full_documentation` |

All pass (see Regression Summary).

## Severity Behavior Confirmed (Contracted / Authorization / Consent)

| Condition | Behavior | Verified by |
|---|---|---|
| Contracted = YES | No finding | `test_contracted_yes_is_no_finding`, matrix `test_contracted_status_axis[YES-...]` |
| Contracted = NO | AT_RISK, never a blocker | `test_contracted_no_is_warning_not_blocker`, matrix `[NO-True]` |
| Contracted = UNKNOWN / absent | AT_RISK | `test_contracted_unknown_or_absent_is_warning`, matrix `[UNKNOWN-True]` |
| Authorization required, no evidence | BLOCKED | `test_required_yes_no_evidence_is_blocker`, matrix `test_authorization_axis[YES-False-True-False]` |
| Authorization required, evidence on file | No finding | `test_required_yes_with_evidence_is_no_finding`, matrix `[YES-True-False-False]` |
| Authorization not required, unverified | AT_RISK | matrix `[NO-False-False-True]` |
| Authorization unknown | AT_RISK | matrix `[UNKNOWN-False-False-True]` |
| Consent present | No finding | matrix `test_consent_axis[True-False]` |
| Consent missing | AT_RISK, never a blocker | matrix `[False-True]` |

## Conclusion

No open SSOT violations remain. The one found (Benefit Period) has been
fixed in code (commit `1ebce65`) and re-verified by full regression. No
further code audit action is required before deployment.
