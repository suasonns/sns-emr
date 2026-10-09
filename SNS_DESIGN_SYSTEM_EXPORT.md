# SNS RNICA Design System Export

**Purpose:** Read-only extraction of the design language currently implemented in code, for use as Figma input (`SNS Layout Standard v1`). No redesign, optimization, or code changes were made to produce this document.

**Source repo:** `suasonns/sns-emr` · **Scope:** `sns-emr-frontend/src` (RNICA + shared clinical theme)

**Stack confirmation:** shadcn/ui primitives (`src/components/ui/*.tsx`, Radix UI + `class-variance-authority` + `clsx` + `tailwind-merge`) restyled via Tailwind's `rnica` color namespace, which maps 1:1 to CSS custom properties (`--sns-*`) set at runtime by `src/theme/theme.tsx`. A second, older inline-style system (`getRnicaColors`/`getRnicaStyles` in `src/theme/clinicalDesign.js`) still powers legacy un-migrated screens. Both read from the same visual intent but are two separate mechanisms — see Section 8.

---

## SECTION 1 — GLOBAL TYPOGRAPHY

### 1A. Current token system (`src/theme/sns-typography.css`) — the forward-going standard

| Token | Font Size | Font Weight | Line Height | Usage |
|---|---|---|---|---|
| `--rnica-h1` | 16px | 500 | 1.3 | Top-level card/section title, patient-header name |
| `--rnica-h2` | 14px | 500 | 1.35 | Card title / sub-screen heading |
| `--rnica-h3` | 12px | 500 | 1.4 | Group/category label inside a card (uppercase applied by selector, not token) |
| `--rnica-body` | 13px | 400 | 1.5 | Standard reading copy/value text inside a card |
| `--rnica-helper` | 11px | 400 | 1.4 | Secondary/helper/meta text; always `var(--sns-muted)` color |

Family: not set by this file (inherits page font — see 1C). Letter-spacing: not set per-token (applied ad hoc by consuming selectors, e.g. `0.03em`–`0.08em` on uppercase labels). Text-transform: not part of the token; applied by individual selectors (e.g. `.rnica-bodysystem-group__heading { text-transform: uppercase }`).

### 1B. Legacy inline-style typography (`getRnicaStyles()`, `src/theme/clinicalDesign.js`)

| Style key | Font Size | Weight | Letter Spacing | Notes |
|---|---|---|---|---|
| `bannerName` | 14px | 800 | -0.02em | Top patient banner name |
| `bannerMeta` | 10px | 400 | 0.01em | Opacity 0.82 |
| `cardTitle` | 13px | 800 | -0.01em | |
| `sectionTitle` | 14px | 800 | -0.02em | |
| `sectionSubtitle` | 10px | 400 | — | `color: gray`, line-height 1.3 |
| `label` | 8.5px | 400 | 0.5px | `text-transform: uppercase`, line-height 1.3 |
| `input` / `select` text | 11.5px | 400 | — | line-height 1.25 |
| `textarea` text | 11.5px | 400 | — | line-height 1.25 |
| `radioLabel` / `checkboxLabel` | 11.5px | 400 | — | |
| `hopeTag` / `sfvTag` / `cmsTag` | 10px | 800 | 0.03em | uppercase |
| `statusBadge` | 10px | 700 | 0.04em | uppercase |
| `btnPrimary` / `btnSecondary` / `btnDanger` | 13px | 700 | — | |
| `th` (table header) | 10px | 700 | — | uppercase |
| `td` | 11.5px | inherit | — | |

### 1C. Font family

`"Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"` — set once in `getRnicaStyles().page.fontFamily`, inherited by the whole RNICA tree. The Owner Platform shell (separate from RNICA) instead declares `Geist` (sans) / `JetBrains Mono` (mono) in `tailwind.config.js`; RNICA pages do not use the Tailwind `fontFamily` theme extension.

### 1D. Density-tier body/section sizes (`ClinicalCommandWorkspace.css`, command workspace)

| Tier (class) | Body size | Section size | Nav/meta size |
|---|---|---|---|
| default (compact) | 11px | 13px | 11px / 10px |
| `.clinical-command--comfortable` | 12.5px | 15px | 11px / 10px |
| `.clinical-command--large` | 14px | 16px | 11px / 10px |

---

