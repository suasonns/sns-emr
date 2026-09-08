# Demo Readiness Report — Thursday Presentation

Branch: `feature/production-hnp-clinical-runtime`
Prepared: 2026-09-08, same day as the companion Deployment Readiness Report
(`docs/planning/deployment_readiness_2026-09-08.md`). That report answers "can this be deployed?"
This report answers **"can I safely present this Thursday?"** — a different, narrower question.

**Verification method**: this report is based on live testing performed today, not inspection
alone. Backend was found down (the PID from an earlier session had died) and was restarted; the
narrative engine and evidence center were invoked directly against the real Loren, Norma, and
Kessler records; the disease-category unit test suite was run. One methodology limitation:
verification calls were made by invoking the service functions directly in a Python shell, not
through an authenticated HTTP request, because no test bearer token was available in this
session. **A real click-through in the browser, logged in as a real user, has not yet been done
and is the single most important remaining action before Thursday** (see Section 9).

---

## Section 1 — Feature Inventory

| Feature | Touched by current branch? | Modified this cycle? | Safe for demo? |
|---|---|---|---|
| RNICA structured assessment form (existing fields) | Y (RNICA.jsx modified) | Y | Y — existing functionality, only additive changes made |
| RNICA Clinical Narrative card (existing quality-gated narrative field) | Y | N (untouched — new panel added alongside it) | Y |
| Documentation Insights panel (new) | Y | Y (new this cycle) | Y, with a live walkthrough first — see Section 3 |
| Narrative V2 preview (new backend + new UI trigger) | Y | Y (new this cycle) | Y, but **budget 30–40 seconds of visible wait per generation** — see Section 2 |
| Evidence Center (new patient-chart panel) | Y | Y (new this cycle) | Y — verified functional, see Section 4 |
| Performance Status fields (PPS/KPS/NYHA/FAST/ECOG) | Y (scale interpretation additions) | Y (interpretation text added; underlying fields pre-existing) | **CONDITIONAL — see Section 2.** PPS/KPS/NYHA confirmed populated for Loren; ECOG is blank for Norma; FAST is blank for Kessler |
| Disease Category Detection (CHF/Cancer/Dementia routing) | Y (new file) | Y (new this cycle) | Y — 12/12 unit tests passing |
| Patient chart navigation / sidebar | Y (one new nav entry added) | Y (additive only) | Y |
| Facesheet, Diagnoses, Medications (existing screens) | N (not touched by this branch) | N | Y — unaffected by this cycle's changes |
| Alembic / DB schema / models | N | N | Y — nothing pending in this area at all |

---

## Section 2 — RNICA

| Check | Result |
|---|---|
| RNICA generation works | **PASS** — `generate_rnica_narrative_v2()` invoked directly against all three assessments; all three returned a complete result with no exception |
| Loren validates | **PASS** — narrative generated, `full_text` 9,005 characters, 1 documentation gap detected, PPS 40%/KPS 40/NYHA IV all present in structured data |
| Norma validates | **PASS with a data gap** — narrative generated (8,346 characters, 4 documentation gaps detected), but her structured `performanceStatus.ecog` field is **blank**, and no ECOG value was found in harvested evidence either |
| Kessler validates | **PASS with a data gap** — narrative generated (8,743 characters, 5 documentation gaps detected), but her structured `performanceStatus.fast` field is **blank**, and no FAST value was found in harvested evidence either |
| PPS displays | **PASS** — confirmed populated for Loren (`40%`) |
| KPS displays | **PASS** — confirmed populated for Loren (`40`) |
| NYHA displays | **PASS** — confirmed populated for Loren (`IV`) |
| FAST displays | **FAIL for the planned demo patient.** Kessler's FAST field is empty in the database. Her primary diagnosis (dementia, ICD-10 G31.1) is correctly on file, so disease-category detection and general narrative content will still work, but there is nothing to show on screen if the script specifically calls out "watch FAST display." |
| ECOG displays | **FAIL for the planned demo patient.** Norma's ECOG field is empty, and her structured `diagnoses.primaryDiagnosis` field on the RNICA form itself is also blank (her cancer diagnosis exists only at the patient level, not on this specific assessment). No ECOG value was found anywhere. |
| Narrative generates | **PASS** for all three patients, no exceptions |
| No runtime errors | **PASS** — zero exceptions across all three narrative generations and all three evidence-center calls. One non-fatal log line appeared for every call: `"Tenant context unavailable; returning mandatory rules only"` — expected in this test methodology (direct function call, no request/tenant middleware) and very likely a non-issue in the real authenticated app, but **not yet confirmed live in-browser** |

