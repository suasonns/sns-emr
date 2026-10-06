# Commit 03902dc Scope Audit

**Purpose:** Per owner directive, this manifest classifies every file in commit
`03902dc` ("chore: commit accumulated RNICA work, Hospice Language Standard
v1.1, and supporting artifacts") so that scope, test status, and
carry-forward eligibility are explicit before any new worktree is created
from it. The commit itself has NOT been undone, reset, rewritten, or
force-pushed, per instruction.

**Commit:** `03902dc` — 102 files changed, 15,535 insertions(+), 412 deletions(-)
**Branch:** `suasonns-hope-complete-cms-alignment`
**Note:** `docs/SNS_HOSPICE_LANGUAGE_STANDARD.md` was subsequently replaced
with the owner-approved v1.2 in a **separate** commit `625e66b` (not part of
03902dc). Going forward, rule/standard documents, Infection work, and other
workstreams will be committed separately as directed.

Legend: Y = yes, N = no, N/A = not applicable, Partial = mixed/ambiguous.

## 1. Backend — Interdisciplinary Continuity / Discipline Service (new feature, untested in this session)

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| backend/alembic/versions/8a200af8635d_add_interdisciplinary_continuity_tables.py | migration | Discipline Service / IDG continuity | N | N | N | N (not run in this session) | Y | Y — needed by discipline_service feature |
| backend/alembic/versions/f3a7c1d9e2b4_add_admission_id_to_idg_reviews.py | migration | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/api/discipline_services.py | backend API | Discipline Service / IDG continuity | N | N | N | Partial — covered by test_discipline_service_continuity.py (not re-run this session) | Y | Y |
| backend/app/api/registry.py | backend API (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/api/visits.py | backend API (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/models/__init__.py | backend model (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/models/discipline_service.py | backend model | Discipline Service / IDG continuity | N | N | N | Partial | Y | Y |
| backend/app/models/enums.py | backend model (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/models/idg_recommendation.py | backend model | Discipline Service / IDG continuity | N | N | N | Partial | Y | Y |
| backend/app/models/idg_review.py | backend model (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/models/patient_issue.py | backend model (modified) | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| backend/app/services/discipline_service_engine.py | backend service | Discipline Service / IDG continuity | N | N | N | Partial — unit tests exist in repo, not re-run this session | Y | Y |
| backend/tests/test_discipline_service_continuity.py | backend test | Discipline Service / IDG continuity | N | N | N | N (not re-run this session) | Y — needs a fresh run before relying on it | Y |
| sns-emr-frontend/src/api/disciplineServices.ts | frontend API client | Discipline Service / IDG continuity | N | N | N | N | Y | Y |
| sns-emr-frontend/src/charts/InterdisciplinaryContinuityBoard.tsx | frontend chart/UI | Discipline Service / IDG continuity | N | N | N | N | Y | Y |

**Note:** This entire workstream is unrelated to Infection/RNICA and was not
exercised or verified in this session. It should have been committed
separately from Infection/RNICA/doc work. Recommend running its backend
test suite (`pytest backend/tests/test_discipline_service_continuity.py`)
before treating it as stable.

## 2. RNICA Core — Infection body system (this session's primary work)

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| sns-emr-frontend/src/components/RNICA.jsx | core component (modified, 1949 lines changed) | Infection Unable-to-Assess removal + Cardio/Respiratory prior fixes | Y (Infection portions) | Y | N | Y — 80/80 Playwright checks + 13 vitest unit tests passing | **Y — NOT ACCEPTED per owner directive** (duplicate allergies, REQUIRES FOLLOW-UP rule, language-standard options still pending) | Y, pending this directive's corrections |
| sns-emr-frontend/src/components/RNICA.infectionUnableToAssessRemoval.test.js | unit test | Infection Unable-to-Assess removal | Y | Y | N | Y — 13/13 passing | N (test itself is stable; underlying feature is unresolved) | Y |
| sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.css | stylesheet (modified, 477 lines changed) | RNICA layout/design system | Partial | Y | N | N | Y | Y |

## 3. RNICA — New sub-modules (Diagnosis & LCD, Pain/Symptom Burden) — unrelated to Infection, not part of this directive

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| sns-emr-frontend/src/components/rn-ica/diagnosis-lcd/DiagnosisLcdOverview.jsx | component | Diagnosis & LCD screen | N | Y | N | N (no e2e run this session) | Y | Y |
| sns-emr-frontend/src/components/rn-ica/diagnosis-lcd/DiagnosisPrimaryEditSheet.jsx | component | Diagnosis & LCD screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/diagnosis-lcd/DiagnosisSecondaryEditSheet.jsx | component | Diagnosis & LCD screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/diagnosis-lcd/diagnosisLogic.js | logic module | Diagnosis & LCD screen | N | Y | N | Y — diagnosisLogic.test.js | N | Y |
| sns-emr-frontend/src/components/rn-ica/diagnosis-lcd/diagnosisLogic.test.js | unit test | Diagnosis & LCD screen | N | Y | N | Y (passing per repo state) | N | Y |
| sns-emr-frontend/src/components/rn-ica/pain-symptom-burden/PainAssessmentEditSheet.jsx | component | Pain/Symptom Burden screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/pain-symptom-burden/PainManagementEditSheet.jsx | component | Pain/Symptom Burden screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/pain-symptom-burden/PainSymptomBurdenOverview.jsx | component | Pain/Symptom Burden screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/pain-symptom-burden/painLogic.js | logic module | Pain/Symptom Burden screen | N | Y | N | N | Y | Y |
| sns-emr-frontend/src/components/rn-ica/performanceScaleInterpretations.js | logic module | Performance scale interpretation | N | Y | N | Y — has a .test.js | N | Y |
| sns-emr-frontend/src/components/rn-ica/performanceScaleInterpretations.test.js | unit test | Performance scale interpretation | N | Y | N | Y | N | Y |

**Note:** None of these were requested or reviewed under the Infection
directive and are outside this directive's scope (items 1–22). They should
not be treated as "Infection accepted" work.

## 4. Cardiovascular / Respiratory — prior-session fixes and verification artifacts

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| sns-emr-frontend/scripts/cardio-layout-audit.mjs | verification script | Cardiovascular layout audit | N | Y | N | Y (self-contained script) | N | Y |
| sns-emr-frontend/scripts/check-current-state.mjs | debug script | Cardiovascular/edema debug | N | Y | N | N/A (debug tool) | N | Partial — candidate for cleanup, non-blocking |
| sns-emr-frontend/scripts/check-edema-bug.mjs | debug script | Cardiovascular edema bug | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/check-edema-type.mjs | debug script | Cardiovascular edema bug | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/debug-chart.mjs | debug script | Cardiovascular debug | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/debug-chart2.mjs | debug script | Cardiovascular debug | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/final-verify.mjs | verification script | Cardiovascular/edema final verification | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/probe-grid.mjs | debug script | Cardiovascular layout probe | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/reproduce-edema-bug.mjs | repro script | Cardiovascular edema bug | N | Y | N | N/A | N | Partial — candidate for cleanup |
| sns-emr-frontend/scripts/restore-baseline-final.mjs | data-restore script | Cardiovascular baseline restore | N | Y | N | Y | N | Y — needed to restore baseline if rerun |
| sns-emr-frontend/scripts/restore-baseline-now.mjs | data-restore script | Cardiovascular baseline restore | N | Y | N | N/A | N | Partial — superseded by restore-baseline-final.mjs |
| sns-emr-frontend/scripts/restore-baseline.mjs | data-restore script | Cardiovascular baseline restore | N | Y | N | N/A | N | Partial — superseded |
| sns-emr-frontend/scripts/restore-baseline2.mjs | data-restore script | Cardiovascular baseline restore | N | Y | N | N/A | N | Partial — superseded |
| sns-emr-frontend/scripts/verify-baseline-restored.mjs | verification script | Cardiovascular baseline restore | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/verify-edema-fix.mjs | verification script | Cardiovascular edema fix | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/verify-edema-review.mjs | verification script | Cardiovascular edema review | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/capture-respiratory-baseline.mjs | capture script | Respiratory baseline screenshots | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/verify-respiratory-date-autofill.mjs | verification script | Respiratory date autofill | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/verify-respiratory-rebuild.mjs | verification script | Respiratory rebuild | N | Y | N | Y | N | Y |
| sns-emr-frontend/scripts/cardio-audit-output/** (16 PNGs + edema/*.png + results.json + report.json + final/*.png) | screenshot/report artifacts | Cardiovascular audit evidence | N | Y | Y (evidence, not code) | N/A | N | Partial — historical evidence; may be pruned from future worktrees to reduce repo size, but should remain retrievable from this commit |
| sns-emr-frontend/scripts/respiratory-rebuild-output/** (8 PNGs) | screenshot artifacts | Respiratory rebuild evidence | N | Y | Y | N/A | N | Partial — same as above |

## 5. Infection — screenshots and capture script (this session's directive evidence)

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| sns-emr-frontend/scripts/capture-infection-screenshots.mjs | capture script | Infection screenshot evidence | Y | Y | N | Y (ran successfully) | N | Y |
| sns-emr-frontend/scripts/__screenshots__/infection-1-no-current-concern.png | screenshot | Infection evidence | Y | Y | Y | N/A | **Y — superseded; contains duplicate-allergy defect per owner review** | N — must be regenerated after items 3–11 fixes, do not present as final evidence |
| sns-emr-frontend/scripts/__screenshots__/infection-2-existing-findings-review.png | screenshot | Infection evidence | Y | Y | Y | N/A | **Y — same defect** | N — regenerate |
| sns-emr-frontend/scripts/__screenshots__/infection-3-new-or-worsening.png | screenshot | Infection evidence | Y | Y | Y | N/A | **Y — same defect** | N — regenerate |
| sns-emr-frontend/scripts/__screenshots__/infection-4-unable-to-assess.png | screenshot | Infection evidence | Y | Y | Y | N/A | **Y — depicts a state now removed from live documentation** | N — misleading; must not be carried as current evidence |
| sns-emr-frontend/scripts/verify-infection-rebuild.mjs | E2E verification script | Infection verification (self-cleaning) | Y | Y | N | Y — 80/80 checks, confirmed zero residual duplicates across 2 consecutive runs in this session | **Y — owner directive requires converting to unique-test-run-ID + guaranteed teardown pattern (item 6); current fix is locator-level only** | Y, pending item 6 upgrade |

## 6. Documentation

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| docs/SNS_HOSPICE_LANGUAGE_STANDARD.md | doc (v1.1 at time of this commit) | Hospice Language Standard | N | N | Y | N/A | **Superseded** — replaced by v1.2 in commit `625e66b` | Y (as superseded-then-replaced; v1.2 is the live copy) |
| SNS_DESIGN_SYSTEM_EXPORT.md | doc | Design system reference export | N | N | Y | N/A | N | Y |
| docs/SNS_DESIGN_SYSTEM_1.0.md | doc (modified) | Design system standard | N | N | Y | N/A | N | Y |
| docs/SNS_LAYOUT_STANDARD_V1_1_AND_GITHUB_CHECKLIST.md | doc (modified) | Layout standard / GitHub checklist | N | N | Y | N/A | N | Y |
| docs/compliance/hope/HOPE_RECONCILIATION_AUTHORIZATION_REQUEST_1.0.md | doc | HOPE compliance | N | N | Y | N/A | N | Y |
| docs/compliance/hope/PAIN_SYMPTOM_BURDEN_SCREEN_FIELD_MAPPING_1.0.md | doc | HOPE compliance / Pain-Symptom Burden field mapping | N | Y (references RNICA sub-module) | Y | N/A | N | Y |
| docs/compliance/hope/PRESERVATION_INVENTORY_1.0.md | doc | HOPE compliance preservation | N | N | Y | N/A | N | Y |
| docs/repository/REPOSITORY_STATE_SNAPSHOT_1.0.md | doc | Repository state snapshot | N | N | Y | N/A | N | Y |

## 7. Shared frontend infrastructure (modified — low risk, widely used)

| File | Type | Workstream | Infection? | RNICA? | Docs-only? | Previously tested? | Unresolved? | Carry forward? |
|---|---|---|---|---|---|---|---|---|
| sns-emr-frontend/package-lock.json | dependency lockfile | Build infra | N | N | N | N/A | N | Y |
| sns-emr-frontend/package.json | dependency manifest | Build infra | N | N | N | N/A | N | Y |
| sns-emr-frontend/src/charts/PatientChart.jsx | chart shell (modified, +3 lines) | RNICA wiring | Partial | Y | N | N | Partial — needs confirmation this is only RNICA registration, not allergy duplication source | Y |
| sns-emr-frontend/src/charts/PatientChartSidebar.jsx | chart shell (modified, +1 line) | RNICA wiring | Partial | Y | N | N | N | Y |
| sns-emr-frontend/src/components/ui/toggle-group.tsx | shared UI primitive (modified) | Design-system pill/toggle restyle | N | N (shared across body systems) | N | N | N | Y |
| sns-emr-frontend/src/components/ui/toggle.tsx | shared UI primitive (modified) | Design-system pill/toggle restyle | N | N | N | N | N | Y |
| sns-emr-frontend/src/main.tsx | app entry (modified, +1 line) | Build infra | N | N | N | N | N | Y |
| sns-emr-frontend/src/theme/sns-typography.css | stylesheet | Design-system typography | N | N | N | N | N | Y |

## Summary

- **Total files:** 102
- **Infection-scoped:** 8 (RNICA.jsx Infection portions, its unit test, 2 capture/verify scripts, 4 screenshots)
- **RNICA-scoped (non-Infection):** ~22 (Diagnosis-LCD, Pain/Symptom Burden, performance-scale, cardio/respiratory scripts & artifacts, CSS)
- **Documentation-only:** 8
- **Unrelated backend feature (Discipline Service/IDG continuity):** 15
- **Shared infra/build:** 8
- **Screenshot/report evidence artifacts:** ~41

**Determination:** Commit `03902dc` is confirmed to combine at least four
independent workstreams (Infection/RNICA clinical work, a new backend
Discipline Service feature, HOPE/compliance documentation, and design-system
changes) as the owner directive described. Per instruction, the commit is
left intact (not reset/rewritten). Going forward this session will:

- commit rule/standard documents separately (already done for v1.2 — `625e66b`);
- commit each body-system's work separately;
- avoid combining backend feature work, documentation, and clinical workflow
  changes in a single commit.

A new worktree branched from `03902dc` inherits **all** of the above, not
only the rule documents. Any workstream above marked "Unresolved: Y" should
not be treated as accepted/final in a new worktree without re-verification.
