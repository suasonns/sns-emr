# Frontend Regression Strategy — Current Gap and Future Direction

Documentation only. No framework is installed or configured by this note.

## Current gap

This repository (`sns-emr-frontend`) has:

- A unit/component test layer: Vitest + React Testing Library, 19 files /
  276 tests as of 2026-09-08 (`npx vitest run`). This layer is solid for
  logic, hooks, and isolated component behavior (e.g.
  `ClinicalNarrativeCard.test.jsx`, `narrativeSupport.test.js`).
- **No end-to-end / browser-automation layer.** `package.json` has no
  Playwright, Cypress, Puppeteer, or Selenium dependency, and no `e2e` or
  `smoke` npm script.

This gap surfaced concretely during the RNICA legacy-narrative-writer removal
(2026-09-08): component tests and a full unit-test-suite run both passed, but
a live, in-browser, click-through confirmation for the three regression
patients (Loren/Norma/Kessler) could not be completed in-session because the
only available browser-automation surface (an embedded browser tool used
interactively by the agent) became unavailable mid-session, with no repo-
native fallback to fall back to. See
`docs/planning/rnica_legacy_writer_removal_verification.md` and
`docs/planning/manual_demo_validation.md` for how that gap was handled for
this specific release (manual checklist in lieu of automated e2e).

## Why this matters going forward

Unit/component tests cannot catch:

- Wiring regressions across real page navigation (routing, auth guards,
  layout).
- Real network request/response shape mismatches between frontend and the
  actually-running backend (mocks in unit tests can silently drift from the
  real API).
- Visual/DOM regressions only observable in a real rendered page (e.g. a
  banner that renders empty, a button that's present but not clickable due to
  an overlapping element).
- End-to-end persistence across a real save → reload cycle against a real
  database, as opposed to a mocked persistence layer.

For a clinical-documentation product where a regression could mean a wrong or
missing clinical value reaching an RN's screen, this is a real coverage gap,
not a cosmetic one.

## Recommendation (not implemented — for future planning)

1. **Adopt Playwright** for a small, targeted e2e suite, rather than
   Cypress or Selenium:
   - Already TypeScript-native, matching this codebase.
   - Runs headless in CI without a licensed cloud runner.
   - Has first-class network-interception APIs, which would have let this
     session's Norma V2-preview network-capture verification
     (`POST .../narrative-v2/preview` → 200, response shape assertions) run
     as a repeatable automated test instead of an ad hoc interactive browser
     session.

2. **Scope the initial e2e suite narrowly**, not broadly:
   - Login → land on `/portal`.
   - Open a known regression patient (Loren/Norma/Kessler, matching the
     patients already designated in the RNICA architecture map's Regression
     Test Matrix, Section 18) → RNICA/Finalization → assert Performance
     Status scale values render.
   - Click "Build Draft from Documented Findings" → assert the real network
     call fires to the real V2 endpoint → assert the resulting narrative
     text contains no banned legacy headings → assert the Quality Gate shows
     PASS.
   - Unsaved-assessment path: create a disposable assessment, attempt Build
     Draft before saving, assert the save-first message appears and no
     network call to the narrative endpoint occurs.
   - Save → hard reload → assert persistence.

   This maps directly onto the manual checklist in
   `docs/planning/manual_demo_validation.md` — that checklist can become the
   first Playwright test's assertions almost line-for-line once implemented.

3. **Run it against the same dev-server pattern already in use**
   (`uvicorn` + `vite --host`), not a separate production-like environment,
   so it stays cheap to run locally and in CI.

4. **Gate it into CI as a required check for RNICA/narrative-touching PRs
   specifically**, rather than making it a blanket requirement for every PR
   on day one — narrow adoption first, expand once stable.

## Explicitly out of scope for now

- No framework is being installed as part of this note or the removal
  release it accompanies.
- No CI changes are being made.
- This is a planning document only, to be picked up as a separate, scoped
  piece of work after the current release.