## SECTION 2 — SPACING SCALE

No single enumerated spacing scale constant exists; spacing is expressed as a mix of rem/px literals and a small set of CSS custom properties. Values actually observed in use:

| Value | Where used |
|---|---|
| 2px | icon/text gaps (`gap: 0.15rem`-ish rounding), badge dot margins |
| 4px (`0.25rem`) | tight internal gaps (chip row gaps, lcd summary counts) |
| 6px (`0.4rem`≈) | `.rnica-bodysystem-group__heading` margin/padding-bottom |
| 8px (`0.5rem`) | `--ccw-gap` compact tier; card `gap` in field grids; `rnica-command-story-grid` gap |
| 10px | legacy `card.padding` (`clinicalDesign.js`) |
| 12px | field-grid column gap (`fieldsGrid: "0px 12px"`); `.rnica-bodysystem-workspace__fields` gap |
| 16px | `.rnica-bodysystem-group__cards` gap (card-to-card spacing within a category) |
| 1.1rem/1.25rem (≈17.6/20px) | `.rnica-ds-card` padding |
| 1.35rem (≈21.6px) | `.rnica-ds-patient-story` / `.rnica-ds-two-col` gap |

### Named spacing custom properties (command workspace density tiers)

| Token | Compact | Comfortable | Large |
|---|---|---|---|
| `--ccw-gap` | 0.5rem (8px) | 0.75rem (12px) | 0.625rem (10px) |
| `--ccw-pad` | 0.625rem (10px) | 0.75rem (12px) | 0.7rem (11.2px) |
| `--ccw-control-height` | 34px | 36px | 36px |

There is **no formal 4/8/12/16/20/24/32/40px scale constant** in code; the above is the de-facto set in current use. Figma should treat 8 / 12 / 16px as the three dominant gap values and 10–12px as the dominant card-padding value.

---

## SECTION 3 — GRID SYSTEM

### Page / workspace width

- `.rnica-command { width: 100%; max-width: none; }` — the workspace intentionally has **no max-width ceiling**; it fills its container.
- No global "page width" or "content width" constant is declared (no `max-width: 1200px`-style container anywhere in RNICA CSS).

### Primary 3-column workspace grid (`.rnica-command-layout`)

```
grid-template-columns: 270px minmax(28rem, 1fr) minmax(17rem, 21rem);
```
- Column 1 (left nav rail): fixed **270px**.
- Column 2 (detail/content): fluid, **min 28rem (448px)**, grows to fill.
- Column 3 (right intelligence/status rail): fluid, **min 17rem (272px) / max 21rem (336px)**.

### Body-system card grid (`.rnica-bodysystem-group__cards`)
```
grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
gap: 16px;
```
### Field grid inside a card (`.rnica-bodysystem-workspace__fields`, legacy `fieldsGrid`)
```
grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));  /* command workspace */
grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));  /* legacy clinicalDesign.js */
gap: 8px 12px;
```
### Section-specific fixed grids (overrides, not the general rule)
- Neurological "core" category row: forced `repeat(3, minmax(0, 1fr))` (exact 3-column row for Consciousness/Orientation/Neurological Overview).
- Neurological "symptoms" category row: forced `repeat(3, minmax(0, 1fr))` at wider breakpoints (Communication and Sensory / Cognitive-Behavioral two-up with a 3rd slot).
- Comorbidity selection grid: `repeat(3, minmax(0, 1fr))`, 1.1rem column-gap / 0.9rem row-gap.
- Functional Status (`rnica-performance-grid`): `repeat(2, minmax(0, 1fr))`.
- 12-column explicit grids exist twice (Cardiovascular workflow rebuild rows): `repeat(12, minmax(0, 1fr))`.

### Breakpoints (global, confirmed across `RNICACommandWorkspace.css`)

| Breakpoint | Type | Effect |
|---|---|---|
| `max-width: 520px` | media (nested inside 700px block) | patient bar becomes column layout |
| `max-width: 700px` | media | **Mobile** — workspace stacks to single column, prep bar becomes horizontal scroll, most forced multi-column rules collapse to `1fr` |
| `max-width: 820px` | container query (`clinical-command-workspace`) | prep bar 2-col, rail 2-col, comorbidity/performance grids collapse to `1fr` |
| `max-width: 900px` | media | secondary collapse point used by a few components (two-col → 1 col) |
| `max-width: 1000px` | container query | rail collapses to full-width 3-col band below content instead of a side column |
| `min-width: 701px and max-width: 1199px` | media | **Tablet** range |
| `max-width: 1100px` | media | rail drops out of the 3-column layout into a below-content 3-up band |
| `≥ 1200px` (i.e., > 1199px, no rule fires) | implicit | **Desktop** — full 3-column `.rnica-command-layout` applies |

