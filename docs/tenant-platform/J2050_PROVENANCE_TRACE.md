# J2050 Provenance Trace

Status: OPEN_QUESTION. Repository trace only — no implementation
performed, per instruction.

## CMS Requirement

J2050 — Symptom Impact Screening: A) was a symptom-impact screening
completed, B) date of screening. Not independently re-derived against
primary CMS text this pass (boolean + date structure assumed from the
mapper's existing label, consistent with the CMS item family alongside
J0900/J2030).

## Repository Evidence

`hopeReportMapper.js` line 689:
```js
{ code: "J2050", label: "Symptom Impact Screening", entries: [
  { label: "A. Completed?", value: boolCode(Boolean(sfv.symptomImpactScreeningCompleted || symptomImpact.assessmentDate)).description },
  { label: "B. Date", value: formatDate(sfv.symptomImpactScreeningDate || symptomImpact.assessmentDate) },
] },
```

| ELEMENT | SNS SOURCE | SOURCE FIELD | TRANSFORMATION | VALIDATION | STATUS |
|---|---|---|---|---|---|
| A. Completed? | RNICA form's `sfv` block (self-attestation) OR `formData.symptomImpact` | `sfv.symptomImpactScreeningCompleted` (RNICA `sfv.*`, same self-attestation family as `sfv.reasonNotCompleted` in J2052C) OR `symptomImpact.assessmentDate` | `boolCode(Boolean(...))` | Boolean derivation only, no CMS code-set restriction beyond Yes/No | **OPEN_QUESTION** |
| B. Date | Same two sources | `sfv.symptomImpactScreeningDate` OR `symptomImpact.assessmentDate` | `formatDate` | None | **OPEN_QUESTION** |

## Key Distinction from J2052/J2053

J2052(A/B) and J2053 were remediated by resolving `sfvRequirement`
(the backend `SFVRequirement`/`ClinicalNote`-linked record) via
trigger-scoped ownership (`triggerSourceType` + `triggerVisitId`). J2050
does **not** read `sfvRequirement` at all — its primary source is
`sfv.symptomImpactScreeningCompleted`/`.symptomImpactScreeningDate`,
which live on the RNICA form's local `sfv` block (self-attestation
captured on the *triggering* record, before the SFV outcome is known),
with `formData.symptomImpact.assessmentDate` as a fallback. This is the
same self-attestation class of field that was disqualified as an export
source for J2052C. The SFV ownership fix did not touch this code path,
so J2050 is unaffected by the P0 remediation and remains unresolved.

## Finding

**STATUS: OPEN_QUESTION.** Two open sub-questions:

1. Does `SFVRequirement`/`ClinicalNote` already carry an equivalent
   "symptom impact screening completed/date" signal that could replace
   the RNICA self-attestation reads, mirroring the J2052/J2053 fix
   pattern? Not traced in this pass.
2. If no such backend-side signal exists, is `formData.symptomImpact.
   assessmentDate` (the non-`sfv` fallback) itself trigger-scoped
   correctly, or does it carry the same cross-timepoint risk class that
   was fixed for J2053? Not traced in this pass.

No repository change is proposed here — trace only, per instruction.
