# SNS Hospice Solutions
# Repository-First Implementation Constitution

**Document Status:** ACTIVE ENGINEERING AUTHORITY
**Applies To:** All SNS Hospice Solutions repositories, applications, platforms, workflows, services, documentation, tests, migrations, and user interfaces
**Primary Purpose:** Prevent context loss, unsupported assumptions, duplicate architecture, requirements rediscovery, visual drift, clinical regression, and unsafe implementation
**Default Development Mode:** Repository-first implementation
**Default Response to Existing Approved Work:** Reuse and implement, not rediscover

## 1. Scope

This constitution governs development involving:

- RNICA
- Patient Story
- Patient Chart
- HOPE
- HUV1 and HUV2
- SFV
- Owner Platform
- Tenant Platform
- Biller Platform
- Admissions
- Elections
- Certifications
- Recertifications
- Visits
- Orders
- Plan of Care
- IDG
- Discharge
- Bereavement
- Audit
- Integrations
- AI services
- Frontend design systems
- Backend services
- Database changes
- Test infrastructure
- Field-testing preparation

No SNS workstream is exempt unless a more specific active repository authority explicitly supersedes part of this constitution.

## 2. Repository-First Rule

Before making any recommendation, design change, code change, refactor, deletion, replacement, dependency addition, migration, workflow change, terminology change, or architectural decision, the implementation agent must inspect the current repository.

Previous conversation memory is not authoritative.

Previous session memory is not authoritative.

Historical summaries are not authoritative when the current repository differs.

The current repository, active authority documents, current implementation, current tests, current database state, and approved design references control the work.

The implementation agent must not assume that a feature, component, rule, API, field, hook, route, token, test, or workflow is missing until repository inspection confirms it.

## 3. Mandatory Session-Start Gate

No source file may be modified until the session-start checklist is completed.

At the beginning of every development session, the implementation agent must inspect:

### Repository state

- repository root
- current branch
- current commit SHA
- working-tree status
- staged files
- modified files
- untracked files
- recent relevant commits
- active pull request or worktree context, if available

### Current workstream

- active platform or workflow
- active implementation phase
- current checkpoint
- last completed checkpoint
- current screen, service, or feature
- next authorized work item
- known open defects
- known closed defects
- known blocked items

### Existing authority

The implementation agent must locate and read:

- active source-of-truth documents
- active implementation-authority documents
- active workflow-authority documents
- active screen-authority documents
- active data-mapping documents
- active design references
- active handoff or phased implementation plans
- active relevant defect records
- active repository instructions

For RNICA work, the agent must locate and review the current repository equivalents of:

- RNICA_IMPLEMENTATION_AUTHORITY.md
- RNICA_SCREEN_AUTHORITY_MATRIX.md
- RNICA_WORKFLOW_AUTHORITY_MAP.md
- RNICA_DATA_MAPPING_MATRIX.md
- RNICA_AI_GOVERNANCE.md
- RNICA_LOCK_READINESS_MATRIX.md
- RNICA_GITHUB_HANDOFF_PLAN.md
- RNICA_REDESIGN_SOURCE_OF_TRUTH.md
- RNICA_PHASED_IMPLEMENTATION_PLAN.md
- RNICA_FEATURE_TO_UI_WIRING_MATRIX.md
- RNICA_UI_DEPENDENCY_MAP.md

The agent must inspect the files rather than relying on remembered contents.

### Existing implementation

Before editing, inspect:

- current route
- current page or component
- parent shell
- data-loading path
- API client
- backend route
- backend service
- model or persistence path
- validation
- authorization
- relevant styles
- theme integration
- existing tests
- active design references

### Session gate result

Before implementation, return the mandatory session-start response defined in Section 18.

If essential evidence is missing, state exactly what is missing.

Do not replace missing evidence with assumptions.

## 4. Authority and Conflict Resolution

Authority must be determined from actual repository status and document content, not filenames alone.

When multiple sources overlap, apply the most specific active authority for the subject.

For RNICA implementation, use this general order unless the active documents specify another order:

1. Current explicit product decision
2. Active implementation authority
3. Active source of truth
4. Screen authority
5. Workflow authority
6. Data mapping
7. AI governance
8. Lock and readiness authority
9. Approved Figma or PNG reference for appearance
10. Phased implementation or GitHub handoff plan
11. Current tested implementation
12. Historical discovery documents
13. Superseded or reference-only documents

Approved design references control appearance.

Repository clinical logic controls behavior.

A Figma or PNG reference does not authorize new clinical logic.

Existing code does not authorize ignoring approved visual design.

