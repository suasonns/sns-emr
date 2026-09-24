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

## Post-Commit Verification Pass — Expanded Trace

Per instruction, the full UI→export chain and isolation questions were
re-examined rather than left as a single self-attestation label:

| Question | Answer | Evidence |
|---|---|---|
| CMS response set | Not independently re-derived — no CMS authority document exists in the repository for J2050 (same gap as I0010/I0000, see `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md` Section A) | NOT_VERIFIED |
| Applicable timepoints | Emitted identically for ADM/HUV1/HUV2 (per `ADM/HUV1/HUV2_COMPLETENESS_MATRIX.md`); not emitted at Discharge (Section J is ADM/HUV1/HUV2-only per the mapper's `sections` construction traced earlier this engagement) | VERIFIED BY REPOSITORY TRACE |
| Actual screening vs. self-attestation | `sfv.symptomImpactScreeningCompleted`/`.symptomImpactScreeningDate` are fields inside the RNICA form's own `sfv` JSON block — the same self-attestation family as `sfv.reasonNotCompleted` (J2052C). No corroborating backend record (`SFVRequirement`/`ClinicalNote`) is read for J2050 at all — confirmed by the absence of any `sfvRequirement`/`sfvStatus` reference in the J2050 line (`hopeReportMapper.js:689`, contrast with J2052/J2053 at lines 691-692 which do reference `sfvStatus`/`sfvRequirement`) | VERIFIED BY REPOSITORY TRACE that no backend corroboration exists |
| Who records it / when | The RNICA clinician, at the time the RNICA form itself is completed (trigger time) — not at SFV completion time. This is a structural mismatch: J2050 asks whether screening was completed, but reads a field set before the screening's own outcome (the SFV) is known | VERIFIED BY REPOSITORY TRACE (structural, same reasoning as J2052C's trigger-vs-completion timing mismatch) |
| Date without a completed response accepted? | Yes — the transformation is `boolCode(Boolean(sfv.symptomImpactScreeningCompleted \|\| symptomImpact.assessmentDate))`; a truthy `symptomImpact.assessmentDate` alone can satisfy "Completed?" even if `sfv.symptomImpactScreeningCompleted` was never set, and vice versa. No cross-validation between the two OR'd fields | VERIFIED BY REPOSITORY TRACE — NOT_VERIFIED whether this is CMS-conformant |
| Can unrelated visits supply it? | `symptomImpact.assessmentDate` is read from the *same* `RnicaAssessment.form_data` as the exported record (not a separate patient-wide query like the pre-fix J2052/J2053 defect) — so it does **not** share the cross-timepoint SFVRequirement-selection defect. However, whether `symptomImpact.assessmentDate` itself is reliably re-populated per-timepoint (vs. carried over/stale from a prior RNICA save) was not independently traced this pass | OPEN_QUESTION (narrower than initially stated — not a cross-timepoint SFV leak, but an unverified within-record staleness question) |
| ADM/HUV1/HUV2 isolation | Each timepoint reads its own `RnicaAssessment.form_data` row (VERIFIED BY REPOSITORY TRACE per `HUV1_PROVENANCE_TRACE.md`/`HUV2_PROVENANCE_TRACE.md`, which independently confirmed this isolation mechanism for the mapper generally) — so J2050 does not cross ADM/HUV1/HUV2 boundaries the way the pre-fix SFV selection did | VERIFIED BY REPOSITORY TRACE |
| Historical accepted records stable? | Not traced — no query was run against historical export records (no live DB available this session) | NOT_VERIFIED |
| Authoritative or only a candidate? | Only a candidate — it is the sole existing source, not a confirmed-correct one | NOT_VERIFIED |

## Finding

**STATUS: OPEN_QUESTION** (retained, now with expanded evidence rather
than a single-line assertion). The prior framing ("reads RNICA
self-attestation; unaffected by SFV ownership fix") is accurate but
incomplete — corrected here to: J2050 does **not** carry the
cross-timepoint SFVRequirement-selection defect (it never reads
`SFVRequirement` at all), but it does carry (a) a CMS-authority gap
identical to I0010/I0000, (b) an unvalidated OR-fallback between two
independent fields, and (c) an unverified within-record staleness
question for `symptomImpact.assessmentDate`. No repository change is
proposed here — trace only, per instruction.
