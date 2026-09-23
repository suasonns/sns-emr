# HOPE Item-Code Conflict Matrix (Phase 2, independent re-trace)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — see `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-002).

**Scope:** every HOPE item code that appears in more than one semantic
context across `backend/app/domain/forms/form_registry.py`,
`sns-emr-frontend/src/components/RNICA.jsx`,
`sns-emr-frontend/src/intake/hopeReportMapper.js`, and any other repository
file surfaced by a full-tree `Select-String` scan for item-code literals.

**Commit inspected:** `16264cf`.

---

## Conflict 1 — N0500 / N0510 / N0520 (CONFIRMED, and wider than previously reported)

Two mutually exclusive semantics are implemented for the same three codes,
in **five** places, spanning both frontend and backend.

| Usage site | File:line | Semantics asserted there |
|---|---|---|
| Registry declaration | `backend/app/domain/forms/form_registry.py:408-412` (`HOPE_MEDICATION_ITEM_CODES`) | Medication-section items |
| Exporter | `sns-emr-frontend/src/intake/hopeReportMapper.js:633-635` (+ inputs `:529-530`) | N0500 = "Scheduled Opioid", N0510 = "PRN Opioid", N0520 = "Bowel Regimen" |
| RNICA form config | `sns-emr-frontend/src/components/RNICA.jsx:9030-9033` (card title "BIMS (Brief Interview for Mental Status)", `hopeCode: "N0500-N0520"`) | N0500 = BIMS Repetition, N0510 = BIMS Recall, N0520 = BIMS Temporal Orientation |
| RNICA validation warning | `RNICA.jsx:1048-1050` ("HOPE N0500: BIMS repetition required"); default state `RNICA.jsx:575` | BIMS |
| Body-system config | `sns-emr-frontend/src/config/bodySystems.js:20` (`hope: ["N0500","N0510","N0520"]` on the neurological system) | BIMS / neurological |
| Backend AI concept mappings | `backend/app/services/evidence/structured_findings.py:1224-1270` (`NEURO_N0500_0` … `NEURO_N0520_3`, writing `hopeItems.n0500/.n0510/.n0520`) | BIMS ("None"/"One word"/"Two words"/"Three words"; "Year/Month/Day of week correct") |
| Generated frontend registry | `sns-emr-frontend/src/components/rn-ica/structuredFindingRegistry.generated.js:1748-1794` | BIMS (mirrors the above) |
| HOPE report remediation links | `sns-emr-frontend/src/intake/HopeReport.jsx:17-18` (`N0510 → "Open physician orders"`, `N0520 → "Open bowel-regimen order"`) | Medication/orders |
| Seed script | `backend/scripts/populate_loren_shields.py:297` (`hopeItems`) vs `:563-565` (`scheduledOpioid`/`prnOpioid`/`bowelRegimen`) | Both semantics written into the same synthetic record |

**Conflict description.** The neurological path
`neurological.hopeItems.n0500/.n0510/.n0520` is written by real UI selects
(`RNICA.jsx:9031-9033`), by the AI structured-finding engine
(`structured_findings.py:1226-1270`), and is warning-gated
(`RNICA.jsx:1049-1050`) — yet **no exporter ever reads it**. Conversely the
exporter reads `medications.scheduledOpioid/.prnOpioid/.bowelRegimen`
(`hopeReportMapper.js:529-530, 633-635`), a section that is **not in**
`FORM_REGISTRY` (`RNICA.jsx:242-249`, 27 sections, no `medications`) and has
no writer anywhere in application code. Both semantics cannot be correct for
the same CMS code triplet; the repository provides no authority that
adjudicates which is.

| Sub-row | Status |
|---|---|
| N0500 dual semantics (BIMS vs Scheduled Opioid) | CONFLICTING |
| N0510 dual semantics (BIMS Recall vs PRN Opioid) | CONFLICTING |
| N0520 dual semantics (BIMS Temporal Orientation vs Bowel Regimen) | CONFLICTING |
| `neurological.hopeItems.*` captured but never exported | PRESENT_NOT_HARVESTED |
| `medications.*` exported but never captured | PRESENT_NOT_WIRED |
| Which semantics is CMS-correct | REQUIRES_AUTHORITY_REVIEW (no repository evidence; external spec not accessible this pass) |

## Conflict 2 — M1190 on two sections

