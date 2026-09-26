# RNICA vs. Reference Nursing-Assessment System — Human Factors Comparison

**Type:** Research and analysis only. No design, code, refactor, or architecture decisions.
**Method:** Reference system evaluated from 15 attached screenshots of a single completed
hospice comprehensive nursing assessment. RNICA evaluated from repository ground truth: the
13-screen authority matrix (`RNICA_SCREEN_AUTHORITY_MATRIX.md`), the completed RNICA Body
Systems Field Inventory (this session), and direct source verification (grep/view) of module
existence for every reference-system feature discussed below. Nothing here is inferred from
memory alone — presence/absence claims are backed by a specific file or doc citation.

---

## Part 1 — Executive Summary

The reference system (a single long scrolling HTML page, "Comprehensive Nursing Assessment")
and RNICA (a 13-screen, tab-based workspace) solve the same clinical problem — hospice RN
comprehensive assessment — with fundamentally different information architectures. The
reference system optimizes for **linear completeness**: everything the RN might need is on one
continuously scrolling page, in a fixed head-to-toe order, with inline HOPE/SFV markers. RNICA
optimizes for **modular ownership and governance**: each clinical domain is a distinct, API-backed
module with explicit ownership rules, AI-assisted evidence review, and a live server-enforced
completion/lock gate.

**Reference system's core strength:** a nurse can see an enormous amount of context at once
(nothing is hidden behind a tab), and several sub-instruments (Braden, PAINAD, LCD eligibility
checklist, ADL dependence scale) are fully built out as compact, self-scoring grids the nurse
never has to leave the page to use.

**RNICA's core strength:** the underlying data model is materially more sophisticated — a live
backend LCD eligibility evaluator (not a static checklist), an AI evidence-harvesting layer that
reads uploaded documents and proposes structured findings with source provenance, a unified
readiness/lock engine shared between the UI and the server (not duplicated logic), and a real
amendment/audit workflow. None of this exists in the reference system as shown.

**Where RNICA is currently behind:** the reference system has several complete, purpose-built
instruments that RNICA has **no equivalent for at all** — a quantified 6-item ADL dependence
score with an auto-calculate action, an itemized DME device-need list, a detailed IV
catheter-care panel, and an explicit Disaster Triage decision tree. RNICA also currently spreads
some assessments the reference system keeps atomic (Mobility, Fall history) across other domains
in ways that create real double-documentation risk, confirmed in this session's own Field
Inventory.

**Net read:** the reference system is not the better nursing-workflow model — it is the better
**exhaustive single-page reference document**. RNICA is not yet the better single-page reference
experience — but it is the more defensible clinical-record architecture. The highest-value moves
are not "make RNICA look like the reference system"; they are "close the handful of real
instrument gaps the reference system exposes, and borrow its compact self-scoring-grid pattern
for RNICA's own existing scores (Braden, ADL, functional scales)."

---

## Part 2 — RNICA vs. Reference System (Side-by-Side)