**Conclusion:** the effective global scheme is **Mobile ≤700px / Tablet 701–1199px / Desktop ≥1200px**, with secondary internal collapse points at 820/900/1000/1100px for specific widgets (not new global tiers).

### Tablet / mobile behavior
- Tablet (701–1199px): right rail drops below content as a 3-column band (`repeat(3, minmax(0,1fr))`); card/field grids keep auto-fit behavior.
- Mobile (≤700px): full single-column stack; `.rnica-command-prep` becomes a horizontally-scrollable row instead of a grid.

---

## SECTION 4 — CARD SPECIFICATION

Two parallel card implementations exist:

### 4A. `.rnica-ds-card` (new design-system card, `RnicaDesignSystem.css`)
```css
background: var(--sns-card);
border: 1px solid var(--sns-border);
border-radius: 0.75rem;      /* 12px */
padding: 1.1rem 1.25rem;     /* 17.6px / 20px */
gap: 0.65rem;                /* 10.4px, flex column */
box-shadow: 0 1px 2px var(--sns-shadow), 0 8px 22px rgba(0,0,0,0.24);
```
Variants: `--primary` (3px left border in teal, padding-left 1.1rem), `--secondary` (bg `--sns-cardSoft`, padding 0.85rem 1rem), `--ai` (purple/teal 3px top gradient bar), `--warning` (orange border).
Header: `display:flex; align-items:flex-start; justify-content:space-between; gap:0.75rem`. Title 13px/600. Subtitle 11px/400 muted. Meta 10px/400 muted.

### 4B. `.rnica-command-card` (command-workspace card, `RNICACommandWorkspace.css`)
```css
border: 1px solid var(--sns-border);
border-radius: 0.6rem;   /* 9.6px */
background: var(--sns-card);
padding: var(--cw-pad);    /* 10–12px depending on density tier */
margin-bottom: var(--cw-gap);  /* 8–12px */
```
Heading `h2`: `font-size: var(--cw-section-size); font-weight: 600;`

### 4C. Legacy inline-style card (`getRnicaStyles().card`, pre-shadcn pages)
```css
background: COLORS.white;
border-radius: 8px;
border: 1px solid COLORS.border;
padding: 10px;
margin-bottom: 8px;
box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
```

**Summary table:**

| | Border Radius | Border Width | Padding | Gap between sections |
|---|---|---|---|---|
| `.rnica-ds-card` | 12px | 1px | 17.6/20px | 10.4px |
| `.rnica-command-card` | 9.6px | 1px | 10–12px (tier) | 8–12px (tier) |
| legacy `card` style | 8px | 1px | 10px | 8px (margin-bottom) |

No explicit header-height token exists in any of the three — header height is content-driven (flex row, no fixed min-height).

---

## SECTION 5 — BUTTON SYSTEM

### Primary / Secondary / Danger (legacy inline, still used on non-migrated screens)

| | Height (derived) | Radius | Font | Padding |
|---|---|---|---|---|
| `btnPrimary` | auto (padding-driven) | 8px | 13px/700 | 8px 14px |
| `btnSecondary` | auto | 8px | 13px/700 | 8px 14px |
| `btnDanger` | auto | 8px | 13px/700 | 8px 14px |

Primary background: `linear-gradient(135deg, teal, tealDark)`, shadow `0 8px 18px rgba(13,148,136,0.2)`. Secondary: white bg, 1px border, dark text. Danger: `linear-gradient(135deg, #ef4444, #dc2626)`.

### Command-workspace buttons (`.rnica-command button`)
```css
min-height: var(--cw-control-height);  /* 34px compact / 36px comfortable+large */
padding: 0.35rem 0.6rem;
border: 1px solid var(--sns-border);
border-radius: 0.45rem;   /* 7.2px */
font-size: var(--cw-button-size);  /* = body size, 11–14px by tier */
```
Hover: border → teal. Disabled: `opacity: 0.55; cursor: not-allowed`.