**Bottom line for Section 2**: the narrative engine itself is stable and error-free across all
three reference patients. The two failures are **data gaps in the demo patients' records**, not
code defects — PPS/KPS/NYHA are proven to work; FAST and ECOG have no bug found, but also no data
to display for Kessler/Norma today.

---

## Section 3 — Documentation Insights

| Check | Result |
|---|---|
| Panel renders | Not yet verified in-browser (see caveat above). Code inspection confirms the panel (`DocumentationInsightsPanel` in `RNICA.jsx`) has explicit `idle / loading / ready / error` states, so it should degrade to a visible error state rather than a blank crash if the API call fails |
| No crashes | Backend calls it depends on (`narrative-v2/preview`) were verified error-free for all 3 patients at the service layer |
| No API failures | Same as above — service layer confirmed clean; HTTP layer (auth, request/response shape) not yet exercised live |
| No blocking bugs | None found in code review or service-layer testing |
| No accidental write operations | **Confirmed by design and by code inspection**: the panel is explicitly documented in its own source comments as "read-only until the RN explicitly clicks Insert... never auto-populates a field, never auto-scores PPS/KPS/FAST/ADLs." The backend endpoint it calls (`preview_rnica_narrative_v2`) has no `db.add`/`commit`/`delete` calls — confirmed via the same grep check used in the Deployment Readiness Report |
| Safe to demonstrate | **Yes, conditionally** — safe from a data-integrity standpoint; recommend one live click-through before Thursday to see the actual rendered panel and timing, not just confirm the underlying calls succeed |

---

## Section 4 — Evidence Center

| Check | Result |
|---|---|
| UI loads | Backend aggregation (`build_evidence_center()`) verified error-free and fast (under 1 second) for all three patients at the service layer; in-browser render not yet separately verified |
| No destructive actions | Confirmed — `evidence_center_service.py` has zero write calls (`db.add`/`commit`/`delete`/`merge`/`update`), confirmed via grep |
| No production data modification | Confirmed for the same reason — this panel is a pure read/aggregate view |
| No demo blockers | None found. This is the lowest-risk new feature in the entire inventory: fast, read-only, and error-free against all three reference patients |

---

## Section 5 — Patient Records

| Check | Result |
|---|---|
| Patient overview loads | Not touched by this branch — no regression risk introduced |
| Assessments load | Not touched by this branch, except for the new preview endpoint added alongside existing RNICA endpoints — existing assessment loading is unaffected |
| Diagnoses load | Not touched by this branch. Note (data observation, not a bug): Norma's specific RNICA assessment has a blank `diagnoses.primaryDiagnosis` structured field even though her patient-level record correctly shows "Metastatic breast cancer (Stage IV, with bone metastasis)" — if the demo script drills into that specific structured field for Norma, it will appear empty |
| Performance status loads | Loads correctly where data exists (Loren); see Section 2 for the two data gaps |
| No broken navigation | The only navigation change is one additive sidebar entry ("AI Documentation" → Evidence Center); all existing entries are untouched |

---

## Section 6 — High Risk Files

For every file marked HOLD or NEEDS TEST in the Deployment Readiness Report:

