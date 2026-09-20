# THEME SYSTEM REQUIREMENTS

STATUS: GLOBAL IMPLEMENTATION RULE — LOCKED

PRIORITY: REQUIRED

APPLIES TO: SNS Tech Solutions Owner Platform, Biller Platform, SNS
Hospice Solutions Tenant Platform — ALL CURRENT AND FUTURE UI
DEVELOPMENT.

This document codifies a permanent, platform-wide rule. It is not
scoped to a single page or module and is not superseded by
page-specific specs elsewhere in `/docs`. Every current and future UI
deliverable across all three platforms must comply.

---

## 1. THEME ARCHITECTURE

All UI components, pages, dialogs, drawers, modals, workflows,
dashboards, reports, grids, and future features must support:

1. Dark Theme
2. Light Theme

Theme support is not optional. Theme support must be implemented as a
**platform-level capability**, not page-by-page customization.

- No page may be developed as dark-theme only.
- No page may be developed as light-theme only.

All approved Figma designs represent the **DARK THEME visual
reference**. An equivalent **LIGHT THEME** implementation must be
created for every approved Figma screen, even when only the dark
version is shown. Lack of a light-theme mockup is never approval to
omit light-theme support.

## 2. THEME SWITCHING

Users must be able to select:
- System Default
- Dark Theme
- Light Theme

Requirements:
- Theme selection must persist per user.
- Theme selection must remain consistent across the Owner Platform,
  Biller Platform, and Tenant Platform.
- Switching themes must not require logout.
- Switching themes must not require a page refresh.

## 3. DESIGN PARITY REQUIREMENT

Dark Theme and Light Theme must provide **identical functionality**.

Theme changes may alter: colors, contrast, borders, shadows, surface
styling.

Theme changes must **never** alter: navigation structure, permissions,
layouts, capabilities, workflow behavior, access controls, business
rules.

## 4. ACCESSIBILITY

Both themes must meet accessibility requirements:
- Readable text
- High-contrast status indicators
- Keyboard navigation
- Focus visibility
- Screen reader compatibility

Status colors must remain distinguishable in both themes.

## 5. STATUS COLOR SYSTEM

The same semantic meaning must exist in both themes. Developers must
never rely on color alone — status text must always be visible
alongside the color.

| Semantic Meaning | Example Statuses | Palette |
|---|---|---|
| Success | ACTIVE, APPROVED, AUTHORIZED, READY | Approved success palette |
| Warning | PENDING, UNDER REVIEW, REVIEW REQUIRED, CONDITIONAL | Approved warning palette |
| Error | DENIED, REVOKED, EXPIRED, BLOCKED, CRITICAL | Approved error palette |
| Neutral | INACTIVE, NOT REQUIRED, INFORMATIONAL | Approved neutral palette |

## 6. TABLES

All tables must support both themes with:
- Readable headers
- Readable row text
- Readable hover states
- Selected row state
- Keyboard focus state

Row striping, if used, must adapt correctly to the active theme.

## 7. CARDS

All cards must support dark surface styling and light surface
styling.
- Dark theme cards must not become pure black.
- Light theme cards must not become pure white without visible
  separation.
- Card hierarchy must remain visually obvious.

## 8. MODALS

All dialogs, drawers, and modals must support a dark overlay and a
light overlay. Focus indicators must remain visible in both themes.

## 9. AUDIT AND GOVERNANCE PAGES

Governance pages contain warnings, errors, review states, and
compliance notices. These indicators must remain clearly visible in
both themes. Do not reduce visibility of: Overdue Reviews, Expired DDE
Authorizations, Access Denials, Audit Findings, Critical Risk
Indicators.

## 10. CHARTS AND REPORTING

All charts (Dashboards, Analytics, Billing Readiness, Workload
Intelligence, Audit Reporting, Financial Reporting) must support both
themes. Chart colors must remain readable in both themes. Theme
changes must not distort meaning.

## 11. EMPTY STATES

All empty states (No Records, No Findings, No Claims, No Assignments,
No Authorization Records) must support both themes with readable text.

## 12. ERROR STATES

All error states (Access Denied, System Error, Network Error,
Permission Error, Validation Error) must support both themes with
prominent visibility.

## 13. IMPLEMENTATION REQUIREMENT

A centralized theme system must be used. Do not hardcode colors
directly into individual pages. Use platform theme tokens, platform
theme variables, and platform design system components. New features
must automatically inherit Dark Theme and Light Theme support without
requiring redesign.

## 14. DEFINITION OF DONE

A feature is not considered complete unless:
- ✓ Dark Theme works
- ✓ Light Theme works
- ✓ Theme switching works
- ✓ Accessibility remains compliant
- ✓ Status indicators remain readable
- ✓ All screens preserve functional parity

Any feature delivered with only one theme is incomplete and not
production ready.

---

## 15. REPOSITORY DISCOVERY — EXISTING THEME INFRASTRUCTURE

Before any future work claims to satisfy this rule, the following
existing infrastructure was identified and classified.

### 15.1 Existing theme engine — REUSE

- **File:** `sns-emr-frontend/src/theme/theme.tsx`
- **What exists:** a working `ThemeModeProvider` / `useThemeMode()`
  React context that already implements a two-mode (`"dark"` |
  `"light"`) token system:
  - `THEME_VARS` defines a parallel dark/light palette (`bg`, `bgAlt`,
    `card`, `cardSoft`, `border`, `teal`, `white`, `muted`, `dim`,
    `green`, `blue`, `purple`, `orange`, `red`, `yellow`, `pink`,
    `shadow`) for each mode.
  - `applyThemeMode(mode)` writes each token to `document.documentElement`
    as a CSS custom property (`--sns-*`), sets `root.dataset.theme`,
    and updates `document.body` background/color directly.
  - Theme selection is persisted via `localStorage`
    (`sns-hospice-theme-mode`), satisfying the "must persist per user"
    (device-level) requirement in Section 2, though not yet
    server-side/per-account persisted (see Section 15.3, Gap 2).
  - Mounted once at the true application root —
    `sns-emr-frontend/src/main.tsx` wraps the entire `<App />` tree in
    `<ThemeModeProvider>`, confirming this is already a platform-level
    capability, not a page-level one, consistent with Section 1's
    requirement.
