# SNS PLAYWRIGHT VALIDATION STANDARD

STATUS: GOVERNANCE RULE — ADOPTED. Established during the PR #170
(Draft, `suasonns-feature/update-recertification-toggle`) human-review
readiness audit's repository-wide Playwright discovery and recovery
assessment.

## 1. RULE

Playwright (via `@playwright/test`'s `chromium` launcher, or an
equivalent Playwright-engine script) is the preferred SNS browser
automation and visual/width-validation tool. Do not introduce Cypress,
Puppeteer, Selenium, another browser-testing harness, another canvas
tool, or another screenshot/visual-regression framework without
architectural review.

## 2. CLASSIFICATION — HISTORICAL RECOVERABLE, NOT YET A REPO-WIDE STANDARD DEPENDENCY

Playwright's status as of this audit:

- **Found historically, committed, and pushed**: commit `03902dc4` on
  branch `suasonns-hope-complete-cms-alignment` (Draft PR #169) added
  `"@playwright/test": "^1.63.0"` to `sns-emr-frontend/package.json` +
  `package-lock.json`, and added
  `sns-emr-frontend/scripts/cardio-layout-audit.mjs` — a real, raw Node
  script (no `playwright.config.*`, no CI integration, manual
  invocation only) documented as a "Permanent QA/acceptance-testing
  tool" used for an owner-directed Cardiovascular-section sign-off. It
  logs into the real app, navigates to a real patient's Cardiovascular
  section, and screenshots at desktop-1440×900 / desktop-1366×768 /
  tablet-1024×768.
- This dependency and script are **not present** in every SNS
  worktree/branch (e.g. not in `suasonns-feature/update-recertification-toggle`
  as of this audit). Classification: **HISTORICAL RECOVERABLE
  ACCEPTANCE-TESTING FRAMEWORK** — explicitly *not* "Production
  Standard" or "Repository Standard" until formally adopted into every
  active branch's `package.json`.
- For this audit's PR #170 validation, the pattern was reused ad hoc
  (global `playwright-core` install outside the repo, explicit
  `executablePath` pointing at an already-cached Chromium binary — no
  changes to any repo `package.json`/lockfile) rather than treated as a
  formal adoption.

## 3. PREFERRED PATTERN (mirrors `cardio-layout-audit.mjs`)

- A raw Node script importing `chromium` from `@playwright/test` (or
  `playwright-core` when the dependency isn't yet installed in a given
  worktree), not a `playwright.config.*`/test-runner-based suite.
- Manual invocation (`node scripts/<name>.mjs`); no CI integration yet
  exists anywhere in SNS.
- Controlled viewport sizes per `SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md`.
- Full-page screenshot capture per viewport/theme/state.
- Numeric DOM measurements (`scrollWidth` vs `clientWidth`, element
  bounding rects) captured via `page.evaluate`, not visual inspection
  alone.

## 4. FUTURE ADOPTION PATH (not yet executed by this audit)

Formal repo-wide adoption (adding `@playwright/test` to every active
worktree's `package.json`, a shared `playwright.config.*`, and CI
integration) is a separate, explicit governance/engineering decision
and is **not authorized by this document alone**. This standard records
the recommended *pattern* only.

## 5. SCOPE

Required validation tool for: BodyShieldShell, Body Systems Registry,
Neurological, Respiratory, Cardiovascular, Integumentary, Review By
Exception, Nurse Review, and any other major SNS clinical UI redesign,
per `SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md`.

## 6. PROVENANCE

Adopted during the PR #170 real-browser width-utilization audit
(`suasonns-feature/update-recertification-toggle`, Draft), following a
repository-wide discovery audit that located the historical, committed,
pushed Playwright asset on PR #169's branch. Does not authorize any
redesign of clinical fields, validation, response values, or workflow
behavior — see
`docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
for the controlling scope boundary, which this rule does not relax.
