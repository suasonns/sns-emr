# Deployment Readiness Report — 2026-09-08

Branch: `feature/production-hnp-clinical-runtime`
Prepared for: Thursday presentation / deploy readiness review
Scope: every uncommitted file in the working tree as of this report. Nothing below has been
merged or deployed. **Nothing should be deployed under category 6 (UNKNOWN).**

Note (2026-09-08, later same day): the RNICA architecture-map and narrative-service work
(`backend/app/services/rnica_narrative_v2_service.py`, `docs/clinical/rnica-architecture-map.md`,
`docs/engineering/architecture_map_policy.md`) has already been **committed** (commit `6bbae0c`)
and is therefore excluded from this inventory — it is no longer uncommitted. Everything listed
below is the *remaining* uncommitted surface.

---

## Summary

| Category | File count | Deploy recommendation |
|---|---|---|
| 1. Safe to Deploy | 0 | — (the only docs/governance changes are already committed, see note above) |
| 2. Clinical Workflow Changes | 6 | HOLD pending manual QA pass — see risk notes per file |
| 3. Database Risk | 0 | None found — no Alembic/migration/model/enum files are uncommitted |
| 4. API Risk | 2 | DEPLOY (both are additive, read-only, no writes) |
| 5. UI Risk | 8 | HOLD pending manual QA pass — see risk notes per file |
| 6. Unknown | 1 | REMOVE (`backend/backend.pid` — a runtime artifact, not source) |

**Total uncommitted files: 17** (6 modified, 11 new/untracked).

---

## 1. Safe to Deploy

None currently uncommitted. The RNICA architecture map, discovery log, regression matrix, and
governance policy were committed separately (`6bbae0c`) before this report and are excluded here.

---

## 2. Clinical Workflow Changes (narrative generation, documentation insights, assessment logic)

| File | Purpose | Risk Level | Safe For Demo | Recommended Action |
|---|---|---|---|---|
| `backend/app/services/evidence_center_service.py` | New service: read-only aggregation of evidence inventory, harvested facts, diagnoses, medications, eligibility/billing-support evidence, computed documentation gaps; also generates AI documentation narratives grounded in existing evidence. Confirmed via grep: **no `db.add`/`commit`/`delete`/`merge`/`update` calls anywhere in the file** — pure read/aggregate. | Medium (new, unreviewed clinical-facing text generation, but non-destructive) | Yes, with caveat: review generated narrative wording before showing to an outside audience | NEEDS TEST — smoke-test against Loren/Norma/Kessler before demo; do not deploy to all users without a manual read of sample output |
| `sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.js` | Detects disease categories (CHF, Cancer, Dementia, Stroke, COPD, Renal, ALS) from diagnoses and maps each to the required performance scale (NYHA, ECOG, FAST, etc.). Pure client-side logic, no API/DB calls. | Low-Medium (drives which scale is required in the UI — a misclassification could suppress a required scale) | Yes | DEPLOY — has a companion unit test file (see below); confirm it passes first |
| `sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.test.js` | Vitest unit tests for the above. | None (test-only) | N/A | DEPLOY — run before merge to confirm it passes |
| `sns-emr-frontend/src/intake/scaleInterpretations.js` | Central scale-interpretation registry (PPS/KPS/NYHA/FAST/ECOG → meaning). Client-side mirror of `backend/app/services/scale_interpretations.py`. **Encoding defect found**: the file's header comment contains garbled UTF-8 box-drawing characters (mojibake, e.g. `â•â•â•...`) instead of the intended `═══` line — cosmetic only (comment text), does not affect runtime, but should be re-saved as UTF-8 before merge. | Low (comment-only defect); Medium (if scale mapping itself has any output errors — not yet independently verified against backend copy) | Yes, after encoding fix | NEEDS TEST — fix mojibake header, diff against `backend/app/services/scale_interpretations.py` to confirm both copies agree, then deploy |
| `backend/app/services/scale_interpretations.py` | Backend mirror of the same scale-interpretation registry, for server-side use (e.g. by `evidence_center_service.py` and narrative generation). | Low-Medium (must stay in sync with the JS copy or narrative text and UI text will disagree) | Yes | NEEDS TEST — confirm backend/frontend copies match before deploy |
| `backend/scripts/loren_evidence_demo.py` | One-off demo script. Explicitly documented in its own docstring as **read-only — does not write to the patient chart, does not create DB rows, does not modify `RnicaAssessment`.** | Low (script, not wired into any running service; only runs if manually invoked) | Yes (as a demo aid) | DEPLOY — safe to keep, but exclude from any automated pipeline; it's a manual demo tool only |

