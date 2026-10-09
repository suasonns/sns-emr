# SNS CLINICAL READABILITY STANDARD

STATUS: GOVERNANCE RULE — ADOPTED. Established during the PR #170
(Draft, `suasonns-feature/update-recertification-toggle`) human-review
readiness audit's real-browser width-utilization review.

## 1. WHO SNS IS FOR

SNS is a hospice clinical documentation platform. It is not primarily a
developer tool, a startup dashboard, or a consumer application. Primary
users include:

- Hospice RNs and LVNs
- Clinical Supervisors
- QA Reviewers
- Compliance Staff
- Hospice Administrators
- Medical Directors
- IDG participants

Many users spend extended sessions reviewing admissions, recertifications,
decline evidence, plans of care, interventions, responses, chart audits,
eligibility review, and compliance documentation. Many have practiced for
years and work long documentation hours.

## 2. CLINICAL FATIGUE RULE

Design decisions must actively reduce documentation fatigue, accounting
for extended chart-review sessions, reduced visual stamina, reading
speed, visual scanning effort, and cognitive load. Do not design or
validate only for short sessions on a developer laptop.

## 3. READABILITY FIRST, DENSITY SECOND

Typography and layout decisions must optimize **readability first**,
information density second — never the reverse. Preferred typography
direction:

- narrow
- sharp
- highly legible
- information-dense
- low visual fatigue

Typography must never be chosen merely because it is fashionable or
modern; it must measurably improve clinical usability (scanning speed,
clarity, low fatigue over long sessions).

## 4. SIMULTANEOUS VISIBILITY

When width is available, use it to increase **useful simultaneous
visibility**, not merely to stretch layout. Examples of information that
should be visible together when clinically beneficial: Current Evidence,
Historical Evidence, Source Attribution, Interventions, Responses,
Follow-Up, Review By Exception. Do not force extra navigation/clicks when
information can safely coexist on screen.

## 5. WORKFLOW EFFICIENCY IS THE PRIMARY METRIC

Width, density, and control size are **supporting evidence only**.
Clinical workflow efficiency is the primary success metric. Before
classifying any layout as a defect, apply this test — if the answer is
**No** to every question, do not classify it as a workflow defect:

1. Does it increase scrolling?
2. Does it increase clicks?
3. Does it increase mouse movement?
4. Does it increase eye movement?
5. Does it increase navigation?
6. Does it reduce readability?
7. Does it reduce simultaneous visibility?
8. Does it reduce workflow efficiency / documentation efficiency?

## 6. "NO WASTED SPACE" DEFINITION (ADOPTED)

**No Wasted Space means:** less scrolling, less clicking, less
navigation, less mouse movement, less eye movement, less window
switching, less documentation fatigue, and more useful information
visible simultaneously.

**No Wasted Space does NOT mean:** fill every pixel, shrink every
control, force every control to an arbitrary max-width, or maximize
density regardless of readability.

## 7. SCOPE — PLATFORM-WIDE, NOT BODY-SYSTEMS-SPECIFIC

This standard is an **SNS platform-wide standard**, not a Body Systems-
specific rule. Readability, workflow efficiency, documentation fatigue,
and "No Wasted Space" apply to every SNS interface, not only clinical
forms. Scope includes, without limitation:

- Clinical platform: RNICA, Body Systems Registry, BodyShieldShell,
  Neurological, Respiratory, Cardiovascular, Integumentary, Review By
  Exception, Nurse Review, Admissions, Recertifications, Visits, HOPE,
  Plans of Care, Orders, Tasks
- Reports and dashboards (clinical, QA, compliance, executive)
- Tenant Owner / Biller platform: Claims, Collections, Financial
  Reporting, Executive Reporting
- Administrator UI and configuration screens
- Any future SNS module

Priority order for these reviews:

1. Readability
2. Simultaneous visibility
3. Reduced scrolling
4. Reduced navigation
5. Reduced documentation burden
6. Reduced eye movement
7. Reduced mouse movement
8. Workflow efficiency

## 8. RELATED STANDARDS

- `docs/governance/SNS_CLINICAL_WORKSPACE_STANDARD.md` — supported
  viewport/device matrix.
- `docs/governance/SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md` — required
  validation methodology and viewport matrix.
- `docs/governance/SNS_PLAYWRIGHT_VALIDATION_STANDARD.md` — recovered
  Playwright pattern mandated as the validation tool.

## 9. PROVENANCE

Adopted during the PR #170 real-browser width-utilization audit
(`suasonns-feature/update-recertification-toggle`, Draft). Does not
authorize any redesign of clinical fields, validation, response values,
or workflow behavior — see
`docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
for the controlling scope boundary, which this rule does not relax.