- **Current adoption:** `useThemeMode()` is already consumed in 20+
  files today, including clinical chart components
  (`charts/PatientChartSidebar.jsx`, `charts/PatientFacesheet.jsx`,
  `charts/PatientChart.jsx`, `charts/IssuesOutcomesBoard.tsx`),
  assessment/ICA components (`assessments/MSWComprehensiveAssessment.jsx`,
  `components/MSWICA.jsx`, `components/SCICA.jsx`, `components/RNICA.jsx`),
  intake workflow pages (`intake/ComplianceHopeBoard.jsx`,
  `intake/ChartCompletionChecklist.jsx`, `intake/HopeReport.jsx`,
  `intake/ConsentNotifications.jsx`, `intake/StaffAssignment.jsx`,
  `intake/PatientNotificationNonCovered.jsx`), `components/VisitNotes.jsx`,
  and both platform dashboards — `owner/OwnerDashboard.jsx` and
  `tenant/TenantDashboard.jsx` (both already expose a
  `toggleMode`-driven theme switch in their header UI).
- **Classification: REUSE.** This is the correct, already-proven
  foundation. It must not be duplicated or replaced with a second
  theme mechanism. All future Owner Platform, Biller Platform, and
  Tenant Platform UI work must consume `useThemeMode()` /
  `--sns-*` CSS variables from this single source, per Section 13
  ("do not hardcode colors directly into individual pages").
- **Repository Evidence:** `sns-emr-frontend/src/theme/theme.tsx`,
  `sns-emr-frontend/src/main.tsx`,
  `sns-emr-frontend/src/owner/shell/tailwind.css` (in-file comment
  confirms Tailwind utility classes are expected to cooperate with
  "the existing light/dark toggle" and `applyThemeMode()`).

### 15.2 Biller Platform frontend — NOT YET BUILT

- **Finding:** No `sns-emr-frontend/src/biller` directory exists.
  Consistent with every prior Biller Platform discovery in this
  documentation set, the Biller Platform frontend has not been
  implemented yet — only the specification documents under
  `docs/biller-platform/` exist today.
- **Classification: N/A (nothing to classify) — forward requirement
  only.** When Biller Platform pages are eventually implemented (per
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`), they must be
  built directly on top of the existing `theme/theme.tsx` engine from
  the very first commit. Biller Platform must **not** introduce its
  own parallel theme system, and must not be built dark-theme-only
  even though the approved Figma references are dark-theme designs
  (per Section 1's Figma Interpretation Rule).

### 15.3 Gaps against this rule in the existing engine

The existing engine is a strong foundation but does not yet fully
satisfy every requirement in this document. These are documented as
open gaps, not yet resolved:

1. **No "System Default" mode.** `ThemeMode` is currently typed as
   `"dark" | "light"` only; there is no third option that follows the
   OS-level `prefers-color-scheme` media query. Section 2 requires a
   "System Default" choice. **Classification: EXTEND** —
   `theme/theme.tsx` needs a `"system"` mode that resolves to the
   OS preference and stays reactive to OS-level changes.
2. **No per-account (server-side) persistence.** Persistence today is
   `localStorage`-only (device-scoped), not tied to the authenticated
   user's account, so switching devices does not carry the same theme
   choice. Section 2 requires persistence "per user." **Classification:
   EXTEND** — requires a small backend preference field/endpoint (or
   reuse of an existing user-preferences mechanism, if one exists —
   not yet confirmed) plus a hydrate-on-login path in the frontend.
3. **Adoption is partial, not platform-wide.** `useThemeMode()` is
   consumed by many clinical/tenant components today, but not
   universally verified across every existing Owner Platform and
   Tenant Platform screen (a full page-by-page dark/light QA sweep
   has not been performed as part of this discovery). **Classification:
   VERIFY (not yet CREATE/EXTEND)** — a follow-up audit is recommended
   before this rule can be marked fully satisfied for existing pages,
   separate from the forward-looking requirement that all *new* work
   comply from day one.

No code changes were made while producing this document. Items in
Section 15.3 are documented as open gaps for a future, explicitly
authorized implementation pass — not authorization to begin that work
now.

---

## 16. RELATIONSHIP TO OTHER DOCUMENTS

This rule applies on top of, and does not replace, every page-level
spec already locked in this documentation set (`BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`,
`docs/room-board/*`, `docs/communications/*`, and all future pages).
Every current and future page-level spec is implicitly amended to
require dark/light parity per this document, even where the
page-level spec does not repeat that requirement explicitly.

---

## 17. CHANGE LOG

| Date | Change |
|---|---|
| 2026-09-18 | Document created. Captured the global Theme System Requirements rule (Dark Theme + Light Theme parity across Owner Platform, Biller Platform, and Tenant Platform) as a permanent, locked governance rule. Performed repository discovery of the existing theme engine (`sns-emr-frontend/src/theme/theme.tsx`, mounted platform-wide via `main.tsx`, already consumed by 20+ files including both Owner and Tenant dashboards) and classified it REUSE. Confirmed the Biller Platform frontend does not yet exist. Documented three open gaps against full compliance: no "System Default" mode, no per-account (server-side) persistence, and unverified platform-wide adoption — none resolved in this pass; documentation only, no code changes made. |