**Two additional scripts in this category involve real writes and are flagged separately for extra caution:**

| File | Purpose | Risk Level | Safe For Demo | Recommended Action |
|---|---|---|---|---|
| `backend/scripts/onboard_norma_from_hnp.py` | One-off script that onboards "Norma" as a real patient record using her real H&P PDFs, running them through the actual production document-ingestion pipeline (Azure Document Intelligence OCR + AI classification + harvest) — same code path as a real upload, invoked directly. **This writes real data** (creates a patient + ingests documents). | Medium-High (writes to the database; correctness depends entirely on the real ingestion pipeline behaving as expected against this input) | Only if Norma is an already-accepted demo/test patient in the target environment | HOLD — do not re-run against a shared/production database without confirming Norma doesn't already exist there; treat as a one-time setup script, not a deployable artifact |
| `backend/scripts/populate_loren_medications_from_pdf.py` | One-off script that populates Loren's medication list from a real source PDF (a specific hospice medication/DME list) to close a previously flagged "0 medications" evidence gap. **This writes real data.** | Medium-High (writes to the database; same category as above) | Only if this is the intended one-time fix for Loren's record in the target environment | HOLD — confirm it has already been run (or should be run) exactly once against the target database before deploy; re-running against an already-populated record risks duplicate medication rows |

---

## 3. Database Risk (Alembic, migrations, models, schema, enums)

**None found.** No files matching Alembic migrations, SQLAlchemy models, schema files, or enum
definitions are present in the current uncommitted set. This category is empty for this cycle —
nothing to isolate or review here.

---

## 4. API Risk (endpoints, requests, responses, validation)

| File | Purpose | Risk Level | Safe For Demo | Recommended Action |
|---|---|---|---|---|
| `backend/app/api/evidence_center.py` | New router: `GET /evidence-center/{patient_id}` (read-only aggregation) and `GET /evidence-center/{patient_id}/narratives` (AI documentation generation, grounded in existing evidence). Both call `get_authorized_patient()` for access control. Docstrings explicitly state no eligibility, certification, prognosis, or discharge recommendations are produced. | Low (GET-only, authorized, no writes) | Yes | DEPLOY |
| `backend/app/api/registry.py` | One-line diff: registers `evidence_center_router` alongside existing routers. | Low (purely additive route registration; does not touch any existing route) | Yes | DEPLOY (depends on `evidence_center.py` above) |
| `backend/app/api/visits.py` | Adds one new endpoint: `POST /visits/rnica/{assessment_id}/narrative-v2/preview`. Docstring and code confirm: fetches the assessment, authorizes the patient, calls `generate_rnica_narrative_v2()`, and returns the result — **no DB write anywhere in this diff.** Labeled "PREVIEW ONLY" in the docstring; the RN must manually copy text into the existing quality-gated `clinicalNarrative` field. | Low-Medium (new code path into the still-evolving narrative engine, but structurally read-only) | Yes | NEEDS TEST — confirm the endpoint returns cleanly for all 3 reference patients (Loren, Norma, Kessler) before demo, since `rnica_narrative_v2_service.py` (its dependency) was just heavily modified today |

---

## 5. UI Risk (frontend screens, components, workflows)

