# SNS DESIGN SYSTEM REFERENCE — FIGMA-APPROVED VISUAL BASELINE

STATUS: REFERENCE ONLY — FOR COMPARISON WHEN REVIEWING SUBMITTED JSX/
TAILWIND FILES. NOT AN IMPLEMENTATION AUTHORIZATION. DOES NOT ITSELF
CREATE, CHANGE, OR APPROVE ANY COMPONENT.

## PURPOSE

The user is providing approved Figma reference screenshots covering
Biller Platform pages (Agency Coverage & Workload detail, Organization
& Teams, Access Denied, User Access Detail) in both dark and light
theme, per the locked `THEME_SYSTEM_REQUIREMENTS.md`. This document
records the visual patterns observed in those references so that any
JSX/Tailwind file submitted later can be checked for conformance
before being merged — colors, typography, spacing, component shapes,
and dark/light parity, not business logic.

Reference images are stored in this session's persistent file store
(`figma-reference/`), not in the repository, since they are design
artifacts rather than source content. This document is the durable,
repo-tracked description of what they show.

## 1. LAYOUT SHELL (both themes)

- Fixed left sidebar: brand block ("SNS Tech Solutions" / platform
  name subtitle, e.g. "BILLER PLATFORM"), an "ASSIGNED AGENCY SCOPE"
  dropdown, a "DASHBOARD" nav group, and a "BILLING ORGANIZATION" nav
  group (Organization & Teams / Agency Coverage & Workload / Access
  Administration) with the active item highlighted (light teal/green
  background + left accent bar in light theme).
- Bottom-of-sidebar persistent "HIPAA AUDIT ACTIVE" badge (amber/
  orange), present on every screen — this must not be page-specific.
- Main content: a breadcrumb-style back link ("← Back to ..."), a
  page `<h1>` with a small pill/badge next to it (status or category
  label), a one-line gray subtitle, then a metrics row of 3-4 stat
  cards, then section cards below.
