# I0010 Principal Diagnosis Provenance Trace

Status: Corrects the prior `I0000_PROVENANCE_TRACE.md`, which did not
distinguish I0010 from I0000. This document performs the two required
traces separately: (A) CMS authority, (B) repository trace, including
the requested full UI→export chain and a duplicate-editable-authority
check.

Last-verified commit: `e3806cb2a480ddff7c1417fb6c836371016c45ed` (HEAD at
time of this trace). Verification date: 2026-09-23.

## A. CMS Authority Trace

**NOT_VERIFIED.** No CMS HOPE Guidance Manual, item-set specification, or
equivalent primary CMS source document is stored anywhere in this
repository. Searched: `docs/**` for "CMS HOPE", "HOPE Guidance Manual",
"CMS Manual", "CMS Authority" — the only regulatory-citation documents
found are `docs/sns-emr-multitenant-docs/regulatory_references.md`
(cites CMS State Operations Manual Appendix M — unrelated to the HOPE
item set) and the California Title 22 citations in
`app/models/patient_response.py` (unrelated). **Missing official
source**: a stored CMS HOPE Item Set / Guidance Manual (or an
equivalent internal citation record naming document, version, effective
period, and page/item location) that could confirm I0010's exact label,
response set, and applicable timepoints, and confirm or refute whether
`I0000` is a real, distinct CMS item. This gap applies equally to I0010
and I0000 — CMS authority cannot be verified for either from repository
contents alone.

## B. Repository Trace

### B.1 — I0010 (registry-confirmed as a real code)

`backend/app/domain/forms/form_registry.py` lines 371-376,
`HOPE_DIAGNOSIS_ITEM_CODES = ["I0010", "I0600", "I6202", "I8005"]` —
I0010 **is** present in this backend registry of declared HOPE item
codes (VERIFIED BY REPOSITORY TRACE that the registry declares it; CMS
correctness of the registry itself is NOT_VERIFIED per Section A).

### B.2 — I0000 (NOT in the registry)

`I0000` does **not** appear in `HOPE_DIAGNOSIS_ITEM_CODES` or any other
list in `form_registry.py`. This is independently corroborated by a
pre-existing repository document not created this session:
`docs/tenant-platform/ITEM_CODE_CONFLICT_MATRIX.md`, "Conflict 5 — I0000
group code not in any registry list" (lines 92-100), which reaches the
same conclusion: *"Status: NOT_VERIFIED — whether `I0000` is a real CMS
item code or an internal grouping label cannot be determined from
repository evidence."* This is external corroboration (a document this
session did not author), not self-referential evidence.

**Correction to `I0000_PROVENANCE_TRACE.md`**: that document cited the
source function as `diagnosisEntries(diagnoses)`. The exact call site
(`hopeReportMapper.js` line 676) is:
```js
{ code: "I0000", label: "Comorbidities and Co-existing Conditions", entries: [{ label: "Active conditions", value: diagnosisList(diagnoses) }] },
```
The field value is produced by `diagnosisList()` (line 379), which
internally calls `diagnosisEntries()` (line 359) and joins the result
with `", "`. The prior trace's function citation was imprecise (named
the inner helper, not the one actually invoked at the I0000 call site);
the underlying source path (`RnicaAssessment.form_data.diagnoses`) was
correct. I0000 is therefore **not** a "Principal Diagnosis" duplicate of
I0010 — its own label is "Comorbidities and Co-existing Conditions," a
different clinical concept, which further weakens (does not eliminate)
the case that it is meant to be a genuine single CMS item — it reads
like an internal summary/grouping row, consistent with
`ITEM_CODE_CONFLICT_MATRIX.md`'s finding.

### B.3 — I0010 full trace (UI → export)

| Stage | Repository Evidence |
|---|---|
| UI field | `RNICA.jsx` Diagnoses screen; principal diagnosis entry with `icd10`/`description`, tagged `hope: ["I0010","J0050"]` in the sidebar registry (`RNICA.jsx:208`, per `ITEM_CODE_CONFLICT_MATRIX.md` Conflict 3 citation) |
| Form state | `formData.diagnoses.primaryDiagnosis = { icd10, description, hopeDiagnosisCategory }` |
| Save payload | RNICA assessment save persists the full `form_data` JSON blob (standard RNICA save path; no field-specific endpoint for this value — same mechanism as all other RNICA `form_data` fields traced this session) |
| API | RNICA assessment create/update endpoints in `backend/app/api/visits.py` (persist `form_data` as-is; no per-field transformation for diagnoses at write time — confirmed by grep: only `primaryDiagnosis` reads exist at `visits.py:263,313`, both read-side for HOPE-comorbidity/CDS purposes, not a diagnosis-specific write transformation) |
| Persistence | `RnicaAssessment.form_data` (JSONB column) |
| Load/hydration | `hopeReportMapper.js` reads `diagnoses = formData.diagnoses` from the loaded `RnicaAssessment.form_data` for the record being exported |
| Diagnosis category mapping | `principalDiagnosisCategoryCode = diagnoses.primaryDiagnosis?.hopeDiagnosisCategory`, looked up against `PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS` (line 576-579) |
| I0010 transformation | `principalDiagnosis = "${icd10} - ${description}"` (line 575); emitted as `{ code: "I0010", label: "Principal Diagnosis", entries: [Category, ICD-10 detail] }` (lines 671-673) |
| HOPE export | Section I of the exported HOPE report |
| Validation | Category code restricted to `PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS` keys; unmapped → placeholder. ICD-10 text itself is free (not validated against an ICD-10 code list) |
| Tests | Not independently located in this pass — no dedicated I0010 unit test was found in `hopeReportMapper.test.js` search results; this is itself an **OPEN_QUESTION** (test coverage for I0010 specifically not confirmed) |

