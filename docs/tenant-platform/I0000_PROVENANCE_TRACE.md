# I0000 Provenance Trace

Status: RESOLVED (Issue #147, fixed in this pass). See "Final Disposition"
below. The original OPEN_QUESTION content is preserved unmodified for
history.

## Item Trace

| CMS ITEM | SNS SOURCE RECORD | SNS SOURCE FIELD | TRANSFORMATION | VALIDATION | STATUS |
|---|---|---|---|---|---|
| I0000 | RnicaAssessment.form_data | `diagnosisEntries(diagnoses)` (`hopeReportMapper.js`) | List join of diagnosis entries into a free-text summary row | None | **OPEN_QUESTION** |

## CMS Requirement

**Not independently re-derived.** `I0000` has not been confirmed as a
real, distinct CMS HOPE item code in this engagement — it was not seen
cited elsewhere in the CMS references gathered during this session's
J2052/J2053/HUV1/HUV2 CMS-verification passes. It is emitted by the
mapper as a diagnosis-list summary row, but whether CMS actually defines
an item numbered `I0000` in the HOPE item set was never independently
confirmed against primary CMS text.

## Repository Evidence

`hopeReportMapper.js::mapRnIcaToHopeReport` emits an item tagged `I0000`
sourced from `diagnosisEntries(diagnoses)`, which joins the patient's
diagnosis list from `RnicaAssessment.form_data` into a single free-text
string. No code-set restriction, no validation, and no crosswalk to a
CMS-defined response set exists for this row.

## Finding

**STATUS: OPEN_QUESTION** — two distinct possibilities remain unresolved:

1. `I0000` is a genuine CMS item code and the current free-text,
   unvalidated transformation is a real provenance gap requiring
   CMS-conformant restructuring.
2. `I0000` is an internal-only summary row (not a real CMS item), in
   which case it should be relabeled/removed from CMS-item-coded exports
   rather than treated as an unverified CMS field.

## Resolution Path

This is a CMS-authority lookup, not a repository trace — the repository
side of this question is fully answered (source field and transformation
are known and cited above). Resolution requires confirming against the
CMS HOPE Guidance Manual item list whether `I0000` exists as a defined
item code. No repository change is implied unless that lookup finds a
mismatch between the current free-text output and a real CMS-defined
response set for that code.

## Final Disposition (Issue #147)

**CMS lookup result:** `I0000` does not appear anywhere in the HOPE
Guidance Manual v1.02 TOC or body (unchanged from v1.01). It is not a
real CMS item code — possibility 2 above is confirmed. Independently
corroborated by `HOPE_DIAGNOSIS_ITEM_CODES` (`form_registry.py:371`),
which lists only `I0010`, `I0600`, `I6202`, `I8005` — no `I0000`. The row
was also fully redundant: `Section I` already emits the real CMS-coded
comorbidity items (`...comorbidityItems`, drawn from the structured HOPE
comorbidity findings) immediately before the `I0000` row, so no CMS-coded
data is lost by removing the fake code.

**Decision:** Option B — keep the row as an internal SNS summary, remove
the false CMS-code implication. No test previously covered this row
(confirmed by grep for `"I0000"` across the test suite — zero hits), so
this was a purely additive, uncovered code path.

**Change (`hopeReportMapper.js`, Section I - Active Diagnoses):**
```diff
- { code: "I0000", label: "Comorbidities and Co-existing Conditions", entries: [...] },
+ { code: "SNS-DX", label: "Diagnosis Summary (SNS internal — not a CMS HOPE item)", entries: [...] },
```
`entries` (the underlying `diagnosisList(diagnoses)` value) is unchanged
— only the `code` and `label` were corrected. `I0010` and the real
CMS-coded comorbidity items are untouched.

**Scope boundary respected:** no changes to diagnosis storage, schema,
migrations, HOPE timing, RNICA, J2050/J2051/J2052/J2053, or any export
path other than this one Section I row.

**Tests added** (`hopeReportMapper.test.js`, new
`describe("mapRnIcaToHopeReport — I0000 mislabeled CMS code removed
(Issue #147)")`):
- `"I0000"` no longer resolves to any exported item.
- `"SNS-DX"` resolves, carries the "not a CMS HOPE item" disclaimer in
  its label, and preserves the diagnosis-summary content.
- `I0010` Principal Diagnosis export is unaffected.

**Verification:**
- Targeted (`hopeReportMapper.test.js`): 173/173 passed (was 170; +3).
- Full frontend suite (`npx vitest run`): 321/321 passed, 22/22 files.
- Frontend build (`npm run build`): exit 0, no new warnings.

**Deployment risk: VERY LOW.** Additive/display-only correction to an
untested, uncovered code path; no schema/migration/data-repair impact;
no change to any CMS-coded item's output.

**Deferred, not addressed here:** the separate duplicate-editable-
diagnosis-authority question (`Patient.primary_diagnosis` vs. RNICA
`diagnoses.primaryDiagnosis`) remains a product/governance decision, not
a code defect, and is intentionally out of scope for this fix.
