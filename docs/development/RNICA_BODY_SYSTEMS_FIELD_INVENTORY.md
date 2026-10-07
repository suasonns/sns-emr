# RNICA Body Systems — Complete Field Inventory (Deliverable 1)

**Status:** Research/inventory artifact. Implementation freeze remains in effect — nothing in this
document has been applied to the UI. No field, path, control type, HOPE mapping, SFV mapping, or
POC binding has been changed to produce this inventory; it is a direct, mechanical read of the
existing `SECTION_CONFIGS` entries in `src/components/RNICA.jsx` (each system's `cards[].fields[]`
array), cross-referenced against `POC_ENABLED_SECTIONS`.

**Global facts that apply to every field below (not repeated per row):**
- **POC binding:** All 10 body systems are in `POC_ENABLED_SECTIONS`. POC is bound at the
  **section level** (one consolidated "Add to POC" control per system, per the `17724ef` redesign),
  not per field — there is no per-field POC flag in the data model today.
- **Visit-type / role applicability:** Not currently encoded per-field in `SECTION_CONFIGS` (it's a
  section-level/route concern via `routes`/`sidebarConfigItems`, not a field attribute). Listed as
  **unresolved** in the Unresolved Decisions list below rather than guessed.
- **Report/export/audit dependency:** Only fields carrying an explicit `hopeCode` are known, verified
  CMS/HOPE export dependencies (via `hopeReportMapper.js`). Fields without `hopeCode`/`sfv` are not
  currently itemized against every downstream report/export — auditing every non-HOPE field against
  every report is out of scope for a mechanical config read and is listed as an unresolved
  verification task, not silently assumed to be "none."
- **"Not Assessed" behavior:** Plain `radio`/`select`/`checkbox` fields have no explicit tri-state —
  an unanswered field is simply an empty string/false and is visually indistinguishable from "assessed
  as negative" today, **except** fields using the `triState` control (`edema.present`, `chestPain.present`,
  `jvd`) which have an explicit "Not Assessed" state built in. This asymmetry is itself an unresolved
  item (see below).