When an older gap report conflicts with later implemented code and passing regression tests, current verified implementation controls and the old gap must be marked resolved or superseded.

When a direct unresolved conflict remains, stop only the affected item. Continue unaffected authorized work.

## 5. No-Assumption Rule

The implementation agent must not assume:

- a feature is missing
- a feature is complete
- a component does not exist
- a component is reusable
- a validation rule is absent
- a field is not stored
- a route is active
- a route is protected
- an API is unused
- a migration is missing
- a response set is undefined
- a workflow is authorized
- a Figma reference is current
- a screen is visually complete
- a defect is still active
- a defect is resolved
- a database is at migration head
- sample data is live data
- AI is connected
- AI is unimplemented

Each conclusion must be supported by repository, test, runtime, database, or design evidence.

Use these classifications:

- VERIFIED
- PARTIAL
- NOT VERIFIED
- CONFLICTING
- NOT FOUND
- SUPERSEDED
- BLOCKED BY EXPLICIT DECISION

Do not use NOT FOUND unless the relevant repository area was actually searched.

## 6. Reuse-Before-Create Rule

Before creating a new:

- component
- hook
- context
- store
- utility
- route
- service
- API client
- model
- schema
- migration
- design token
- validation rule
- test helper
- layout
- navigation system
- role
- permission
- enum
- status value

the implementation agent must search for an existing repository implementation.

The agent must report one of:

- EXISTING IMPLEMENTATION FOUND
- EXISTING PARTIAL IMPLEMENTATION FOUND
- NO EXISTING IMPLEMENTATION FOUND
- CONFLICTING IMPLEMENTATIONS FOUND

If an existing implementation is usable, reuse it.

If an existing implementation is partial, extend it when safe.

Do not create parallel architecture merely because creating a new implementation is easier.

## 7. Implementation-Over-Reporting Rule

If the repository already contains:

- an active source of truth
- implementation authority
- a gap report
- a design specification
- a phased implementation plan
- a current backlog

the default action is implementation.

Do not create another:

- source of truth
- authority matrix
- gap report
- roadmap
- document inventory
- terminology review
- traceability audit
- implementation plan

unless:

- explicitly requested
- a direct conflict exists
- a blocking decision is missing
- data loss is possible
- a security boundary is unclear
- a schema change requires approval
- evidence proves that the existing document is obsolete

Status reporting must not replace implementation.

## 8. RNICA Preservation Rule

RNICA redesign is primarily a presentation, navigation, organization, usability, and responsive-design project.

Unless a verified and authorized defect requires correction, preserve:

- all existing clinical fields
- all existing response values
- all existing requiredness
- all current conditional visibility
- assessment applicability
- HOPE behavior
- ACP behavior
- save behavior
- autosave
- readiness
- Finalization
- Lock
- amendments
- signatures
- attestations
- audit history
- Orders integration
- Plan of Care integration
- certification support
- recertification support
- historical records
- tenant isolation
- patient authorization

Do not create new clinical policy while re-skinning RNICA.

Do not change existing clinical behavior to make a visual component easier to implement.

Patient Story is an approved read-only aggregation layer and owns no clinical data.

## 8a. RNICA Workflow Order

**[PRODUCT-AUTHORITY DECISION — 2026-09-22]** The canonical RNICA workflow
order is:

1. Patient Story
2. Evidence & Intake
3. Pain & Symptom Burden
4. Diagnosis & LCD
5. Functional Status
6. Body Systems
7. Caregiver & Support
8. Safety & Clinical Risk
9. ACP & Goals of Care
10. Orders & POC
11. Compliance & Readiness
12. AI Action Center
13. Finalization