### Chip / toggle (`.rnica-ds-chip`, built on shadcn `toggle-group.tsx` → `ToggleGroupItem`)
```css
display: inline-flex; gap: 0.3rem;
font-size: 10px; font-weight: 400; letter-spacing: 0.02em; text-transform: uppercase;
padding: 0.15rem 0.5rem;   /* 2.4px / 8px */
border-radius: 999px;      /* pill */
border: 1px solid transparent;
```
Selected/deselected states are color variants, not size variants: `--neutral` / `--success` / `--warning` / `--critical` / `--info` / `--ai`, each swapping `background` + `color` + `border-color` only (e.g. `--success`: bg `var(--sns-successBg)`, text `var(--sns-green)`, border `color-mix(... green 40% ...)`). Selected chip = `data-[state=on]` applies the teal-filled variant; deselected = outline/neutral variant. No separate height — chips share the button line-height/padding box above.

---

## SECTION 6 — FORM CONTROL SYSTEM

### Legacy inline (`getRnicaStyles()`)

| Control | Height (derived) | Padding | Font | Radius |
|---|---|---|---|---|
| `input` | auto | 5px 7px | 11.5px/400, line-height 1.25 | 5px |
| `textarea` | min-height 46px | 5px 7px | 11.5px/400 | 5px |
| `select` | auto | 5px 7px | 11.5px/400 | 5px |
| `radioGroup`/`checkboxGroup` | — | gap 3px 10px, flex-wrap | 11.5px | — |

### Command-workspace overrides (`.rnica-command-active input/select/textarea`)
```css
min-height: var(--cw-control-height);  /* 34–36px */
padding: 0.4rem 0.55rem;
font-size: var(--cw-input-size);
border-radius: 6px;
```
Minimum width: none fixed at the control level; fields rely on the parent grid's `minmax(200px, 1fr)` (legacy: `minmax(150px, 1fr)`) as the effective minimum column/field width.

### Chip selector
Built on `ui/toggle-group.tsx`; sizing = Section 5's chip spec (pill, 10px/400 text, `0.15rem 0.5rem` padding). Wraps via `flex-wrap: wrap` in every `*-chips`/`*-grid__chips` container — no horizontal scroll, no fixed chip width.

---

## SECTION 7 — BODY SYSTEM INVENTORY

Section order (`BODY_SYSTEM_CATEGORY_ORDER`, used to bucket every card inside a body system):
```
core → symptoms → functional → disease → treatments → response → observation
```
(Only categories with ≥1 real card for that system render a heading; cards are tagged with `category:` and sorted into these buckets, not rendered in literal array order.)

### Full body-system list (10 systems with `category`-bucketed cards)

| System | Cards (in bucket order where known) |
|---|---|
| **Neurological** | Consciousness · Orientation · Neurological Overview · SNS Cognitive Screen *(core)* → Communication and Sensory · Cognitive/Behavioral Findings *(symptoms)* → Psychiatric History *(functional)* → Sleep/Responsiveness *(core, full-width, collapsed by default)* → Notes *(observation)* |
| **Cardiovascular** | Cardiovascular Overview · Circulation & Perfusion *(core)* → Cardiovascular Symptoms *(symptoms)* → Cardiac Devices *(treatments)* → Clinical Status Change *(response)* → Cardiovascular Notes *(observation)* |
| **Respiratory** | Respiratory Assessment *(core)* → Oxygen Therapy · Ventilator/Airway Support *(treatments)* → Clinical Status Change *(response)* → Notes *(observation)* |
| **Infection** | Allergies · Immune Status *(core)* → Infection Assessment *(disease)* → Infection Symptoms *(symptoms)* → Antibiotic Treatment *(treatments)* → Clinical Status Change *(response)* → Notes *(observation)* |
| **Gastrointestinal** | Constipation (auto-suggested) · Abdominal/Bowel Assessment *(core)* → GI Symptoms *(symptoms)* → Feeding Devices *(treatments)* → Clinical Status Change *(response)* → Notes *(observation)* |
| **Nutrition** | Nutritional Assessment · Oral Cavity *(core)* → Nutrition Symptoms *(symptoms)* → Nutrition Support · NPO/Artificial Feeding *(treatments)* → Clinical Status Change *(response)* → Nutrition Notes *(observation)* |
| **Endocrine** | Endocrine Impairment · Thyroid Assessment *(core)* → Diabetes Management *(disease)* → Endocrine Symptoms *(symptoms)* → Endocrine Treatment *(treatments)* → Clinical Status Change *(response)* → Notes *(observation)* |
| **Genitourinary** | Urinary Status · Urine Output *(core)* → Reproductive Concerns *(symptoms)* → Catheter Assessment · Bladder Management *(treatments)* → Clinical Status Change *(response)* → GU Notes *(observation)* |
| **Musculoskeletal** | Musculoskeletal Assessment *(core)* → Mobility Assessment *(functional)* → Clinical Status Change *(response)* → Fall History & Notes *(observation)* — *(Motor/Balance from Neurological is slated to be bound here per owner directive; not yet implemented)* |
| **Skin** | Skin Assessment (HOPE M1190) · Braden Scale *(core)* → Clinical Status Change *(response)* |