| Usage site | File:line | Semantics |
|---|---|---|
| Sidebar tagging | `RNICA.jsx:209` (`performanceStatus` … `hope: ["M1190", …]`) | Performance status |
| Registry | `form_registry.py:402-406` (`HOPE_SKIN_ITEM_CODES`) | Skin |
| Exporter | `hopeReportMapper.js:625` (`skin.skinConditionsPresent`) | Skin |

Status: **CONFLICTING** — the sidebar completion indicator will mark the
Performance Status screen incomplete/complete based on a skin item, because
`getHopeAdmissionStatus` evaluates each sidebar section against the codes it
declares (`hopeReportMapper.js:689-697`).

## Conflict 3 — J0050 on two fields

| Usage site | File:line | Semantics |
|---|---|---|
| Diagnoses field tag | `RNICA.jsx:8925` (`Terminal Prognosis`, `hopeCode: "J0050"`) | Prognosis window |
| Sidebar tagging | `RNICA.jsx:208` (`diagnoses` … `hope: ["I0010","J0050"]`) | Diagnoses screen |
| Exporter | `hopeReportMapper.js:609` reads `imminentDeath.appearsThreeDaysOrLess` | Imminent death |
| Imminent-death module | `RNICA.jsx:9379-9383` (indicators) | Imminent death |

Status: **CONFLICTING** — the Diagnoses screen is credited/penalized for a
J0050 answer it does not own; the value actually exported comes from a
different module.

## Conflict 4 — J2051 granularity

| Usage site | File:line | Semantics |
|---|---|---|
| Registry | `form_registry.py:386-394` declares `J2051A` … `J2051H` | Per-symptom codes |
| Exporter | `hopeReportMapper.js:617` emits one item with `code: "J2051"` whose entries are lettered A-H (`symptomEntries` `:384-393`) | Single grouped code |
| SFV mirror | `RNICA.jsx:9403-9410` tags the SFV copies `J2053A` … `J2053H` | Per-symptom codes |

Status: **CONFLICTING** — a consumer keyed on `J2051A` (as the registry
declares) finds no such item in the exporter output; `getHopeAdmissionStatus`
treats unknown codes as "not a gap" (`hopeReportMapper.js:685`), so the
mismatch fails silently.

## Conflict 5 — I0000 group code not in any registry list

| Usage site | File:line |
|---|---|
| Exporter | `hopeReportMapper.js:603` (`code: "I0000"`, "Comorbidities and Co-existing Conditions") |
| Registry | absent from `HOPE_DIAGNOSIS_ITEM_CODES` (`form_registry.py:371-376`) |

Status: **NOT_VERIFIED** — whether `I0000` is a real CMS item code or an
internal grouping label cannot be determined from repository evidence.

## Conflict 6 — comorbidity codes emitted but not declared

`hopeReportMapper.js:440-453` emits I0100, I0900, I0950, I1101, I1510,
I2102, I2900, I2910, I4501, I4801, I5150, I5401 (each mirrored by a checkbox
at `RNICA.jsx:2499-2512` / `:2636`), none of which appears in
`HOPE_DIAGNOSIS_ITEM_CODES` (`form_registry.py:371-376`, which lists only
I0010, I0600, I6202, I8005).

Status: **CONFLICTING** (registry inventory is a strict subset of the
exporter inventory; the registry is therefore not a reliable declaration of
what RN ICA harvests).

## Conflict 7 — Z0400 declared but never emitted

| Usage site | File:line |
|---|---|
| Registry | `form_registry.py:416` |
| Exporter | no occurrence of `"Z0400"` anywhere in `sns-emr-frontend/src` (full-tree scan) |

Status: **PRESENT_NOT_HARVESTED**.

---

## Scan method (reproducible)

```
Get-ChildItem -Recurse -Include *.js,*.jsx,*.py,*.ts,*.tsx -File . |
  Where-Object { $_.FullName -notmatch 'node_modules|\.venv|dist|build' } |
  Select-String -Pattern 'N0500|N0510|N0520'
```
(and equivalents for `M1190`, `J0050`, `J2051`, `I0000`, `Z0400`).

**Counts:** 7 distinct item-code conflicts; 3 codes (N0500/N0510/N0520) with
fully contradictory clinical semantics implemented simultaneously in
frontend UI, frontend exporter, and backend AI concept mappings.