- **Conditional trigger / dependents:** None of the current fields are conditionally
  shown/hidden today — every field in every card always renders. Progressive disclosure (e.g., "show
  oxygen details only when Oxygen in Use = Yes") does not exist yet; it is 100% new UI behavior, not a
  reorganization of existing behavior. Flagged per-system below where the owner's directive proposes it.

---

## 1. Neurological
*Card order today: Mental Status → BIMS → Communication & Sensory → Psychiatric/Cognitive → Sleep/Rest → Motor Deficit → Notes*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `symptomsDemeanor` | Symptoms / Demeanor | checkboxGroup | Anxiety, Agitation, Peaceful, Confused, Angry, Restless, Depressed, Seizure, Combative, Sundowning, Tremors/twitching, Other | — | — | Multi | Coexistence intended (agitation + tremors, etc.) |
| `consciousness` | Level of Consciousness | radio | Alert, Lethargic, Obtunded, Stuporous, Comatose, Awake, Minimally responsive, Coma | — | — | Single | **Unresolved:** "Alert" and "Awake" both present as separate mutually-exclusive options — overlapping clinical meaning, needs RN clarification |
| `orientation.time/place/person/situation` | Oriented to Time/Place/Person/Situation | 4× checkbox | boolean | — | — | Multi (independent) | Correct as independent checkboxes |
| `orientation.disoriented` | Disoriented | checkbox | boolean | — | — | — | **Unresolved:** can coexist with "Oriented to X" checked — needs exclusivity rule |
| `hopeItems.n0500` | N0500 — Repetition | select | 0–3 | **N0500** | — | Single | HOPE BIMS |
| `hopeItems.n0510` | N0510 — Recall | select | 0–3 | **N0510** | — | Single | HOPE BIMS |
| `hopeItems.n0520` | N0520 — Temporal Orientation | select | 0–3 | **N0520** | — | Single | HOPE BIMS |
| `communication` | Communication | radio | Clear, Impaired, Unable, Normal, Aphasia, Slurred speech, Speech limited to ≤6 words, Other | — | — | Single | **Unresolved:** "Clear"/"Normal" overlap; Aphasia/Slurred speech arguably could coexist with Impaired |
| `hearing` | Hearing | radio | Adequate, Impaired, Deaf, Hearing aid | — | — | Single | "Hearing aid" is a device fact, not a status — semantic mismatch, candidate to split into status + device checkbox |
| `vision` | Vision | radio | Adequate, Impaired, Blind, Corrective lenses | — | — | Single | Same device/status mismatch as Hearing |
| `balance` | Balance | radio | Steady, Unsteady, Unable to stand, Normal, Impaired | — | — | Single | "Steady"/"Normal" overlap |
| `sensoryDeficits` | Sensory Deficits | checkboxGroup | Numbness, Tingling, Decreased sensation, Phantom pain | — | — | Multi | Correct |
| `sensoryAids` | Sensory Aids | checkboxGroup | Glasses, Hearing aids, Other | — | — | Multi | Correct (device list) |
| `cognition` | Cognition Assessment | free text input | — | — | — | — | Free text; feeds Structured Findings ("Cognitive status: ...") |
| `delirium` | Delirium | checkbox | boolean | — | — | — | Correct |
| `seizureHistory` | Seizure History | checkbox | boolean | — | — | — | Correct |
| `psychiatricHistoryType` | Psychiatric History | checkboxGroup | None, Bipolar disorder, OCD, Schizophrenia, Depression, Other | — | — | Multi | **Unresolved — exclusive-None candidate**: "None" can be selected alongside a real diagnosis today |
| `psychiatricHistory` | Psychiatric History Notes | textarea | — | — | — | — | — |
| `sleepRest.sleepPattern` | Sleep Pattern | radio | Normal, Insomnia, Hypersomnia, Fragmented, Somnolence, None identified, Overly drowsy, Excessive sleep, Lack of sleep, Satisfied with sleep | — | — | Single | **Unresolved — largest semantics problem in this system.** 10 mutually-exclusive options include several that plausibly coexist (Insomnia + Overly drowsy; Fragmented + Lack of sleep). Needs RN review before any control-type change. |
| `sleepRest.averageSleepHours` | Average Sleep Hours | number input | — | — | — | — | — |
| `sleepRest.nighttimeSymptoms` | Nighttime Symptoms | checkboxGroup | Pain, Dyspnea, Restlessness, Confusion, Anxiety, Nausea, None | — | — | Multi | Exclusive-None candidate (same pattern as above) |
| `sleepRest.sleepAids` | Sleep Aids / Interventions | checkboxGroup | Medication, Positioning, White noise, Warm milk/tea, Other | — | — | Multi | Correct |
| `sleepRest.response` | Response to Interventions | free text | — | — | — | — | — |
| `sleepRest.restfulness` | Restfulness | radio | Adequate, Inadequate | — | — | Single | Correct |
| `sleepRest.notes` | Sleep Notes | textarea | — | — | — | — | — |
| `motorDeficit` | Motor Deficit Present | checkbox | boolean | — | — | — | Correct trigger candidate for progressive disclosure of Affected Side/Deficit Type |
| `affectedSide` | Affected Side | radio | Left, Right, Bilateral | — | — | Single | Correct; should be conditional on `motorDeficit` per owner directive (not yet implemented) |
| `deficitType` | Deficit Type | checkboxGroup | Hemiparesis, Hemiplegia, Paraparesis, Quadriparesis, Other | — | — | Multi | Correct; same conditional candidate |
| `notes` | Neurological Notes | textarea | — | — | — | — | — |

## 2. Cardiovascular
*Card order today: single "Cardiovascular Assessment" card (all fields flat, no sub-grouping)*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `bpSymptoms` | BP Symptoms | checkboxGroup | Orthostatic, Hypertensive, Hypotensive, Normal | — | — | Multi | Exclusive-None-style candidate ("Normal" alongside others) |
| `pulseSites` | Pulse Sites | checkboxGroup | Apical, Pedal, Radial, Femoral | — | — | Multi | Correct (multiple sites assessed) |
| `pulseQuality` | Pulse Quality | radio | Regular, Strong, Weak, Thready, Bounding, Irregular, Tachycardia, Bradycardia, Absent | — | — | Single | **Unresolved:** conflates rhythm (Regular/Irregular/Tachycardia/Bradycardia) with amplitude (Strong/Weak/Thready/Bounding) — two clinically distinct axes forced into one exclusive choice |
| `edema.present` | Edema Present | **triState** | Yes/No/Not Assessed | — | — | Single | Already has explicit tri-state — good conditional trigger candidate |
| `edema.location` | Edema Location | checkboxGroup | Bilateral LE, Unilateral LE, Sacral, Periorbital, Upper extremities, Generalized | — | — | Multi | Should be conditional on `edema.present = Yes` (not yet implemented) |
| `edema.severity` | Edema Severity | radio | Trace, 1+, 2+, 3+, 4+ | — | — | Single | Same conditional candidate |
| `chestPain.present` | Chest Pain Present | **triState** | Yes/No/Not Assessed | — | — | Single | Conditional trigger candidate |
| `chestPain.type` | Chest Pain Type | free text | — | — | — | — | Should be conditional on `chestPain.present = Yes` |
| `peripheralCirculation` | Peripheral Circulation | free text | — | — | — | — | Free text where a controlled vocabulary may be more consistent — flag for RN input, not changed |
| `heartSounds` | Heart Sounds | free text | — | — | — | — | Same as above |
| `jvd` | JVD | **triState** | Yes/No/Not Assessed | — | — | Single | — |
| `skinColor` | Skin Color | free text | — | — | — | — | **Unresolved — likely duplicate**: `skin.skinColorFinding` (Integumentary) is a structured radio for the same concept; this CV free-text field may be redundant. Needs owner/RN decision on ownership, not removed here. |
| `pacemaker` / `internalDefibrillator` / `varicoseVeins` / `centralVenousLine` / `coolExtremities` / `stasisUlcer` / `heartFailurePresent` | (6 device/condition flags) | checkbox | boolean | — | — | — | Correct, all independent |
| `heartFailureType` | Heart Failure Type | checkboxGroup | Systolic, Diastolic, Unspecified | — | — | Multi (should likely be single) | **Unresolved:** clinically a patient is usually one type — candidate for radio, but flagged not converted |
| `notes` | Cardiovascular Notes | textarea | — | — | — | — | — |

## 3. Respiratory
*Card order today: Respiratory Assessment → Oxygen Therapy → Ventilator/Airway Support → Notes*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `sobSeverity` | SOB Severity | radio | None, Mild, Moderate, Severe, At rest | **—** | **sfv: true** | Single | HOPE J2051B / SFV-triggering field — highest-priority field in this system |
| `treatmentDeclined` | Treatment Declined | checkbox | boolean | — | — | — | — |
| `exertionLevel` | Exertion Level | radio | At rest, Minimal/Moderate/Severe exertion, With speech, Push of speech, Pursed-lip breathing, Other | — | — | Single | **Unresolved:** mixes exertion trigger (At rest/Minimal/...) with breathing technique (Pursed-lip breathing) in one exclusive list |
| `shortnessOfBreathScreened` | Screened for SOB | checkbox | boolean | — | — | — | Part of SFV screening workflow |
| `screeningDate` | SOB Screening Date | date | — | — | — | — | — |
| `treatmentInitiated` | Treatment for SOB Initiated | checkbox | boolean | — | — | — | — |
| `treatmentDate` | SOB Treatment Date | date | — | — | — | — | — |
| `lungSounds` | Lung Sounds | checkboxGroup | Clear, Crackles, Wheezes, Rhonchi, Diminished, Absent, Stridor, Pleural rub, Rales | — | — | Multi | "Clear" + others is an exclusive-None-style pattern (can a lung field be Clear + Crackles simultaneously — yes, per lobe, but UI doesn't distinguish sides) — flagged, not changed |
| `respirations` | Respiration Pattern | checkboxGroup | Regular, Normal, Irregular, Labored, Cheyne-Stokes, Apneic episodes, Kussmaul, Agonal, Tachypnea, Bradypnea, Orthopnea | — | — | Multi | **Unresolved:** "Regular"/"Normal"/"Irregular" as independently-selectable checkboxes is very likely meant to be exclusive |
| `coughType` | Cough Type | select | None, Productive, Non-productive, Hemoptysis, Barrel chest | — | — | Single | "Barrel chest" is a chest-wall finding, not a cough type — semantic mismatch flagged |
| `sputumCharacter` | Sputum Character | free text | — | — | — | — | — |
| `oxygenTherapy.inUse` | Oxygen in Use | checkbox | boolean | — | — | — | **Primary progressive-disclosure trigger** for the rest of the Oxygen Therapy card — not yet implemented |
| `oxygenTherapy.type` | Delivery Type | select | Nasal cannula, Simple mask, Non-rebreather, Venturi mask, High flow | — | — | Single | Should be conditional |
| `oxygenTherapy.litersPerMinute` | Liters/Minute | number | — | — | — | — | Should be conditional |
| `oxygenTherapy.hoursPerDay` | Hours/Day | text input | — | — | — | — | Should be conditional |
| `oxygenTherapy.deliveryMode` | Delivery Mode | radio | Continuous, PRN | — | — | Single | Should be conditional |
| `oxygenTherapy.onRoomAir` | On Room Air | checkbox | boolean | — | — | — | **Unresolved:** logically mutually exclusive with `inUse = true` (can't be both on room air and on oxygen) — no current guard |
| `oxygenTherapy.satOnO2` | SpO2 on O2 | number | — | — | — | — | Should be conditional |
| `ventilator.shortTermVentilator` / `longTermVentilator` | Ventilator flags | 2× checkbox | boolean | — | — | Multi | **Unresolved:** should likely be mutually exclusive (short-term vs. long-term), currently independent checkboxes |
| `ventilator.ventilatorTypeAndSettings` / `tracheostomyType` / `tracheostomySize` | Vent/trach detail | free text ×3 | — | — | — | — | Should be conditional on ventilator/trach presence — no explicit "Ventilator Present"/"Tracheostomy Present" boolean exists today; owner directive assumes one exists — **flag: needs a trigger field to be added, or existing flags repurposed** |
| `notes` | Respiratory Notes | textarea | — | — | — | — | — |

## 4. Infection
*Card order today: Allergies (custom) → Immune Status → Infection Assessment → Additional Findings*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| *(Allergies)* | Allergies | `customRenderer: patientAllergies` | — | — | — | — | Not a plain field — custom widget, out of scope for control-type review |
| `immunosuppressed` | Immunosuppressed | checkbox | boolean | — | — | — | — |
| `precautions` | Precautions | checkboxGroup | Standard, Contact, Droplet, Airborne | — | — | Multi | Correct (can combine e.g. Contact + Droplet) |
| `antibioticResistantInfection` | Antibiotic-Resistant Infection (current) | checkboxGroup | None, MRSA, C. difficile, Other | — | — | Multi | Exclusive-None candidate |
| `historyOfResistantInfections` | History of Resistant Infection | checkboxGroup | None, MRSA, C. difficile, Other | — | — | Multi | Exclusive-None candidate |
| `currentInfections` | Current Active Infection | checkboxGroup | None, Sepsis, UTI, Respiratory tract, IV site, Wound, HIV-related, Pressure area, Other | — | — | Multi | Feeds Structured Findings; exclusive-None candidate |
| `antibioticUse` | Antibiotic Use | checkbox | boolean | — | — | — | — |
| `temperature` | Temperature | number | — | — | — | — | Duplicate-candidate: `vitals.temperature` already exists in the Vitals section — **unresolved ownership question** |
| `recurrentInfection` | Recurrent Infection | checkbox | boolean | — | — | — | — |
| `infectionHistory` | Infection History | textarea | — | — | — | — | — |
| `notes` | Other Observations / Notes | textarea | — | — | — | — | — |

## 5. Gastrointestinal
*Card order today: Constipation Auto-Assess (custom) → GI Symptoms → Abdominal/Bowel → Feeding Devices*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `nausea` | Nausea | radio | None, Mild, Moderate, Severe | — | **sfv: true** | Single | SFV-triggering |
| `vomiting` | Vomiting | radio | None, Mild, Moderate, Severe | — | **sfv: true** | Single | SFV-triggering |
| `vomitingOccurrences24h` | Vomiting Occurrences (24h) | number | — | — | — | — | Should be conditional on Vomiting ≠ None |
| `diarrhea` | Diarrhea | radio | None, Mild, Moderate, Severe | — | **sfv: true** | Single | SFV-triggering |
| `constipation` | Constipation | radio | None, Mild, Moderate, Severe | — | **sfv: true** | Single | SFV-triggering; also has an auto-suggestion custom renderer above it |
| `bowelSounds` | Bowel Sounds | radio | Normal, Hyperactive, Hypoactive, Absent | — | — | Single | Correct |
| `abdomen` | Abdomen | radio | Soft, Firm, Tympanic, Distended, Tender, Nontender, Rigid | — | — | Single | **Unresolved:** "Tender"/"Nontender" and "Soft"/"Firm"/"Rigid" are two different clinical axes forced into one exclusive list |
| `ascites` | Ascites | checkbox | boolean | — | — | — | — |
| `abdominalGirth` | Abdominal Girth | free text | — | — | — | — | — |
| `stoolCharacter` | Stool | checkboxGroup | Normal, Bloody, Colostomy, Ileostomy | — | — | Multi | **Unresolved:** "Colostomy"/"Ileostomy" are device facts, not stool characteristics — mixed with `ostomy.present`/`ostomy.type` below (possible duplicate) |
| `bowelStatus` | Bowel Status | radio | Regular, Irregular, Impaction, Continent, Incontinent, Bowel/bladder program | — | — | Single | Conflates regularity with continence — two axes |
| `bowelFrequency` | Bowel Frequency | free text | — | — | — | — | — |
| `lastBM` | Last BM Date | date | — | — | — | — | Feeds the Constipation auto-suggestion custom renderer |
| `reasonBowelRegimenNotInitiated` | Reason Bowel Regimen Not Initiated | textarea | — | — | — | — | — |
| `feedingTube.present` | Feeding Tube Present | checkbox | boolean | — | — | — | Conditional trigger candidate for `feedingTube.type` |
| `feedingTube.type` | Tube Type | select | NG, PEG, PEJ, G-tube, J-tube | — | — | Single | Should be conditional |
| `ostomy.present` | Ostomy Present | checkbox | boolean | — | — | — | Conditional trigger; **possible duplicate with `stoolCharacter` Colostomy/Ileostomy options above** |
| `ostomy.type` | Ostomy Type | select | Colostomy, Ileostomy, Urostomy | — | — | Single | Should be conditional |
| `notes` | GI Notes | textarea | — | — | — | — | — |

## 6. Nutrition
*Card order today: Anthropometric Reference (custom) → Weight Loss Auto-Calc (custom) → Nutritional Assessment → NPO/Artificial Feeding → Oral Cavity*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `weightLossPastSixMonths` | Weight Loss (past 6 months) | free text | — | — | — | — | Feeds Structured Findings; free text where a number+unit pair may be more consistent |
| `appetite` | Appetite | radio | Good, Fair, Poor, Anorexic | — | — | Single | Correct |
| `dietType` | Diet Type | free text | — | — | — | — | — |
| `fluidIntake` | Fluid Intake | radio | Adequate, Decreased, Minimal | — | — | Single | Correct |
| `swallowingIssues` | Swallowing Issues | checkboxGroup | Dysphagia, Aspiration risk, Pocketing, Coughing with swallowing, None | — | — | Multi | Exclusive-None candidate; **possible duplicate/overlap with GI dysphagia concerns** — owner directive explicitly calls this out ("do not duplicate GI swallowing findings") |
| `oralMucosa` | Oral Mucosa | free text | — | — | — | — | Possible overlap with `oralCavityFindings` below |
| `dentures.upper` / `dentures.lower` | Dentures | 2× checkbox | boolean | — | — | Multi | Correct |
| `nutritionalSupplements` | Nutritional Supplements | free text | — | — | — | — | — |
| `notes` | Nutrition Notes | textarea | — | — | — | — | — |
| `npoStatus` | NPO Status | radio | Not NPO, NPO, NPO except meds, Modified/thickened liquids only | — | — | Single | Correct |
| `artificialFeeding` | Artificial Feeding/Access Devices | checkboxGroup | PEG, NG, J-tube, Pump, TPN, None | — | — | Multi | **Unresolved — likely duplicate** of GI's `feedingTube.type`/`.present` — two separate places record the same device |
| `oralCavityFindings` | Oral Cavity Findings | checkboxGroup | Edentulous, Stomatitis, Thrush, Poor dentition, Normal | — | — | Multi | Exclusive-None-style ("Normal" + a finding); overlaps `oralMucosa` free text above |

## 7. Endocrine
*Card order today: Endocrine Impairment → Thyroid Assessment → Diabetes Management → Endocrine Symptoms & Treatment*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `endocrineImpairment` | Impairment | checkboxGroup | Thyroid, Parathyroid, Pituitary, Adrenal, Pancreas, None | — | — | Multi | Exclusive-None candidate; drives conditional disclosure of Thyroid/Diabetes cards (not yet implemented) |
| `thyroid.assessment` | Thyroid | radio | Normal, Enlarged, Tender, Nodular, Not assessed | — | — | Single | Has its own explicit "Not assessed" option (inconsistent pattern vs. plain radios elsewhere with no such option) |
| `thyroid.notes` | Thyroid Notes | textarea | — | — | — | — | — |
| `diabetes.type` | Diabetes Type | radio | Type 1, Type 2, Not diabetic, Unknown | — | — | Single | Feeds Structured Findings; correct trigger candidate |
| `diabetes.dependency` | Diabetes Dependency | radio | Insulin-dependent, Non-insulin-dependent, Glucose-management concern, Not applicable | — | — | Single | Should be conditional on `diabetes.type` ≠ Not diabetic |
| `diabetes.glucoseMonitoring` | Glucose Monitoring Frequency | select | None, Daily, BID, TID, QID, Weekly | — | — | Single | Should be conditional |
| `diabetes.lastHbA1c` / `.lastHbA1cDate` | Last HbA1c value/date | free text / date | — | — | — | — | Should be conditional |
| `diabetes.insulinType` / `.insulinDose` | Insulin Type/Dose | free text ×2 | — | — | — | — | Should be conditional on dependency = Insulin-dependent |
| `diabetes.oralHypoglycemics` | Oral Hypoglycemics | checkboxGroup | Metformin, Sulfonylurea, DPP-4 inhibitor, SGLT2 inhibitor, None | — | — | Multi | Exclusive-None candidate; should be conditional |
| `endocrineSymptoms` | Symptoms Present | checkboxGroup | Fatigue, Weight changes, Temperature intolerance, Hair/skin changes, Polydipsia, Polyuria, Tremors | — | — | Multi | Correct |
| `currentEndocrineMeds` | Current Treatment | checkboxGroup | Levothyroxine, Insulin, Oral hypoglycemics, Corticosteroid replacement, Other, None | — | — | Multi | **Unresolved — likely duplicate** with `diabetes.insulinType`/`oralHypoglycemics` above (insulin/oral hypoglycemics recorded twice) |
| `notes` | Other Observations / Notes | textarea | — | — | — | — | — |

## 8. Genitourinary
*Card order today: Urinary Status → Catheter Assessment → Urine Output → Reproductive Concerns → Bladder Management*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `urinaryStatus` | Continence | radio | Continent, Stress/Urge/Functional/Total incontinence, Catheterized, Bladder program, Urostomy, Retention, Painful urination, Nocturia | — | — | Single | **Unresolved — major duplicate risk**: "Catheterized" here overlaps entirely with the separate `catheter.present`/`catheter.type` card below; "Urostomy" here overlaps `ostomy.type` in GI |
| `frequency` | Frequency | free text | — | — | — | — | — |
| `urineCharacteristics` | Urine | checkboxGroup | Clear, Cloudy, Pale, Blood, Odor | — | — | Multi | "Clear"/"Cloudy"/"Pale" plausibly exclusive; "Blood"/"Odor" independent — mixed axes |
| `urineColor` | Urine Color | free text | — | — | — | — | Overlaps `urineCharacteristics` (Pale/Clear are color-adjacent) |
| `catheter.present` | Catheter Present | checkbox | boolean | — | — | — | Conditional trigger for the rest of this card (not yet implemented); duplicate risk with `urinaryStatus = Catheterized` above |
| `catheter.type` | Type | select | None, Foley, Suprapubic, Condom, Intermittent, Urostomy | — | — | Single | Should be conditional |
| `catheter.size` / `.insertionDate` / `.lastChangeDate` | Catheter detail | text/date ×3 | — | — | — | — | Should be conditional |
| `catheter.condition` | Condition | radio | Patent, Blocked, Leaking | — | — | Single | Should be conditional |
| `catheter.urineCharacteristics` | Urine Characteristics (Catheter) | checkboxGroup | Clear, Cloudy, Amber, Dark, Hematuria, Sediment, Foul odor | — | — | Multi | **Duplicate** of the section-level `urineCharacteristics` field above, scoped to catheter — intentional per current design (catheter-specific), but flagged since the owner directive doesn't distinguish the two |
| `catheter.irrigation.solution/.frequency/.duration` | Irrigation detail | text ×3 | — | — | — | — | — |
| `catheterCare` | Catheter Care | textarea | — | — | — | — | — |
| `urineOutput` | Output | radio | Adequate, Decreased, Anuria, Polyuria | — | — | Single | Correct |
| `twentyFourHourVolume` | 24-Hour Volume | number | — | — | — | — | — |
| `reproductive.concerns` | Concerns | checkboxGroup | Vaginal bleeding, Vaginal discharge, Penile discharge, Scrotal edema, Testicular mass | — | — | Multi | Correct (sex-specific options mixed in one list — UI-level consideration, not a data problem) |
| `reproductive.notes` | Reproductive Notes | textarea | — | — | — | — | — |
| `bladderManagement` | Interventions | checkboxGroup | Bladder training, Scheduled toileting, Pelvic floor exercises, External collection device | — | — | Multi | Correct |
| `notes` | GU Notes | textarea | — | — | — | — | — |

## 9. Musculoskeletal
*Card order today: Musculoskeletal Assessment → Mobility Assessment → Fall History & Notes*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| `weakness` | Weakness | radio | None, Mild, Moderate, Severe, Paralysis | — | — | Single | Correct |
| `rigidity` | Rigidity | radio | None, Mild, Moderate, Severe | — | — | Single | **Unresolved — duplicate**: `rigidityPresent` (below) is a separate boolean for the same concept |
| `rigidityPresent` | Rigidity Present (severity not documented) | checkbox | boolean | — | — | — | Duplicate of `rigidity` above; likely legacy field kept for back-compat — needs owner confirmation before any consolidation |
| `contractures` | Contractures | radio | None, Mild, Moderate, Severe | — | — | Single | Same duplicate pattern as Rigidity |
| `contracturesPresent` | Contractures Present (severity not documented) | checkbox | boolean | — | — | — | Duplicate of `contractures` |
| `contracturesLocation` | Contracture Location | checkboxGroup | Bilateral LE, Unilateral LE, Upper extremities, Hands/fingers, Neck/spine, Generalized | — | — | Multi | Should be conditional on Contractures/`contracturesPresent` |
| `romLimitations` | ROM Loss Location | checkboxGroup | Upper extremities, Lower extremities, Neck/spine, Hands/fingers, Generalized | — | — | Multi | — |
| `musculoskeletalIssues` | Issues | checkboxGroup | Joint swelling, Spasms/cramps, Amputation, Prosthesis, ROM loss, None | — | — | Multi | Exclusive-None candidate; "ROM loss" here duplicates the dedicated `romLimitations` field above |
| `paralysis` | Disability | radio | None, Paraplegia, Quadriplegia, Right/Left hemiplegia, Right/Left hemiparesis | — | — | Single | **Unresolved — duplicate** with Neurological's `deficitType`/`affectedSide` (Hemiparesis/Hemiplegia/Left/Right) — same clinical fact recorded in two body systems |
| `gait` | Gait | radio | Normal, Unsteady, Shuffling, Unable | — | — | Single | Correct |
| `assistiveDevices` | Assistive Devices | checkboxGroup | Walker, Wheelchair, Cane, Crutches, Hospital bed, Hoyer lift, None | — | — | Multi | Exclusive-None candidate; owner directive says Falls Assessment (separate module) also owns "Assistive Devices" — **cross-module duplicate, explicitly flagged by the owner's own directives** |
| `mobility.ambulatoryStatus` | Ambulatory Status | radio | Independent, Supervised, Assisted, Dependent, Bedbound | — | — | Single | Correct |
| `mobility.endurance` | Endurance | radio | Good, Fair, Poor | — | — | Single | Correct |
| `mobility.transferAbility` | Transfer Ability | radio | Independent, Standby assist, 1-person assist, 2-person assist, Hoyer lift | — | — | Single | Correct |
| `strength` | Strength | radio | Normal, Decreased, Absent | — | — | Single | Correct |
| `balance` | Balance | radio | Normal, Impaired | — | — | Single | **Unresolved — duplicate**: Neurological already has its own `balance` field (Steady/Unsteady/Unable to stand/Normal/Impaired) — two body systems each capture "balance" independently with different option sets |
| `painWithMovement` | Pain with Movement | radio | None, Mild, Moderate, Severe | — | — | Single | Possible overlap with the dedicated Pain Assessment module |
| `fallHistory.fallsLast90Days` | Falls in Last 90 Days | number | — | — | — | — | Owner directive: Falls Assessment is a separate, protected module — **this field duplicates that ownership inside Musculoskeletal** |
| `fallHistory.fallInjuries` | Fall Injuries | free text | — | — | — | — | Same duplicate-ownership concern |
| `notes` | Musculoskeletal Notes | textarea | — | — | — | — | — |

## 10. Skin / Wounds
*Card order today: Skin Assessment (consolidated, includes Body Map) → Braden Scale → Wound Documentation (custom)*

| Field ID (path) | Label | Control | Options | HOPE | SFV | Single/Multi | Notes |
|---|---|---|---|---|---|---|---|
| *(Skin Assessment card carries `hopeCode: "M1190"` at the card level)* | | | | **M1190** | — | — | Card-level HOPE tag, not itemized per field |
| `skinConditionsPresent` | Skin Conditions Present | checkbox | boolean | — | — | — | — |
| `skinStatus` | Skin Status | checkboxGroup | Intact, Dry, Fragile, Edematous, Bruising, Rash, Jaundice, Cyanotic, Mottled | — | — | Multi | **Unresolved — overlaps** `skinMoisture`, `skinColorFinding`, and `skinEdema` (Dry/Jaundice/Cyanotic/Mottled/Edematous are each also captured as their own dedicated radio field below) |
| `skinTurgor` | Skin Turgor | radio | Good, Fair, Poor, Tenting | — | — | Single | Correct |
| `skinMoisture` | Skin Moisture | radio | Dry, Moist, Diaphoretic | — | — | Single | Duplicate of "Dry" option inside `skinStatus` above |
| `skinTemperature` | Skin Temperature | radio | Warm, Cool, Hot | — | — | Single | Correct |
| `skinColorFinding` | Skin Color | radio | Normal, Pale, Cyanotic, Jaundiced, Mottled, Flushed | — | — | Single | Duplicate of Cyanotic/Jaundice/Mottled inside `skinStatus`; also possible duplicate with Cardiovascular's free-text `skinColor` field |
| `skinEdema.severity` | Edema | radio | None, 1+, 2+, 3+, 4+ | — | — | Single | Duplicate concept with Cardiovascular's `edema.present`/`.severity`/`.location` (two body systems each record edema independently, different scales — CV uses Trace/1–4+, Skin uses None/1–4+) |
| `skinEdema.location` | Edema Location | free text | — | — | — | — | Should be conditional on severity ≠ None |
| `additionalSkinFindings` | Additional Skin Findings | checkboxGroup | Bruising, Skin Tears, Excoriation, Pruritus, Dry Scaling, None | — | — | Multi | Exclusive-None candidate; "Bruising" duplicates `skinStatus` above |
| `braden.sensoryPerception/.moisture/.activity/.mobility/.nutrition/.frictionShear` | Braden subscales | 6× select | Ordinal 1–4 (or 1–3 for Friction & Shear) | — | — | Single each | Standardized instrument — leave structure untouched |
| `pressureInjuryRisk` | Pressure Injury Risk | radio | Low (19-23), Moderate (15-18), High (≤14) | — | — | Single | Should be derived/auto-calculated from Braden subscale sum rather than a separately-selected radio — **flagged as a data-integrity risk** (nurse could pick a risk level inconsistent with the entered subscale scores); not changed here |
| *(Wound Documentation)* | Wounds | `customRenderer: woundList` | — | — | — | — | Structured wound records — out of scope for control-type review |

---

## Cross-System Duplicate/Ownership Flags (summary, all sourced from the table rows above)

| Concept | Recorded in | Conflict |
|---|---|---|
| Skin color | Cardiovascular (`skinColor`, free text) **and** Skin (`skinColorFinding`, structured radio) | Same clinical fact, two owners, two representations |
| Edema | Cardiovascular (`edema.*`, Trace/1+–4+) **and** Skin (`skinEdema.*`, None/1+–4+) | Same clinical fact, two owners, two scales |
| Balance | Neurological (`balance`) **and** Musculoskeletal (`balance`) | Same field name, different option sets, two systems |
| Hemiparesis/Hemiplegia + side | Neurological (`deficitType`/`affectedSide`) **and** Musculoskeletal (`paralysis`) | Same clinical fact recorded twice |
| Assistive devices | Musculoskeletal (`assistiveDevices`) **and** the separate, protected Falls Assessment module (per owner directive) | Cross-module duplicate the owner has already flagged |
| Falls history | Musculoskeletal (`fallHistory.*`) **and** the separate, protected Falls Assessment module | Musculoskeletal currently holds fields that belong to Falls' protected ownership |
| Temperature | Infection (`temperature`) **and** Vitals (`vitals.temperature`) | Same vital sign, two locations |
| Feeding/ostomy devices | Gastrointestinal (`feedingTube.*`, `ostomy.*`) **and** Nutrition (`artificialFeeding`) **and** GI's own `stoolCharacter` (Colostomy/Ileostomy) | Same devices referenced in up to three places |
| Catheter/Urostomy | Genitourinary (`catheter.*`) **and** `urinaryStatus` option list (Catheterized, Urostomy) **and** GI `ostomy.type` (Urostomy) | Same device across two-to-three fields/systems |
| Insulin / oral hypoglycemics | Endocrine `diabetes.insulinType`/`.oralHypoglycemics` **and** `currentEndocrineMeds` | Same treatment recorded twice within the same system |
| Rigidity / Contractures severity vs. presence | Musculoskeletal (`rigidity` + `rigidityPresent`, `contractures` + `contracturesPresent`) | Two fields per concept within the same system |
| Swallowing/dysphagia | Nutrition (`swallowingIssues`) **and** GI (implied by hospice decline guidance) | Owner directive already names this exact pair as a duplication risk |

**None of these duplicates are resolved in this document.** Per the freeze, no field has been removed,
merged, or renamed. Each is listed for owner + RN adjudication (keep both with distinct scope, consolidate
to one owner with a linked read-only summary elsewhere, or mark one legacy/deprecated) before any change is made.
