# RNICA Legacy Frontend Narrative Writer — Removal Verification Record

Branch: `feature/production-hnp-clinical-runtime`
Removal commit: `8fde005` — `fix(rnica): remove legacy frontend narrative writer`
Follow-up commit: `f93988a` — `docs(rnica): remove stale legacy-writer reference`
Date: 2026-09-08

## 1. Objective

Prove the legacy frontend deterministic narrative writer
(`clinicalNarrativeBuilder.js` / `buildClinicalNarrative()`) has been removed —
not renamed, not merely demoted to a fallback — and that backend RNICA V2
(`generate_rnica_narrative_v2()` / `previewRnicaNarrativeV2()`) is the sole
clinical-narrative-composition engine, with a safe save-first UX replacing the
old unsaved-assessment fallback.

## 2. Architecture before

- `diagnoses.clinicalNarrative` had two independent write paths:
  - Frontend deterministic template (`clinicalNarrativeBuilder.js`), invoked
    directly by "Build Draft from Documented Findings" when an assessment had
    no `assessmentId` yet, or when the V2 API call failed.
  - Backend V2 engine, invoked via `previewRnicaNarrativeV2()` in all other
    cases.
- Whichever path fired last determined what the RN saw, with no on-screen
  indicator of which engine produced the text.

## 3. Architecture after

- `clinicalNarrativeBuilder.js` and its test are deleted from the repository.
- `ClinicalNarrativeCard.handleBuildDraft()` (`RNICA.jsx`) has no branch that
  generates narrative text locally. If `assessmentId` is falsy it sets
  `draftError = "SAVE_REQUIRED"` and generates nothing.
- A new `handleSaveThenBuildDraft()` calls `saveNow()` (new awaitable action on
  `useAssessmentAutosave()`) and only then invokes
  `previewRnicaNarrativeV2()`.
- Shared, engine-agnostic infrastructure formerly in the deleted file (Disease
  Trajectory constants/helpers, `computeNarrativeContextFingerprint()`,
  `evaluateNarrativeQualityGate()`) now lives in a new module,
  `narrativeSupport.js`, independently confirmed to contain no narrative
  composition logic (Section 8).

## 4. Deleted files

- `sns-emr-frontend/src/intake/clinicalNarrativeBuilder.js`
- `sns-emr-frontend/src/intake/clinicalNarrativeBuilder.test.js`

Filesystem check (this segment): `Test-Path` on both paths returns `False`.
Both are absent from the current `HEAD` (`git status`/`git show HEAD --stat`
confirm the deletions are part of commit `8fde005`).

## 5. Changed files (commit `8fde005`)

- `sns-emr-frontend/src/components/RNICA.jsx`
- `sns-emr-frontend/src/hooks/useAssessmentAutosave.ts`
- `sns-emr-frontend/src/intake/narrativeSupport.js` (new)
- `sns-emr-frontend/src/intake/narrativeSupport.test.js` (new)
- `sns-emr-frontend/src/components/ClinicalNarrativeCard.test.jsx` (new)
- `docs/clinical/rnica-architecture-map.md`

Follow-up commit `f93988a`:
- `backend/app/services/rnica_narrative_v2_service.py` (stale docstring that
  still referenced the deleted frontend file by name — documentation only, no
  behavior change)

## 6. SSOT declaration

Backend RNICA V2 (`generate_rnica_narrative_v2()`, reached from the frontend
exclusively via `previewRnicaNarrativeV2()`) is the only executable path that
composes `diagnoses.clinicalNarrative` prose. No frontend module composes
narrative prose.

## 7. Static-search results

Repo-wide search (frontend `src/`, backend `app/`) for:
`clinicalNarrativeBuilder`, `buildClinicalNarrative` — 3 files match, all
historical/doc-comment references (`narrativeSupport.js` header comment,
`rnica-architecture-map.md`, `rnica_narrative_v2_service.py` docstring — this
last one was corrected in `f93988a` to describe the removal accurately rather
than reference the deleted file as if it still existed). Zero executable
imports or calls remain.