| File | Risk | Why it exists | Why it should not deploy yet | Required action |
|---|---|---|---|---|
| `sns-emr-frontend/src/components/RNICA.jsx` | **High** — largest diff in the branch (446 insertions / 34 deletions), touches the most-used clinical screen | Adds the new Documentation Insights panel directly into the existing Clinical Narrative card | The 34 deleted lines in an existing, heavily-used file have not been individually reviewed against a live RNICA screen; a regression here would affect every RN's daily documentation workflow, not just the new feature | Open a real RNICA in the browser, exercise the existing Clinical Narrative card end-to-end, and confirm nothing that previously worked has changed, before this is shown live |
| `backend/scripts/onboard_norma_from_hnp.py` | Medium-High — writes real patient/document data via the production ingestion pipeline | One-off setup script used to create the Norma demo patient from real source PDFs | Re-running it against a database where Norma already exists risks duplicate patient/document rows | Do not re-run before Thursday; Norma's record already exists and is verified working — leave it alone |
| `backend/scripts/populate_loren_medications_from_pdf.py` | Medium-High — writes real medication rows | One-off fix for a previously flagged "0 medications" gap on Loren's record | Re-running it risks duplicate medication rows | Do not re-run before Thursday; this has already been applied |
| `backend/app/services/evidence_center_service.py` | Medium — new, unreviewed clinical-text generation, but non-destructive | Powers the new Evidence Center's AI documentation narratives | Not yet independently reviewed by a clinician for wording accuracy, only for functional correctness (which passed) | Do one manual read of the AI-generated narrative text for at least one patient before presenting it as clinician-facing output |
| `sns-emr-frontend/src/intake/scaleInterpretations.js` | Low, cosmetic | Client-side scale-interpretation registry | Header comment contains a mojibake-encoded box-drawing line (garbled characters instead of `═══`) — comment-only, does not affect runtime, but looks unprofessional if anyone opens the file during the demo | Re-save the file as UTF-8 to fix the header before Thursday; low priority, cosmetic only |
| `backend/app/services/scale_interpretations.py` | Low-Medium | Backend mirror of the same registry | Must stay in sync with the JS copy or on-screen text could disagree with generated narrative text | Diff the two copies to confirm agreement (not yet done in this report — recommend a quick side-by-side check before Thursday) |
| `backend/backend.pid` | N/A — not a risk, a stray artifact | Leftover from manual backend restarts during development (including the restart performed for this report) | Not source code; must never be committed | Delete and gitignore `backend/*.pid` |

---

## Section 7 — Should Deploy

(Repeated from the Deployment Readiness Report for convenience — see that report for full
per-file reasoning.)

- `backend/app/api/evidence_center.py`
- `backend/app/api/registry.py`
- `backend/app/api/visits.py`
- `sns-emr-frontend/src/api/evidenceCenter.ts`
- `sns-emr-frontend/src/api/icaAssessments.ts`
- `sns-emr-frontend/src/charts/PatientChart.jsx`
- `sns-emr-frontend/src/charts/PatientChartSidebar.jsx`
- `sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.js` (+ its test file — 12/12
  passing, verified today)
- `sns-emr-frontend/src/components/EvidenceCenter.jsx` — verified functional at the service layer
  today; recommend one in-browser click-through before Thursday, but nothing found to block it
- `backend/app/services/evidence_center_service.py` — verified functional and error-free against
  all three reference patients today

## Section 8 — Should Not Deploy

- `sns-emr-frontend/src/components/RNICA.jsx` — **hold until a manual QA pass on the existing
  Clinical Narrative card is done**; this is the one file in the entire inventory with a real,
  unverified regression risk
- `backend/scripts/onboard_norma_from_hnp.py` — one-time setup script, not deployable application
  code; do not re-run
- `backend/scripts/populate_loren_medications_from_pdf.py` — same category, do not re-run
- `backend/backend.pid` — delete, not application code

---

## Section 9 — Demo Script Validation

**Script**: Open patient → Open RNICA → Generate Narrative → View Documentation Insights → View
Performance Status → View Supporting Evidence → Confirm no errors. Repeat for Loren, Norma,
Kessler.

