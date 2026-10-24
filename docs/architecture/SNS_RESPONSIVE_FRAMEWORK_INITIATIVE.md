# SNS RESPONSIVE FRAMEWORK INITIATIVE (DEFERRED)

**Status:** DEFERRED — Product Owner directive (2026-10-14), "Responsive
Defect Deferment, RNICA Completion Takes Priority." RNICA discipline
completion (GI, Nutrition, GU, Integumentary, Musculoskeletal, Safety,
remaining workflow items) takes priority. This initiative resumes after
RNICA documentation/disciplines are frozen, per the approved sequence:
1. Finish RNICA documentation
2. Finish all disciplines
3. Freeze workflows
4. Ontology expansion
5. AI expansion
6. **Platform-wide responsive initiative (this document)**

**Correction (2026-10-23 stabilization pass):** the RNICA shell CSS fix
(Section 3) and the GI/Cardiovascular `segmentedTriState` field-grid fix
(Section 4) described below are **now committed** and reachable from the
`RNICA-V1-FIELD-TEST-CANDIDATE` baseline (`1c6358a6`) — confirmed present
in `RNICACommandWorkspace.css` and `RNICA.jsx` in the current working
tree, which is otherwise clean. They are no longer uncommitted
working-tree-only edits. Sections 5–7 (Tenant/Billing/Owner) remain
accurately described as not yet implemented.

---

## 1. Scope

Full platform-wide responsive remediation, covering:

- RNICA (Body Systems workspace shell) — **root cause fixed, Phase 1 + 2
  complete, see Section 3**
- Tenant platform — **audited, fix NOT implemented (deferred)**
- Billing platform — not yet audited
- Owner platform — not yet audited (closest to compliant on prior
  inspection; fluid `auto-fit` grid + `min(1180px,100%)`)
- Shared dashboards, Orders, Medication workflows, Reports — not yet
  audited

Required validation device classes (per Product Owner, requested
repeatedly over ~10 months):

- 34" monitor (3440px effective)
- 15" laptop
- 13" laptop
- iPad
- iPhone
- Split-screen / quarter-screen / docked window widths

Minimum verification width matrix used during RNICA remediation:
3440 / 2560 / 1920 / 1600 / 1536 / 1440 / 1366 / 1280 / 1024 / 768 / 390 px.

---

## 2. Platform Ownership Finding (established, do not re-investigate)

No shared layout/rail framework exists across RNICA, Tenant, Billing, and
Owner. Each platform area is independently implemented:

| Platform | Shell file | Mechanism | Breakpoint behavior |
|---|---|---|---|
| RNICA | `RNICACommandWorkspace.css` | CSS Grid (`.rnica-bodysystems`) | **Fixed prior to fix** (see Section 3) |
| Tenant | `src/tenant/TenantDashboard.jsx` | Inline styles, hardcoded `width: 220` sidebar | **None — no media query anywhere in the file** |
| Billing | `src/components/billing/BillerShell.tsx` | MUI `sx` props, hardcoded `width: 264` sidebar | **None found on prior inspection** |
| Owner | `src/.../PortalShell.tsx` (via `OwnerDashboard.tsx`) | Inline styles, fluid `auto-fit` grid + `min(1180px, 100%)` | Closest to already-correct behavior |

Conclusion: this is **not** one shared root cause. Each area needs its own
targeted fix; there is no single shared component to patch once for the
whole platform.

---

## 3. RNICA Body Systems Shell — ROOT CAUSE FIXED (do not revert)

### 3.1 Root cause

`.rnica-bodysystems` (in `RNICACommandWorkspace.css`) was a CSS Grid:

```css
.rnica-bodysystems {
  grid-template-columns: minmax(0, 1fr) 18rem; /* hard-fixed 288px rail */
}
@media (max-width: 1100px) {
  /* single cliff: rail vanishes entirely below 1100px */
}
```

Above 1100px, the "Structured Findings" rail always consumed exactly
288px regardless of total available width, so the main assessment column
absorbed the *entire* width loss as the viewport shrank (e.g. 702px main
width at 1536px viewport → 446px main width at 1280px viewport). Below
1100px the rail vanished entirely and main width jumped back up (734px at
1024px). This produced a **non-monotonic** relationship — some wider
windows (1280px) were more cramped than both narrower (1024px) and wider
(1536px) windows. This was the exact defect reported by the Product
Owner.