Search for the specific banned legacy headings
(`HOSPICE CLINICAL PICTURE`, `REASON FOR HOSPICE ADMISSION`,
`EVIDENCE OF DECLINE`, `DISEASE-SPECIFIC SUPPORT`, `DOCUMENTATION GAPS`,
`RN FOLLOW-UP`) across `sns-emr-frontend/src` and `backend/app` — **zero
matches**.

## 8. `narrativeSupport.js` export inventory

| Export | Category | Caller(s) | Composes prose? | Writes narrative field? |
|---|---|---|---|---|
| `DISEASE_TRAJECTORY_OPTIONS` | constant | `RNICA.jsx` | No | No |
| `LEGACY_DISEASE_TRAJECTORY_VALUES` | constant | internal + `RNICA.jsx` | No | No |
| `isLegacyDiseaseTrajectoryValue()` | lookup helper | `RNICA.jsx` | No | No |
| `getDiseaseTrajectoryLabel()` | lookup helper | `RNICA.jsx` | No (label lookup only) | No |
| `computeNarrativeContextFingerprint()` | hash/fingerprint helper | `RNICA.jsx` | No (djb2 hash of a JSON-stringified field subset) | No |
| `evaluateNarrativeQualityGate()` | text-quality check | `RNICA.jsx` | No (regex linter over existing text; never generates or alters text) | No |

Conclusion: `narrativeSupport.js` validates, labels, and fingerprints —
it cannot independently generate a clinical narrative. It has no access to
harvested evidence, no prompt/template construction, and no write path to
`diagnoses.clinicalNarrative`. This inventory itself, plus
`ClinicalNarrativeCard.test.jsx`'s assertion that the unsaved-assessment path
"calls nothing," is the regression guard against a future prose-composition
export being added here unreviewed.

## 9. Unsaved-assessment behavior (component-test verified)

`ClinicalNarrativeCard.test.jsx`: when `assessmentId` is falsy, clicking
"Build Draft" sets `draftError = "SAVE_REQUIRED"`, renders the jargon-free
save-first message and a "Save Assessment" button, and calls neither
`previewRnicaNarrativeV2` nor any local generator. Clicking "Save Assessment"
invokes `onSaveNow()` (proxy for `saveNow()`).

Live-browser confirmation of this exact flow (new disposable assessment →
Build Draft → save-first message → Save → Build Draft again → V2 call) was
**not completed this segment** — see Section 17 (Open Gaps).

## 10. Save-failure behavior

Covered indirectly: `saveNow()` reuses the same `runAutosave()` logic as the
existing periodic autosave (extracted into a shared function specifically so
both paths share identical gating/error behavior), and the periodic autosave's
existing error handling (loading state always clears, no data loss, error
surfaced) is unchanged by this refactor. A dedicated live/simulated
save-failure click-through was not performed this segment (see Section 17).

## 11. V2-failure behavior (component-test verified, unchanged from before)

`ClinicalNarrativeCard.test.jsx`: a rejected `previewRnicaNarrativeV2()` call
shows the Retry UI, never writes a fallback narrative, and never touches
existing narrative text.

## 12. Existing-narrative protection (component-test verified)

`ClinicalNarrativeCard.test.jsx`: generating a draft when a narrative already
exists requires an explicit "Replace with New Draft" confirmation before the
new text overwrites the field; a successful draft writes narrative text +
context fingerprint + reset review status together as a single unit.

## 13. Autosave / `saveNow` validation

`useAssessmentAutosave.ts`: the interval tick's save logic was extracted into
`runAutosave()`, called by both the existing 30s interval and the new
`saveNow()` export, so both paths share the exact same
skip-if-unchanged/locked/saving/already-autosaving gating. `saveNow()` is
awaitable and propagates thrown errors to the caller; the interval tick still
only logs and swallows errors (unchanged prior behavior). No new dedicated
concurrency/duplicate-request unit test was added this segment beyond what
`ClinicalNarrativeCard.test.jsx` exercises (Save Assessment → `onSaveNow()`
proxy). Full hook-level concurrency stress-testing (concurrent autosave +
manual save race, component-unmount-mid-save) was not performed — flagged as
an open gap (Section 17), not asserted as passing.