### B.4 — Duplicate editable authority check

A **second, independently editable** primary/terminal-diagnosis field
exists outside RNICA:

| | |
|---|---|
| Model | `backend/app/models/patient.py:53` — `Patient.primary_diagnosis = Column(String(255), nullable=False)` |
| UI | `sns-emr-frontend/src/charts/PatientFacesheet.jsx` — editable `Icd10DiagnosisInput` bound to `draft.primary_diagnosis` (line 1834), labeled "Primary Diagnosis" in the Diagnoses & Allergies card and "Terminal Diagnosis" in the Hospice Snapshot card (line 987) |
| Save payload | `buildPayload()` (`PatientFacesheet.jsx:391,434`) submits `primary_diagnosis` to the Facesheet save endpoint |
| API | `backend/app/api/patients.py` (multiple read/write sites: lines 94, 99, 208, 212, 234, 262, 396, 660, 1024, 1337-1339) |
| Consumers | `app/billing/services/claim_export_service.py`, `app/services/chart_pdf.py`, `app/services/eligibility/engine.py` — this field feeds billing/claims, chart PDF, and eligibility, **not** the HOPE mapper |

**Finding: `DUPLICATE_EDITABLE_AUTHORITY` — CONFIRMED.** Two
independently editable "primary diagnosis" concepts exist:
1. `Patient.primary_diagnosis` (Facesheet-owned; feeds billing/claims/
   chart PDF/eligibility)
2. `RnicaAssessment.form_data.diagnoses.primaryDiagnosis` (RNICA-owned;
   feeds HOPE I0010 export)

**Repository trace confirms the HOPE I0010 exporter reads exclusively
from source (2), never source (1).** No code path was found where
`hopeReportMapper.js` or `visits.py`'s HOPE-adjacent code reads
`Patient.primary_diagnosis`. This means the two fields can diverge
(a clinician could update the Facesheet's diagnosis without it ever
appearing in a HOPE export, or vice versa) with no reconciliation,
cross-validation, or single-source-of-truth enforcement between them.

**Correction (post-commit verification pass):** this finding is **not**
new to this engagement. A pre-existing repository document (not created
this session), `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` line 1363, already
documents the same duplication under "Chart primary diagnosis": *"is a
distinct RNICA assertion, not a mirror... No removal — keep both,
labelled distinctly."* That document treats it as an accepted,
by-design separation (Facesheet = chart/billing-facing, RNICA = HOPE-
facing) rather than an open defect, and does not flag it as
`DUPLICATE_EDITABLE_AUTHORITY` or escalate it as unresolved. This trace
does not adopt that prior document's conclusion uncritically: "keep
both, labelled distinctly" does not by itself establish that no
cross-validation is needed, nor does it confirm clinicians are never
confused by two differently-labeled diagnosis fields on different
screens. The prior document's recommendation is noted here as existing,
prior guidance — the open question of whether it is sufficient (vs.
requiring active reconciliation/cross-validation) is preserved below,
not resolved by this trace either.

**No reconciliation is implemented or proposed here**, per instruction.
This is escalated as an open question requiring a policy decision on
which field is the single source of truth for hospice principal/
terminal diagnosis, and whether the HOPE exporter's current exclusive
read from RNICA is correct or should incorporate/validate against the
Facesheet value.

## Summary

| Question | Answer |
|---|---|
| I0010 authoritative source | RNICA `diagnoses.primaryDiagnosis` (VERIFIED BY REPOSITORY TRACE as the HOPE exporter's sole read path) |
| I0010 CMS accuracy | NOT_VERIFIED (no CMS authority document in repo) |
| I0000 real CMS item or internal label | OPEN_QUESTION (corroborated by pre-existing `ITEM_CODE_CONFLICT_MATRIX.md`) |
| I0000 == I0010 | NO — confirmed distinct labels, distinct source functions, distinct registry status |
| Duplicate editable authority | **YES** — `Patient.primary_diagnosis` (Facesheet) vs. `RnicaAssessment.form_data.diagnoses.primaryDiagnosis` (RNICA/HOPE), unsynchronized. **Not newly discovered** — already documented in pre-existing `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md:1363` as an accepted by-design separation, though that document does not evaluate sufficiency of "keep both, labelled distinctly" against cross-validation risk |
| Reconciliation implemented | NO — requires a Romel/Clinical Operations decision on single source of truth, or explicit re-affirmation that the existing "keep both, labelled distinctly" guidance is sufficient |