### 3.2 Fix implemented (uncommitted, in working tree)

File: `sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.css`

- `.rnica-bodysystems` `grid-template-columns` changed from
  `minmax(0, 1fr) 18rem` to `minmax(0, 1fr) clamp(12rem, 22%, 20rem)` —
  rail now scales with a percentage of the grid's own rendered width,
  floor 192px / ceiling 320px, guaranteeing the main column's width is
  monotonically non-decreasing as total width increases.
- Full-stack `@media` breakpoint lowered from `max-width: 1100px` to
  `max-width: 700px` (below 1100px the nav is already hamburger-collapsed
  so viewport ≈ content width, making a simple media query accurate
  again; 700px keeps iPad portrait at 768px in fluid 2-column mode while
  true phone widths still fully stack).
- `.rnica-bodysystems--rail-collapsed` (icon-only `2.25rem` rail variant)
  left untouched — intentional separate minimal state, not part of the
  cliff bug.

### 3.3 Verification (post-fix, confirmed monotonic)

Main assessment column width by viewport (px):

| Viewport | 3440 | 2560 | 1920 | 1600 | 1536 | 1440 | 1366 | 1280 | 1024 | 768 | 390 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Main width | 2574 | 1694 | 1068 | 819 | 769 | 694 | 628 | 542 | 526 | 540 | 369 |

Monotonic non-increasing as viewport shrinks, with one benign +14px
exception at 768px vs 1024px, attributable to an existing, legitimate
`.rnica-screen__content` padding-reduction rule at narrow widths (not a
layout defect — reported and accepted).

GI column counts (1/2/3-column `@container` breakpoints, unaffected by
this fix but re-verified for regression): 1/1/1/1/1/2/2/2/3/3/3 for
390→3440px — monotonic non-decreasing, no backwards cliffs.

Screenshots captured at 1024/1280/1440/1536px confirmed clean rendering,
no overlap, correct hamburger/nav behavior.

**User-approved, "Do not revert this work."**

---

## 4. GI Field-Grid Overlap — ROOT CAUSE FIXED (do not revert)

### 4.1 Root cause

`getFieldSpan()` (in `RNICA.jsx`) assigns a CSS grid column-span to each
rendered field based on its `type`. The `segmentedTriState` field type
(renders a fixed 3-button "Not Assessed"/"No"/"Yes" `FormSegmented` row,
used by GI's Ascites/Feeding Tube/Ostomy Present and Cardiovascular's
JVD/Edema/Chest Pain/Syncope) had **no explicit case**, so it fell to the
function's default span of 1 (~150px column). The nowrap "Not Assessed"
(or custom `unassessedLabel`, e.g. "Unable To Determine") button row
could not fit in a single ~150px auto-fit column, causing GI's Ascites
field to visually overflow past its own grid cell into the neighboring
column — concretely, "Abdominal Girth" bled into "Last BM Size" at
1536px viewport width. This is the same class of bug previously fixed for
`booleanPill` (long nowrap label defaulting to span 1).

### 4.2 Fix implemented (uncommitted, in working tree)

File: `sns-emr-frontend/src/components/RNICA.jsx`, `getFieldSpan()`

Added an explicit `segmentedTriState` case: computes the max label length
across "Not Assessed"/custom `unassessedLabel`, "No", "Yes" and returns
span 2 (maxLabelLen ≤ 20) or span 3 (longer), matching the existing
label-aware heuristic already used for `radio`/`segmented` fields. This
is a **generic, shared fix** — it applies to every `segmentedTriState`
field platform-wide (GI and Cardiovascular), not a GI-specific patch.

### 4.3 Verification

- 1536px (original defect site): confirmed resolved against the pre-fix
  screenshot (`scripts/responsive-audit-output/postfix-gi-1536.png`,
  which shows the overlapping "ABDOMINAL GIRTH"/"LAST BM SIZE" text).
- 1440px, 1600px, 1366px: all clean, no overlap
  (`scripts/responsive-audit-output/phase2-gi-*.png`).
- Cardiovascular (JVD — heavy `segmentedTriState` user): screenshot
  confirms no regression (`phase2-cv-1536.png`).
- Other field types defaulting to span 1 (`input`, `select`, `checkbox`,
  `note`, `legacyReadOnly`, unused `triState`, `gatedRadio`) reviewed —
  none pose the same overflow risk; `gatedRadio`'s one usage already has
  an explicit `fieldSpan: 2` override.

