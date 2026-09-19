# AI Visibility Matrix

**STATUS: PLANNING / DISCOVERY ONLY — NO CODE — NO SCHEMA — NO MIGRATIONS**

This matrix classifies every RNICA AI/heuristic feature by when its output
becomes visible to the clinician, to answer with evidence: **"Why does AI
feel unresponsive?"** It builds on the AI inventory already established in
`RNICA_USABILITY_AND_AI_REVIEW.md` §2 and `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`.

Classification values: **LIVE**, **SAVE-TRIGGERED**, **LOCK-TRIGGERED**,
**HIDDEN**, **BACKEND ONLY**, **UNKNOWN**.

---

## 1. Classification Table

| AI Feature | Trigger | Classification | Evidence |
|---|---|---|---|
| RN ICA Intelligence panel (summary/findings/recommendations/missing-evidence) | Assessment load (mount/`assessmentId` change) + explicit Save + explicit Lock | **SAVE-TRIGGERED** (and load/lock-triggered; never live while typing) | `RNICA.jsx:10917-10921,11024,11069-11071` |
| LCD disease detection | Debounced 250ms on diagnosis-text change | **LIVE** (debounced, but continuous as text changes) — first link in a chain that then becomes effectively delayed by steps 2–3 below | `RNICA.jsx:1617-1636` |
| LCD config load | Fires only once disease detected | **HIDDEN behind step 1** — technically live-triggered, but invisible until detection resolves; shows a loading label ("Loading LCD criteria…") | `RNICA.jsx:1641-1661,1884` |
| LCD eligibility evaluation | Debounced 250ms, fires only once config resolves | **LIVE but chained/delayed** — up to 3 sequential network round trips before result appears | `RNICA.jsx:1674-1700,1864` |
| Structured findings application ("Build Draft from Documented Findings") | Explicit manual click only | **HIDDEN** — works instantly once triggered, but nothing prompts the clinician to click it; easy to never discover | `RNICA.jsx:2009,2106` |
| Allergy + medication interaction check | Debounced, live as clinician types medication name | **LIVE** — the one unambiguously live AI-adjacent feature in RNICA | `RNICA.jsx:6306,6328-6345` |
| Prior-assessment history / decline comparison | Loads once on section mount | **HIDDEN** — correct and useful, but requires navigating to a specific section; not surfaced in the main Intelligence panel or elsewhere | `RNICA.jsx:2721-2736,2804` |
| Caregiver-related recommendation text (embedded in Intelligence output) | Same as Intelligence panel (Save/Lock/load) | **SAVE-TRIGGERED** and **HIDDEN** (unlabeled, mixed in with generic recommendations) | `backend/app/services/rnica_intelligence.py:98-156` |
| Evidence harvesting (`gather_patient_evidence`, `list_pending_structured_findings`) | Runs as an input step every time Intelligence refreshes | **BACKEND ONLY** from the clinician's perspective — its existence is invisible; only its downstream effect (Intelligence panel content) is seen | `backend/app/api/visits.py:1657-1676` |
| CTI/F2F/Patient Story/Explanation Engine/Survey Readiness AI | No implementation exists | **UNKNOWN / NOT APPLICABLE** — cannot classify visibility of something that was not found in the repository | See `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` "NOT FOUND / NOT BUILT" rows |

---

## 2. What Already Works

- The RN ICA Intelligence panel is real, correctly wired, and produces
  clinically meaningful output (priority, findings, recommendations,
  missing evidence) — it is not broken, just infrequently refreshed
  (`rnica_intelligence.py:184-222`).
- The allergy/interaction checker is a genuinely responsive, live AI-adjacent
  feature and should be treated as the internal reference pattern for "what
  responsive feels like" (`RNICA.jsx:6328-6345`).
- Structured findings application and prior-assessment comparison both work
  correctly when used — the issue is discoverability, not correctness.

## 3. What Is Hidden

- "Build Draft from Documented Findings" (manual trigger, no visual prompt
  drawing attention to it).
- Prior-assessment decline comparison (buried in its own section).
- Caregiver-related recommendation text (present but unlabeled inside the
  general recommendations list, indistinguishable from other findings).

## 4. What Is Not Surfaced

- Evidence harvesting has no independent UI representation — the clinician
  never sees "here is the evidence that was gathered," only the panel that
  results from it.
- Admission-readiness gating (from `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`)
  is not AI, but shares the same "invisible until it fails" pattern as the
  LCD chain — it's an error message, not a proactive indicator.

## 5. What Is Not Wired

- Nothing found in this review is "backend exists, correct data, frontend
  simply forgot to call it" — every AI feature that exists has *some*
  frontend surface. The unresponsiveness is a **timing/discoverability**
  problem, not a **missing wire**. Features with no frontend surface at all
  (CTI, F2F, Patient Story, Explanation Engine, Survey Readiness) also have
  no backend implementation — see
  `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`.

## 6. What Nurses Never See

- The intermediate steps of the LCD chain (detect → config → eval) beyond
  brief loading labels — a nurse sees "Evaluating..." but not *why* three
  separate calls are happening.
- Any indication that the Intelligence panel is stale relative to their
  current in-progress edits (no "your last save was N minutes ago, refresh
  to update AI findings" cue exists).
- Evidence-harvesting inputs (patient evidence bundle, structured findings
  signals) as a standalone, inspectable list — only the derived
  findings/recommendations are shown.

---

## 7. Documented Evidence-Based Answer: "Why does AI feel unresponsive?"

1. **The primary AI surface (Intelligence panel) is refresh-gated on
   Save/Lock, not on typing** — this is the dominant cause. A clinician
   actively working through a section sees no AI feedback until they stop
   and save (`RNICA.jsx:10917-11071`).
2. **The LCD signal requires three sequential, independently-debounced
   network calls** before any result appears, compounding perceived latency
   (`RNICA.jsx:1617-1700`).
3. **Some working AI-adjacent features require an undiscoverable manual
   trigger** (structured-findings draft button), so clinicians who don't
   find the button conclude "there is no AI here" rather than "AI is
   available on request" (`RNICA.jsx:2009,2106`).
4. **The Intelligence engine is a deterministic rules engine, not a
   perceptibly "smart" ML/LLM system** — its `"recommendation_only"` output
   mode (`rnica_intelligence.py:195`) means even when it does run, its
   output can feel more like validation warnings than "AI," reinforcing an
   impression of inactivity even when it is functioning correctly.

This is a **presentation/timing problem, not a missing-capability
problem** for the features that exist. Features that don't exist (CTI,
F2F, Patient Story, Explanation Engine, Survey Readiness) are a separate,
out-of-scope gap, not a wiring defect.

**Inventory and analysis only. No implementation, redesign, or code
change is proposed.**
