# I0010 Principal Diagnosis Provenance Trace

Status: Corrects the prior `I0000_PROVENANCE_TRACE.md`, which did not
distinguish I0010 from I0000. This document performs the two required
traces separately: (A) CMS authority, (B) repository trace, including
the requested full UI→export chain and a duplicate-editable-authority
check.

Last-verified commit: `e3806cb2a480ddff7c1417fb6c836371016c45ed` (HEAD at
time of this trace). Verification date: 2026-09-23.

## A. CMS Authority Trace — VERIFIED BY CMS (reverified against v1.02, 2026-09-24)

**Superseded finding**: the original NOT_VERIFIED conclusion below
applied when no CMS source document had yet been retrieved. A CMS
source has now been retrieved and read directly (see
`HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md` for the full citation/URL/
checksum). No stored copy is kept in-repository (see that register's
Repository Storage Policy Decision) — this repository still contains
no CMS document, but the item's official definition has been verified
externally against the live CMS source, not merely re-asserted.

**I0010. Principal Diagnosis** — *HOPE Guidance Manual v1.02*, Effective
October 1, 2025, p.55. Timepoint: **Admission (ADM) only** (not HUV1,
HUV2, or Discharge). Verbatim CMS instruction:

> "The principal diagnosis is defined as the condition established
> after reviewing all available information to be chiefly responsible
> for the patient's admission... This item should be completed based on
> the patient's principal diagnosis **at the time of admission to
> hospice**... Item completion must be based on what is indicated in
> the clinical record. Do not use sources external to the clinical
> record."

Single-select coded response (e.g., 01=Cancer, 02=Dementia, 06=cardiac
excluding heart failure, 07=heart failure, ..., 99=None of the above).

**v1.01→v1.02 change status**: I0010 does not appear in any of the 7
rows of the v1.01→v1.02 change table — **unchanged between versions**.

**Consequence for this trace**: CMS defines I0010 as an
**admission-time, clinical-record-based** value. It does not itself
name which SNS system-of-record is authoritative when more than one
clinical-record location captures a principal/terminal diagnosis — that
remains an SNS product-ownership decision (Section B.4/B.5 below), not
something CMS resolves.

### A.1 — Original (pre-CMS-retrieval) finding, retained for audit trail

The original pass found: no CMS HOPE Guidance Manual, item-set
specification, or equivalent primary CMS source document was stored
anywhere in this repository. Searched: `docs/**` for "CMS HOPE", "HOPE
Guidance Manual", "CMS Manual", "CMS Authority" — the only regulatory-
citation documents found were `docs/sns-emr-multitenant-docs/regulatory_references.md`
(cites CMS State Operations Manual Appendix M — unrelated to the HOPE
item set) and the California Title 22 citations in
`app/models/patient_response.py` (unrelated). This remains true as a
**repository-storage** fact (still NO stored CMS document in-repo), but
is no longer true as an **externally-verified-authority** fact — see
A above.

I0000's CMS status is unaffected by this reverification: **I0000 does
not appear anywhere in the v1.02 manual's table of contents or body**
(cross-checked against the extracted table of contents, which lists
I0010 at p.54 with no adjacent "I0000" entry). This corroborates, from
an actual CMS-source read (not silence-by-absence in a change table),
the pre-existing `ITEM_CODE_CONFLICT_MATRIX.md` finding that I0000 is
not a confirmed CMS item.

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

### B.5 — Precise ownership-language distinctions (required correction)

The prior pass's summary line, *"I0010 authoritative owner: RNICA
`diagnoses.primaryDiagnosis`, for HOPE export only, not Facesheet,"*
over-stated what has actually been verified. "Authoritative owner" is a
product/clinical-governance conclusion; what this trace can actually
verify by repository trace is narrower — that RNICA is the exporter's
**current read path**, not that RNICA has been designated the
enterprise's authoritative source by any product decision. Distinguishing
these precisely:

