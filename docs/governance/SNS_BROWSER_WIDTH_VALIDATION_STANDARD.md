# SNS BROWSER WIDTH VALIDATION STANDARD

STATUS: GOVERNANCE RULE — ADOPTED. Established during the PR #170
(Draft, `suasonns-feature/update-recertification-toggle`) human-review
readiness audit's real-browser width-utilization review.

## 1. RULE

Actual browser rendering at controlled viewport widths is required
before approving any major SNS clinical UI redesign. DOM-only/CSS-only
inspection, component-test assertions, flex-wrap verification, or
screenshot review without controlled viewport sizing are **not
sufficient by themselves**.

## 2. REQUIRED VALIDATION MATRIX

Every major clinical UI must be validated at (at minimum) these
viewports, covering the environments defined in
`SNS_CLINICAL_WORKSPACE_STANDARD.md`:

| Tier | Width | Representative device |
|---|---|---|
| Ultrawide | 3440 | 34" ultrawide monitor (primary workstation) |
| Large Desktop | 1920 | Desktop monitor |
| Standard Desktop | 1440 | Desktop monitor |
| Laptop | 1366 | 15-inch laptop |
| Small Laptop | 1280 | 13-inch laptop |
| Tablet | 1024 | iPad |
| Large Phone | 430 | iPhone (large) |
| Phone | 390 | iPhone |

Each viewport/state combination must be validated for both light and
dark theme.

## 3. REQUIRED MEASUREMENTS PER VIEWPORT

1. Viewport dimensions
2. Visible content width
3. Left/right wasted margin (gutter) width
4. Primary container width
5. Sidebar/navigation width (or explicit "N/A" with reason)
6. Control widths (selects, inputs, text areas) where relevant
7. Scrollable regions
8. Horizontal overflow (boolean)
9. Clipped/truncated content
10. Responsive-transition behavior
11. Plain-language usability assessment

## 4. "NO WASTED SPACE" — TWO FAILURE MODES

Per `SNS_CLINICAL_READABILITY_STANDARD.md`, "No Wasted Space" covers two
opposite failure modes, both are defects only if they fail the
workflow-efficiency test in that standard:

- **Failure A — Unused space:** giant empty margins, narrow content on
  wide displays, unnecessary whitespace, mobile-sized layouts on desktop.
- **Failure B — Overstretched controls:** form controls, dropdowns, or
  inputs stretching far beyond a readable width purely because screen
  width is available, with no corresponding workflow benefit.

Width alone is not a defect signal. A control/layout is only a defect
if it demonstrably increases scrolling, clicks, mouse movement, eye
movement, or navigation, or reduces readability, simultaneous
visibility, or workflow efficiency (see the 8-question workflow test in
`SNS_CLINICAL_READABILITY_STANDARD.md` §5).

## 5. VALIDATION METHODOLOGY

Use the recovered Playwright-based rendering pattern — see
`SNS_PLAYWRIGHT_VALIDATION_STANDARD.md`. Do not introduce Cypress,
Selenium, Puppeteer, or another browser-testing/visual-regression
framework without architectural review.

## 6. SCOPE

Required before approving: BodyShieldShell, Body Systems Registry,
Neurological, Respiratory, Cardiovascular, Integumentary, Review By
Exception, Nurse Review, and any other major SNS clinical UI redesign.

## 7. PROVENANCE

Adopted during the PR #170 real-browser width-utilization audit
(`suasonns-feature/update-recertification-toggle`, Draft), which
validated `AssessmentTypeToggle.jsx` and
`MedicareNonCoveredReviewPanel.jsx` across the full matrix in §2 with
zero horizontal-overflow/clipping/responsive defects found. Does not
authorize any redesign of clinical fields, validation, response values,
or workflow behavior — see
`docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
for the controlling scope boundary, which this rule does not relax.