**GI is frozen per Product Owner directive pending this initiative's
resumption; no further responsive work on GI until then.**

---

## 5. Tenant Platform — AUDITED, FIX DEFERRED (do not implement yet)

File: `sns-emr-frontend/src/tenant/TenantDashboard.jsx`

```jsx
<div style={{ display: 'flex', minHeight: '100vh', ... }}>
  <div style={{ width: 220, background: COLORS.card, ... }}>
    {/* sidebar: logo, dark-mode toggle, nav items, user footer */}
  </div>
  <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
    <ActivePage ... />
  </div>
</div>
```

Findings:

- Sidebar is a **hardcoded 220px**, inline style, with **zero media
  queries anywhere in this file** — unlike RNICA's rail, it never
  collapses at any viewport width.
- Content area is `flex: 1` with no `min-width`/`max-width`, so it does
  shrink proportionally, but the sidebar unconditionally consumes 220px
  even at a 390px iPhone width, leaving ~170px for content — almost
  certainly unusable at phone/narrow-tablet widths.
- No audit yet performed of the individual Tenant pages
  (`DashboardOverview`, `PatientCensus`, `Referrals`, `Clinical`,
  `Analytics`, `AgencySettings`, `SecureInbox`, `Settings`) for their own
  internal fixed-width grids/tables.

**Proposed fix (not implemented):** add a narrow-width breakpoint
mirroring RNICA's working hamburger-collapse pattern, collapsing/hiding
the sidebar below approximately 700–768px.

**Explicitly deferred per this directive — do not begin implementation
until this initiative resumes.**

---

## 6. Billing Platform — NOT YET RE-AUDITED THIS PASS

File: `sns-emr-frontend/src/components/billing/BillerShell.tsx`

Prior-session finding (not re-verified this pass): MUI `sx` props,
hardcoded `width: 264` sidebar, no breakpoint found. Likely needs an
analogous fix to Tenant. **Full audit (container tree, page-level content
grids) not yet performed — do this first when the initiative resumes.**

---

## 7. Owner Platform — NOT YET RE-AUDITED THIS PASS

File: `src/.../PortalShell.tsx` (via `OwnerDashboard.tsx`)

Prior-session finding (not re-verified this pass): already uses a fluid
`auto-fit` grid + `min(1180px, 100%)` — closer to correct responsive
behavior than Tenant/Billing. May only need confirmation/minor polish
rather than a structural fix, but has not been screenshotted/verified at
the full width matrix.

---

## 8. Evidence Preserved

Screenshots (uncommitted, in
`sns-emr-frontend/scripts/responsive-audit-output/`):

- `postfix-gi-1024.png`, `postfix-gi-1280.png`, `postfix-gi-1440.png`,
  `postfix-gi-1536.png` — Phase 1 (RNICA shell) verification; the 1536px
  file is also the pre-Phase-2-fix evidence of the field-grid overlap.
- `phase2-gi-1366.png`, `phase2-gi-1440.png`, `phase2-gi-1536.png`,
  `phase2-gi-1600.png` — Phase 2 (field-grid) post-fix verification.
- `phase2-cv-1536.png` — Cardiovascular regression check post-Phase-2-fix.

Container-width audit data (viewport → nav → `.rnica-screen__content` →
`.rnica-bodysystems` grid+columns → `.rnica-bodysystem-workspace__content`
→ GI grid columns) captured at 1536/1280/1024px during root-cause
analysis — summarized in Section 3.1/3.3 above; full raw Playwright
console output was not persisted to a file and would need to be
re-captured if required again.

---

## 9. Resume Checklist (when this initiative is reactivated)

1. Re-run a fresh SNS Governance Checkpoint (branch/HEAD may have
   changed since this document was written).
2. Confirm Sections 3 and 4 (RNICA shell + GI field-grid fixes) are still
   present in the working tree/merged, not reverted.
3. Implement the Tenant sidebar fix (Section 5).
4. Perform the full Billing container-tree audit (Section 6), then fix.
5. Perform the full Owner container-tree audit/verification (Section 7),
   fix only if needed.
6. Audit shared dashboards, Orders, Medication workflows, Reports (not
   yet touched at all).
7. Re-verify the entire platform across the full width matrix (Section 1)
   with Playwright screenshots as evidence, per Product Owner requirement.
