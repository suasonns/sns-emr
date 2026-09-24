# J2050 Provenance Trace

Status: OPEN_QUESTION. Repository trace only — no implementation
performed, per instruction.

## CMS Requirement — VERIFIED BY CMS (reverified against v1.02)

Source: *HOPE Guidance Manual v1.02*, Effective October 1, 2025, p.73–74
(see `HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md`). Verified 2026-09-24.
Timepoints: **Admission (ADM), HOPE Update Visit 1 (HUV1), HOPE Update
Visit 2 (HUV2)** — not Discharge. Verbatim CMS text:

> "A. Was a symptom impact screening completed?
> &nbsp;&nbsp;- Code 0, No, if the patient was not screened for symptom
>   impact and Skip to Item M1190, Skin Conditions.
> &nbsp;&nbsp;- Code 1, Yes, if the patient was screened for symptom
>   impact.
>
> B. Date of symptom impact screening
> &nbsp;&nbsp;- Enter the date of the symptom impact screening was
>   performed."

**CMS v1.01→v1.02 change status**: J2050 does not appear in any of the
7 rows of the v1.01→v1.02 change table — **unchanged between
versions**. The prior pass's placeholder assumption ("boolean + date
structure assumed... not independently re-derived against primary CMS
text") is now superseded: the structure is confirmed directly from the
retrieved v1.02 manual text, not assumed.

**Consequence for the OR-fallback question below**: CMS defines A
(completion Boolean) and B (date) as **two related but textually
distinct sub-items on the same instrument**, both driven by "was the
screening completed." CMS's own text does not describe A as derivable
from B or vice versa — it presents A as the primary skip-logic
determinant (0/1) and B as a dependent detail collected once A = 1.
CMS does not, on its face, authorize treating a truthy date alone (with
no completion flag) as sufficient evidence that "A = Completed"; this
supports treating the repository's OR-fallback as an **SNS
implementation choice not shown to be CMS-required**, not as a
CMS-mandated fallback. This is not a production-code change — it is a
documentation-only conclusion for Romel's decision.

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

## Operand-by-Operand Trace of the Exact Production Boolean Expression

**Repository path**: `sns-emr-frontend/src/intake/hopeReportMapper.js`
**Line**: 689
**Complete expression**: `boolCode(Boolean(sfv.symptomImpactScreeningCompleted || symptomImpact.assessmentDate)).description`
**Commit at time of trace**: HEAD `1955016`, unchanged as of this pass.

| | Operand A — `sfv.symptomImpactScreeningCompleted` | Operand B — `symptomImpact.assessmentDate` |
|---|---|---|
| Repository path | `sns-emr-frontend/src/components/RNICA.jsx` | same file |
| UI control | Checkbox, "Symptom Impact Screening Completed" (`RNICA.jsx:9506`) | Not directly editable as a standalone field in this card; populated as part of the `symptomImpact` block elsewhere in the RNICA form (the screening/pain-assessment section) |
| Field default | `false` (`RNICA.jsx:760`) | Not defaulted in the same object literal shown; sourced from the broader `symptomImpact` form section |
| Persisted location | `RnicaAssessment.form_data.sfv.symptomImpactScreeningCompleted` (JSONB) | `RnicaAssessment.form_data.symptomImpact.assessmentDate` (JSONB) |
| Type | Boolean | Date string |
| Null handling | `undefined`/`false` → falsy, does not satisfy the OR on its own | `undefined`/`""` → falsy, does not satisfy the OR on its own |
| Can be populated independently of the other | **YES** — confirmed by inspecting the RNICA form: the checkbox (Operand A) and the symptom-impact date (Operand B, part of the pain/symptom assessment section that also drives J2051) are separate UI controls with no code-level linkage found in `RNICA.jsx` or `hopeReportMapper.js` | **YES** — same evidence, symmetric |
| Applicable timepoint | ADM, HUV1, HUV2 (same `RnicaAssessment.form_data`, read per-record — confirmed isolated per timepoint, see below) | same |
| Tests proving this specific branch | `hopeReportMapper.test.js` sets `sfv.symptomImpactScreeningDate` (a **different** field from `symptomImpactScreeningCompleted`) and `symptomImpact.assessmentDate` together in its shared `baseFormData` helper (lines 769-770, 853-854, 901-902) — **no test isolates Operand A (`symptomImpactScreeningCompleted`) from Operand B (`assessmentDate`)** to independently prove either OR-branch; all located tests exercise both truthy simultaneously | **NOT_VERIFIED** — no test coverage found for the OR-fallback boundary itself |
| Historical behavior | Not traced — no historical export record query available this session (no live DB) | same |
| CMS v1.02 rule | CMS presents completion (A) as the primary skip-logic gate and date (B) as a dependent field collected once A=1; CMS text does not equate a truthy date with "screening was completed" | same |
| Mismatch vs. CMS | **Possible** — the production OR-fallback allows `symptomImpact.assessmentDate` alone (Operand B) to report "A. Completed? = Yes" even if the actual completion checkbox (Operand A) was never checked. CMS's structure (A gates, B depends on A) does not obviously authorize inferring A from B. This is a **documentation-only finding**; no code change is made | Same conclusion, symmetric framing |

## Documentation-Only Truth Table (no production logic changed)

| Operand A (`symptomImpactScreeningCompleted`) | Operand B (`assessmentDate`) | Current production result (`A. Completed?`) | CMS-authorized result (per v1.02 text, Section A above) | Status |
|---|---|---|---|---|
| `false` | `""` (empty) | No | No | Match |
| `true` | `""` (empty) | Yes | Yes | Match |
| `false` | `"2026-01-01"` (truthy date) | **Yes** (via OR) | **NOT_VERIFIED / OPEN QUESTION** — CMS does not state a date alone constitutes "screening completed" | **Mismatch risk** |
| `true` | `"2026-01-01"` | Yes | Yes | Match |
| `null`/`undefined` | `null`/`undefined` | No (both falsy) | No | Match |
| `false` | date carried over from a prior, unrelated symptom assessment within the same record (staleness scenario) | **Yes** (via OR) — the mapper cannot distinguish a fresh date from a stale one | NOT_VERIFIED — CMS does not address staleness; this is an SNS data-quality question, not a CMS-authority question | **Open risk, distinct from the OR-boundary risk above** |

This table is documentation-only per instruction; the production OR
expression at `hopeReportMapper.js:689` is unchanged.

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