- Page footer: "Platform Version X.Y.Z | Last Sync: <date>" on the
  left, a policy statement on the right ("Access and capability
  reviews follow configured billing-organization policy.").

## 2. COLOR SYSTEM (from observed screens)

**Light theme**
- Page background: white / very light gray (`#F8FAFC`-ish sidebar vs.
  white main canvas).
- Primary text: near-black (`#0F172A`-ish).
- Secondary/label text: mid gray (`#64748B`-ish), used for all-caps
  field labels ("ACTIVE PATIENTS", "COVERAGE STATUS", etc.).
- Primary accent (teal/green): used for the active nav item, page-
  title status pill backgrounds, primary numeric highlight text (e.g.
  "Full Coverage", "Active" badges), and primary buttons (e.g.
  "Request Access" filled teal button).
- Success/Active badges: light green background, dark green text
  ("ACTIVE", "✓ YES").
- Warning badges: light amber/orange background, amber text
  ("PENDING REVIEW", HIPAA badge).
- Error/Denied badges and icon: red background circle + red icon
  outline, red pill badge ("CAPABILITY NOT GRANTED").
- Card borders: thin light-gray 1px borders, white/near-white card
  fill, subtle shadow — cards are never pure white-on-white without a
  visible border/separation (consistent with
  `THEME_SYSTEM_REQUIREMENTS.md`'s "light theme cards must not become
  pure white without visible separation" rule).

**Dark theme (Access Denied dark reference)**
- Page background: very dark navy/near-black (`#0B1220`-ish), not
  pure black — consistent with the locked rule "dark theme cards must
  not become pure black."
- Card fill: slightly lighter dark navy than the page background, so
  the card is still visually distinct from the page (same separation
  principle as light theme, inverted).
- Primary text: near-white/light gray.
- Secondary text: muted blue-gray.
- Error state: same semantic red, adapted for dark background (red
  outline circle/icon, red-bordered pill badge with lighter red text
  for contrast) — same meaning, adapted contrast, per the locked
  Status Color System rule ("theme changes may alter colors/contrast...
  must not alter... business rules").
- Primary button (Request Access): teal-bordered/teal-text button on
  dark surface rather than a solid fill — an example of the same
  action rendering as a different, theme-appropriate visual treatment
  while remaining the identical action.

## 3. TYPOGRAPHY

- Page title: large, bold, sans-serif (looks like a rounded/geometric
  sans — e.g. similar to Poppins/Inter Bold), dark/near-black in light
  theme, white in dark theme.
- Section headers (e.g. "CURRENT ASSIGNMENTS", "Assigned Capabilities"):
  bold, smaller than page title, often paired with an all-caps
  eyebrow label above and a small right-aligned badge/pill.
  Two-tier heading pattern: a small **all-caps gray eyebrow label**
  (e.g. "AUDIT TRAIL") followed immediately by a larger **bold section
  title** (e.g. "Recent Assignment Activity") — every major card on
  every screen follows this same two-line header pattern.
- Field labels: all-caps, small, gray, letter-spaced.
- Field values: bold or semi-bold, dark/near-black (light) or white
  (dark).
- Body/description text: regular weight, gray, smaller size.

## 4. COMPONENT PATTERNS

- **Stat card row**: 3-4 equal-width bordered cards, each with an
  all-caps label on top and a large bold number/value below.
- **Status pill/badge**: rounded-full, small padding, colored
  background matching semantic meaning (green/amber/red/neutral),
  bold colored text — used identically for coverage status, DDE
  authorization, capability status, access-denied state, and org
  section labels (just recolored per meaning).
- **List/table rows with a right-aligned status badge**: staff
  assignment cards and table rows consistently place the status pill
  at the far right of the row.
- **Nested "sub-card" panel inside a card**: a slightly shaded (light
  gray / darker-navy) inset panel inside a white/dark card, used for
  secondary supporting data (e.g. "Organization-Wide Staff Workload"
  inside a staff assignment card, "Scope: Medicare Coverage Only"
  inside a backup-contact card).
- **Timeline / audit trail list**: a vertical line with dot markers
  per entry, date in teal on the left, bold title, gray description
  below — used identically for "Recent Assignment Activity" and
  "Recent Access Activity."
- **Access Denied full-page state**: centered icon in a colored
  circle, large bold heading, one-line gray description, a bordered
  "Security Context Details" panel (label/value rows), a bold
  statement + gray sub-statement, then two buttons side by side
  (secondary "← Return to Dashboard" outline button, primary "Request
  Access →" filled/accented button), then a final gray footnote line.
  This exact structure/order is present in both the light and dark
  reference and must be preserved identically apart from color/
  contrast treatment, per the locked Section (Unauthorized Access
  State) architecture.

## 5. THEME PARITY CHECKLIST (derived from these references)

When a submitted JSX/Tailwind file is reviewed against this baseline,
confirm:

- [ ] Uses platform theme tokens/variables (per
      `THEME_SYSTEM_REQUIREMENTS.md`) rather than hardcoded hex colors.
- [ ] Every status badge/pill has a light-theme and dark-theme
      treatment with identical semantic color mapping (green=success,
      amber=warning, red=error/critical, neutral=informational).
- [ ] Card surfaces are never pure white (light) or pure black (dark)
      and remain visibly separated from the page background.
- [ ] Two-tier header pattern (all-caps eyebrow label + bold title)
      is used consistently for section headers.
- [ ] Stat-card row, timeline/audit-trail list, and nested sub-card
      panel patterns match the shapes described above rather than
      introducing new ad hoc layouts for the same kind of data.
- [ ] Access-denied/error states fully replace the workspace (never a
      partial/degraded render) and preserve the exact section order
      above.
- [ ] Sidebar shell (brand block, agency scope selector, nav groups,
      HIPAA badge, footer) is not duplicated or reimplemented
      per-page — it is a shared layout, not page-specific markup.

## 6. REFERENCE IMAGE INVENTORY

Stored in this session's persistent file store under
`figma-reference/` (not committed to the repository):

| File | Page | Theme |
|---|---|---|
| `01-agency-detail-light.png` | Agency Coverage & Workload → Agency Detail (Angela Hospice) | Light |
| `02-organization-teams-light.png` | Organization & Teams | Light |
| `03-access-denied-light.png` | Unauthorized Access State | Light |
| `04-user-access-detail-light.png` | User Access Detail (Robert Park) | Light |
| `05-access-denied-dark.png` | Unauthorized Access State | Dark |
| `06-image.png` through `10-image.png` | Additional approved references (not yet individually reviewed — attached beyond this pass's image-view limit) | Unreviewed |

**Note:** five additional images (`06`–`10`) were attached in the same
message but could not be individually inspected in this pass (session
image-view limit reached). They are saved for later reference; if they
cover pages/themes not already described above, revisit them before
finalizing this baseline.

## STATUS

Documentation/reference only. No schema, migration, model, service,
route, or UI component created or changed. This document does not
authorize implementation of any page — it exists so that future JSX/
Tailwind submissions can be checked against the approved visual
baseline once implementation is separately authorized.
