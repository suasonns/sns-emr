# SNS Global Body-System Standard v1.0

**Status:** Authoritative implementation standard for every RNICA body-system section (Neurological, Cardiovascular, Respiratory, Infection, Gastrointestinal, Nutrition, Endocrine, Genitourinary, Musculoskeletal, Skin/Wounds), and the pattern to extend to future RN/LVN visit, MSW, Chaplain, CHHA, and Bereavement assessments.
**Reference implementation:** Gastrointestinal (this document was synthesized against GI and applied to GI first; GI is now the second reference implementation alongside Infection and Cardiovascular/Neurological).
**Supersedes:** Nothing — this document does not replace `SNS_DESIGN_SYSTEM_1.0.md`, `SNS_LAYOUT_STANDARD_V1_1_AND_GITHUB_CHECKLIST.md`, or `SNS_HOSPICE_LANGUAGE_STANDARD.md`. It is a **synthesis and application index**: it pulls the rules that govern a single body-system section out of those three source documents into one place, and records how each rule maps onto a concrete body-system implementation. Where this document and a source document conflict, the source document controls — update this document, not the other way around.
**Verification date:** 2026-10-05

---

## 1. Purpose

Every prior body-system pass (Infection, then Gastrointestinal) independently rediscovered the same handful of structural rules from three separate standards documents, which is exactly the "multiple redesign cycles" risk the owner flagged. This document exists so the next body system (Nutrition, Endocrine, Genitourinary, Skin/Wounds, Musculoskeletal) starts from a single checklist instead of a fresh read of three long documents.

This document does not introduce new rules. Every rule below cites its source section in `SNS_DESIGN_SYSTEM_1.0.md` (**DS**), `SNS_LAYOUT_STANDARD_V1_1_AND_GITHUB_CHECKLIST.md` (**LS**), or `SNS_HOSPICE_LANGUAGE_STANDARD.md` (**LANG**).

---

## 2. The eight-part body-system checklist

Apply these eight checks, in order, to any body-system section before calling it "done."

### 2.1 Structural order (LS §10)

Cards render in this fixed order: **Summary → Overview → Core Findings → Symptoms → Management → Notes → POC.** In RNICA this is already enforced structurally by `BODY_SYSTEM_CATEGORY_ORDER = ["core", "symptoms", "functional", "disease", "treatments", "response", "observation", "profile"]` (`RNICA.jsx`) — Overview and Core Findings share the `"core"` bucket (Overview is simply the first card in that bucket), Symptoms is `"symptoms"`, Management is `"treatments"`/`"response"`, Notes is `"observation"`. **A new body system does not need new ordering code — only correct `category` values on each card.**

### 2.2 Current vs. historical findings gate (LS §10, prior Infection/GI governance)

Every body system with findings that can be either active or historical needs an Overview-gate card (`"No Current <System> Concern" / "Existing <System> Findings Review" / "New or Worsening <System> Findings"`), following the `respiratoryOverview`/`giOverview` precedent. Historical findings must never, by themselves, generate follow-up (LANG §2.5, §7.11 — "do not force decline language"; see the Infection `computeInfectionRequiresFollowUp` and GI `computeGastrointestinalRequiresFollowUp` rewrites).

### 2.3 Progressive visibility (DS §2.4, LS §12.2 rule 15, prior GI directive)

Default view shows only the minimum fields needed to answer "is anything here clinically meaningful." Every additional field must have an explicit, documented reveal condition (a specific severity, a specific value, or a manual toggle) — never "always show everything the data model supports." Hidden/untriggered content must consume **zero layout space** (LS §8.4, §12.2 rule 15) — in RNICA this means either the render-loop's conditional-field guard (field-level hiding) or a card-level collapse-to-reveal-button pattern (see GI's "Abdominal / Bowel Assessment" → "+ Additional Bowel Details"), never a `display:none` div that still reserves height.

### 2.4 Follow-up governance (LANG §2.4–§2.5, §3.4, §7; prior Infection/GI directives)

`compute<System>RequiresFollowUp()` must require **genuinely supporting current evidence**, never a single severity value alone. Pattern: `conditionA & supportingFindingA`, OR `conditionB & supportingFindingB`, OR a concerning exam/objective finding, OR an explicit Decline/New-Finding Clinical Status Change selection. Precautionary/reference-only data (allergies, historical findings, risk factors/immune status) must never independently trigger follow-up (LANG §3.4: "no concern" and "stable" must not be inferred from missing or unrelated data).

### 2.5 Documentation guidance banners (LANG §3.4, §8.5, prior GI directive)

Any contextual guidance banner must: (a) only appear when a narrow, named trigger fires — never for normal/unremarkable findings; (b) use neutral, observation-focused prompts ("Consider asking: ...") — never a diagnosis, named complication, or causal statement (LANG §3.4 prohibits unsupported causal/diagnostic system-generated language); (c) render `null`/nothing, not an empty card, when no trigger applies (LS §12.2 rule 15).

### 2.6 Summary categorization (LANG §7 summary-generation rules)

