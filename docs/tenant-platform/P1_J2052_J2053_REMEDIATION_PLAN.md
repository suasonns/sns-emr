# P1 — J2052 / J2053 Remediation Plan

**Document Status:** PRIORITY 1 REMEDIATION PLAN — produced per the
"RNICA \u2192 HOPE REDESIGN EXECUTION DIRECTIVE" (2026-09-23). Builds on
`J2052_J2053_LINEAGE_AUDIT.md` (trace complete). Per directive: "Do not
start redesign implementation until this plan is completed." This
document is a **plan**, not implementation — no code has been changed.

## J2052 — Completion status / date

| Attribute | Value |
|---|---|
| **CURRENT SOURCE** | `form_data.sfv.inPersonSfvCompleted` / `form_data.sfv.sfvDate` on the **triggering** RNICA record, kept in sync by a client-side effect (`SfvStatusCard`, `RNICA.jsx:7959-7979,8401-8404`) that re-fetches `GET /visits/sfv-requirements` on every RNICA `sfv`-section mount |
| **TARGET SOURCE** | `SFVRequirement.status` / `SFVRequirement.completed_at`, read directly at HOPE-generation time — no denormalized copy |
| **DATABASE FIELD** | Current: `rnica_assessments.form_data` (JSONB, path `sfv.inPersonSfvCompleted`/`sfv.sfvDate`). Target: `sfv_requirements.status`, `sfv_requirements.completed_at` (already exist; no schema change needed) |
| **API FIELD** | Current: none dedicated — read implicitly as part of the RNICA record's `form_data` blob returned by `GET /rnica-assessments/{id}`. Target: `HopeGenerationService` reads `SFVRequirement` via its existing repository/query layer (`GET /visits/sfv-requirements` equivalent, server-side, no HTTP round-trip needed once generation is server-side) |
| **EXPORT FIELD** | `hopeReportMapper.js:618` (`sfv.inPersonSfvCompleted`, `sfv.sfvDate`, `sfv.reasonNotCompleted`) — becomes a `HopeGenerationService` read of `SFVRequirement` once that service exists (see `HOPE_GENERATION_SERVICE_DESIGN.md`) |
| **VALIDATION FIELD** | None today. Target: `HopeValidationService` rule "J2052 status/date must match the current `SFVRequirement` record for the patient's active SFV cycle at generation time" (see `HOPE_VALIDATION_ENGINE.md`) |
| **TEST COVERAGE** | None found for the sync effect itself (`SfvStatusCard`) beyond incidental coverage in existing SFV completion tests. No test asserts that a HOPE export reflects a *just-completed* `SFVRequirement` without first reloading the RNICA screen. |
| **PROPOSED FIX** | (1) Near-term/no-schema-change: no fix required for the current UI-driven export path — the sync already produces a correct value as long as the RNICA screen has loaded at least once since completion. (2) Structural fix, required before server-side generation: `HopeGenerationService` must read `SFVRequirement` directly and must NOT depend on `form_data.sfv.*` for this field. The RNICA-side `form_data.sfv.inPersonSfvCompleted`/`sfvDate` copy may remain as a UI convenience/display field but should be explicitly documented as non-authoritative once the service exists. |
| **RISK LEVEL** | MEDIUM today (masked by the sync effect's UI-triggered timing); escalates to HIGH the moment any export path bypasses the RNICA UI (batch export, scheduled export, admin-triggered export) |
| **SCHEMA IMPACT** | **None.** `SFVRequirement.status`/`completed_at` already exist and are already authoritative. This is a read-path fix, not a data-model change. |

### J2052 — "reason not completed"

| Attribute | Value |
|---|---|
| **CURRENT SOURCE** | Free-text, user-typed, on the RNICA `sfv` section (`form_data.sfv.reasonNotCompleted`) |
| **TARGET SOURCE** | Undetermined — no `SFVRequirement` field currently represents "why the SFV was not completed" |
| **DATABASE FIELD** | Current: `rnica_assessments.form_data` path only. Target: candidate new column `sfv_requirements.non_completion_reason` (nullable text or enum) — **requires product decision, not assumed here** |
| **API FIELD** | Current: none dedicated. Target: TBD pending product decision |
| **EXPORT FIELD** | `hopeReportMapper.js:618` (`sfv.reasonNotCompleted`) |
| **VALIDATION FIELD** | None today; target TBD |
| **TEST COVERAGE** | None found |
| **PROPOSED FIX** | Do not silently pick a default. Two options for product sign-off: (A) add `non_completion_reason` to `SFVRequirement` so it becomes reconcilable/authoritative like status/date; (B) explicitly document this field as a RNICA-only annotation, exempt from the single-source-of-truth rule, since it only applies when no completion occurred (i.e., there is no competing "real" encounter record to consult). Recommend (A) for full CMS-defensibility, but this is a scope/cost decision, not a technical one. |
| **RISK LEVEL** | MEDIUM — low volume (only populated when SFV is not completed by the due window), but currently unverifiable against any system of record |
| **SCHEMA IMPACT** | Depends on decision: Option A requires a migration adding one column to `sfv_requirements`; Option B requires none (documentation only) |

## J2053 — Symptom impact at SFV

| Attribute | Value |
|---|---|
| **CURRENT SOURCE** | RNICA form's own `sfv` section, radio fields `symptomImpactAtSfv.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` (`RNICA.jsx:9518-9525`) — editable on the **triggering** RNICA record, not the completion visit |
| **TARGET SOURCE** | The completion visit's own clinical documentation — captured through `SymptomFollowUpVisitSection` (`VisitNotes.jsx`) at the moment of SFV completion |
| **DATABASE FIELD** | Current: `rnica_assessments.form_data` path `sfv.symptomImpactAtSfv.*`. Target: candidate new JSONB column `sfv_requirements.symptom_impact` (mirrors the 8-field shape), populated at completion time — **requires product/schema decision** |
| **API FIELD** | Current: none — the completion endpoint accepts only `{ completionVisitId }` (`sfv.ts::completeSfvRequirement`). Target: extend the completion request body to accept an optional `symptomImpact` payload matching the 8 sub-fields |
| **EXPORT FIELD** | `hopeReportMapper.js:619` (`symptomEntries(sfv.symptomImpactAtSfv || {})`) — becomes a `HopeGenerationService` read of `SFVRequirement.symptom_impact` once the schema/UI change lands |
| **VALIDATION FIELD** | None today. Target: `HopeValidationService` rule "J2053 must be present and attributed to the completion visit, not the triggering visit, when `SFVRequirement.status == COMPLETED`" (see `HOPE_VALIDATION_ENGINE.md`) |
| **TEST COVERAGE** | None found for J2053 capture on the completion visit, because the capability does not exist. Existing SFV tests (P3-009 remediation) cover authorization only, not symptom-impact data capture. |
| **PROPOSED FIX** | (1) Add a `symptom_impact` JSONB field to `SFVRequirement` (or a dedicated child row keyed to the completion visit — either is acceptable, schema choice deferred to implementation). (2) Extend `SymptomFollowUpVisitSection` (`VisitNotes.jsx`) with the same 8 radio fields, submitted alongside `completionVisitId` to the completion endpoint. (3) Extend the completion endpoint/service to accept and persist this payload. (4) Re-point `hopeReportMapper.js:619` (and the future `HopeGenerationService`) to read from the new field. (5) Decide whether to retire, hide, or mark historical-only the RNICA-form `sfv` section's `symptomImpactAtSfv.*` fields once the new path exists, to prevent clinicians from continuing to document on the wrong encounter. |
| **RISK LEVEL** | **CRITICAL** — no capture path exists today through the correct workflow; clinicians using `VisitNotes.jsx` as designed cannot document this HOPE-required field at all |
| **SCHEMA IMPACT** | Migration required: add `symptom_impact` (JSONB, nullable) to `sfv_requirements`, or an equivalent child table if per-attempt history is desired. This is the **only schema change required** across both J2052 and J2053 that is not already optional/deferred. |

## Priority 2 answer (see also chat response)

**Can a nurse document J2053 data inside the actual SFV completion
visit today? NO.** `SymptomFollowUpVisitSection` has no fields for it,
and the completion API contract does not accept it. This remains a
**CRITICAL release blocker**: the follow-up outcome cannot be harvested
from the encounter where it actually occurred.

## Summary status

| Item | Status |
|---|---|
| J2052 status/date | Sync mechanism exists and is functionally correct for today's UI-driven export; structural fix (service reads `SFVRequirement` directly) required before server-side generation — **no schema change required** |
| J2052 reason-not-completed | Fix requires a product decision (Option A/B above) — **not yet decided** |
| J2053 (all 8 sub-fields) | Fix requires new schema field + UI + API change — **CRITICAL, not yet implemented, plan only** |

No implementation has been performed. This plan requires approval
before any of the above schema/API/UI changes begin.