| File | Purpose | Risk Level | Safe For Demo | Recommended Action |
|---|---|---|---|---|
| `sns-emr-frontend/src/charts/PatientChart.jsx` | Wires the new `EvidenceCenter` component into the patient chart's section switch (`case 'evidence-center'`). | Low (additive; does not modify any existing case/route) | Yes | DEPLOY (depends on `EvidenceCenter.jsx` below) |
| `sns-emr-frontend/src/charts/PatientChartSidebar.jsx` | Adds one new sidebar nav entry: "AI Documentation" → `evidence-center`. | Low (additive; existing nav entries untouched) | Yes | DEPLOY (same dependency) |
| `sns-emr-frontend/src/components/EvidenceCenter.jsx` | New patient-chart panel (366 lines) rendering the Evidence Center: evidence inventory, harvested facts, AI-generated documentation narratives. Calls the new read-only `/evidence-center/*` endpoints only. | Medium (new, user-facing screen shown to clinicians for the first time; not yet clinically reviewed end-to-end) | Yes, with a live walkthrough first | NEEDS TEST — click through with a real patient before Thursday; confirm loading/error states render sensibly if the backend call fails |
| `sns-emr-frontend/src/api/evidenceCenter.ts` | New typed API client for the Evidence Center endpoints. | Low (typed wrapper, no logic) | Yes | DEPLOY (depends on backend endpoints above) |
| `sns-emr-frontend/src/api/icaAssessments.ts` | Adds `previewRnicaNarrativeV2()` typed client call for the new preview endpoint, plus response types. Explicit comment: "PREVIEW ONLY — this endpoint never writes to the assessment." | Low (typed wrapper, additive) | Yes | DEPLOY (depends on backend endpoint above) |
| `sns-emr-frontend/src/components/RNICA.jsx` | **Largest and highest-risk file in this inventory: 446 insertions / 34 deletions.** Adds a full new "Documentation Insights" panel inside the existing Clinical Narrative card: compares RN visit discussion against structured RNICA fields, surfaces evidence-supported documentation gaps, and offers an on-demand Narrative V2 preview with an explicit, RN-initiated "Insert into Clinical Narrative" action. Per its own code comments: **read-only until the RN explicitly clicks Insert; never auto-populates a field; never auto-scores PPS/KPS/FAST/ADLs.** Reuses the existing preview endpoint — no new backend surface from this file. Also imports `diagnosesIncludeDiseaseCategory` and `getScaleInterpretation` from the two utility files above. | **High** (largest diff, touches the primary clinical documentation screen used on every RNICA visit; the 34 deletions in an existing, heavily-used file are the specific lines to double-check) | No — do not put in front of an outside audience until manually walked through end-to-end | HOLD — this file needs a dedicated manual QA pass (open a real RNICA, exercise the Documentation Insights panel, confirm the 34 deleted lines were intentional and nothing regressed in the existing Clinical Narrative card) before Thursday |
| `backend/backend.pid` | A stray runtime PID file (`20428`) left over from a manual backend restart during this session's development. Not source code. | N/A (not a code artifact) | N/A | REMOVE — delete the file and add `backend/*.pid` to `.gitignore` if not already present; must never be committed |

---

## 6. Unknown

None. Every uncommitted file above was traced to a specific purpose via diff/docstring inspection;
nothing remains unclassified. (`backend/backend.pid` is listed under UI Risk's table only because
git shows it as untracked in the working tree scan — it is not a UI file and carries no deploy
risk beyond being noise in the diff; treat its recommended action as REMOVE regardless of section
placement.)

---

## Recommended Path to Thursday

1. **Remove immediately**: `backend/backend.pid` (not source; delete and gitignore).
2. **Deploy now** (additive, read-only, low risk): `backend/app/api/evidence_center.py`,
   `backend/app/api/registry.py`, `backend/app/api/visits.py`, `sns-emr-frontend/src/api/evidenceCenter.ts`,
   `sns-emr-frontend/src/api/icaAssessments.ts`, `sns-emr-frontend/src/charts/PatientChart.jsx`,
   `sns-emr-frontend/src/charts/PatientChartSidebar.jsx`,
   `sns-emr-frontend/src/components/rn-ica/diseaseCategoryDetection.js` (+ its test file).
3. **Needs a targeted test pass before deploy**: `backend/app/services/evidence_center_service.py`,
   `backend/app/services/scale_interpretations.py`, `sns-emr-frontend/src/intake/scaleInterpretations.js`
   (fix mojibake header first), `sns-emr-frontend/src/components/EvidenceCenter.jsx`.
4. **Hold for dedicated manual QA — highest priority item**: `sns-emr-frontend/src/components/RNICA.jsx`.
   This is the single highest-risk uncommitted file: it is the largest diff, touches the most-used
   clinical screen, and includes deletions in existing code.
5. **Hold — one-time data-writing scripts, do not treat as deployable code**:
   `backend/scripts/onboard_norma_from_hnp.py`, `backend/scripts/populate_loren_medications_from_pdf.py`.
   Confirm target-environment state before ever running either again.
6. **No database-layer changes are pending** — Alembic/migrations/models/schema are clean.

Nothing in this inventory should be merged until items 3 and 4 have been manually exercised against
at least one of the three reference test patients (Loren, Norma, Kessler — see
`docs/clinical/rnica-architecture-map.md`, Section 17).