Generated summaries must separate **current status** from **history** from **precautionary/reference information** (LANG §7 rules 5, 11, 12 — "include new/worsening before unchanged background," "separate current findings from history"). Do not combine allergy/risk-factor reference data with active clinical findings under one generic "Findings Present" bucket (see the Infection Patient Safety Findings / Historical Findings / Current Status split, already the model GI's `categorizeGastrointestinalSummaryIssues()` follows).

### 2.7 Layout and density (LS §4–§12)

- Canonical spacing only: 4 / 8 / 10 / 12 / 16 / 24 (LS §4).
- Card min-width 260, max routine width 420, card padding 10 (dense secondary 8/10) (LS §6).
- Shared `Card` component + `.rnica-h1`–`.rnica-helper-text` typography utility classes already deliver DS §3 compliance automatically — do not hand-roll new font sizes/weights/card shadows per body system.
- Short, content-driven peer cards (e.g. a device/equipment card next to a one-control Clinical Status Change card) should be explicitly paired into a 50/50 row instead of each reserving a full-width row, when **both are populated** (LS §10 "Management: 2-column... when both groups are populated"). Pattern: scope a `flex-direction: row; flex-wrap: wrap` override to `.rnica-bodysystem-workspace[data-section="<system>"] .rnica-bodysystem-workspace__content`, give the adjacent `"treatments"`/`"response"` category groups `flex-basis: calc(50% - 2px)`, and collapse to `flex-basis: 100%` under `900px` — this is now shipped for both Cardiovascular (`Cardiac Devices` + `Clinical Status Change`) and Gastrointestinal (`Feeding Devices` + `Clinical Status Change`); reuse it verbatim for the next body system rather than inventing a new technique.
- Never stretch peer cards to equal height for symmetry (`align-items: flex-start`, not `stretch`) (LS §6, §12.2 rule 17).
- No empty peer columns, no reserved hidden-content space, no horizontal clinical-form scrolling (LS §12.2).

### 2.8 Language and wording (LANG §2–§4, §6)

- Prefer "observed / measured / reported by X / documented in Y" phrasing over bare conclusions ("stable," "doing well") used alone (LANG §3.1–§3.3).
- Use the body-system word list in LANG §6 for any new controlled vocabulary.
- Never let the EMR auto-generate a diagnosis, prognosis, eligibility, or relatedness conclusion (LANG §3.4) — body-system follow-up logic must read as "requires follow-up" / "no follow-up," never a diagnostic label.

---

## 3. Verification requirements (LS §15.5)

Any PASS/NOT ACCEPTED claim for a body-system pass must be backed by real-browser verification at real viewport widths (1440×900, 1366×768, 1024×768) — not a forced inline style, not a narrow in-app canvas alone, not DOM/source inspection alone. See `sns-emr-frontend/scripts/verify-respiratory-rebuild.mjs` as the template Playwright script pattern. **Known gap, disclosed honestly:** this pass's GI layout verification (§4 below) relied on DOM/text reads and a screenshot capture because the in-session `evaluate_javascript` canvas action was non-functional (returned `undefined` for every script, including `1+1`); pixel-level `getBoundingClientRect()` confirmation of the new Feeding Devices/Clinical Status Change row pairing is still outstanding and should be done via a Playwright script before this is called a full LS §15.5 PASS.

---

## 4. Applied to GI (this pass)

| Checklist item | GI status before this pass | Action taken |
|---|---|---|
| 2.1 Structural order | Already compliant (shared `BODY_SYSTEM_CATEGORY_ORDER`) | None needed |
| 2.2 Current vs. historical gate | Already compliant (`GI Overview` card, Phase 1) | None needed |
| 2.3 Progressive visibility | Already compliant (2026-10-23 GI Progressive Visibility Revision) | None needed |
| 2.4 Follow-up governance | Already compliant (2026-10-23 rewrite) | None needed |
| 2.5 Documentation guidance | Already compliant (2026-10-23 rewrite) | None needed |
| 2.6 Summary categorization | Already compliant (`categorizeGastrointestinalSummaryIssues`) | None needed |
| 2.7 Layout/density — Management row pairing | **Gap**: Feeding Devices (`treatments`) and Clinical Status Change (`response`) each reserved a full-width row, unlike the Cardiovascular precedent for the same category pair | **Fixed**: added the `[data-section="gastrointestinal"]` 50/50 row-pairing CSS in `RNICACommandWorkspace.css`, verbatim-patterned on the existing Cardiovascular rule |
| 2.8 Language/wording | Already compliant | None needed |

No clinical field, value, validation, workflow, persistence, or audit behavior was changed by this pass — only a CSS layout addition.

---

## 5. Governance

- This document is maintained alongside the three source standards. Any future revision to DS, LS, or LANG that changes a rule cited above must be reflected here in the same change.
- The next body system to receive a full pass (per existing sequencing: Nutrition, Endocrine, Genitourinary, Skin/Wounds, Musculoskeletal) should start from Section 2 of this document, not from re-reading the three source documents from scratch.