| Category | Reference System | RNICA | Verdict |
|---|---|---|---|
| **Visibility** | Everything on one continuously scrolling page — high visibility, zero navigation, but the page is very long (the Braden table alone screenshot shows ~15 sections above/below it) | 13 discrete screens; only the active screen's content is visible at once | Reference wins raw visibility; RNICA wins per-screen signal-to-noise. Tradeoff, not a clear winner. |
| **Workflow** | Fixed head-to-toe order baked into the page; no way to skip ahead except scrolling | Screens are explicitly sequenced by clinical reasoning order (Evidence & Intake → HOPE Admin → Pain/Symptom → Diagnosis/LCD → Functional Status → Body Systems → Caregiver/Support → Safety/Risk → ACP → Orders/POC → Compliance → AI → Finalization), documented and owner-approved | RNICA's sequencing is more deliberately designed; reference system's is just "how the form was originally laid out" |
| **Navigation** | None needed within a visit, but the tree sidebar (Admission/Assessment/Tx-Med-DME/IDG/POC/etc.) is 20+ items deep and undifferentiated by urgency | Tab rail of 13 named screens, each independently addressable/deep-linkable, with a persistent readiness/AI rail | RNICA's navigation model is more scalable; reference system's sidebar risks "20 gray links" fatigue for less frequent module types |
| **Documentation Safety** | No visible required-field enforcement beyond HOPE red-highlighted items; a nurse could scroll past an entire section (e.g. Endocrine) without any signal | RNICA has a **server-enforced** hard-required field list plus a Compliance & Readiness screen that is the same function used by the Lock gate itself — no drift between "what the UI warns about" and "what blocks Lock" | RNICA's model is structurally safer where it is enforced. But RN ICA's Body Systems explicitly **skip** the generic full-ROS completeness validator (confirmed: `_validate_required_ros` returns early for RN ICA) — so within Body Systems specifically, neither system currently prevents a skipped section. |
| **Clinical Thinking Alignment** | Follows a recognizable head-to-toe order, but symptom axes are sometimes conflated (pulse quality mixes rhythm+amplitude as one exclusive choice; abdomen mixes shape+tenderness) — flagged as unresolved in this session's own inventory when RNICA has the same pattern | RNICA's newly-approved target IA (Summary → Core Assessment → Symptoms → Functional Impact → Disease-Specific → Treatments → Notes → POC) is a more deliberate nursing-workflow model, not yet built | Neither system is clean today; RNICA's *target* design is more rigorous, but unimplemented |
| **Findability** | A nurse must scroll to find anything; the same clinical fact can appear in 2-3 places (Foley/catheter status appears in both the Urinary Continence row and a separate Catheter row on the same screen) | Findability is via 13 named tabs; within Body Systems, findability is presently poor per the owner's own screenshots (dense, ungrouped fields) — the reorg work is in progress | Reference system: scroll-search burden. RNICA today: tab-then-scan burden within Body Systems. Comparable burden, different shape. |
| **Completion Tracking** | No visible per-section completion indicator; only a page-level Progress Status stepper (Draft → Review → Sign & Submit) | Screen-level Compliance & Readiness view lists every blocker/warning with a link back to its source screen | RNICA's completion-tracking model is materially better once built out — a single source of truth, not a stepper with no detail |
| **User Burden** | Very low navigation burden, moderate-to-high scroll burden (one visit's assessment is a multi-thousand-pixel single page); several sub-instruments (Braden, PAINAD, LCD checklist) are efficient once reached | Low-to-moderate scroll burden per screen, low-to-moderate navigation burden (13 known tabs vs. unlimited scrolling), but Body Systems screens currently have high visual-scanning burden per the owner's own review | Roughly comparable total burden today, concentrated in different places |

---

## Part 3 — What RNICA Already Does Better

1. **Live, backend-evaluated LCD eligibility**, not a static checklist. The reference system's LCD
   panel is a fixed set of dropdowns that a nurse fills in manually with no computed verdict shown
   beyond a "Validate LCD Eligibility" button of unknown behavior. RNICA calls a real
   `detectLCD`/`evaluateLCD` service against structured facts built from the actual documented
   fields (`buildClientLcdFacts`), and is explicitly governed to show criteria-match evidence, not
   a false "eligible/not eligible" verdict — a stronger clinical-safety posture than a static form.
2. **AI-assisted evidence harvesting with source provenance.** RNICA's Evidence & Intake screen
   reads facesheet/imported-document evidence and proposes structured findings a nurse reviews and
   applies, retaining traceability to the source document. Nothing resembling this exists in the
   reference system's screenshots — the reference system requires 100% manual entry of everything,
   including one-time "Import Data from Previous Assessment" for PAINAD alone.
3. **A single source of truth for completion/lock state.** RNICA's readiness engine
   (`getRnicaFinalizationReadiness`) is the *same function* the server calls to gate Lock — there
   is no separate "what the UI thinks is required" vs. "what the server actually enforces." The
   reference system shows no equivalent architecture; its only visible gate is a generic
   Sign & Submit button.
4. **A real amendment/audit workflow post-Lock** (`requestRnicaCorrection`, approve/deny amendment,
   full audit trail) — the reference system's screenshots show only a static "Electronically
   Signed" stamp and a Lock button, with no visible correction/amendment mechanism.
5. **Diagnosis-conditional functional scales.** RNICA shows FAST only when dementia-relevant and
   NYHA only when cardiac-relevant (server-enforced), whereas the reference system always displays
   all four scales (KPS/PPS/FAST/NYHA) regardless of diagnosis — extra irrelevant fields for most
   patients, a small but real per-visit burden the reference system pays on every single chart.
6. **Deliberate, owner-approved screen sequencing** aligned to a clinical-reasoning order (pain and
   symptom burden identified before diagnosis is established; diagnosis before functional
   interpretation) — the reference system's order is simply "the historical form layout," not a
   documented clinical-reasoning rationale.
7. **Explicit module-ownership rules preventing scope creep** (e.g., "Body Systems does not own
   Falls/Safety/Skin-program-specific workflows") — a governance layer the reference system has no
   analogue for; its screenshots show real evidence of the opposite problem (Falls fields
   physically embedded inside the reference system's own MusculoSkeletal panel).
8. **Multiple validated pain scales available as distinct components** (NumericPainScale, PAINAD,
   FLACC) versus the reference system's PAINAD-only radio toggle (with FLACC as the only listed
   alternative) — RNICA's pain module is architected for more patient populations (verbal adults,
   dementia, pediatric/nonverbal) even though FLACC and PAINAD alone were visible in the reference
   screenshots too.

---

## Part 4 — What RNICA Is Missing (High-Value Only)

1. **A quantified ADL dependence score.** The reference system has a 6-item (Ambulation, Toileting,
   Transfer, Dressing, Feeding, Bathing) 0-3 dependence scale with an explicit "Calculate ADL Score"
   action producing a 0-18 total plus a "X of 6 activities with complete dependence" summary.
   Confirmed: no equivalent scoring construct (`adlScore`, `dependenceScale`, or a GG-item-style
   grid) exists anywhere in the RNICA frontend today. RNICA's mobility/functional fields are
   qualitative and scattered (ambulatory status, endurance, transfer ability recorded as separate
   free-standing fields inside Musculoskeletal per this session's own Field Inventory) rather than
   a single scored instrument. This is a genuine capability gap, not a cosmetic one — a quantified,
   trackable ADL score has visit-to-visit trending value the current qualitative fields cannot
   provide.
2. **An itemized DME device-need list inside the nursing assessment itself.** The reference system
   lets the RN mark Need/blank for ~17 specific devices (air mattress, bed, bedpan, egg crate,
   overbed table, cane, walker, wheelchair, shower chair, geri-chair, Hoyer lift, urinal, commode,
   nebulizer, suction machine, O2 concentrator, E-tank) directly during the visit. RNICA's DME
   handling exists only at the order/vendor level (`ordersHub.ts`, `PhysicianOrdersBoard.jsx`,
   `OrderPackManagement.jsx`) — there is no confirmed in-visit "what does this patient need today"
   itemized checklist feeding those orders. This is a real workflow gap: the reference system lets
   assessment-time observation trigger ordering in one place; RNICA appears to require a separate
   ordering workflow entirely disconnected from the assessment screen.
3. **A dedicated IV therapy assessment panel.** The reference system captures type, size, location,
   insertion date, dressing type, change frequency, flush solution/frequency, and purpose for any
   IV access, with a "No IVs" fast-path checkbox. No equivalent panel was found anywhere in RNICA.
   For a hospice population with occasional IV/subQ access needs, this is a real, if likely
   low-frequency, documentation gap.
4. **Disaster Triage — CORRECTION (post-publication):** this item originally claimed Disaster
   Triage was "confirmed still absent from the codebase." **That was incorrect.** A full Disaster
   Triage card already exists in the `safety` section of `RNICA.jsx` (`disasterLevel`,
   `disasterLevelOneConditions`, `disasterLevelTwoConditions`, `disasterLevelThreeConditions`) using
   the same three-level, criteria-driven pattern described below — bed/chair-confined, dependent on
   walker/cane, lives above ground floor, requires electricity for medical equipment. The original
   grep result set that produced this claim was misread. See
   `RNICA_DISASTER_TRIAGE_FIELD_CLASSIFICATION.md` for the verified, field-level inventory of what
   already exists versus what is genuinely new (contact/escalation workflow, backup-caregiver
   detail, facility verification, electricity-dependence flags). The reference system's version
   remains a useful comparison for the same reason: three fixed levels, each with concrete,
   checkable criteria driving the level selection rather than a free-text judgment call — RNICA's
   existing implementation already follows this pattern.
5. **A single, compact "Personal Care & Support Needs" instrument.** The reference system captures
   Hospice Aide / Volunteer / Community Support needs (each with a fixed small option set) in three
   tight rows. RNICA has a `personalCare` module per the screen authority matrix, but its detailed
   field-level shape has not been verified this session and should be checked against this
   reference pattern before assuming parity.
6. **Explicit score-level descriptive helper text next to functional scales.** The reference system
   shows a yellow inline explanation of what the selected KPS/PPS/FAST value actually means
   clinically, immediately next to the dropdown. This reduces reliance on the nurse's memorized
   scale definitions and is a real training-burden reducer; no equivalent was found in RNICA's
   functional-status handling.
7. **A visible, structured cross-system comorbidity checklist organized by HOPE I-code category**
   (Heart/Circulation, GI, GU, Infections, Metabolic, Neurological, Pulmonary, Other) as a single
   compact grid the nurse checks once. RNICA's `diagnoses` module owns comorbidities per the screen
   matrix, but whether it presents this exact category-grouped, HOPE-I-coded checklist shape (vs.
   a longer free-form list) is unverified this session and worth confirming — if RNICA's version
   is a longer scrolling list instead of a compact category grid, that is a real density regression
   relative to the reference system.

---

## Part 5 — Top 20 Opportunities (Ranked)

| # | Priority | Opportunity | Nurse Time Saved | Doc Quality | Reduced Omissions | Training Burden | Workflow |
|---|---|---|---|---|---|---|---|
| 1 | **High** | Add a quantified ADL dependence score (6-item, 0-3 scale, auto-total) to Functional Status | Medium | High | High | Low | High |
| 2 | **High** | Add itemized in-visit DME device-need checklist, wired to trigger the existing ordering workflow rather than duplicating it | High | High | High | Low | High |
| 3 | **High** | ~~Build Disaster Triage under Safety~~ — CORRECTED: already exists (`safety.disasterLevel*`, criteria-driven 3-level pattern). Remaining work is de-duplicating its 4 policy-factor checkboxes against existing Mobility/Musculoskeletal fields — see `RNICA_DISASTER_TRIAGE_FIELD_CLASSIFICATION.md` | Low | Medium | Medium | Low | Low |
| 4 | **High** | Add inline descriptive helper text for KPS/PPS/FAST/NYHA score meanings next to each dropdown | Low | Medium | Medium | High | Low |
| 5 | **High** | Resolve the Musculoskeletal/Falls duplicate-field conflict identified in this session's inventory (`fallHistory.*` inside Musculoskeletal) before it causes conflicting-source documentation | Low | High | High | Low | Medium |
| 6 | **Medium** | Add a compact, single-instrument "Mobility" presentation (Ambulatory vs. Non-Ambulatory exclusive branch, device + endurance in one place) instead of scattering mobility fields across Musculoskeletal | Medium | Medium | Medium | Medium | High |
| 7 | **Medium** | Verify and, if needed, compact the Diagnosis & LCD comorbidity checklist into the reference system's category-grouped grid shape | Low | Medium | Low | Low | Medium |
| 8 | **Medium** | Add a dedicated compact IV/subQ access panel with a "No IVs" fast path | Low | Medium | Low | Low | Low |
| 9 | **Medium** | Apply the reference system's compact self-scoring-grid visual pattern (used well for Braden/PAINAD) to any future RNICA scored instrument, rather than inventing a new visual pattern per score | Low | Medium | Low | Medium | Medium |
| 10 | **Medium** | Resolve the ACP field-count gap (3 enforced vs. 6 target) already logged in `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md` — the reference system's F2000/F2100/F2200 pattern is a reasonable existing analog to benchmark against | Low | High | Medium | Low | Low |
| 11 | **Medium** | Confirm Personal Care & Support Needs module matches the reference system's tight three-row shape rather than a longer form | Low | Low | Low | Low | Medium |
| 12 | **Medium** | Add an explicit "Response to treatment" concept where clinically meaningful (already flagged as a structural gap in the Unresolved Decisions doc) — the reference system does not model this well either, so this is an opportunity to exceed both systems, not just match one | Medium | High | Medium | Low | Medium |
| 13 | **Low** | Consider a single always-visible patient-context banner (SOC/EOC/Dx/Age/Allergies/Triage/Code Status/LOC/Payer) at the top of every RNICA screen, mirroring the reference system's persistent header — reduces context-switch cost when moving between the 13 screens | Medium | Low | Low | Low | Medium |
| 14 | **Low** | Evaluate whether RNICA's Fall Risk/Morse scoring should be added to the hard-required Lock list — currently an open discovery item per the Screen Authority Matrix, and the reference system treats it as a first-class linked assessment | Low | Medium | Medium | Low | Low |
| 15 | **Low** | Consider a compact "Teaching Needs" checklist matching the reference system's flat 7-item shape (Diagnosis/Meds/Med Reconciliation/Oxygen/DME/Infection Control/Controlled-med safety) if RNICA's current version differs materially — unverified this session | Low | Low | Low | Medium | Low |
| 16 | **Low** | Investigate whether RNICA's `record.status = "DRAFT"` reset on every autosave tick (confirmed pre-existing defect, `visits.py:1118`) creates any nurse-facing confusion comparable to the reference system's clean Progress Status stepper | Low | Medium | Low | Low | Low |
| 17 | **Low** | Consider surfacing RNICA's readiness/blocker list in a persistently visible location analogous to the reference system's always-present top toolbar, rather than requiring a screen navigation to see it | Medium | Low | Low | Low | Medium |
| 18 | **Low** | Evaluate whether Genitourinary's catheter/urinary-status/ostomy triple-overlap (already flagged in Unresolved Decisions) should be resolved using the reference system's single-row condensed pattern as a density reference, once the ownership question is settled | Low | Medium | Medium | Low | Low |
| 19 | **Low** | Consider whether Vitals should adopt the reference system's single-row condensed display (Temp/Pulse/Resp/BP-by-position/Ht/Wt/MAC/BMI/O2-Sat-by-device in one compact strip) if RNICA's vitals module is currently more spread out — unverified this session, worth a follow-up visual check | Low | Low | Low | Low | Low |
| 20 | **Low** | Evaluate borrowing the reference system's exclusive-radio Ambulatory/Non-Ambulatory branch pattern generally as a model for other true either/or clinical states elsewhere in RNICA, independent of the Mobility-specific opportunity above | Low | Low | Low | Medium | Low |

---

## Part 6 — Ideas We Should Reject

1. **The single-page, unlimited-scroll architecture itself.** This is precisely the pattern the
   owner has repeatedly and correctly flagged as causing nurse-miss risk and excessive scrolling in
   RNICA's own prior iterations. Copying the reference system's overall page shape would reintroduce
   the exact problem RNICA's redesign work this session exists to solve. The reference system's
   *individual instruments* are worth studying; its *page architecture* is not.
2. **Duplicating the same clinical fact in multiple places on the same screen "for convenience."**
   The reference system records catheter/urostomy status in at least three separate places
   (Urinary Continence row, Urine row, Catheter row) and Falls-related fields inside a body-system
   panel that a separate module is supposed to own. This is a documentation-integrity anti-pattern,
   not a UX convenience — RNICA should not adopt it even where scanning speed briefly appears to
   benefit.
3. **All-scales-always-visible functional status.** The reference system always shows KPS, PPS,
   FAST, and NYHA regardless of diagnosis relevance. RNICA's existing diagnosis-conditional display
   (FAST only for dementia, NYHA only for cardiac) is the more disciplined pattern and should not be
   abandoned in favor of "just show everything, always."
4. **A single giant auto-generated narrative textbox as the primary clinical record.** The reference
   system's "Narrative And Disease Trajectory" panel is one large freeform paragraph block covering
   the entire visit. RNICA's Finalization screen already treats narrative generation, readiness,
   attestation, and signature as separate, governed steps — collapsing that back into one big
   text block for the sake of "matching" the reference system would remove structure RNICA has
   already correctly built.
5. **Checkbox-based (non-exclusive) recording of what are actually mutually exclusive physiologic
   states**, as seen in the reference system's Pulse assessment (Regular/Irregular/Weak/
   Tachycardia/Bradycardia/Absent presented as independent checkboxes per pulse site, allowing
   contradictory combinations like "Irregular" and "Weak" and "Tachycardia" simultaneously with no
   guardrail). This is a documentation-safety hazard in the reference system, not a strength — do
   not import this control-type choice into RNICA even where it looks compact.
6. **A LCD eligibility checklist with no computed verdict.** The reference system's "Validate LCD
   Eligibility" button and long Yes/No/Select dropdown list give no visible indication of what the
   answers actually mean for eligibility. RNICA's real backend-evaluated LCD facts model is already
   architecturally superior and should not be replaced with a static form for the sake of visual
   simplicity.
7. **A 20+ item flat sidebar tree as primary navigation.** The reference system's left-hand tree
   (Admission/Assessment/Tx-Med-DME/IDG/POC/Issues-Outcome/Physician/Visit Notes/HA/Volunteer/
   Comm-Progress/Document-Image/Discharge/Bereavement/Compliance/Incident/Misc/Faxes/Care
   Overview/Monthly Schedule) is undifferentiated by frequency or clinical priority. RNICA's
   13-screen, clinically-sequenced tab model is the better foundation and should not be replaced
   with an unranked flat list for the sake of exposing more destinations at once.

---

*No fields, controls, validation rules, HOPE/SFV mappings, or UI were changed to produce this
analysis. All "unverified this session" items (Personal Care shape, Teaching Needs shape,
Vitals layout, Diagnosis comorbidity grid shape) are explicitly flagged as needing a follow-up
look before being treated as confirmed gaps or confirmed parity.*