This supersedes any prior numbering in `RNICA_WORKFLOW_AUTHORITY_MAP.md`,
`RNICA_SCREEN_AUTHORITY_MATRIX.md`, and `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
(all three have been updated to reflect it). The full rationale and
navigation-ownership model live in
`docs/tenant-platform/RNICA_NAVIGATION_SPECIFICATION.md` — treat that
document as authoritative for workflow order and navigation questions.
Non-linear navigation between screens remains permitted; this is the
default/recommended sequence, not a server-enforced gate.

## 8b. RNICA Workflow Navigation

- **Patient Chart Navigation** (global chart areas: Facesheet, Care
  Overview, Intake & Admission, Nursing Assessment, Visits, Orders,
  Medications, Physician Orders) and **RNICA Workflow Navigation**
  (navigation between the 13 RNICA screens) are separate concerns owned by
  separate components. Never merge them into one navigation surface.
- RNICA workflow navigation is owned by the RNICA workspace shell
  (`RnicaScreenShell` in `RNICACommandWorkspace.jsx`), not by any global
  chart-navigation component.
- Desktop: RNICA workflow navigation is a dedicated rail with active-state
  and progress indication — not a horizontal, scrolling tab bar.
- Mobile: the rail collapses to a compact current-screen control that
  opens a full list for navigation; no horizontal overflow.
- See `docs/tenant-platform/RNICA_NAVIGATION_SPECIFICATION.md` for full
  detail before implementing any navigation change.

## 9. shadcn/ui Policy

shadcn/ui is an implementation toolkit, not the SNS design authority.

SNS owns:

- product identity
- branding
- information architecture
- navigation
- workflows
- clinical ownership
- accessibility requirements
- Light and Dark themes
- Figma composition
- responsive behavior
- status meanings
- clinical interaction patterns

shadcn/ui may supply accessible primitives.

Approved primitive categories include:

- Card
- Button
- Badge
- Alert
- AlertDialog
- Dialog
- Sheet
- Drawer
- Popover
- Tooltip
- Accordion
- Tabs
- Table
- Command
- ScrollArea
- Select
- Combobox
- Input
- Textarea
- Checkbox
- RadioGroup
- Switch
- Breadcrumb
- Separator
- Skeleton
- Progress
- DropdownMenu

Do not import or adopt complete shadcn:

- dashboards
- admin templates
- application shells
- sidebars
- patient-chart templates
- EMR layouts
- generated workflow screens
- hardcoded mock pages

Do not create a second navigation architecture.

Do not create a disconnected preview route.

Do not copy hardcoded sample patient data.

## 10. shadcn Pre-Installation Gate

Before installing shadcn dependencies:

1. Inspect package.json.
2. Inspect the lockfile.
3. Inspect the current framework and build tool.
4. Inspect the current React version.
5. Inspect Tailwind configuration.
6. Inspect path aliases.
7. Inspect the existing class-merging utility.
8. Inspect existing component primitives.
9. Inspect the current icon library.
10. Inspect theme providers and CSS-variable conventions.
11. Determine whether the required dependency already exists.
12. Determine whether a native or existing component is already sufficient.

Do not install duplicate libraries.

Do not install another icon library merely because a copied shadcn example uses it.

Do not replace the existing theme system.

Do not alter global package versions without direct evidence and authorization.

Record every dependency added and why it was necessary.

## 11. shadcn Integration Standard

Every adopted shadcn primitive must:

- use existing SNS semantic tokens
- work in Light and Dark themes
- preserve keyboard navigation
- preserve visible focus states
- preserve accessible names
- preserve disabled states
- work at supported mobile widths
- support real repository data
- preserve loading, empty, error, and unavailable states
- avoid hardcoded patient information
- avoid hardcoded workflow conclusions
- avoid creating new business logic

Prefer thin SNS wrapper components over repeated direct styling.

Examples:

- SnsCard wrapping Card
- SnsStatusBadge wrapping Badge
- SnsClinicalAlert wrapping Alert
- SnsDrawer wrapping Sheet or Drawer
- SnsDataTable using Table primitives
- RnicaCard using the SNS wrapper system

Do not create wrappers that merely rename shadcn without enforcing SNS tokens or interaction standards.

## 12. Theme and Token Rule

All new UI must use the existing SNS Light and Dark theme architecture.

Do not create RNICA-only themes.

Do not hardcode dark colors.

Do not build Light theme through inversion.

Use existing semantic tokens or add new semantic tokens only when an actual design need is not represented.

Required token categories include:

- application background
- navigation background
- surface
- raised surface
- inset surface
- border
- primary text
- secondary text
- muted text
- primary accent
- secondary accent
- information
- success
- warning
- critical/error
- AI advisory
- selected state
- hover state
- focus state
- disabled state
- overlay
- shadow

A new token requires:

- documented purpose
- Light value
- Dark value
- affected components
- contrast verification
- no equivalent existing token

## 13. Four-Mode Verification

Every redesigned screen must be verified in:

1. Desktop Light
2. Desktop Dark
3. Mobile Light
4. Mobile Dark

Source inspection is not visual verification.

Computed styles alone are not complete visual verification.

Every mode must be exercised in the running application.

Verify:

- layout
- information hierarchy
- theme
- contrast
- typography
- card composition
- navigation
- selected state
- scrolling
- long text
- loading
- empty state
- error state
- disabled state
- keyboard use
- focus visibility
- data preservation
- theme switching
- mobile access to required controls

If screenshot capture is unavailable, explicitly state that visual parity remains NOT VERIFIED. DOM inspection may support implementation validation but cannot be reported as Figma parity.

## 14. Screen Completion Rule

A screen is not complete because:

- a route exists
- a component renders
- data loads
- tests pass
- the build passes
- CSS tokens resolve
- a navigation item exists

A screen is complete only when:

- the approved composition is implemented
- legacy presentation is no longer dominant
- real repository data is connected
- existing behavior is preserved
- all four modes are verified
- relevant tests pass
- the production build passes
- no critical defect exists
- remaining variances are documented

## 15. Data-Integrity Stop Conditions

Stop the affected implementation immediately if any of these occur:

- unexpected record creation
- data loss
- cross-patient data
- cross-tenant data
- save failure
- autosave regression
- duplicate draft creation
- unauthorized access
- Lock bypass
- amendment loss
- signature loss
- audit-history loss
- migration drift
- destructive test behavior
- Patient Story mutating source data
- theme switching changing clinical state

Preserve evidence.

Reproduce safely.

Use an isolated test target where possible.

Do not delete records merely to hide a defect.

Do not continue visual work over an active data-integrity defect.

## 16. Schema and Migration Rule

Before recommending a schema change:

1. Inspect models.
2. Inspect migration history.
3. Inspect current migration head.
4. Inspect the actual target database.
5. Inspect JSON or form-data storage.
6. Inspect API and service mappings.
7. Determine whether the issue is presentation, validation, mapping, fixture drift, or schema.

Use forward-only revisions.

Do not rewrite migration history.

Do not create a migration when an existing migration only needs to be applied to the correct database.

## 17. Commit Discipline

Before editing:

- record branch
- record commit SHA
- record git status
- identify prior modified and untracked work

During implementation:

- preserve unrelated work
- avoid broad formatting changes
- do not reset or clean the working tree
- do not silently overwrite existing documentation
- keep defect remediation separate from visual redesign when practical

Before commit:

- inspect complete diff
- list changed files
- confirm scope
- run targeted tests
- run applicable regression tests
- run production build
- verify no credential or secret was added
- verify no sample patient data was hardcoded
- verify documentation status
- verify the session checklist result

Do not commit a checkpoint marked FAIL.

## 18. Mandatory Session-Start Response Template

Every implementation session must begin with the following completed response.

The agent must fill every field.

Use NOT FOUND, NOT APPLICABLE, NOT VERIFIED, or BLOCKED when appropriate.

Blank fields are prohibited.

```text
SNS SESSION START