### Reusable component/layout patterns across systems
- Every system follows an **Overview/Gate card first** (segmented triage: "No Current Concern / Existing Findings / New-Worsening / Unable to Assess") that conditionally reveals the rest of the system.
- **Clinical Status Change** card is the near-universal response-category card (segmented or radio, system-specific option sets).
- **Notes** card (textarea, `autoGrow`, `rows: 1–2`) is the final, observation-category card in every system.
- Card/field grids use `auto-fit`/`minmax`, not fixed/explicit columns, except where an owner directive forced an explicit `repeat(3, …)`/`repeat(12, …)` override for a specific section (Neurological core row, Comorbidities, two Cardiovascular 12-col rebuilds).

### Non-body-system RNICA sections (flat card lists, no category bucketing)
Psychosocial Referral Determination, Spiritual Referral Determination, Bereavement Referral Determination, Personal Care & Support Needs, Imminent Death Assessment — these use plain `cards: [...]` arrays without `category`/bucket sorting; they are part of the broader RNICA workflow but outside the "Body Systems" accordion group.

---

## SECTION 8 — COLOR SYSTEM

### 8A. Canonical runtime tokens (`src/theme/theme.tsx` → `--sns-*`, authoritative; both shadcn/Tailwind `rnica-*` classes and `RnicaDesignSystem.css` read these)

