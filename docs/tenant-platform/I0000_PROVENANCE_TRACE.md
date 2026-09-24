# I0000 Provenance Trace

Status: OPEN_QUESTION. This trace reformats the existing I0000 finding
already on file in `HOPE_ITEM_PROVENANCE_MATRIX.md` into a dedicated
per-item template. No new repository research was performed for this
document — the underlying trace was completed in a prior pass.

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