SESSION GATE:
PASS / FAIL

REPOSITORY
- Repository root:
- Current branch:
- Current commit SHA:
- Worktree:
- Active PR:
- Git status:
- Staged files:
- Modified files:
- Untracked files:

ACTIVE WORKSTREAM
- Platform:
- Feature or workflow:
- Current phase:
- Current checkpoint:
- Current screen or service:
- Last completed item:
- Next authorized item:

AUTHORITY REFRESH
- Repository constitution reviewed:
- Source-of-truth documents reviewed:
- Implementation-authority documents reviewed:
- Workflow-authority documents reviewed:
- Screen-authority documents reviewed:
- Data-mapping documents reviewed:
- Design references reviewed:
- Handoff or phased plan reviewed:

CURRENT IMPLEMENTATION
- Route inspected:
- Parent shell inspected:
- Primary component inspected:
- Data-loading path inspected:
- API client inspected:
- Backend route inspected:
- Backend service inspected:
- Persistence path inspected:
- Validation inspected:
- Authorization inspected:
- Theme and tokens inspected:
- Existing tests inspected:

REUSE REVIEW
- Existing components found:
- Existing hooks found:
- Existing utilities found:
- Existing APIs found:
- Existing tokens found:
- Existing tests found:
- New code genuinely required:

SHADCN REVIEW
- shadcn already configured:
- package.json reviewed:
- lockfile reviewed:
- Tailwind configuration reviewed:
- aliases reviewed:
- class-merging utility reviewed:
- icon library reviewed:
- existing equivalent primitives found:
- dependencies proposed:
- reason each dependency is required:

DEFECT STATE
- Open defects:
- Closed defects:
- Blocked items:
- Data-integrity risks:
- Schema or migration impact:
- Security or authorization impact:

IMPLEMENTATION DECISION
- Work authorized:
- Files expected to change:
- Tests expected to run:
- Build command:
- Stop conditions:
- Session gate explanation:

REPOSITORY REFRESH COMPLETE:
YES / NO
```