| Field | Status |
|---|---|
| **I0010 CURRENT EXPORT SOURCE** | **VERIFIED BY REPOSITORY TRACE** — `RnicaAssessment.form_data.diagnoses.primaryDiagnosis`, read exclusively by `hopeReportMapper.js` (line 575), confirmed by trace in B.3 |
| **I0010 CURRENT EDITABLE SOURCE** | **VERIFIED BY REPOSITORY TRACE** — same RNICA field, editable via `RNICA.jsx` Diagnoses screen |
| **CLINICAL PRINCIPAL DIAGNOSIS OWNER** | **OPEN QUESTION** — no product/clinical-governance document was found in this repository designating either `Patient.primary_diagnosis` or the RNICA field as the enterprise's single clinical authority for principal diagnosis |
| **FACE SHEET DIAGNOSIS OWNER** | **VERIFIED BY REPOSITORY TRACE** — `Patient.primary_diagnosis` (`backend/app/models/patient.py:53`), editable via `PatientFacesheet.jsx` |
| **BILLING/ELIGIBILITY DIAGNOSIS OWNER** | **VERIFIED BY REPOSITORY TRACE** — same `Patient.primary_diagnosis` field, consumed by `claim_export_service.py`, `chart_pdf.py`, `eligibility/engine.py` (B.4 citations) |
| **DUPLICATE EDITABLE AUTHORITY** | **CONFIRMED** (see B.4) — both fields are independently editable, both persist, both can coexist with different values for the same patient/admission, no synchronization code exists, both are read by at least one production workflow, conflicting values are possible, and no deterministic precedence rule exists in code. All 7 elements of the duplicate-authority rubric are independently satisfied by the citations already gathered in B.3/B.4 |
| **PRECEDENCE RULE** | **NOT_VERIFIED** — no code, configuration, or documentation was found establishing which field wins if the two diverge |
| **HISTORICAL ADMISSION SNAPSHOT** | **OPEN QUESTION** — CMS defines I0010 as an admission-time value (Section A). Whether the RNICA field is treated as a fixed admission-time snapshot or can be edited after admission (and if so, whether that retroactively changes a HOPE record already submitted) was **not traced this pass** — this is a genuine gap, not answered by existing evidence |
| **TARGET SINGLE SOURCE OF TRUTH** | **REQUIRES ROMEL DECISION** — not determined by CMS authority (CMS does not name an SNS system-of-record) and not resolved by any repository or product document found |
| **ROMEL DECISION REQUIRED** | **YES** — which field (or a new consolidated field) is authoritative, whether/how to reconcile the two, and whether the RNICA-only HOPE export path is intentionally correct or an oversight |

Mapper usage alone (i.e., the fact that `hopeReportMapper.js` currently
reads the RNICA field) does not, by itself, establish clinical
ownership — it establishes only which field the exporter currently
consumes. Issue #147 remains open pending the Romel decision above.

## Summary

| Question | Answer |
|---|---|
| I0010 CMS definition | **VERIFIED BY CMS** — v1.02, p.55, ADM-only, admission-time clinical-record value (unchanged from v1.01) |
| I0010 current export source | **VERIFIED BY REPOSITORY TRACE** — RNICA `diagnoses.primaryDiagnosis` (exporter's sole read path; not asserted as the enterprise clinical authority — see B.5) |
| I0010 authoritative clinical owner | **OPEN QUESTION — REQUIRES ROMEL DECISION** (see B.5) |
| I0000 real CMS item or internal label | **NOT_VERIFIED**, now corroborated two ways: (1) absent from `HOPE_DIAGNOSIS_ITEM_CODES` registry, (2) absent from the actual CMS v1.02 manual body/TOC — leans toward "internal grouping label," but not conclusively proven since the full 138-page manual body was not exhaustively searched for every possible synonym |
| I0000 == I0010 | NO — confirmed distinct labels, distinct source functions, distinct registry status |
| Duplicate storage vs. duplicate editable authority | Distinct concepts: both fields being *stored* in different tables is not itself a defect; the defect (if any) is that both are independently *editable* with no synchronization or precedence rule — see B.5 |
| Duplicate editable authority | **YES** — `Patient.primary_diagnosis` (Facesheet) vs. `RnicaAssessment.form_data.diagnoses.primaryDiagnosis` (RNICA/HOPE), unsynchronized. **Not newly discovered** — already documented in pre-existing `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md:1363` as an accepted by-design separation, though that document does not evaluate sufficiency of "keep both, labelled distinctly" against cross-validation risk |
| Reconciliation implemented | NO — requires a Romel/Clinical Operations decision on single source of truth, or explicit re-affirmation that the existing "keep both, labelled distinctly" guidance is sufficient |