## 14. Frontend tests

Command: `npx vitest run` (from `sns-emr-frontend/`)
Result: **19 test files, 276 tests — all passing.**

## 15. Backend tests

Command:
`python backend/scripts/run_isolated_tests.py -- -k "rnica or narrative_v2 or performance_status" -q`
Result: **62 tests collected, 62 passed, 0 failed, 0 errors** (isolated
per-worktree Postgres test database, Alembic migrated to head
`8d3911bbf250`).

## 16. Build result

`tsc -b` on the changed files (`RNICA.jsx`, `narrativeSupport.js`,
`useAssessmentAutosave.ts`) introduces zero new errors. Pre-existing,
unrelated MUI prop-type errors in `FacilityCollectionsReportPage.tsx` were
confirmed present on the unmodified baseline via `git stash` and are out of
scope for this change.

## 17. Service process verification (this segment)

Both dev servers were found **stopped** at the start of this segment
(`Get-NetTCPConnection` showed nothing listening on 5173 or 8000; no
`node`/`python` process present) — this matches the `ERR_CONNECTION_REFUSED`
the user observed, and was a real process outage, not only a browser-tool
symptom. Restarted both from this exact worktree:

- Backend: `python -m uvicorn app.main:fastapi_app --host 0.0.0.0 --port 8000`
  from `backend/` — PID `47660`. `curl http://localhost:8000/health` →
  `{"status":"ok","environment":"development"}` (HTTP 200). Startup log
  confirms schema hash match, Alembic at head, application startup complete.
- Frontend: `npm run dev -- --port 5173 --host` from `sns-emr-frontend/` —
  PID `47352`. `curl http://localhost:5173/` → HTTP 200. Vite startup log
  confirms `Local: http://localhost:5173/`.
- `Get-NetTCPConnection -State Listen` confirms both ports listening,
  correctly bound (`0.0.0.0:8000`, `::5173`).

**Remaining limitation**: the embedded browser canvas tool completed one
login sequence successfully immediately after the restart (proving the
services are reachable through the browser layer too), then became
unresponsive across further read/navigate attempts (~15 retries over several
minutes, across multiple fresh page instances). No supported alternative
end-to-end browser runner exists in this repository (no Playwright/Cypress/
Puppeteer dependency, no `e2e`/`smoke` npm script) to substitute. This is
recorded as a tool-level limitation, not a service-health or code problem,
because the services independently and consistently respond via direct HTTP
throughout.

## 18. Loren live result

**Not completed this segment** — blocked by the browser-tool limitation in
Section 17, after service restart. Prior-segment live verification (recorded
in Section 13 of the architecture map, dated 2026-09-08, prior to this
removal) confirmed PPS 40%/KPS 40/NYHA IV with zero legacy headers against an
earlier commit (`65b2187`) — that verification predates and does not stand in
for verification against `8fde005`/`f93988a`.

## 19. Norma live result

**Not completed this segment** — same limitation as Section 18.

## 20. Kessler live result

**Not completed this segment** — same limitation as Section 18.

## 21. Quality-gate result

Verified via `narrativeSupport.test.js` (component/unit level, not live
browser): `evaluateNarrativeQualityGate()` rejects camelCase field keys, raw
`Label: value` field-dump lines, UUID-shaped internal IDs, and raw JSON
fragments; accepts clean RN prose. No changes were made to gate logic in this
removal — it was copied verbatim from the deleted file.

## 22. Open gaps

1. **Live browser click-through for Loren/Norma/Kessler against commit
   `8fde005`/`f93988a` is not complete.** This is the single remaining item
   before this removal can be marked `VERIFIED_LEGACY_WRITER_REMOVED`.