| Token | Dark | Light | Usage |
|---|---|---|---|
| `bg` | `#07111d` | `#f3f8f7` | Page background |
| `bgAlt` | `#091525` | `#edf5f3` | Alt surface / inset panels |
| `card` | `#101f31` | `#ffffff` | Card background |
| `cardSoft` | `#182c42` | `#f3f7fa` | Secondary/soft card background |
| `border` | `rgba(148,163,184,0.16)` | `#d9e6eb` | Default border |
| `teal` | `#35e0c1` | `#0d7d7a` | Primary brand/accent |
| `white` (text) | `#f8fafc` | `#18354c` | Primary text (named "white" for historical reasons; it's the primary foreground) |
| `muted` | `#a9bcd0` | `#4a5f73` | Secondary text |
| `dim` | `#7890a8` | `#6d7d8b` | Tertiary/label text |
| `green` | `#4ade80` | `#2d7b63` | Success |
| `blue` | `#38bdf8` | `#4d7dc2` | Info / CMS |
| `purple` | `#a78bfa` | `#7b61d8` | AI accent |
| `orange` | `#fbbf24` | `#d38a2b` | Warning |
| `red` | `#fb7185` | `#d64d57` | Error/critical/SFV |
| `yellow` | `#f4d06a` | `#b7861b` | — |
| `pink` | `#ee7cc1` | `#cf5eb7` | — |
| `shadow` / `shadowStrong` | `rgba(0,0,0,0.22)` / `0.28` | `rgba(15,23,42,0.08)` / `0.16` | Box-shadow base |
| `teal` state: `tealHover`/`tealPressed` | `#5ce9d0` / `#20bfa4` | `#0a6663` / `#095350` | Interactive states |
| `successBg`/`infoBg`/`warningBg`/`criticalBg`/`aiBg` | 12% alpha of green/blue/orange/red/purple | 10% alpha (light-tuned) | Status chip/badge backgrounds |
| `borderStrong`/`borderSelected`/`borderWarning`/`borderCritical`/`borderAI` | alpha-variant borders | alpha-variant borders | Emphasis borders |
| `focusRing` / `focusHalo` | `#5eead4` / `rgba(94,234,212,0.28)` | `#0d7d7a` / `rgba(13,125,122,0.22)` | Keyboard focus |
| `textStrong`/`textDisabled`/`textInverse` | `#dce7f3` / `#526a82` / `#031317` | `#1f2937` / `#94a3b8` / `#ffffff` | Text tiers |
| `inputBg`/`hoverSurface`/`selectedSurface` | `#0d1b2b` / `#1c334b` / `#163a48` | `#ffffff` / `#e4f1ee` / `#dcf3ee` | Control surfaces |
| `overlay` / `shadowDrawer` | `rgba(2,8,23,0.72)` / `rgba(0,0,0,0.48)` | `rgba(15,23,42,0.45)` / `rgba(15,23,42,0.24)` | Modal scrims |

### 8B. Legacy `getRnicaColors(mode)` tokens (`clinicalDesign.js`, used by non-migrated pages — a parallel but distinct palette from 8A)

| Token | Light | Dark |
|---|---|---|
| `navy` | `#1E3A5F` | `#1E3A5F` |
| `hope` | `#059669` | `#4ade80` |
| `sfv` | `#DC2626` | `#fb7185` |
| `cms` | `#2563EB` | `#38bdf8` |
| `teal` / `tealDark` | `#0D9488` / `#0F766E` | `#35e0c1` / `#5ce9d0` |
| `pageBg` | `#EEF3F8` | `#07111d` |
| `sidebarBg` / `sidebarActiveColor` | `#F8FBFD` / `#0F766E` | `#091525` / `#35e0c1` |
| `warning`/`error`/`success` | `#F59E0B`/`#EF4444`/`#10B981` | `#fbbf24`/`#fb7185`/`#4ade80` |
| `hopeTagBg`/`sfvTagBg`/`cmsTagBg` | `#ECFDF5`/`#FEF2F2`/`#EFF6FF` | rgba-alpha equivalents |

### 8C. Tailwind `rnica` namespace (`tailwind.config.js`)
Every `rnica-*` Tailwind color (e.g. `bg-rnica-teal`, `border-rnica-border`, `text-rnica-dim`) is a direct 1:1 `var(--sns-*)` passthrough of table 8A — there is no independent Tailwind-side hex value; Tailwind is a utility-class convenience layer over the same runtime tokens.

---

## SECTION 9 — MEASURED SCREEN REFERENCES

**Methodology note:** values below are computed directly from the CSS grid/column definitions in Section 3 (not a live pixel-measured screenshot), since the grid uses explicit `fr`/`minmax()` terms that resolve deterministically for a known container width. Figures assume the workspace fills the full browser viewport width with no outer page padding (observed: `.rnica-command` has no horizontal margin/max-width).

### Desktop 1440×900
- Total width: 1440px (no scrollbar-reserve assumed)
- Rail (col 1): 270px fixed
- Right rail (col 3): clamps to its max, 21rem = **336px** (plenty of room above the 17rem floor)
- Detail/content (col 2): `1440 − 270 − 336 = ` **834px**
- Body-system card row at 834px content width: `auto-fit, minmax(260px,1fr)` → **3 cards per row** (3×260=780 ≤ 834; 4×260=1040 > 834)
- Field row inside a card (assuming a card ≈ 834/3 ≈ 278px wide minus ~20px padding ≈ 258px): `minmax(200px,1fr)` → **1 field per row** inside a 3-up card layout (a full-width card, e.g. Sleep/Responsiveness, gets the full 834px and fits **4 fields/row**: 4×200=800 ≤ 834)

### Desktop 1366×768
- Rail: 270px · Right rail: 336px (max) · Detail: `1366 − 270 − 336 = ` **760px**
- Body-system cards: `auto-fit, minmax(260px,1fr)` at 760px → **2 cards per row** (3×260=780 > 760)
- Full-width card field row at 760px: `minmax(200px,1fr)` → **3 fields/row** (4×200=800 > 760)

### Neurological vs. Cardiovascular at these widths
Both sections share the identical `.rnica-command-layout`/`.rnica-bodysystem-group__cards` grid — the only measured difference is **card count per category**, not column math (Neurological additionally forces an exact `repeat(3,1fr)` override for its "core" bucket regardless of the computed auto-fit count above, so Consciousness/Orientation/Neurological Overview always render exactly 3-up at both 1440 and 1366 widths, never 2-up).

---

## SECTION 10 — CONSTRAINTS

| Constraint | Value |
|---|---|
| Minimum card width (auto-fit floor) | 260px (body-system cards) |
| Minimum field width (auto-fit floor) | 200px (command workspace); 150px (legacy `fieldsGrid`) |
| Minimum touch/control height | 34px (compact tier) / 36px (comfortable & large tiers) — `--cw-control-height` |
| Right rail width range | 272px (17rem) – 336px (21rem) |
| Left nav rail width | 270px fixed, all breakpoints ≥1101px; collapses to a static block below 1100px/1000px |
| Responsive breakpoints | 520 / 700 / 820 / 900 / 1000 / 1100 / 1199px (see Section 3 table) |
| Auto-grow behavior | Notes/narrative textareas use `autoGrow: true` with a small starting `rows` (1–2) instead of a tall fixed box; grows with content, no max-height cap found |
| Textarea minimum height (legacy input system) | 46px |
| Chip wrapping | `flex-wrap: wrap` on every chip/toggle container — no horizontal scroll, no fixed chip width |
| Card-to-card gap (same category) | 16px |
| Field-to-field gap | 8px row / 12px column |
| No max workspace width | `.rnica-command { max-width: none }` — intentionally unconstrained |
| No horizontal scroll by design | mobile breakpoint forces single-column stacking instead; only `.rnica-command-prep` (context strip) explicitly uses horizontal scroll on mobile |

---

## SECTION 11 — FIGMA MIGRATION DATA

*(Measurements, tokens, typography, spacing, grids, and constraints only — no implementation/CSS/JSX discussion. Copy this section directly into Figma variables/styles.)*

**Typography scale (5 tokens):**
- H1: 16 / 500 / 1.3
- H2: 14 / 500 / 1.35
- H3: 12 / 500 / 1.4 (uppercase, 0.03–0.05em tracking where applied)
- Body: 13 / 400 / 1.5
- Helper: 11 / 400 / 1.4

**Spacing scale (dominant values):** 4, 6, 8, 10, 12, 16, 17.6(1.1rem), 20px.

**Grid — Desktop workspace (3 columns):** 270 / fluid(min 448) / fluid(min 272, max 336).

**Grid — Card row:** auto-fit, 260px minimum column, 16px gutter.

**Grid — Field row:** auto-fit, 200px minimum column, 8/12px gutter.

**Breakpoints:** 520, 700, 820, 900, 1000, 1100, 1199px. Effective tiers: Mobile ≤700 / Tablet 701–1199 / Desktop ≥1200.

**Card:** radius 8–12px (8 legacy, 9.6 command, 12 new design-system), 1px border, padding 10–20px.

**Control height:** 34px (compact) / 36px (comfortable, large).

**Button radius:** 7.2px (command) / 8px (legacy primary/secondary/danger).

**Chip:** pill radius (999px), padding 2.4×8px, 10px/400/uppercase text.

**Color tokens (dark mode primary set):** bg `#07111d` · card `#101f31` · cardSoft `#182c42` · border `rgba(148,163,184,.16)` · teal `#35e0c1` · text `#f8fafc` · muted `#a9bcd0` · green `#4ade80` · blue `#38bdf8` · orange `#fbbf24` · red `#fb7185` · purple `#a78bfa`.

**Color tokens (light mode primary set):** bg `#f3f8f7` · card `#ffffff` · cardSoft `#f3f7fa` · border `#d9e6eb` · teal `#0d7d7a` · text `#18354c` · muted `#4a5f73` · green `#2d7b63` · blue `#4d7dc2` · orange `#d38a2b` · red `#d64d57` · purple `#7b61d8`.

**Desktop screen math (computed):**
- 1440×900 → rail 270 / content 834 / rail 336 → 3 cards/row
- 1366×768 → rail 270 / content 760 / rail 336 → 2 cards/row

---

*End of export. No source file was modified to produce this document.*
