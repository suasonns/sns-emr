# SNS RNICA SHADCN/UI ADOPTION RULE

STATUS: GOVERNANCE RULE — IMPLEMENTED. Formalizes a decision already
executed on branch `suasonns-feature/update-recertification-toggle`
(Draft PR #170): refactoring `AssessmentTypeToggle.jsx` and
`MedicareNonCoveredReviewPanel.jsx` from hand-rolled inline-styled
markup onto shadcn/ui primitives.

## 1. RULE

shadcn/ui is the **preferred primitive toolkit** for new interactive
RNICA UI (toggles, selects, checkboxes, text inputs, alerts, cards,
badges, buttons, labels). shadcn/ui components are never used with
their default/library palette or as pre-built templates/dashboards —
every primitive **must** be restyled exclusively onto the existing
`rnica-*` Tailwind token namespace (`sns-emr-frontend/tailwind.config.js`,
backed by `--sns-*` CSS custom properties switched via `data-theme`).
This is consistent with, and does not relax, the repository
constitution's rule that shadcn/ui is "a primitive toolkit only... never
shadcn templates, dashboards, or generated layouts, and never a
competing design system."

This rule governs **implementation only**. It does not authorize any
redesign of clinical fields, validation, response values, or workflow
behavior — see `docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
and the RNICA preservation rule for the controlling scope boundary.

## 2. INSTALLED PRIMITIVES (`sns-emr-frontend/src/components/ui/`)

| File | Backing | Notes |
|---|---|---|
| `button.tsx` | plain | pre-existing |
| `card.tsx` | plain | pre-existing |
| `badge.tsx` | plain | pre-existing |
| `label.tsx` | `@radix-ui/react-label` | new |
| `radio-group.tsx` | `@radix-ui/react-radio-group` | new |
| `select.tsx` | `@radix-ui/react-select` | new — available for future use; see §4 for why it is *not* used by `MedicareNonCoveredReviewPanel.jsx` |
| `checkbox.tsx` | `@radix-ui/react-checkbox` | new |
| `input.tsx` | plain | new |
| `textarea.tsx` | plain | new |
| `alert.tsx` | plain | new |

All Radix dependencies (`@radix-ui/react-radio-group`, `@radix-ui/react-label`,
`@radix-ui/react-select`, `@radix-ui/react-checkbox`) are installed via
`npm install ... --save` in `sns-emr-frontend/package.json`.

## 3. `components.json`

`sns-emr-frontend/components.json` declares the shadcn/ui style
configuration (`new-york` style, Tailwind config/CSS entry point,
`lucide` icon library, `cssVariables: true`). **Aliases intentionally
use relative-style paths** (`src/components`, `src/lib/utils`, etc.)
rather than a `@/...` path alias, because **no `@` alias exists
anywhere in this repository** (`tsconfig.app.json`, `vite.config.ts`
both use only relative imports). All hand-authored primitives in this
change follow that existing convention. If the `npx shadcn` CLI is run
against this repo in the future, generated imports must be converted
from `@/...` to relative paths by hand before merging — the CLI will
not know an alias does not exist.

## 4. KNOWN, DELIBERATE EXCEPTION: native `<select>` in the Medicare panel

`MedicareNonCoveredReviewPanel.jsx`'s "Determination" and "Election
Addendum" dropdowns use a **restyled native `<select>`**, not the
Radix-based `ui/select.tsx` primitive, even though `ui/select.tsx`
exists and is available. Reasons, recorded here so this is never
mistaken for an oversight:

- The existing test suite (`MedicareNonCoveredReviewPanel.test.jsx`)
  validates behavior with native `fireEvent.change(select, { target:
  { value } })` semantics, which a Radix listbox does not support
  (Radix Select is composed of buttons/divs, not a native `<select>`).
  Preserving this meant keeping the native element.
- Radix's `Select` renders through a `Portal` and depends on pointer-
  capture APIs that require extra polyfilling under jsdom/Vitest;
  avoiding that was a reasonable complexity trade for a short, flat
  option list.
- A native `<select>` gives equivalent or better accessibility for a
  short flat list (built-in keyboard/typeahead/AT support) with zero
  custom ARIA wiring required.

`ui/select.tsx` remains in the component library for any future RNICA
UI that needs a richer, searchable, or multi-level listbox.

## 5. ACCESSIBILITY TESTING

`jest-axe` is installed (`sns-emr-frontend/package.json`,
devDependency) and wired globally via
`sns-emr-frontend/src/test/setupTests.js`
(`expect.extend(toHaveNoViolations)`), so any test file can assert
`expect(await axe(container)).toHaveNoViolations()` with no per-file
setup. `AssessmentTypeToggle.test.jsx` and
`MedicareNonCoveredReviewPanel.test.jsx` each include axe-driven
accessibility assertions across their enabled/disabled/locked render
states, in addition to their pre-existing behavioral tests.

## 6. SERVER-SIDE PURPOSE IMMUTABILITY (related, same change)

`backend/app/api/visits.py`'s `update_rnica_assessment` (PUT
`/rnica/{assessment_id}`) now explicitly rejects (HTTP 409) any payload
that attempts to change `assessment_type`/`assessmentSubtype` after
creation, with a structured audit log entry
(`RNICA_ASSESSMENT_TYPE_CHANGE_REJECTED`). `assessment_type` was
already structurally immutable (only `save_rnica_assessment`, the
one-time creation endpoint, ever wrote it) — this change adds an
explicit guard/error/audit trail rather than closing an actual mutation
vulnerability. See `backend/tests/test_rnica_finalization.py` for
coverage (omitted-key no-op, rejected via both payload key variants,
allowed when resending the same value, audit log written on
rejection).

## 7. NON-GOALS / OUT OF SCOPE

This rule does not introduce, approve, or reference a "Body Systems"
registry, comparison engine, or any multi-table assessment
architecture. Per the controlling product decision, there is **one**
Comprehensive RN Assessment, **one** Body Systems-free flat form, and
**one** toggle (`AssessmentTypeToggle.jsx` → `assessment_type`). Any
future Body Systems architecture work is governed separately by
`docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md`
and `sns-emr-frontend/src/domain/body-systems/` (per
`docs/governance/SNS_RULES_MANIFEST.json`'s `featureAuthorities`) and is
untouched by this change.

## STATUS

Implemented. No clinical fields, validation, response values, or
workflow behavior changed. No new design-system tokens introduced —
every new/refactored component uses only the existing `rnica-*`
namespace in `tailwind.config.js`.