2. Dedicated hook-level concurrency tests for `saveNow()` vs. the periodic
   autosave interval (race conditions, component-unmount-mid-save) were not
   added this segment.
3. A live (not just component-test) save-failure and V2-failure simulation
   was not performed this segment.

None of these gaps involve the legacy writer itself reappearing — all are
about completing live/expanded verification of the already-removed state.

## 23. Deployment scope

**In scope for this release (isolated, commits `8fde005` + `f93988a`):**
All files listed in Sections 5 above.

**Explicitly excluded from this release (uncommitted, unrelated work in the
same worktree):**

| Path | Status | Related to removal? | Include? |
|---|---|---|---|
| `backend/app/api/registry.py` | modified | No | No |
| `backend/app/api/visits.py` | modified | No | No |
| `sns-emr-frontend/src/api/icaAssessments.ts` | modified | No | No |
| `sns-emr-frontend/src/charts/PatientChart.jsx` | modified | No | No |
| `sns-emr-frontend/src/charts/PatientChartSidebar.jsx` | modified | No | No |
| `backend/app/api/evidence_center.py` | untracked | No (Evidence Center feature) | No |
| `backend/app/services/evidence_center_service.py` | untracked | No | No |
| `backend/app/services/scale_interpretations.py` | untracked | No | No |
| `backend/scripts/loren_evidence_demo.py` | untracked | No | No |
| `backend/scripts/onboard_norma_from_hnp.py` | untracked | No | No |
| `backend/scripts/populate_loren_medications_from_pdf.py` | untracked | No | No |
| `docs/testing/` | untracked | No | No |
| `sns-emr-frontend/src/api/evidenceCenter.ts` | untracked | No | No |
| `sns-emr-frontend/src/components/EvidenceCenter.jsx` | untracked | No | No |
| `sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.js` (+ test) | untracked | No | No |
| `sns-emr-frontend/src/intake/scaleInterpretations.js` | untracked | No | No |
| `backend/backend.pid` | untracked | No (process artifact) | No — should be gitignored, not committed |

No file in this list is classified as "unknown" — each is explicitly
identified as unrelated pre-existing session work (Evidence Center feature,
chart-sidebar tweaks, disease-category-detection helpers, scale-interpretation
helpers, a testing-docs folder) that was deliberately left uncommitted per
scope isolation and requires its own separate review before release.

## 24. Rollback reference

- Removal commit: `8fde005`
- Parent commit: `65b2187` — "Fix Kessler FAST/PPS/KPS data gap; confirm
  Norma ECOG gap is genuine"
- Follow-up (docs-only) commit: `f93988a`
- Deployment commit set for this feature: `8fde005` + `f93988a`
- Rollback command: `git revert f93988a 8fde005` (revert in this order, most
  recent first) — reverting `8fde005` **would restore the deleted legacy
  writer file and its reachable-when-unsaved/on-failure fallback path**.
  Per the removal directive, this is explicitly not recommended except in a
  critical release failure with the risk consciously accepted; prefer a
  forward-fix commit over reverting the removal.

## 25. Final status

**LIVE_BROWSER_VERIFICATION_PENDING**

- `CODE_REMOVAL_VERIFIED`: yes (Sections 4, 7)
- `AUTOMATED_TESTS_VERIFIED`: yes (Sections 14, 15 — 276/276 frontend, 62/62
  targeted backend)
- `SERVICE_HEALTH_VERIFIED`: yes (Section 17 — both services confirmed
  running from this worktree/commit, both HTTP 200)
- `LIVE_PATIENT_CLICK_THROUGH`: pending — blocked by an embedded browser-tool
  outage that persisted after service health was independently confirmed; no
  alternative supported end-to-end runner exists in this repository to
  substitute.

Do not read this as `VERIFIED_LEGACY_WRITER_REMOVED` — that status requires
the Loren/Norma/Kessler live click-through in Sections 18–20 to actually
complete.