| Step | Loren | Norma | Kessler |
|---|---|---|---|
| Open patient | Not yet tested in-browser (record confirmed to exist) | Not yet tested in-browser (record confirmed to exist) | Not yet tested in-browser (record confirmed to exist) |
| Open RNICA | Assessment confirmed to exist (`1fcea12a-...`) | Assessment confirmed to exist (`cb060604-...`) | Assessment confirmed to exist (`5d39cc37-...`) |
| Generate Narrative | **PASS** — 9,005 chars, ~37s | **PASS** — 8,346 chars, ~31s | **PASS** — 8,743 chars, ~31s |
| View Documentation Insights | Verified at service layer; not yet clicked through in-browser | Same | Same |
| View Performance Status | **PASS** — PPS/KPS/NYHA all populated and correct | **GAP** — ECOG is blank; nothing will display for the one scale this patient is supposed to demonstrate | **GAP** — FAST is blank; nothing will display for the one scale this patient is supposed to demonstrate |
| View Supporting Evidence | **PASS** — Evidence Center returns cleanly | **PASS** — Evidence Center returns cleanly | **PASS** — Evidence Center returns cleanly |
| Confirm no errors | **PASS** — zero exceptions | **PASS** — zero exceptions (aside from the missing-data gap above, which is not an error) | **PASS** — zero exceptions (aside from the missing-data gap above, which is not an error) |

**Timing note**: each Narrative V2 generation took 30–37 seconds. If this is shown live, either
narrate through the wait, pre-generate before walking the room through it, or set audience
expectations up front ("this calls a live AI model, it takes about half a minute").

**Data gap note**: the ECOG (Norma) and FAST (Kessler) gaps are the most important finding in this
entire report for the demo script specifically. Recommended options, in order of preference:
1. Enter the missing ECOG score for Norma and FAST score for Kessler before Thursday (fastest,
   lowest-risk fix — this is a data-entry gap, not a code defect).
2. If there isn't time, adjust the live script to not specifically claim "watch the ECOG/FAST
   score display" for these two patients — show the rest of their narrative and evidence
   (which works correctly) and demonstrate ECOG/FAST/PPS/KPS/NYHA display generically using Loren
   instead, where PPS/KPS/NYHA are all confirmed populated.

---

## Section 10 — Go/No-Go Recommendation

# GO WITH LIMITATIONS

**Rationale**:

- Every backend and service-layer code path exercised today — narrative generation, evidence
  center aggregation, and the disease-category unit tests — ran **with zero exceptions** across
  all three reference patients (Loren, Norma, Kessler). No functional defect was found in any
  new code this cycle.
- The one large, high-risk file (`RNICA.jsx`) has not caused any failure so far, but its 34
  deleted lines in existing, heavily-used code have not been manually walked through live — this
  is a real gap in verification, not a known defect, and should be closed with a short manual
  pass before Thursday.
- Two **data gaps**, not code defects, were found: Norma's ECOG and Kessler's FAST scores are
  blank in the database. These will make two specific demo beats ("watch ECOG/FAST display")
  fail to show anything, though nothing will error or crash.
- No database/schema/migration risk exists in this cycle at all.
- Verification today was performed by calling backend services directly, not through the real
  authenticated browser flow — a final in-browser click-through, logged in as a real user, has
  not yet happened and is the single remaining action that would move this from "GO WITH
  LIMITATIONS" to a clean "GO."

**Before Thursday, in priority order**:
1. Do one authenticated, in-browser click-through of the full demo script for all three patients
   (the one verification step not yet completed).
2. Either populate Norma's ECOG and Kessler's FAST scores, or adjust the script to demonstrate all
   five scales using Loren instead and treat Norma/Kessler as narrative/evidence-only demos.
3. Manually exercise the existing Clinical Narrative card inside `RNICA.jsx` to confirm the 34
   deleted lines didn't remove anything a presenter would rely on.
4. Delete `backend/backend.pid`.
5. Do not re-run `onboard_norma_from_hnp.py` or `populate_loren_medications_from_pdf.py` —
   both patients' records are already correctly set up.
